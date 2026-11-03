<#
  ZeroTrace · Publicador local

  Lo ejecuta el Programador de tareas de Windows cada 2 minutos. Si encuentra la
  marca .zerotrace\publicar.json (que solo aparece cuando apruebas una edición),
  hace commit FIRMADO con tu clave SSH y push a GitHub con tu propia cuenta.

  Salvaguardas:
    - Solo publica en la rama main.
    - Solo acepta cambios en es/, en/, data/ e index.html. Cualquier otro cambio detiene la publicación.
    - El mensaje de commit no puede contener saltos de línea ni atribuciones de terceros.
    - El commit se firma siempre (-S). Si la firma falla, no se publica nada.
    - Este script se instala en %LOCALAPPDATA%\ZeroTrace, fuera del repositorio,
      para que nada que llegue al repositorio pueda cambiar lo que se ejecuta.
#>
param(
  [Parameter(Mandatory = $true)][string]$Repo
)

$ErrorActionPreference = 'Stop'
$estado    = Join-Path $Repo '.zerotrace'
$marca     = Join-Path $estado 'publicar.json'
$resultado = Join-Path $estado 'resultado.json'
$registro  = Join-Path $estado 'publicador.log'

if (-not (Test-Path -LiteralPath $marca)) { exit 0 }

function Escribir-Log([string]$texto) {
  "$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ss')  $texto" | Add-Content -LiteralPath $registro -Encoding UTF8
}

function Invoke-Git {
  # Sin bloque param: así -A, -S o -m llegan tal cual a git. git escribe su progreso
  # en stderr, que en Windows PowerShell no debe tratarse como error: se usa el código de salida.
  $anterior = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  $salida = & git.exe @args 2>&1 | ForEach-Object { "$_" }
  $codigo = $LASTEXITCODE
  $ErrorActionPreference = $anterior
  if ($codigo -ne 0) { throw "git $($args -join ' ') ha fallado: $($salida -join ' ')" }
  return $salida
}

try {
  $peticion = Get-Content -LiteralPath $marca -Raw -Encoding UTF8 | ConvertFrom-Json
  $fecha    = [string]$peticion.fecha
  $mensaje  = [string]$peticion.mensaje

  if ($fecha -notmatch '^\d{4}-\d{2}-\d{2}$') { throw "Fecha no válida en la marca: '$fecha'" }
  if ([string]::IsNullOrWhiteSpace($mensaje) -or $mensaje.Length -gt 120 -or $mensaje -match "[`r`n]") {
    throw 'Mensaje de commit vacío, demasiado largo o con saltos de línea'
  }
  if ($mensaje -match '(?i)claude|anthropic|co-authored|generated') {
    throw 'El mensaje de commit contiene una atribución no permitida'
  }

  Set-Location -LiteralPath $Repo
  $rama = (Invoke-Git rev-parse --abbrev-ref HEAD | Select-Object -First 1).ToString().Trim()
  if ($rama -ne 'main') { throw "La rama actual es '$rama', no 'main'" }

  # Nada preparado a medias de antes: el índice debe coincidir con HEAD.
  & git.exe diff --cached --quiet
  if ($LASTEXITCODE -ne 0) { throw 'Hay cambios preparados (staged) que no son de ZeroTrace. Revísalos antes de publicar.' }

  $permitidas = '^(es/|en/|data/|index\.html$)'
  $cambios = @(& git.exe -c core.quotepath=off status --porcelain=v1 --untracked-files=all)
  if ($cambios.Count -eq 0) { throw 'No hay cambios que publicar' }
  foreach ($linea in $cambios) {
    $ruta = $linea.Substring(3).Trim('"')
    if ($ruta -match ' -> ') { $ruta = ($ruta -split ' -> ')[1].Trim('"') }
    if ($ruta -notmatch $permitidas) { throw "Cambio fuera de las rutas permitidas: $ruta" }
  }

  Invoke-Git add -A es en data index.html | Out-Null
  Invoke-Git commit -S -m $mensaje | Out-Null
  Invoke-Git push origin main | Out-Null

  $hash = (Invoke-Git rev-parse --short HEAD | Select-Object -First 1).ToString().Trim()
  Remove-Item -LiteralPath $marca -Force
  [ordered]@{ estado = 'publicado'; fecha = $fecha; commit = $hash; hora = (Get-Date -Format 'yyyy-MM-ddTHH:mm:ss') } |
    ConvertTo-Json | Set-Content -LiteralPath $resultado -Encoding UTF8
  Escribir-Log "PUBLICADO $fecha $hash"
}
catch {
  $detalle = $_.Exception.Message
  Escribir-Log "ERROR $detalle"
  [ordered]@{ estado = 'error'; detalle = $detalle; hora = (Get-Date -Format 'yyyy-MM-ddTHH:mm:ss') } |
    ConvertTo-Json | Set-Content -LiteralPath $resultado -Encoding UTF8
  # Se aparta la marca para no reintentar en bucle. Para reintentar, se vuelve a crear tras corregir el problema.
  if (Test-Path -LiteralPath $marca) { Move-Item -LiteralPath $marca -Destination (Join-Path $estado 'publicar.fallido.json') -Force }
  exit 1
}
