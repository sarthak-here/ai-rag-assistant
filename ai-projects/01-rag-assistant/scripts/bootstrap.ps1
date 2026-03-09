param(
  [string]$Source = "data.sample",
  [string]$Out = "index.json"
)

python ingest.py --source $Source --out $Out
Write-Host "Bootstrap complete -> $Out"
