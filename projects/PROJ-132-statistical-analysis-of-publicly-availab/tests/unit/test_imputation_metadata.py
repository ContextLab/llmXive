import json
import pytest
from pathlib import Path

def test_imputation_metadata_exists():
    """
    T017d: Verify Imputation Metadata.
    
    Checks for file `data/processed/imputation_metadata.json`, validates JSON schema,
    and asserts that every record with `is_imputed = true` has a non-null `imputation_source`.
    """
    # Define the expected path relative to project root
    # The test assumes it is run from the project root or that the path is adjusted accordingly.
    # Standard convention: data/processed relative to CWD (project root)
    project_root = Path(__file__).parent.parent.parent
    metadata_path = project_root / "data" / "processed" / "imputation_metadata.json"

    # 1. Check file existence
    assert metadata_path.exists(), f"Imputation metadata file not found at {metadata_path}"

    # 2. Load and validate JSON schema
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        pytest.fail(f"Invalid JSON format in {metadata_path}: {e}")
    except Exception as e:
        pytest.fail(f"Failed to read {metadata_path}: {e}")

    # Ensure data is a list of records
    assert isinstance(data, list), "Imputation metadata must be a list of records."

    # 3. Assert schema constraints
    # Requirement: Every record with `is_imputed = true` must have a non-null `imputation_source`.
    errors = []
    for idx, record in enumerate(data):
        if not isinstance(record, dict):
            errors.append(f"Record at index {idx} is not a dictionary.")
            continue

        is_imputed = record.get("is_imputed")
        imputation_source = record.get("imputation_source")

        if is_imputed is True:
            if imputation_source is None or (isinstance(imputation_source, str) and imputation_source.strip() == ""):
                errors.append(
                    f"Record at index {idx} has `is_imputed=true` but `imputation_source` is null or empty."
                )

    if errors:
        pytest.fail("Imputation metadata validation failed:\n" + "\n".join(errors))

    # If we reach here, the file exists, is valid JSON, and passes the specific constraint.
    assert len(data) > 0, "Imputation metadata file is empty."