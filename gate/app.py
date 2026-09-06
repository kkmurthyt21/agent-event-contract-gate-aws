"""Validate agent events, prevent duplicates, and publish accepted events."""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

from contract_validation import validate_envelope


LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)
METRIC_NAMESPACE = "AgentContractGate"


def _metric(cloudwatch: Any, name: str) -> None:
    cloudwatch.put_metric_data(
        Namespace=METRIC_NAMESPACE,
        MetricData=[{"MetricName": name, "Value": 1, "Unit": "Count"}],
    )


def _is_duplicate_error(exc: Exception) -> bool:
    response = getattr(exc, "response", {})
    code = response.get("Error", {}).get("Code") if isinstance(response, dict) else None
    return code == "ConditionalCheckFailedException"


def process_event(
    envelope: dict[str, Any],
    *,
    dynamodb: Any,
    eventbridge: Any,
    sqs: Any,
    cloudwatch: Any,
    dedupe_table: str,
    quarantine_queue_url: str,
    event_bus_name: str,
) -> dict[str, Any]:
    errors = validate_envelope(envelope)
    if errors:
        sqs.send_message(
            QueueUrl=quarantine_queue_url,
            MessageBody=json.dumps({"reason": "CONTRACT_INVALID", "errors": errors, "event": envelope}),
        )
        _metric(cloudwatch, "RejectedEvents")
        return {"status": "REJECTED", "errors": errors}

    event_id = envelope["id"]
    data = envelope["data"]
    idempotency_key = data["idempotencyKey"]
    now = int(time.time())

    try:
        dynamodb.put_item(
            TableName=dedupe_table,
            Item={
                "idempotencyKey": {"S": idempotency_key},
                "eventId": {"S": event_id},
                "createdAt": {"N": str(now)},
                "expiresAt": {"N": str(now + 604800)},
            },
            ConditionExpression="attribute_not_exists(idempotencyKey)",
        )
    except Exception as exc:
        if not _is_duplicate_error(exc):
            raise
        _metric(cloudwatch, "DuplicateEvents")
        return {"status": "DUPLICATE", "eventId": event_id}

    result = eventbridge.put_events(
        Entries=[
            {
                "Source": "sample.contract-gate",
                "DetailType": "AgentTaskAccepted",
                "Detail": json.dumps(envelope, separators=(",", ":")),
                "EventBusName": event_bus_name,
            }
        ]
    )
    if result.get("FailedEntryCount", 0):
        dynamodb.delete_item(
            TableName=dedupe_table,
            Key={"idempotencyKey": {"S": idempotency_key}},
        )
        _metric(cloudwatch, "PublishFailures")
        raise RuntimeError(f"EventBridge rejected event: {result.get('Entries', [])}")

    _metric(cloudwatch, "AcceptedEvents")
    return {"status": "ACCEPTED", "eventId": event_id}


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    import boto3

    response = process_event(
        event,
        dynamodb=boto3.client("dynamodb"),
        eventbridge=boto3.client("events"),
        sqs=boto3.client("sqs"),
        cloudwatch=boto3.client("cloudwatch"),
        dedupe_table=os.environ["DEDUPE_TABLE"],
        quarantine_queue_url=os.environ["QUARANTINE_QUEUE_URL"],
        event_bus_name=os.environ["EVENT_BUS_NAME"],
    )
    LOGGER.info(json.dumps(response))
    return response
