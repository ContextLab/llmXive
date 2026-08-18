"""
Contract test for fingerprint schema in the preprocessing pipeline.

This test verifies that the output of the preprocessing pipeline adheres to the
defined schema for reaction mechanism fingerprints. It ensures:
1. The output is a list of dictionaries.
2. Each dictionary contains the required keys: 'fingerprint', 'label', 'source_id', 'provenance'.
3. 'fingerprint' is a list of floats with exactly 512 elements.
4. 'label' is one of the valid mechanism classes: 'SN1', 'SN2', 'E1'.
5. 'source_id' is a non-empty string.
6. 'provenance' is a non-empty string indicating the data source type.
7. No NaN or infinite values exist in the fingerprint vectors.
"""
import pytest
import numpy as np
from typing import List, Dict, Any, Union

VALID_MECHANISM_LABELS = {'SN1', 'SN2', 'E1'}
EXPECTED_FINGERPRINT_LENGTH = 512
REQUIRED_KEYS = {'fingerprint', 'label', 'source_id', 'provenance'}


def validate_fingerprint_schema(data: Union[List[Dict[str, Any]], Dict[str, Any]]) -> None:
    """
    Validates a single fingerprint record or a list of records against the schema.

    Args:
        data: A single record (dict) or a list of records to validate.

    Raises:
        AssertionError: If the data does not conform to the schema.
    """
    if isinstance(data, dict):
        records = [data]
    elif isinstance(data, list):
        records = data
    else:
        raise AssertionError(f"Expected list or dict, got {type(data)}")

    if not records:
        raise AssertionError("Input data list is empty.")

    for idx, record in enumerate(records):
        # Check type
        if not isinstance(record, dict):
            raise AssertionError(f"Record {idx} is not a dictionary.")

        # Check required keys
        missing_keys = REQUIRED_KEYS - set(record.keys())
        if missing_keys:
            raise AssertionError(f"Record {idx} is missing required keys: {missing_keys}")

        extra_keys = set(record.keys()) - REQUIRED_KEYS
        if extra_keys:
            raise AssertionError(f"Record {idx} contains unexpected keys: {extra_keys}")

        # Validate 'fingerprint'
        fp = record['fingerprint']
        if not isinstance(fp, (list, np.ndarray)):
            raise AssertionError(f"Record {idx}: 'fingerprint' must be a list or numpy array.")

        if len(fp) != EXPECTED_FINGERPRINT_LENGTH:
            raise AssertionError(
                f"Record {idx}: 'fingerprint' length is {len(fp)}, expected {EXPECTED_FINGERPRINT_LENGTH}."
            )

        # Check for NaN/Inf in fingerprint
        fp_array = np.array(fp, dtype=float)
        if not np.all(np.isfinite(fp_array)):
            raise AssertionError(f"Record {idx}: 'fingerprint' contains NaN or Inf values.")

        # Validate 'label'
        label = record['label']
        if not isinstance(label, str):
            raise AssertionError(f"Record {idx}: 'label' must be a string.")
        if label not in VALID_MECHANISM_LABELS:
            raise AssertionError(
                f"Record {idx}: 'label' is '{label}', expected one of {VALID_MECHANISM_LABELS}."
            )

        # Validate 'source_id'
        source_id = record['source_id']
        if not isinstance(source_id, str) or not source_id.strip():
            raise AssertionError(f"Record {idx}: 'source_id' must be a non-empty string.")

        # Validate 'provenance'
        provenance = record['provenance']
        if not isinstance(provenance, str) or not provenance.strip():
            raise AssertionError(f"Record {idx}: 'provenance' must be a non-empty string.")


