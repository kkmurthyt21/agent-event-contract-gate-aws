param(
    [string]$Profile = "community-builder-sam",
    [string]$Region = "us-east-1"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "Checking AWS identity..."
aws sts get-caller-identity --profile $Profile | Out-Null

Write-Host "Running local tests..."
py -3.12 -m unittest discover -s tests -v

Write-Host "Validating the SAM template..."
sam validate --lint --profile $Profile --region $Region

Write-Host "Building..."
sam build

Write-Host "Deploying stack agent-event-contract-gate..."
sam deploy `
    --stack-name agent-event-contract-gate `
    --resolve-s3 `
    --capabilities CAPABILITY_IAM `
    --profile $Profile `
    --region $Region `
    --confirm-changeset `
    --no-fail-on-empty-changeset

