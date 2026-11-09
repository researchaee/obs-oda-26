"""Refresh market quotations embedded in observatory-data.json."""

from __future__ import annotations

import base64
import io
import json
import math
import re
import secrets
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, urlencode, urljoin
from urllib.request import Request, urlopen

import requests
import websocket


ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = ROOT / "observatorio-maizoryza" / "observatory-data.json"
ISMEA_URL = "https://www.ismeamercati.it/flex/cm/pages/ServeBLOB.php/L/IT/IDPagina/849/UT/systemPrint"
SEVILLA_URL = "https://lonjadesevilla.com/consultor-precios/"
SEVILLA_ENDPOINT = "https://lonjadesevilla.com/wp-content/themes/salient-child/ajaxPrecios.php"
EU_CEREALS_URL = "https://agridata.ec.europa.eu/extensions/DashboardCereals/ExtCerealsPrice.html"
EU_CEREALS_APP_ID = "5e97b24c-b841-494a-b34b-119ac2caa765"
EU_CEREALS_SHEET_ID = "cf43a3de-5293-4e88-99b5-a2c0737644ef"
EU_CEREALS_TABLE_ID = "FmjsK"
EU_CEREALS_COUNTRIES = {
    "Bulgaria": ("BG", "Bulgária"),
    "France": ("FR", "França"),
    "Greece": ("EL", "Grécia"),
    "Portugal": ("PT", "Portugal"),
}
EU_CEREALS_PRODUCTS = {
    "Breadmaking common wheat": ("soft_wheat", "Trigo mole panificável"),
    "Breadmaking common wheat - TVT": ("soft_wheat", "Trigo mole panificável — TVT"),
    "Durum wheat": ("durum_wheat", "Trigo duro"),
    "Feed barley": ("barley", "Cevada para ração"),
    "Feed maize": ("maize", "Milho para ração"),
    "Feed oats": ("oats", "Aveia para ração"),
    "Feed rye": ("rye", "Centeio para ração"),
    "Feed wheat": ("soft_wheat", "Trigo para ração"),
    "Malting barley": ("barley", "Cevada para malte"),
    "Milling oats": ("oats", "Aveia"),
    "Milling rye": ("rye", "Centeio"),
    "Milling wheat": ("soft_wheat", "Trigo mole"),
    "Rye of breadmaking quality": ("rye", "Centeio panificável"),
    "Triticale": ("triticale", "Triticale"),
}
USER_AGENT = "Observatorio-de-Precos-do-Arroz/1.0"


class TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[str]]] = []
        self.table: list[list[str]] | None = None
        self.row: list[str] | None = None
        self.cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            self.table = []
            self.tables.append(self.table)
        elif tag == "tr" and self.table is not None:
            self.row = []
            self.table.append(self.row)
        elif tag in ("td", "th") and self.row is not None:
            self.cell = []

    def handle_data(self, data: str) -> None:
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in ("td", "th") and self.cell is not None and self.row is not None:
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        elif tag == "tr":
            self.row = None
        elif tag == "table":
            self.table = None


def fetch(url: str, data: bytes | None = None) -> str:
    headers = {"User-Agent": USER_AGENT}
    if data is not None:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    request = Request(url, data=data, headers=headers)
    with urlopen(request, timeout=30) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset)


def parse_tables(document: str) -> list[list[list[str]]]:
    parser = TableParser()
    parser.feed(document)
    parser.close()
    return parser.tables


def unaccent(value: str) -> str:
    return "".join(
        char for char in unicodedata.normalize("NFD", value) if unicodedata.category(char) != "Mn"
    ).casefold()


def parse_number(value: str) -> float | None:
    normalized = value.replace("\xa0", " ").replace("−", "-")
    match = re.search(r"-?[\d.]+(?:,\d+)?", normalized)
    if not match:
        return None
    number = match.group()
    if "," in number:
        number = number.replace(".", "").replace(",", ".")
    return float(number)


