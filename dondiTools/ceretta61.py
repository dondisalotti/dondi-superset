#!/usr/bin/env python3
"""
Convert Superset 6.1.0 dashboard exports to 6.0.0-compatible format.

Fixes applied:
  datasets:
    column.datetime_format  -> column.python_date_format  (renamed in 6.1.0)
    dataset.currency_code_column -> removed (no 6.0.0 equivalent)
  databases:
    configuration_method -> removed (no 6.0.0 equivalent)
  dashboards:
    native_filter.requiredFirst: <DOM event object> -> true (6.1.0 serialization bug)
    native_filter.requiredFirst: {} -> false (empty object means not required)
"""

import os
import shutil
import sys
import tempfile
import zipfile

import yaml

STRIP_DATASET_FIELDS = {"currency_code_column"}
STRIP_DATABASE_FIELDS = {"configuration_method"}
RENAME_COLUMN_FIELDS = {"datetime_format": "python_date_format"}


def clean_column(col):
    for old, new in RENAME_COLUMN_FIELDS.items():
        if old in col:
            col[new] = col.pop(old)


def clean_dataset(data):
    for field in STRIP_DATASET_FIELDS:
        data.pop(field, None)
    for col in data.get("columns", []):
        clean_column(col)


def clean_database(data):
    for field in STRIP_DATABASE_FIELDS:
        data.pop(field, None)


def normalize_required_first(value):
    """
    In 6.1.0 a bug serialized the raw checkbox DOM event into requiredFirst
    instead of a boolean. Normalize to a proper bool.
    - DOM event object (has 'nativeEvent' or 'target') -> True (it was checked)
    - empty dict {} -> False
    - already a bool -> unchanged
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, dict):
        if not value:
            return False
        if "nativeEvent" in value or "target" in value:
            target = value.get("target", {})
            return bool(target.get("checked", True))
        return bool(value)
    return bool(value)


def clean_dashboard(data):
    metadata = data.get("metadata", {})
    if not isinstance(metadata, dict):
        return

    filters = metadata.get("native_filter_configuration", [])
    if not isinstance(filters, list):
        return

    for f in filters:
        if not isinstance(f, dict):
            continue
        if "requiredFirst" in f:
            f["requiredFirst"] = normalize_required_first(f["requiredFirst"])
        if "targets" not in f or f["targets"] == []:
            f["targets"] = [{}]


def process_file(path):
    with open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if data is None:
        return False

    before = str(data)

    if "columns" in data:
        clean_dataset(data)

    if "sqlalchemy_uri" in data or "configuration_method" in data:
        clean_database(data)

    if "dashboard_title" in data:
        clean_dashboard(data)

    after = str(data)
    if before != after:
        with open(path, "w", encoding="utf-8") as fh:
            yaml.dump(data, fh, allow_unicode=True, sort_keys=False)
        print(f"  Converted: {os.path.relpath(path)}")
        return True

    return False


def main(input_zip):
    if not os.path.isfile(input_zip):
        print(f"Error: file not found: {input_zip}")
        sys.exit(1)

    base = os.path.splitext(input_zip)[0]
    output_zip = f"{base}_60compat.zip"

    tmpdir = tempfile.mkdtemp()
    try:
        print(f"Extracting {input_zip}...")
        with zipfile.ZipFile(input_zip, "r") as zf:
            zf.extractall(tmpdir)

        print("Processing YAML files...")
        total = 0
        for root, _, files in os.walk(tmpdir):
            for fname in files:
                if fname.endswith(".yaml"):
                    if process_file(os.path.join(root, fname)):
                        total += 1

        print(f"Converted {total} file(s).")
        print(f"Writing {output_zip}...")
        with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(tmpdir):
                for fname in files:
                    full_path = os.path.join(root, fname)
                    arcname = os.path.relpath(full_path, tmpdir)
                    zf.write(full_path, arcname)

        print(f"\nDone. Import this file into Superset 6.0.0:\n  {output_zip}")
    finally:
        shutil.rmtree(tmpdir)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 strip_61_fields.py <dashboard_export.zip>")
        sys.exit(1)
    main(sys.argv[1])
