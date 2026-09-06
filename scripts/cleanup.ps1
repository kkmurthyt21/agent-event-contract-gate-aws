param(
    [string]$Profile = "community-builder-sam",
    [string]$Region = "us-east-1"
)

$ErrorActionPreference = "Stop"
sam delete `
    --stack-name agent-event-contract-gate `
    --profile $Profile `
    --region $Region `
    --no-prompts

