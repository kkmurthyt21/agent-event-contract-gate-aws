"""Small, dependency-free validator for the JSON Schema keywords used by this sample.

This is intentionally not a complete JSON Schema implementation. Production systems
that accept broader schemas should use a standards-compliant validator.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


SCHEMA_FILES = {
    "1.0.0": "agent-task-1.0.0.json",
    "1.1.0": "agent-task-1.1.0.json",
}


def load_schema(version: str) -> dict[str, Any]:
    """Load only explicitly supported schemas; never build a path from input."""
    filename = SCHEMA_FILES.get(version)
    if filename is None:
        raise ValueError(f"Unsupported schemaVersion: {version!r}")
    path = Path(__file__).with_name("schemas") / filename
    return json.loads(path.read_text(encoding="utf-8"))


def validate_envelope(envelope: Any) -> list[str]:
    if not isinstance(envelope, dict):
        return ["$: expected object"]
    data = envelope.get("data")
    if not isinstance(data, dict):
        return ["$.data: expected object"]
    version = data.get("schemaVersion")
    if not isinstance(version, str):
        return ["$.data.schemaVersion: expected string"]
    try:
        schema = load_schema(version)
    except ValueError as exc:
        return [str(exc)]
    return validate(envelope, schema)


def validate(instance: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    """Validate the schema subset used in this repository."""
    errors: list[str] = []
    expected_type = schema.get("type")

    if expected_type == "object":
        if not isinstance(instance, dict):
            return [f"{path}: expected object"]
        required = schema.get("required", [])
        for key in required:
            if key not in instance:
                errors.append(f"{path}.{key}: required property is missing")
        properties = schema.get("properties", {})
        for key, value in instance.items():
            child_path = f"{path}.{key}"
            if key in properties:
                errors.extend(validate(value, properties[key], child_path))
            elif schema.get("additionalProperties") is False:
                errors.append(f"{child_path}: additional property is not allowed")

    elif expected_type == "array":
        if not isinstance(instance, list):
            return [f"{path}: expected array"]
        item_schema = schema.get("items")
        if item_schema:
            for index, value in enumerate(instance):
                errors.extend(validate(value, item_schema, f"{path}[{index}]"))

    elif expected_type == "string":
        if not isinstance(instance, str):
            return [f"{path}: expected string"]
        if len(instance) < schema.get("minLength", 0):
            errors.append(f"{path}: string is shorter than minLength")
        pattern = schema.get("pattern")
        if pattern and re.fullmatch(pattern, instance) is None:
            errors.append(f"{path}: does not match required pattern")
        if schema.get("format") == "date-time":
            try:
                datetime.fromisoformat(instance.replace("Z", "+00:00"))
            except ValueError:
                errors.append(f"{path}: expected ISO-8601 date-time")

    elif expected_type == "integer":
        if isinstance(instance, bool) or not isinstance(instance, int):
            return [f"{path}: expected integer"]

    elif expected_type == "number":
        if isinstance(instance, bool) or not isinstance(instance, (int, float)):
            return [f"{path}: expected number"]

    elif expected_type == "boolean" and not isinstance(instance, bool):
        return [f"{path}: expected boolean"]

    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}: expected constant value {schema['const']!r}")
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: value is not in the allowed set")

    return errors
