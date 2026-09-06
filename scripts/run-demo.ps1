param(
    [string]$Profile = "community-builder-sam",
    [string]$Region = "us-east-1",
    [string]$StackName = "agent-event-contract-gate"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$Outputs = aws cloudformation describe-stacks `
    --stack-name $StackName `
    --profile $Profile `
    --region $Region `
    --query "Stacks[0].Outputs" `
    --output json | ConvertFrom-Json

function Get-OutputValue([string]$Key) {
    return ($Outputs | Where-Object { $_.OutputKey -eq $Key }).OutputValue
}

$FunctionName = Get-OutputValue "ContractGateFunctionName"
$ExecutionTable = Get-OutputValue "ExecutionTableName"
$QuarantineQueue = Get-OutputValue "QuarantineQueueUrl"
$DeliveryQueue = Get-OutputValue "DeliveryDeadLetterQueueUrl"
$OutputDir = Join-Path $ProjectRoot "demo-output"
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

function Invoke-Sample([string]$EventFile, [string]$ResultFile) {
    aws lambda invoke `
        --function-name $FunctionName `
        --cli-binary-format raw-in-base64-out `
        --payload "fileb://$EventFile" `
        --profile $Profile `
        --region $Region `
        $ResultFile | Out-Null
    return Get-Content $ResultFile -Raw
}

Write-Host "1. Valid v1 event"
Write-Host (Invoke-Sample "events/valid-v1.json" "$OutputDir/accepted.json")

Write-Host "2. Same event again"
Write-Host (Invoke-Sample "events/valid-v1.json" "$OutputDir/duplicate.json")

Write-Host "3. Unsupported, breaking v2 event"
Write-Host (Invoke-Sample "events/breaking-v2.json" "$OutputDir/rejected.json")

Write-Host "Waiting for EventBridge delivery and SQS queue metadata..."
Start-Sleep -Seconds 65
Write-Host "4. Executor record (executionCount should be 1)"
$ExecutionKeyFile = Join-Path $OutputDir "execution-key.json"
'{"eventId":{"S":"event-1001"}}' | Set-Content -Path $ExecutionKeyFile -Encoding Ascii
aws dynamodb get-item `
    --table-name $ExecutionTable `
    --key "file://$ExecutionKeyFile" `
    --consistent-read `
    --profile $Profile `
    --region $Region

Write-Host "5. Quarantine queue count (should be at least 1)"
aws sqs get-queue-attributes `
    --queue-url $QuarantineQueue `
    --attribute-names ApproximateNumberOfMessages `
    --profile $Profile `
    --region $Region

Write-Host "6. Delivery DLQ count (should be 0)"
aws sqs get-queue-attributes `
    --queue-url $DeliveryQueue `
    --attribute-names ApproximateNumberOfMessages `
    --profile $Profile `
    --region $Region
