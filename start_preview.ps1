param([int]$Port=8767)
$runtime = 'C:/Users/39015/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
if (-not (Test-Path -LiteralPath $runtime)) { $runtime = 'python' }
& $runtime -m http.server $Port --bind 127.0.0.1 --directory $PSScriptRoot
