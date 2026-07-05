"""
Integration/Contract test for T011.
Verifies the schema of data/derived/study_records_raw.json against specs/contracts/study_record.schema.yaml.
"""
import json
import os
import sys
from pathlib import Path
import yaml
import jsonschema
from jsonschema import validate, ValidationError

# Add project root to path for imports if running as script
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

DATA_PATH = project_root / "data" / "derived" / "study_records_raw.json"
SCHEMA_PATH = project_root / "specs" / "contracts" / "study_record.schema.yaml"

def test_study_records_schema():
    """
    Contract test: Verify output schema of data/derived/study_records_raw.json
    against specs/contracts/study_record.schema.yaml.
    """
    # 1. Verify files exist
    assert DATA_PATH.exists(), f"Data file not found at {DATA_PATH}. Has extraction (T016) run?"
    assert SCHEMA_PATH.exists(), f"Schema file not found at {SCHEMA_PATH}. Has schema been created?"

    # 2. Load schema
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)

    # 3. Load data
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 4. Handle both list and single object cases (though spec implies list)
    if not isinstance(data, list):
        data = [data]

    # 5. Validate each record
    errors = []
    for i, record in enumerate(data):
        try:
            validate(instance=record, schema=schema)
        except ValidationError as e:
            errors.append(f"Record {i}: {e.message} (Path: {list(e.absolute_path)})")

    # 6. Assert no errors
    assert not errors, (
        f"Schema validation failed for {len(errors)} record(s):\n" + "\n".join(errors)
    )

    # 7. Verify minimum sample size constraint (SC-004) if applicable to this dataset
    # Note: T026a handles the hard halt for <30, but this test ensures the file structure is valid first.
    assert len(data) > 0, "Data file is empty. No records found."

    print(f"Contract test passed: {len(data)} records validated against schema.")

if __name__ == "__main__":
    test_study_records_schema()
