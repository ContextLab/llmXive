"""
Manual verification script for T042b.

This script can be run directly (python tests/unit/test_prevalence_sample_size_exclusion_manual.py)
to manually inspect the cross-check between audit_report.json and prevalence.json.
"""
import json
import sys
from pathlib import Path
from typing import List, Dict, Any


def load_json_file(file_path: Path) -> List[Dict[str, Any]]:
    """Load a JSON file and return its contents as a list of records."""
    if not file_path.exists():
        print(f"ERROR: Required file not found: {file_path}")
        sys.exit(1)
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'records' in data:
        return data['records']
    elif isinstance(data, dict) and 'audit_records' in data:
        return data['audit_records']
    else:
        return [data] if data else []


def check_sample_size_exclusion():
    """
    Manually verify that prevalence.json excludes sample-size mismatch entries.
    """
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent.parent

    audit_report_path = project_root / 'output' / 'audit_report.json'
    prevalence_path = project_root / 'output' / 'prevalence.json'

    print("=" * 70)
    print("T042b Verification: Sample-Size Mismatch Exclusion Check")
    print("=" * 70)

    # Load files
    print(f"\nLoading audit report from: {audit_report_path}")
    audit_records = load_json_file(audit_report_path)
    print(f"  Found {len(audit_records)} audit records")

    print(f"\nLoading prevalence results from: {prevalence_path}")
    prevalence_records = load_json_file(prevalence_path)
    print(f"  Found {len(prevalence_records)} prevalence records")

    # Identify sample-size mismatch records
    print("\n" + "-" * 70)
    print("Identifying sample-size mismatch flagged records...")
    print("-" * 70)

    sample_size_mismatch_records = []
    for i, record in enumerate(audit_records):
        flags = record.get('flags', {}) or {}
        data_quality_warnings = record.get('data_quality_warnings', []) or []
        notes = record.get('notes', '') or ''

        is_mismatch = (
            flags.get('sample_size_mismatch', False) or
            any('sample_size' in str(w).lower() for w in data_quality_warnings) or
            ('sample_size' in notes.lower() and 'mismatch' in notes.lower())
        )

        if is_mismatch:
            record_id = record.get('url') or record.get('id') or f"record_{i}"
            sample_size_mismatch_records.append({
                'index': i,
                'id': record_id,
                'flags': flags,
                'warnings': data_quality_warnings
            })

    print(f"\nFound {len(sample_size_mismatch_records)} records flagged for sample-size mismatch:")
    for record in sample_size_mismatch_records[:5]:  # Show first 5
        print(f"  - {record['id']}")
    if len(sample_size_mismatch_records) > 5:
        print(f"  ... and {len(sample_size_mismatch_records) - 5} more")

    # Check prevalence records
    print("\n" + "-" * 70)
    print("Checking prevalence records for excluded entries...")
    print("-" * 70)

    prevalence_ids = set()
    for record in prevalence_records:
        record_id = record.get('url') or record.get('id') or record.get('url_hash')
        if record_id:
            prevalence_ids.add(record_id)

    # Find any overlap
    overlap = []
    for mismatch_record in sample_size_mismatch_records:
        if mismatch_record['id'] in prevalence_ids:
            overlap.append(mismatch_record['id'])

    # Report results
    print("\n" + "=" * 70)
    print("VERIFICATION RESULT")
    print("=" * 70)

    if overlap:
        print(f"❌ FAILED: Found {len(overlap)} sample-size mismatch entries in prevalence.json:")
        for entry in overlap:
            print(f"  - {entry}")
        print("\nThese entries should have been excluded per T025c requirement.")
        sys.exit(1)
    else:
        print("✅ PASSED: No sample-size mismatch entries found in prevalence.json")
        print(f"  - Total audit records: {len(audit_records)}")
        print(f"  - Sample-size mismatch flagged: {len(sample_size_mismatch_records)}")
        print(f"  - Prevalence records: {len(prevalence_records)}")
        print(f"  - Excluded records: {len(audit_records) - len(prevalence_records)}")
        print("\nT042b verification successful: prevalence.json correctly excludes")
        print("all entries flagged for sample-size mismatch.")
        sys.exit(0)


if __name__ == '__main__':
    check_sample_size_exclusion()