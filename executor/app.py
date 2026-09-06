"""Minimal downstream consumer that records each execution."""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime
from typing import Any


LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    import boto3

    envelope = event["detail"]
    data = envelope["data"]
    boto3.client("dynamodb").update_item(
        TableName=os.environ["EXECUTION_TABLE"],
        Key={"eventId": {"S": envelope["id"]}},
        UpdateExpression=(
            "SET correlationId = :correlation, taskId = :task, processedAt = :processed "
            "ADD executionCount :one"
        ),
        ExpressionAttributeValues={
            ":correlation": {"S": data["correlationId"]},
            ":task": {"S": data["taskId"]},
            ":processed": {"S": datetime.now(UTC).isoformat()},
            ":one": {"N": "1"},
        },
    )
    result = {"status": "EXECUTED", "eventId": envelope["id"]}
    LOGGER.info(json.dumps(result))
    return result
