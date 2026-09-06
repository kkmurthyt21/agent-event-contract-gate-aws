"""Detect a focused set of producer/consumer breaking JSON Schema changes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def find_breaking_changes(
    old: dict[str, Any], new: dict[str, Any], path: str = "$"
) -> list[str]:
    changes: list[str] = []
    old_type = old.get("type")
    new_type = new.get("type")
    if old_type != new_type:
        changes.append(f"{path}: type changed from {old_type!r} to {new_type!r}")
        return changes

    version_marker_paths = {"$.dataschema", "$.data.schemaVersion"}
    if (
        path not in version_marker_paths
        and "const" in old
        and old.get("const") != new.get("const")
    ):
        changes.append(f"{path}: constant changed from {old.get('const')!r} to {new.get('const')!r}")

    old_enum = set(old.get("enum", []))
    new_enum = set(new.get("enum", []))
    if old_enum and not old_enum.issubset(new_enum):
        changes.append(f"{path}: enum removed values {sorted(old_enum - new_enum)!r}")

    if old_type == "object":
        old_properties = old.get("properties", {})
        new_properties = new.get("properties", {})
        old_required = set(old.get("required", []))
        new_required = set(new.get("required", []))

        for name in sorted(old_required - set(new_properties)):
            changes.append(f"{path}.{name}: required property was removed")
        for name in sorted(new_required - old_required):
            changes.append(f"{path}.{name}: new required property was added")
        for name in sorted(old_properties.keys() & new_properties.keys()):
            changes.extend(
                find_breaking_changes(old_properties[name], new_properties[name], f"{path}.{name}")
            )

    return changes


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("old_schema", type=Path)
    parser.add_argument("new_schema", type=Path)
    args = parser.parse_args()
    changes = find_breaking_changes(load(args.old_schema), load(args.new_schema))
    if changes:
        print("BREAKING")
        for change in changes:
            print(f"- {change}")
        return 1
    print("COMPATIBLE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
