<#
  ZeroTrace · Instalación del publicador local (una sola vez)

  Uso (PowerShell normal, sin administrador), desde la carpeta del repositorio:
      powershell -ExecutionPolicy Bypass -File .\tools\instalar-publicador.ps1

  Qué hace:
    1. Copia publicar.ps1 a %LOCALAPPDATA%\ZeroTrace (fuera del repositorio).
    2. Registra la tarea «ZeroTrace Publicador» en el Programador de tareas:
       se ejecuta cada 2 minutos mientras tienes la sesión iniciada, sin ventanas.
  Si cambias publicar.ps1 en el repositorio, vuelve a ejecutar este instalador.

  Para desinstalar:
      Unregister-ScheduledTask -TaskName 'ZeroTrace Publicador' -Confirm:$false
#>
param(
  [string]$Repo = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'
$Repo = (Resolve-Path -LiteralPath $Repo).Path

if (-not (Test-Path -LiteralPath (Join-Path $Repo '.git'))) {
  throw "No encuentro un repositorio git en '$Repo'. Haz primero 'git init' y el primer commit."
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'git no está en el PATH.' }

$destino = Join-Path $env:LOCALAPPDATA 'ZeroTrace'
New-Item -ItemType Directory -Force -Path $destino | Out-Null
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'publicar.ps1') -Destination (Join-Path $destino 'publicar.ps1') -Force

$script = Join-Path $destino 'publicar.ps1'
$argumentos = "--headless powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$script`" -Repo `"$Repo`""

$accion     = New-ScheduledTaskAction -Execute 'conhost.exe' -Argument $argumentos
$disparador = New-ScheduledTaskTrigger -Once -At (Get-Date).Date -RepetitionInterval (New-TimeSpan -Minutes 2) -RepetitionDuration (New-TimeSpan -Days 3650)
$ajustes    = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
                -ExecutionTimeLimit (New-TimeSpan -Minutes 10) -MultipleInstances IgnoreNew
$usuario    = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName 'ZeroTrace Publicador' -Action $accion -Trigger $disparador -Settings $ajustes -Principal $usuario `
  -Description 'Publica en GitHub (commit firmado y push) las ediciones de ZeroTrace que apruebas.' -Force | Out-Null

New-Item -ItemType Directory -Force -Path (Join-Path $Repo '.zerotrace') | Out-Null
Write-Host "Publicador instalado. Repositorio: $Repo"
Write-Host "Script: $script"
Write-Host "Comprueba la tarea con: Get-ScheduledTask -TaskName 'ZeroTrace Publicador' | Get-ScheduledTaskInfo"
