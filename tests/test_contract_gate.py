from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "gate"))
sys.path.insert(0, str(ROOT / "scripts"))

from app import process_event  # noqa: E402
from check_compatibility import find_breaking_changes  # noqa: E402
from contract_validation import load_schema, validate_envelope  # noqa: E402


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class ConditionalFailure(Exception):
    response = {"Error": {"Code": "ConditionalCheckFailedException"}}


class FakeDynamoDB:
    def __init__(self) -> None:
        self.keys: set[str] = set()

    def put_item(self, **kwargs) -> None:
        key = kwargs["Item"]["idempotencyKey"]["S"]
        if key in self.keys:
            raise ConditionalFailure()
        self.keys.add(key)

    def delete_item(self, **kwargs) -> None:
        self.keys.discard(kwargs["Key"]["idempotencyKey"]["S"])


class FakeEventBridge:
    def __init__(self) -> None:
        self.entries: list[dict] = []

    def put_events(self, **kwargs) -> dict:
        self.entries.extend(kwargs["Entries"])
        return {"FailedEntryCount": 0, "Entries": [{"EventId": "accepted"}]}


class FakeSQS:
    def __init__(self) -> None:
        self.messages: list[dict] = []

    def send_message(self, **kwargs) -> None:
        self.messages.append(kwargs)


class FakeCloudWatch:
    def __init__(self) -> None:
        self.names: list[str] = []

    def put_metric_data(self, **kwargs) -> None:
        self.names.append(kwargs["MetricData"][0]["MetricName"])


class ContractValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.valid = read_json(ROOT / "events" / "valid-v1.json")

    def test_01_valid_v1_is_accepted(self) -> None:
        self.assertEqual(validate_envelope(self.valid), [])

    def test_02_valid_v11_is_accepted(self) -> None:
        event = read_json(ROOT / "events" / "valid-v1.1.json")
        self.assertEqual(validate_envelope(event), [])

    def test_03_missing_required_field_is_rejected(self) -> None:
        event = copy.deepcopy(self.valid)
        del event["data"]["correlationId"]
        self.assertTrue(any("correlationId" in error for error in validate_envelope(event)))

    def test_04_additional_field_is_rejected(self) -> None:
        event = copy.deepcopy(self.valid)
        event["data"]["uncontracted"] = True
        self.assertTrue(any("additional property" in error for error in validate_envelope(event)))

    def test_05_unsupported_version_is_rejected_without_path_lookup(self) -> None:
        event = copy.deepcopy(self.valid)
        event["data"]["schemaVersion"] = "../../secret"
        errors = validate_envelope(event)
        self.assertEqual(errors, ["Unsupported schemaVersion: '../../secret'"])

    def test_06_packaged_schema_matches_source_schema(self) -> None:
        packaged = load_schema("1.0.0")
        source = read_json(ROOT / "schemas" / "agent-task-1.0.0.json")
        self.assertEqual(packaged, source)

    def test_07_optional_v11_change_is_compatible(self) -> None:
        old = read_json(ROOT / "schemas" / "agent-task-1.0.0.json")
        new = read_json(ROOT / "schemas" / "agent-task-1.1.0.json")
        self.assertEqual(find_breaking_changes(old, new), [])

    def test_08_v2_rename_is_breaking(self) -> None:
        old = read_json(ROOT / "schemas" / "agent-task-1.0.0.json")
        new = read_json(ROOT / "schemas" / "agent-task-2.0.0.json")
        changes = find_breaking_changes(old, new)
        self.assertTrue(any("taskId" in change for change in changes))
        self.assertTrue(any("workItemId" in change for change in changes))

    def test_09_gate_returns_accepted_duplicate_and_rejected(self) -> None:
        dynamodb = FakeDynamoDB()
        eventbridge = FakeEventBridge()
        sqs = FakeSQS()
        cloudwatch = FakeCloudWatch()
        clients = {
            "dynamodb": dynamodb,
            "eventbridge": eventbridge,
            "sqs": sqs,
            "cloudwatch": cloudwatch,
            "dedupe_table": "dedupe",
            "quarantine_queue_url": "https://example.invalid/quarantine",
            "event_bus_name": "agent-bus",
        }

        accepted = process_event(self.valid, **clients)
        duplicate = process_event(self.valid, **clients)
        rejected = process_event(read_json(ROOT / "events" / "breaking-v2.json"), **clients)

        self.assertEqual(accepted["status"], "ACCEPTED")
        self.assertEqual(duplicate["status"], "DUPLICATE")
        self.assertEqual(rejected["status"], "REJECTED")
        self.assertEqual(len(eventbridge.entries), 1)
        self.assertEqual(len(sqs.messages), 1)
        self.assertEqual(cloudwatch.names, ["AcceptedEvents", "DuplicateEvents", "RejectedEvents"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
