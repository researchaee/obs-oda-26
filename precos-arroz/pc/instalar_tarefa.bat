@echo off
rem Instala no PC a recolha semanal do Intermarche e do El Corte Ingles.
rem Pode correr-se de qualquer pasta (ex.: Transferencias). Pode repetir-se sem problema.
rem Antes: os ficheiros precos-arroz\pc\* e precos-arroz\scraper\run.py ja tem de estar no GitHub.
setlocal EnableExtensions
chcp 65001 >nul
set "PYTHONUTF8=1"

echo.
echo === 1/4  Copia local do repositorio ===
rem Prefere a copia fora do OneDrive (o OneDrive pode estragar a pasta .git a meio de um commit).
set "REPO=%USERPROFILE%\obs-oda-26"
if not exist "%REPO%\.git" set "REPO=%USERPROFILE%\OneDrive - CONSULAI\01_Atalhos\MAIZORYZA_Observatorio - Documentos\observatorio-maizoryza\obs-oda-26"
if not exist "%REPO%\.git" (echo Nao encontrei a copia local do repositorio. & goto erro)
cd /d "%REPO%" || goto erro
echo Copia usada: %CD%
git pull --rebase --autostash || goto erro
if not exist "precos-arroz\pc\recolha_semanal.bat" (echo Os ficheiros novos ainda nao estao no GitHub. Carregue-os primeiro. & goto erro)

echo.
echo === 2/4  Python e bibliotecas ===
set "PY="
py -3 --version >nul 2>&1 && set "PY=py -3"
if not defined PY (python --version >nul 2>&1 && set "PY=python")
if not defined PY (echo Python nao encontrado. Instale-o em https://www.python.org e volte a correr este ficheiro. & goto erro)
%PY% -m pip install --user -q -r precos-arroz\requirements.txt || goto erro

echo.
echo === 3/4  Teste rapido (5 lojas Intermarche + El Corte Ingles, nada e gravado no repositorio) ===
pushd precos-arroz
%PY% -m scraper.run --cadeias intermarche elcorteingles --intermarche-lojas 5 --pasta "%TEMP%\teste-precos-arroz"
popd
echo.
echo Se acima aparecer "intermarche: N produtos" e "elcorteingles: N produtos", este PC consegue recolher.
echo Se aparecer "403 Forbidden", a rede deste PC tambem esta bloqueada (a tarefa e criada na mesma).

echo.
echo === 4/4  Criar a tarefa agendada (segundas-feiras, 11:00) ===
powershell -NoProfile -ExecutionPolicy Bypass -File "%CD%\precos-arroz\pc\criar_tarefa.ps1" -Repo "%CD%" || goto erro

echo.
echo Feito. A tarefa corre todas as segundas as 11:00 (ou logo que o PC seja ligado).
echo Registo de cada execucao: %LOCALAPPDATA%\ObservatorioMaizoryza\recolha.log
echo Para correr ja: Agendador de Tarefas ^> Observatorio Maizoryza ^> clique direito ^> Executar.
pause
exit /b 0

:erro
echo.
echo Algo falhou no passo acima. Copie esta janela e envie ao Claude.
pause
exit /b 1
