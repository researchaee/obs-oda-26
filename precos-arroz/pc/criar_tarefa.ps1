# Cria (ou atualiza) a tarefa agendada da recolha semanal. Chamado por instalar_tarefa.bat.
param([Parameter(Mandatory)][string]$Repo)
$bat = Join-Path $Repo 'precos-arroz\pc\recolha_semanal.bat'
if (-not (Test-Path $bat)) { throw "Nao encontrei $bat" }
$acao = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument "/c `"`"$bat`"`"" -WorkingDirectory $Repo
$quando = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At '11:00'
$opcoes = New-ScheduledTaskSettingsSet -StartWhenAvailable -RunOnlyIfNetworkAvailable `
  -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 1)
Register-ScheduledTask -TaskPath '\Observatorio Maizoryza\' -TaskName 'Precos arroz Intermarche ECI' `
  -Action $acao -Trigger $quando -Settings $opcoes -Force `
  -Description 'Recolha semanal dos precos do arroz no Intermarche e no El Corte Ingles (Observatorio Maizoryza). Registo em %LOCALAPPDATA%\ObservatorioMaizoryza\recolha.log' | Out-Null
Write-Host "Tarefa criada: \Observatorio Maizoryza\Precos arroz Intermarche ECI (segundas, 11:00)"