class TestFingerprintSchema:
    """
    Test suite for the fingerprint schema contract.
    """

    def test_valid_single_record(self):
        """Test that a valid single record passes validation."""
        valid_record = {
            "fingerprint": [0.1] * EXPECTED_FINGERPRINT_LENGTH,
            "label": "SN2",
            "source_id": "NIST_12345",
            "provenance": "kinetic studies"
        }
        # Should not raise
        validate_fingerprint_schema(valid_record)

    def test_valid_list_of_records(self):
        """Test that a valid list of records passes validation."""
        valid_records = [
            {
                "fingerprint": [0.5] * EXPECTED_FINGERPRINT_LENGTH,
                "label": "SN1",
                "source_id": "NIST_67890",
                "provenance": "validated intermediates"
            },
            {
                "fingerprint": [0.0] * EXPECTED_FINGERPRINT_LENGTH,
                "label": "E1",
                "source_id": "NIST_11111",
                "provenance": "kinetic studies"
            }
        ]
        # Should not raise
        validate_fingerprint_schema(valid_records)

    def test_missing_key(self):
        """Test that a record with a missing key fails validation."""
        invalid_record = {
            "fingerprint": [0.1] * EXPECTED_FINGERPRINT_LENGTH,
            "label": "SN2",
            "source_id": "NIST_12345"
            # 'provenance' is missing
        }
        with pytest.raises(AssertionError) as exc_info:
            validate_fingerprint_schema(invalid_record)
        assert "missing required keys" in str(exc_info.value)

    def test_invalid_fingerprint_length(self):
        """Test that a record with wrong fingerprint length fails validation."""
        invalid_record = {
            "fingerprint": [0.1] * 510,  # Wrong length
            "label": "SN2",
            "source_id": "NIST_12345",
            "provenance": "kinetic studies"
        }
        with pytest.raises(AssertionError) as exc_info:
            validate_fingerprint_schema(invalid_record)
        assert "expected 512" in str(exc_info.value)

    def test_invalid_label(self):
        """Test that a record with an invalid label fails validation."""
        invalid_record = {
            "fingerprint": [0.1] * EXPECTED_FINGERPRINT_LENGTH,
            "label": "E2",  # Invalid label
            "source_id": "NIST_12345",
            "provenance": "kinetic studies"
        }
        with pytest.raises(AssertionError) as exc_info:
            validate_fingerprint_schema(invalid_record)
        assert "expected one of" in str(exc_info.value)

    def test_nan_in_fingerprint(self):
        """Test that a record with NaN in fingerprint fails validation."""
        fp = [0.1] * EXPECTED_FINGERPRINT_LENGTH
        fp[10] = float('nan')
        invalid_record = {
            "fingerprint": fp,
            "label": "SN2",
            "source_id": "NIST_12345",
            "provenance": "kinetic studies"
        }
        with pytest.raises(AssertionError) as exc_info:
            validate_fingerprint_schema(invalid_record)
        assert "NaN or Inf" in str(exc_info.value)

    def test_inf_in_fingerprint(self):
        """Test that a record with Inf in fingerprint fails validation."""
        fp = [0.1] * EXPECTED_FINGERPRINT_LENGTH
        fp[20] = float('inf')
        invalid_record = {
            "fingerprint": fp,
            "label": "SN2",
            "source_id": "NIST_12345",
            "provenance": "kinetic studies"
        }
        with pytest.raises(AssertionError) as exc_info:
            validate_fingerprint_schema(invalid_record)
        assert "NaN or Inf" in str(exc_info.value)

    def test_empty_source_id(self):
        """Test that a record with empty source_id fails validation."""
        invalid_record = {
            "fingerprint": [0.1] * EXPECTED_FINGERPRINT_LENGTH,
            "label": "SN2",
            "source_id": "",
            "provenance": "kinetic studies"
        }
        with pytest.raises(AssertionError) as exc_info:
            validate_fingerprint_schema(invalid_record)
        assert "non-empty string" in str(exc_info.value)

    def test_empty_provenance(self):
        """Test that a record with empty provenance fails validation."""
        invalid_record = {
            "fingerprint": [0.1] * EXPECTED_FINGERPRINT_LENGTH,
            "label": "SN2",
            "source_id": "NIST_12345",
            "provenance": "   "
        }
        with pytest.raises(AssertionError) as exc_info:
            validate_fingerprint_schema(invalid_record)
        assert "non-empty string" in str(exc_info.value)

    def test_extra_keys(self):
        """Test that a record with extra keys fails validation."""
        invalid_record = {
            "fingerprint": [0.1] * EXPECTED_FINGERPRINT_LENGTH,
            "label": "SN2",
            "source_id": "NIST_12345",
            "provenance": "kinetic studies",
            "extra_field": "should_fail"
        }
        with pytest.raises(AssertionError) as exc_info:
            validate_fingerprint_schema(invalid_record)
        assert "unexpected keys" in str(exc_info.value)

    def test_non_list_fingerprint(self):
        """Test that a record with non-list fingerprint fails validation."""
        invalid_record = {
            "fingerprint": "not_a_list",
            "label": "SN2",
            "source_id": "NIST_12345",
            "provenance": "kinetic studies"
        }
        with pytest.raises(AssertionError) as exc_info:
            validate_fingerprint_schema(invalid_record)
        assert "must be a list or numpy array" in str(exc_info.value)