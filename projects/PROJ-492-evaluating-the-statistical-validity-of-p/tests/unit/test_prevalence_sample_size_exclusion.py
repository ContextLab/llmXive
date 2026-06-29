"""
Test T042b: Verify that prevalence.json does not contain entries flagged for sample-size mismatch.

This test cross-checks the audit_report.json (from T025) against the output/prevalence.json
to ensure that any summary flagged with data_quality_warning for sample-size mismatch
is excluded from the prevalence calculations (per T025c requirement).
"""
import json
import pytest
from pathlib import Path
from typing import List, Dict, Any


def load_json_file(file_path: Path) -> List[Dict[str, Any]]:
    """Load a JSON file and return its contents as a list of records."""
    if not file_path.exists():
        pytest.fail(f"Required file not found: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # Handle both list and dict with records key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'records' in data:
        return data['records']
    elif isinstance(data, dict) and 'audit_records' in data:
        return data['audit_records']
    else:
        return [data] if data else []


def test_prevalence_excludes_sample_size_mismatch_entries():
    """
    Verify that prevalence.json does not contain any entries flagged for sample-size mismatch.

    This implements T042b by cross-checking:
    1. Load audit_report.json to find records with data_quality_warning for sample-size mismatch
    2. Load prevalence.json to get the records included in prevalence calculations
    3. Assert no overlap between flagged records and prevalence records
    """
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent.parent
    audit_report_path = project_root / 'output' / 'audit_report.json'
    prevalence_path = project_root / 'output' / 'prevalence.json'

    # Load audit report
    audit_records = load_json_file(audit_report_path)

    # Identify records flagged for sample-size mismatch
    sample_size_mismatch_ids = set()
    for record in audit_records:
        # Check for sample-size mismatch flag in various possible locations
        flags = record.get('flags', {}) or {}
        data_quality_warnings = record.get('data_quality_warnings', []) or []
        notes = record.get('notes', '') or ''

        # Check if any flag or warning indicates sample-size mismatch
        is_sample_size_mismatch = (
            flags.get('sample_size_mismatch', False) or
            any('sample_size' in str(w).lower() for w in data_quality_warnings) or
            'sample_size' in notes.lower() and 'mismatch' in notes.lower()
        )

        if is_sample_size_mismatch:
            # Extract unique identifier (url, id, or index)
            record_id = record.get('url') or record.get('id') or record.get('url_hash')
            if record_id:
                sample_size_mismatch_ids.add(record_id)

    # Load prevalence results
    prevalence_records = load_json_file(prevalence_path)

    # Get identifiers from prevalence records
    prevalence_ids = set()
    for record in prevalence_records:
        record_id = record.get('url') or record.get('id') or record.get('url_hash')
        if record_id:
            prevalence_ids.add(record_id)

    # Verify no overlap
    overlap = sample_size_mismatch_ids.intersection(prevalence_ids)

    if overlap:
        pytest.fail(
            f"Prevalence.json contains {len(overlap)} entries that were flagged for "
            f"sample-size mismatch in audit_report.json. "
            f"Overlapping IDs: {overlap}"
        )

    # Additional check: ensure prevalence.json was actually generated
    assert len(prevalence_records) > 0, "prevalence.json should contain at least one record"


def test_sample_size_mismatch_flagging_consistency():
    """
    Verify that the sample-size mismatch detection in validator.py is consistent
    with the filtering applied in prevalence.py.

    This ensures T025c and T042b requirements are aligned.
    """
    project_root = Path(__file__).parent.parent.parent
    audit_report_path = project_root / 'output' / 'audit_report.json'
    prevalence_path = project_root / 'output' / 'prevalence.json'

    # Load both files
    audit_records = load_json_file(audit_report_path)
    prevalence_records = load_json_file(prevalence_path)

    # Count flagged records
    flagged_count = 0
    for record in audit_records:
        flags = record.get('flags', {}) or {}
        if flags.get('sample_size_mismatch', False):
            flagged_count += 1

    # Verify the filter_for_prevalence function was called correctly
    # by checking that prevalence records don't include flagged ones
    prevalence_count = len(prevalence_records)
    audit_count = len(audit_records)

    # If there were flagged records, prevalence count should be less than audit count
    if flagged_count > 0:
        assert prevalence_count <= audit_count - flagged_count, (
            f"Expected prevalence count ({prevalence_count}) to be at most "
            f"audit count ({audit_count}) minus flagged count ({flagged_count})"
        )


def test_prevalence_json_structure_valid():
    """
    Verify that prevalence.json has the expected structure with required fields.
    """
    project_root = Path(__file__).parent.parent.parent
    prevalence_path = project_root / 'output' / 'prevalence.json'

    if not prevalence_path.exists():
        pytest.skip("prevalence.json not generated yet - run pipeline first")

    with open(prevalence_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Handle different possible structures
    if isinstance(data, list):
        records = data
    elif isinstance(data, dict):
        records = data.get('records', data.get('audit_records', [data]))
    else:
        records = []

    assert len(records) > 0, "prevalence.json should contain records"

    # Check for required fields in at least one record
    first_record = records[0]
    required_fields = ['inconsistent_rate', 'wilson_ci_lower', 'wilson_ci_upper']
    for field in required_fields:
        assert field in first_record, f"prevalence.json record missing required field: {field}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