def parse_ismea_product(raw_product: str) -> tuple[str, str] | None:
    parts = [part.strip() for part in raw_product.split(" - ")]
    first = unaccent(parts[0])
    second = parts[1] if len(parts) > 1 else ""
    second_normalized = unaccent(second)

    if first == "riso":
        variety = second.removesuffix(" - n.s.")
        if variety == "S.Andrea":
            variety = "Sant'Andrea"
        return "rice", variety
    if first.startswith("mais"):
        return "maize", "Milho importado" if "estero" in first else "Milho nacional"
    if first.startswith("frumento duro"):
        crop = "durum_wheat"
        label = "Trigo duro"
    elif first.startswith("frumento tenero"):
        crop = "soft_wheat"
        label = "Trigo mole"
    elif first.startswith("orzo"):
        return "barley", "Cevada importada" if "estero" in first else "Cevada nacional"
    elif first.startswith("avena"):
        return "oats", "Aveia importada" if "estera" in first or "estero" in first else "Aveia nacional"
    elif first.startswith("triticale"):
        return "triticale", "Triticale"
    elif first.startswith("girasole"):
        return "sunflower", "Girassol"
    else:
        return None

    quality = {
        "buono mercantile": "mercantil de boa qualidade",
        "fino": "fino",
        "mercantile": "mercantil",
        "comunitario": "importação comunitária",
        "non comunitario": "importação extracomunitária",
    }.get(second_normalized, second)
    if "estero" in first:
        origin = parts[2] if len(parts) > 2 else ""
        quality = f"importado — {origin or quality}"
    return crop, f"{label} — {quality}" if quality else label


def translate_market(value: str) -> str:
    return {"Milano": "Milão"}.get(value, value)


def translate_stage(value: str) -> str:
    return {
        "Franco azienda": "À saída da exploração",
        "Franco magazzino - arrivo": "À chegada ao armazém",
        "Franco magazzino - partenza": "À expedição do armazém",
    }.get(value, value)


def ismea_records() -> list[dict[str, object]]:
    tables = parse_tables(fetch(ISMEA_URL))
    latest: dict[tuple[str, str, str, str], tuple[datetime, dict[str, object]]] = {}
    for table in tables:
        for cells in table:
            if len(cells) != 6:
                continue
            market, raw_date, raw_product, raw_price, raw_change, raw_stage = cells
            product_info = parse_ismea_product(raw_product)
            if not product_info:
                continue
            price = parse_number(raw_price)
            if price is None:
                continue
            quote_date = datetime.strptime(raw_date, "%d-%m-%y")
            crop, product = product_info
            stage = translate_stage(raw_stage)
            record: dict[str, object] = {
                "crop": crop,
                "country_code": "IT",
                "country": "Itália",
                "product": product,
                "source_product": raw_product,
                "market": translate_market(market),
                "stage": stage,
                "price_eur_t": price,
                "date": raw_date,
                "weekly_change_pct": parse_number(raw_change),
                "source": "ISMEA",
                "source_url": ISMEA_URL,
            }
            key = (crop, product, market, stage)
            if key not in latest or quote_date > latest[key][0]:
                latest[key] = (quote_date, record)
    if not latest:
        raise RuntimeError("A tabela ISMEA não devolveu cotações reconhecíveis.")
    return [
        item[1]
        for item in sorted(latest.values(), key=lambda item: item[0], reverse=True)
    ]


def qlik_call(
    connection: websocket.WebSocket,
    request_id: int,
    method: str,
    handle: int,
    params: list[object],
) -> dict[str, object]:
    connection.send(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "handle": handle,
                "method": method,
                "params": params,
            }
        )
    )
    while True:
        response = json.loads(connection.recv())
        if not isinstance(response, dict):
            raise RuntimeError(f"Resposta inválida da API Qlik ({method}).")
        if response.get("id") != request_id:
            continue
        if "error" in response:
            raise RuntimeError(f"Falha na API Qlik ({method}): {response['error']}")
        result = response.get("result")
        if not isinstance(result, dict):
            raise RuntimeError(f"Resposta inválida da API Qlik ({method}).")
        return result


