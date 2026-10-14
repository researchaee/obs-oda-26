"""Testes dos parsers com excertos reais do HTML de cada site (outubro de 2026).

Correr com:  python -m pytest -q
Se um site mudar o HTML, o teste do parser continua a passar, mas a recolha
devolve 0 produtos e o run.py regista o erro — é esse o sinal para rever.
"""
from scraper import continente, pingodoce, auchan, elcorteingles
from scraper.common import peso_em_gramas, eur_kg_de_texto, classificar, Registo

CONTINENTE = """
<div class="product-tile" data-product-tile-impression='{"name":"Arroz Basmati Caçarola","id":"3040677","price":5.91,"brand":"Caçarola"}'>
 <div class="ct-product-tile-badge ct-product-tile-badge--promotional"></div>
 <a href="https://www.continente.pt/produto/arroz-basmati-cacarola-3040677.html"></a>
 <p class="pwc-tile--quantity">emb. 2,5 kg</p>
 <div class="prices-wrapper"><div class="list "><span class="pvpr-info">PVPR</span> 7,50€</div>
 <span class="pwc-tile--price-primary">5<span class="decimalPrice">,91€</span></span></div>
 <div class="pwc-tile--price-secondary ">2,36€/kg</div>
</div>
<div class="product-tile" data-product-tile-impression='{"name":"Arroz Carolino Continente","id":"8966552","price":1.05,"brand":"Continente"}'>
 <p class="pwc-tile--quantity">emb. 1 kg</p>
 <div class="prices-wrapper"><div class="list d-none"></div></div>
 <div class="pwc-tile--price-secondary d-none"></div>
</div>"""

PINGODOCE = """
<div class="product-tile-pd retail-media" data-gtm-info='{"items":[{"item_id":"1","item_name":"Batatas","item_brand":"X","price":1.0}]}'></div>
<div class="product-tile-pd" data-gtm-info='{"items":[{"item_id":"623900","item_name":"Arroz Agulha","item_brand":"Cigala","price":1.25,"discount":0}]}'>
 <div class="product-name-link"><a href="/home/produtos/x-623900.html">Arroz Agulha</a></div>
 <div class="product-brand-name"> Cigala </div>
 <div class="product-unit"> 1 Kg | 1,25 €/Kg </div>
 <div class="product-price"><span class="prices-list"><span class="strike-through list"><span class="value" content="1.64"></span></span>
 <span class="sales"><span class="value" content="1.25"></span> 1,25 €</span></span></div>
</div>
<div class="product-tile-pd" data-gtm-info='{"items":[{"item_id":"1013757","item_name":"Arroz Agulha","item_brand":"Oriente","price":2.24}]}'>
 <div class="product-name-link"><a href="/x">Arroz Agulha</a></div>
 <div class="product-brand-name">Oriente</div>
 <div class="product-unit"> 1.5 Un | 1,49 €/Un </div>
 <div class="product-price"><span class="sales"><span class="value" content="2.24"></span></span></div>
</div>"""

AUCHAN = """
<div class="product-tile" data-pid="820163" data-gtm-new='{"item_id":"820163","item_name":"ARROZ AGULHA CAÇAROLA EXTRA LONGO 1KG","item_brand":"CAÇAROLA","price":"1.57","discount":"0.30"}'>
 <div class="auc-product-tile__name"><h3><a class="link" href="/pt/x/820163.html">arroz agulha caçarola extra longo 1kg</a></h3></div>
 <span class="auc-measures--price-per-unit">1.27 €/Kg</span>
 <div class="price"><span class="sales"><span class="value" content="1.27"> 1,27 € </span>
 <span class="pvp-recommended">PVP Recomendado: 1,57 €</span></span></div>
</div>"""

ECI = """
<li data-type="item"><div class="food-prices"><div class="food-prices__offer">2,09 €</div><div class="food-prices__price--original">2,59 €</div></div>
 <div class="food-prices__measurement-unit">( 2,09 € / Kg )</div>
 <a class="food-product-preview-responsive__description" href="/supermercado/B052018005802519-cigala-arroz-thai-jasmim-embalagem-1-kg/">Arroz Thai Jasmim  Cigala</a>
 <span class="food-product-preview-responsive__sale_type">embalagem <span>|</span> 1 kg</span></li>
<li data-type="item"><div class="food-prices"><div class="food-prices__price">1,35 €</div></div>
 <a class="food-product-preview-responsive__description" href="/supermercado/B052018005801222-el-corte-ingles-arroz-agulha-1-kg/">Arroz Agulha  El Corte Inglés</a></li>"""


def test_continente():
    a, b = continente.parse(CONTINENTE)
    assert (a.id, a.preco, a.peso_g, a.eur_kg, a.preco_ref, a.promo) == ("3040677", 5.91, 2500, 2.36, 7.5, True)
    assert (b.preco, b.peso_g, b.preco_ref, b.promo) == (1.05, 1000, None, False)


def test_pingodoce():
    regs = pingodoce.parse(PINGODOCE)
    assert len(regs) == 2  # o patrocinado é ignorado
    a, b = regs
    assert (a.marca, a.preco, a.peso_g, a.eur_kg, a.preco_ref, a.promo) == ("Cigala", 1.25, 1000, 1.25, 1.64, True)
    assert b.peso_g == 1500 and b.eur_kg is None and "inferido" in b.nota


def test_auchan():
    (a,) = auchan.parse(AUCHAN)
    assert (a.preco, a.peso_g, a.eur_kg, a.preco_ref, a.promo) == (1.27, 1000, 1.27, 1.57, True)


def test_elcorteingles():
    a, b = elcorteingles.parse(ECI)
    assert (a.nome, a.marca, a.preco, a.preco_ref, a.promo, a.peso_g) == ("Arroz Thai Jasmim", "Cigala", 2.09, 2.59, True, 1000)
    assert (b.marca, b.preco, b.peso_g) == ("El Corte Inglés", 1.35, 1000)


def test_pesos():
    assert peso_em_gramas("emb. 2 x 125 gr") == 250
    assert peso_em_gramas("arroz carolino louro 1kg+25%") == 1250
    assert peso_em_gramas("arroz basmati auchan em saquetas 500g(4x125g)") == 500
    assert peso_em_gramas("arroz vaporizado oriente d'oro 1.5kg") == 1500
    assert eur_kg_de_texto("0 € / Kg") is None


def test_classificar():
    def c(nome, marca="X", peso=1000):
        r = classificar(Registo("T", "1", nome, marca, 1.0, peso))
        return r and (r.tipo, r.segmento)
    assert c("Arroz Basmati Vaporizado Continente", "Continente")[0] == "Vaporizado / Estufado"
    assert c("Arroz Carolino Continente", "Continente") == ("Carolino", "Marca própria")
    assert c("Arroz Agulha Pronto a Comer Cigala", "Cigala", 250)[0] == "Pronto a comer / preparados"
    assert c("Arroz Doce, 125g", "Alsa", 125) is None
    assert c("Arroz doce especial, embalagem de 500g", "Saludães", 500)[0] == "Carolino"
    assert c("konjac keto chef arroz bio 270g") is None
    assert c("Arroz Arborio Risotto", "Riso Gallo", 500) == ("Risotto (arbório, carnaroli)", "Premium / Bio")
