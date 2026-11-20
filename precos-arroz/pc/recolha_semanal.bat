@echo off
rem Recolha semanal do Intermarche e do El Corte Ingles, corrida no PC.
rem Estes dois sites recusam os pedidos dos servidores do GitHub (erro 403);
rem as outras tres cadeias continuam a ser recolhidas pelo GitHub Actions.
rem Corre a partir da Tarefa Agendada "Observatorio Maizoryza\Precos arroz Intermarche ECI".
setlocal EnableExtensions
chcp 65001 >nul
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

set "REGISTO_DIR=%LOCALAPPDATA%\ObservatorioMaizoryza"
if not exist "%REGISTO_DIR%" mkdir "%REGISTO_DIR%"
set "LOG=%REGISTO_DIR%\recolha.log"

for /f %%d in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"') do set "HOJE=%%d"
echo.>>"%LOG%"
echo ===== %HOJE% %TIME% =====>>"%LOG%"

cd /d "%~dp0..\.." || goto falha
set "PY="
py -3 --version >nul 2>&1 && set "PY=py -3"
if not defined PY (python --version >nul 2>&1 && set "PY=python")
if not defined PY (echo Python nao encontrado.>>"%LOG%" & goto falha)

set TENTATIVA=1
:inicio
echo [tentativa %TENTATIVA%] git pull>>"%LOG%"
git pull --rebase --autostash >>"%LOG%" 2>&1 || goto falha

pushd precos-arroz
%PY% -m scraper.run --cadeias intermarche elcorteingles >>"%LOG%" 2>&1
%PY% -m tools.merge_into_observatory >>"%LOG%" 2>&1 || (popd & goto falha)
%PY% -m tools.build_dashboard >>"%LOG%" 2>&1 || (popd & goto falha)
git add data/ index.html ../observatorio-maizoryza/observatory-data.json >>"%LOG%" 2>&1
popd

git diff --cached --quiet && (echo Sem alteracoes para guardar.>>"%LOG%" & goto fim)
git commit -m "Precos do arroz (Intermarche e El Corte Ingles): recolha de %HOJE% no PC" >>"%LOG%" 2>&1 || goto falha
git push >>"%LOG%" 2>&1 && goto fim

rem O push falhou: alguem (ex.: o GitHub Actions) gravou entretanto. Desfaz o nosso commit
rem (--keep nao toca em alteracoes por gravar) e repete tudo uma vez a partir da versao nova.
echo Push recusado; a repetir a partir da versao mais recente.>>"%LOG%"
git reset --keep HEAD~1 >>"%LOG%" 2>&1 || goto falha
if %TENTATIVA%==2 goto falha
set TENTATIVA=2
goto inicio

:fim
echo OK>>"%LOG%"
exit /b 0

:falha
echo FALHOU (ver acima)>>"%LOG%"
exit /b 1