def qlik_handle(result: dict[str, object], method: str) -> int:
    returned = result.get("qReturn")
    if not isinstance(returned, dict):
        raise RuntimeError(f"A API Qlik não devolveu um objeto para {method}.")
    handle = returned.get("qHandle")
    if not isinstance(handle, int):
        raise RuntimeError(f"A API Qlik não devolveu um identificador para {method}.")
    return handle


def excel_cell_value(cell: ET.Element, shared_strings: list[str]) -> str:
    value = cell.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v")
    if value is None or value.text is None:
        inline_text = cell.findall(
            ".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t"
        )
        return "".join(text.text or "" for text in inline_text)
    if cell.get("t") == "s":
        return shared_strings[int(value.text)]
    return value.text


def excel_column_index(reference: str) -> int:
    column = re.match(r"[A-Z]+", reference)
    if column is None:
        raise RuntimeError(f"Referência de célula Excel inválida: {reference}")
    index = 0
    for character in column.group():
        index = index * 26 + ord(character) - ord("A") + 1
    return index - 1


def excel_date(value: str) -> date:
    try:
        return (datetime(1899, 12, 30) + timedelta(days=float(value))).date()
    except ValueError:
        for date_format in ("%d/%m/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(value, date_format).date()
            except ValueError:
                continue
    raise RuntimeError(f"Data de cotação Excel inválida: {value}")


def parse_eu_cereals_export(content: bytes) -> list[dict[str, object]]:
    namespace = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    with zipfile.ZipFile(io.BytesIO(content)) as workbook:
        strings_root = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
        shared_strings = [
            "".join(text.text or "" for text in item.findall(f".//{namespace}t"))
            for item in strings_root.findall(f"{namespace}si")
        ]
        sheet = ET.fromstring(workbook.read("xl/worksheets/sheet1.xml"))

    xml_rows = sheet.findall(f".//{namespace}sheetData/{namespace}row")
    if len(xml_rows) < 2:
        raise RuntimeError("A exportação Cereals prices não contém linhas de dados.")

    def row_values(xml_row: ET.Element) -> list[str]:
        values: list[str] = []
        for cell in xml_row.findall(f"{namespace}c"):
            index = excel_column_index(cell.get("r", ""))
            if len(values) <= index:
                values.extend([""] * (index + 1 - len(values)))
            values[index] = excel_cell_value(cell, shared_strings)
        return values

    headers = row_values(xml_rows[0])
    required_headers = (
        "Reference period",
        "Member State",
        "Product Name",
        "Market Name",
        "Stage Name",
        "Price (€/Tonne)",
    )
    missing = [header for header in required_headers if header not in headers]
    if missing:
        raise RuntimeError(
            f"A exportação Cereals prices mudou de formato; faltam colunas: {', '.join(missing)}."
        )
    columns = {header: headers.index(header) for header in required_headers}
    histories: dict[
        tuple[str, str, str, str, str], list[tuple[date, float]]
    ] = {}

    for xml_row in xml_rows[1:]:
        values = row_values(xml_row)
        country_name = values[columns["Member State"]]
        country = EU_CEREALS_COUNTRIES.get(country_name)
        product = EU_CEREALS_PRODUCTS.get(values[columns["Product Name"]])
        price_text = values[columns["Price (€/Tonne)"]]
        if country is None or product is None or not price_text:
            continue
        try:
            price = float(price_text)
        except ValueError as error:
            raise RuntimeError(f"Preço inválido na exportação Cereals prices: {price_text}") from error
        if not math.isfinite(price) or price <= 0:
            continue

        quote_date = excel_date(values[columns["Reference period"]])
        market = values[columns["Market Name"]]
        stage = values[columns["Stage Name"]]
        code = country[0]
        crop, localized_product = product
        key = (code, crop, localized_product, market, stage)
        histories.setdefault(key, []).append((quote_date, price))

    expected_countries = {country[0] for country in EU_CEREALS_COUNTRIES.values()}
    available_countries = {key[0] for key in histories}
    missing_countries = sorted(expected_countries - available_countries)
    if missing_countries:
        raise RuntimeError(
            "A exportação Cereals prices não contém preços para: "
            + ", ".join(missing_countries)
        )

    records: list[dict[str, object]] = []
    for (code, crop, product, market, raw_stage), quotes in histories.items():
        quotes.sort(key=lambda quote: quote[0], reverse=True)
        quote_date, price = quotes[0]
        previous = next((quote for quote in quotes[1:] if quote[0] < quote_date), None)
        weekly_change = None
        if previous is not None and quote_date - previous[0] == timedelta(days=7):
            weekly_change = round((price / previous[1] - 1) * 100, 1)
        localized_country = next(
            name for country_code, name in EU_CEREALS_COUNTRIES.values() if country_code == code
        )
        stage = {
            "Departure from farm or from production area - on truck or other transport means":
                "À saída da exploração ou da zona de produção, em camião",
            "Departure from silo - after some storage - on truck or other transport means":
                "À saída do silo, após armazenagem, em camião",
            "Shipped to the place (port), unloaded, on truck leaving port":
                "Desembarcado no porto, em camião à saída",
            "National Average - Not Specified": "Média nacional — fase não especificada",
        }.get(raw_stage, raw_stage)
        records.append(
            {
                "crop": crop,
                "country_code": code,
                "country": localized_country,
                "product": product,
                "market": market,
                "stage": stage,
                "price_eur_t": price,
                "date": quote_date.isoformat(),
                "weekly_change_pct": weekly_change,
                "source": "Comissão Europeia",
                "source_url": EU_CEREALS_URL,
            }
        )
    return records


def eu_cereals_records() -> list[dict[str, object]]:
    base_url = "https://agridata.ec.europa.eu"
    reload_url = (
        f"{base_url}/single/?appid={EU_CEREALS_APP_ID}"
        f"&sheet={EU_CEREALS_SHEET_ID}&opt=ctxmenu"
    )
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    bootstrap = session.get(reload_url, timeout=30)
    bootstrap.raise_for_status()

    token = base64.urlsafe_b64encode(secrets.token_bytes(16)).decode().rstrip("=")
    socket_url = (
        f"wss://agridata.ec.europa.eu/app/{EU_CEREALS_APP_ID}"
        f"?reloadUri={quote(reload_url, safe='')}&qlik-csrf-token={token}"
    )
    cookie = "; ".join(f"{name}={value}" for name, value in session.cookies.items())
    connection = websocket.create_connection(
        socket_url,
        timeout=120,
        origin=base_url,
        cookie=cookie,
    )
    try:
        document = qlik_call(
            connection,
            1,
            "OpenDoc",
            -1,
            [EU_CEREALS_APP_ID, "", "", "", False],
        )
        document_handle = qlik_handle(document, "OpenDoc")
        field = qlik_call(connection, 2, "GetField", document_handle, ["Member State Name"])
        field_handle = qlik_handle(field, "GetField")
        countries = [{"qText": country} for country in EU_CEREALS_COUNTRIES]
        selection = qlik_call(
            connection,
            3,
            "SelectValues",
            field_handle,
            [countries, False, False],
        )
        if selection.get("qReturn") is not True:
            raise RuntimeError("A API Qlik não aplicou os filtros de país solicitados.")
        table = qlik_call(
            connection,
            4,
            "GetObject",
            document_handle,
            [EU_CEREALS_TABLE_ID],
        )
        table_handle = qlik_handle(table, "GetObject")
        export = qlik_call(
            connection,
            5,
            "ExportData",
            table_handle,
            ["OOXML", "/qHyperCubeDef", "", "A", True],
        )
    finally:
        connection.close()

    export_path = export.get("qUrl")
    if not isinstance(export_path, str) or not export_path:
        raise RuntimeError("A API Qlik não devolveu o endereço da exportação Cereals prices.")
    export_url = urljoin(base_url, export_path)
    response = session.get(export_url, timeout=120)
    response.raise_for_status()
    if not response.content.startswith(b"PK"):
        raise RuntimeError("A API Cereals prices não devolveu uma exportação Excel válida.")
    return parse_eu_cereals_export(response.content)


def sevilla_crop(header: str) -> tuple[str, str, str] | None:
    normalized = unaccent(header)
    if normalized.startswith("trigo blando"):
        return "soft_wheat", header.replace("Trigo Blando", "Trigo mole"), "Nacional"
    if normalized.startswith("trigo duro"):
        return "durum_wheat", header.replace("Trigo Duro", "Trigo duro"), "Nacional"
    if normalized == "pienso importacion":
        return "soft_wheat", "Trigo para ração — importação", "Importação"
    if normalized.startswith("triticale"):
        suffix = "importado" if "importacion" in normalized else "nacional"
        return "triticale", f"Triticale — {suffix}", suffix.capitalize()
    if normalized.startswith("avena"):
        suffix = "importada" if "importacion" in normalized else "nacional"
        return "oats", f"Aveia — {suffix}", suffix.capitalize()
    if normalized.startswith("cebada"):
        if "importacion" in normalized:
            return "barley", "Cevada — importação", "Importação"
        if ">= 64" in normalized or "≥ 64" in header:
            return "barley", "Cevada — peso específico ≥64", "Nacional"
        if "< 64" in normalized:
            return "barley", "Cevada — peso específico <64", "Nacional"
    if normalized.startswith("maiz"):
        suffix = "importado" if "importacion" in normalized else "nacional"
        return "maize", f"Milho — {suffix}", suffix.capitalize()
    if normalized.startswith("girasol"):
        return "sunflower", header.replace("Girasol", "Girassol"), "Nacional"
    return None


def sevilla_records(today: date) -> list[dict[str, object]]:
    start = today - timedelta(days=365)
    records: list[dict[str, object]] = []
    for category in ("trigo", "triticale", "avena", "cebada", "maiz", "girasol"):
        body = urlencode(
            {
                "fecha1": start.isoformat(),
                "fecha2": today.isoformat(),
                "cultivo": category,
                category: "todos",
            }
        ).encode()
        tables = parse_tables(fetch(SEVILLA_ENDPOINT, body))
        if not tables or len(tables[0]) < 2:
            raise RuntimeError(f"A Lonja de Sevilla não devolveu uma tabela para {category}.")
        table = tables[0]
        headers, current = table[0], table[1]
        previous = table[2] if len(table) > 2 else []
        if len(current) != len(headers):
            raise RuntimeError(f"A tabela da Lonja de Sevilla está incompleta para {category}.")
        published = datetime.strptime(current[0], "%d/%m/%Y").date()
        previous_published = (
            datetime.strptime(previous[0], "%d/%m/%Y").date().isoformat()
            if previous and re.fullmatch(r"\d{2}/\d{2}/\d{4}", previous[0])
            else None
        )
        for index, header in enumerate(headers[1:], 1):
            product_info = sevilla_crop(header)
            if not product_info:
                continue
            price = parse_number(current[index])
            if price is None:
                continue
            crop, product, stage = product_info
            previous_price = parse_number(previous[index]) if index < len(previous) else None
            change = (
                (price / previous_price - 1) * 100
                if previous_price not in (None, 0)
                else None
            )
            records.append(
                {
                    "crop": crop,
                    "country_code": "ES",
                    "country": "Espanha",
                    "product": product,
                    "market": "Lonja de Sevilla",
                    "stage": stage,
                    "price_eur_t": price,
                    "date": published.isoformat(),
                    "weekly_change_pct": round(change, 2) if change is not None else None,
                    "source": "Lonja de Sevilla",
                    "source_url": SEVILLA_URL,
                    "previous": previous_price,
                    "previous_date": previous_published,
                    "volume": "S/D",
                }
            )
    return records


def update_source(sources: list[dict[str, object]], name: str, fields: dict[str, str]) -> None:
    for source in sources:
        if source.get("source") == name:
            source.update(fields)
            return
    raise RuntimeError(f"Fonte não encontrada no catálogo: {name}")


def main() -> None:
    today = datetime.now(timezone.utc).date()
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    ismea = ismea_records()
    sevilla = sevilla_records(today)
    eu_cereals = eu_cereals_records()

    old_sevilla = data["quotes"]["sevilla"]
    sunflower = []
    for row in old_sevilla["rows"]:
        if row.get("crop") != "sunflower":
            continue
        sunflower.append(
            {
                **row,
                "quote_date": row.get("quote_date", old_sevilla["session_date"]),
                "source_url": old_sevilla["url"],
            }
        )
    sevilla_rows = sunflower + [
        {
            "crop": row["crop"],
            "product": row["product"],
            "price": row["price_eur_t"],
            "previous": row["previous"],
            "volume": row["volume"],
            "quote_date": row["date"],
            "source_url": row["source_url"],
            "previous_date": row.get("previous_date"),
        }
        for row in sevilla
    ]
    sevilla_rows.sort(key=lambda row: (row["quote_date"], row["crop"], row["product"]), reverse=True)

    latest_session = max(date.fromisoformat(row["quote_date"]) for row in sevilla_rows)
    previous_sessions = {
        row["previous_date"] for row in sevilla if row["previous_date"] is not None
    }
    previous_session = max(previous_sessions) if previous_sessions else old_sevilla.get("previous_session")
    for row in sevilla_rows:
        if row["crop"] == "sunflower":
            row.setdefault("previous_date", previous_session)
    old_sevilla.update(
        {
            "session_date": latest_session.isoformat(),
            "previous_session": previous_session,
            "next_session": None,
            "url": SEVILLA_URL,
            "consultor_url": SEVILLA_URL,
            "rows": sevilla_rows,
        }
    )

    history_sevilla = data["history"]["sevilla"]
    existing_history = {
        (row.get("quote_date"), row.get("product")) for row in history_sevilla
    }
    for row in sevilla_rows:
        key = (row["quote_date"], row["product"])
        if key in existing_history:
            continue
        history_sevilla.append(
            {
                "captured": today.isoformat(),
                "quote_date": row["quote_date"],
                "product": row["product"],
                "price_eur_t": row["price"],
                "previous": row.get("previous"),
                "volume": row.get("volume"),
                "crop": row["crop"],
                "source_url": row["source_url"],
            }
        )

    rice = [row for row in ismea if row["crop"] == "rice"]
    history_ismea = data["history"]["ismea"]
    existing_ismea = {
        (row.get("quote_date"), row.get("country"), row.get("product"), row.get("market"))
        for row in history_ismea
    }
    for row in rice:
        key = (row["date"], row["country"], row["product"], row["market"])
        if key in existing_ismea:
            continue
        history_ismea.append({
            "captured": today.isoformat(),
            "quote_date": row["date"],
            "country": row["country"],
            "product": row["product"],
            "market": row["market"],
            "stage": row["stage"],
            "price_eur_t": row["price_eur_t"],
        })

    existing_market_records = [
        row
        for row in data["crop_comparison"]["market_prices"]["records"]
        if row.get("source") not in ("ISMEA", "Lonja de Sevilla")
    ]
    sevilla_market_records = [
        {
            "crop": row["crop"],
            "country_code": "ES",
            "country": "Espanha",
            "product": row["product"],
            "market": "Lonja de Sevilla",
            "stage": "Cotação semanal",
            "price_eur_t": row["price"],
            "date": row["quote_date"],
            "source": "Lonja de Sevilla",
            "source_url": row["source_url"],
        }
        for row in sevilla_rows
    ]
    eu_source = next(
        (source for source in data["sources"] if source.get("source") == "Comissão Europeia"),
        None,
    )
    if eu_source is None:
        data["sources"].append(
            {
                "source": "Comissão Europeia",
                "authority": "European Commission — DG AGRI",
                "api": "Dashboard Cereals Price — exportação pública do Data Explorer",
                "url": EU_CEREALS_URL,
                "used_for": "Cotações de cereais por produto, mercado, fase e data",
                "coverage": "Portugal, Grécia, Bulgária e França",
                "status": "Integrada na página Cotações",
                "notes": (
                    "São usados apenas preços publicados na exportação oficial. "
                    "Não são estimados valores para semanas ou mercados sem cotação."
                ),
            }
        )
    else:
        eu_source.update(
            {
                "authority": "European Commission — DG AGRI",
                "api": "Dashboard Cereals Price — exportação pública do Data Explorer",
                "url": EU_CEREALS_URL,
                "used_for": "Cotações de cereais por produto, mercado, fase e data",
                "coverage": "Portugal, Grécia, Bulgária e França",
                "status": "Integrada na página Cotações",
                "notes": (
                    "São usados apenas preços publicados na exportação oficial. "
                    "Não são estimados valores para semanas ou mercados sem cotação."
                ),
            }
        )
    data["quotes"]["market_prices"] = {
        "retrieved": today.isoformat(),
        "unit": "EUR/t",
        "records": existing_market_records + ismea + sevilla_market_records + eu_cereals,
        "sources": ["ISMEA Mercati", "Lonja de Sevilla", "Comissão Europeia"],
        "method": (
            "Cotações por praça e produto. A página pública do ISMEA é lida integralmente; "
            "a Lonja de Sevilla é consultada pelo respetivo formulário de preços; os cereais "
            "dos restantes países são obtidos na exportação oficial Cereals prices da Comissão "
            "Europeia."
        ),
    }

    update_source(
        data["sources"],
        "ISMEA Mercati",
        {
            "used_for": (
                "Cotações de arroz por variedade e de milho, trigo duro e mole, cevada e aveia "
                "nas praças publicadas"
            ),
            "coverage": "Itália; todas as praças e produtos disponíveis na tabela pública",
            "status": "Integrada na página Cotações",
            "notes": (
                "A página HTML pública devolve a tabela completa (sem limite de API observado). "
                "As praças são extraídas de todas as linhas publicadas."
            ),
        },
    )
    update_source(
        data["sources"],
        "Lonja de Sevilla",
        {
            "used_for": (
                "Cotações de milho, girassol, trigo duro e mole, cevada, aveia e triticale"
            ),
            "coverage": "Espanha (Andaluzia), semanal",
            "status": "Integrada na página Cotações",
            "notes": (
                "A tabela histórica é consultada através do formulário oficial; os produtos sem "
                "preço publicado não recebem um valor estimado."
            ),
        },
    )
    data["metadata"]["title"] = "Observatório de Preços do Arroz"

    temporary_path = DATA_PATH.with_suffix(".json.tmp")
    temporary_path.write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    temporary_path.replace(DATA_PATH)

    markets = sorted({row["market"] for row in rice})
    crops = sorted({row["crop"] for row in ismea + sevilla_rows})
    print(
        f"Atualizadas {len(rice)} cotações ISMEA de arroz em {len(markets)} praças "
        f"({', '.join(markets)}); {len(ismea) - len(rice)} cotações ISMEA de outras culturas; "
        f"{len(sevilla_rows)} linhas Lonja de Sevilla; {len(eu_cereals)} cotações da Comissão "
        f"Europeia. Culturas: {', '.join(crops)}."
    )


if __name__ == "__main__":
    main()
