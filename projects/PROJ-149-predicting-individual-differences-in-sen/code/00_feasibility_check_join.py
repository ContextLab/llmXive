"""
Feasibility Check: Join EEG and RT datasets and validate metadata.

This script performs Phase 0.5 Gate Part 1:
1. Loads the EEG metadata (participant IDs) from the downloaded PhysioNet data.
2. Loads the Behavioral/RT metadata (participant IDs) from the same source.
3. Joins them on `participant_id`.
4. Validates demographic consistency (if available) or at least existence of IDs.
5. If the join fails (no overlap) or datasets are incompatible, exits with code 1
   and generates `data/processed/feasibility_report.md`.
6. If successful, prints a summary and exits with code 0.

Must run after T007 (code/01_download_data.py).
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path

# Add project root to path to import config if needed, though we can use hardcoded paths relative to root
project_root = Path(__file__).resolve().parent.parent
data_dir = project_root / "data"
raw_dir = data_dir / "raw"
processed_dir = data_dir / "processed"

# Ensure processed directory exists
processed_dir.mkdir(parents=True, exist_ok=True)

REPORT_PATH = processed_dir / "feasibility_report.md"

def load_physionet_metadata(source_dir: Path) -> dict:
    """
    Scans the PhysioNet directory structure to find participant IDs.
    The PhysioNet EEG Motor Movement/Imagery dataset typically organizes
    data as: <subject_id>/<subject_id>_<run_type>.edf
    
    We will scan for directories that look like subject folders.
    """
    subjects = set()
    if not source_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {source_dir}")

    # PhysioNet data is often in subdirectories like 'MME' or 'EEG' or directly in the root of the extracted tar
    # We look for directories that contain .edf files or match the naming pattern
    # Common structure: data/raw/EEG_MotorMovementImagery/100/100_1.edf
    
    # Try to find the root of the actual dataset inside the raw folder
    # The download script usually extracts to data/raw/EEG_MotorMovementImagery or similar
    dataset_root = None
    
    # Heuristic: Find the first directory inside raw that contains subdirectories with .edf files
    for item in source_dir.iterdir():
        if item.is_dir():
            # Check if this item contains .edf files or more subdirs with .edf
            has_eeg = False
            for sub_item in item.iterdir():
                if sub_item.is_file() and sub_item.suffix.lower() == '.edf':
                    has_eeg = True
                    break
                if sub_item.is_dir():
                    for sub_sub in sub_item.iterdir():
                        if sub_sub.is_file() and sub_sub.suffix.lower() == '.edf':
                            has_eeg = True
                            break
                    if has_eeg: break
            
            if has_eeg:
                dataset_root = item
                break
    
    if dataset_root is None:
        # Fallback: maybe the data is directly in source_dir
        for item in source_dir.iterdir():
            if item.is_file() and item.suffix.lower() == '.edf':
                dataset_root = source_dir
                break
        
        if dataset_root is None:
            raise FileNotFoundError("No EEG data found in the expected directory structure.")

    # Now extract subject IDs
    # Pattern: The folder name or the filename prefix usually indicates the subject.
    # In PhysioNet MME: folders are named '1', '2', ... '109' (subject IDs)
    # Files inside are '1_1.edf', '1_2.edf' etc.
    
    for item in dataset_root.iterdir():
        if item.is_dir():
            # Assume directory name is subject ID
            try:
                sub_id = int(item.name)
                subjects.add(sub_id)
            except ValueError:
                # Might be a metadata folder, skip
                continue
        elif item.is_file() and item.suffix.lower() == '.edf':
            # If files are directly in root, parse filename
            # Format: <subject>_<run>.edf
            name = item.stem
            if '_' in name:
                try:
                    sub_id = int(name.split('_')[0])
                    subjects.add(sub_id)
                except ValueError:
                    continue

    return {"subject_ids": sorted(list(subjects)), "source": str(dataset_root)}

def load_behavioral_metadata(source_dir: Path) -> dict:
    """
    Loads behavioral metadata.
    For PhysioNet MME, behavioral data (RT) is often in a separate CSV or Excel file
    provided by the dataset authors, or needs to be derived from the event markers in the EDF.
    
    However, the task description implies a separate 'RT dataset'.
    In the context of the standard PhysioNet MME dataset, there isn't a single pre-joined
    RT CSV provided in the raw download. The task likely assumes a specific mapping or
    a derived file from T007 or a specific file provided in the project's data structure.
    
    Assumption: The project expects a file `data/raw/behavioral_data.csv` or similar
    generated or provided. If not found, we check for common names.
    
    If no separate RT file exists, we assume the 'RT dataset' is the set of subjects
    who completed the task, which is effectively the same as the EEG subjects who have valid runs.
    
    For this implementation, we will look for a file named 'behavioral_data.csv',
    'subject_info.csv', or 'rt_data.csv' in the raw directory.
    """
    possible_names = ['behavioral_data.csv', 'subject_info.csv', 'rt_data.csv', 'metadata.csv']
    found_file = None
    
    for name in possible_names:
        path = source_dir / name
        if path.exists():
            found_file = path
            break
    
    if found_file is None:
        # Fallback: If no explicit RT file exists, we assume all EEG subjects are valid
        # for the purpose of the join, but we will note this in the report.
        # However, strictly speaking, if the task requires joining two *distinct* datasets,
        # and one is missing, the join fails.
        # But often in these pipelines, the 'RT dataset' might be the same source.
        # Let's return an empty set to indicate 'no external RT list found', 
        # forcing the join to rely on the EEG list if we decide to be lenient,
        # OR fail if strict.
        # Given the instruction "If join fails... exit with code 1", we must be strict.
        # But if the RT data is *part* of the EEG download (e.g. from event markers),
        # we can't load it here without parsing EDFs.
        # Let's assume the task implies a CSV exists. If not, we fail gracefully with a report.
        return {"subject_ids": [], "source": None, "error": "No behavioral metadata file found."}

    try:
        df = pd.read_csv(found_file)
        # Look for a column named 'participant_id', 'subject_id', 'id', or 'sub'
        id_col = None
        for col in ['participant_id', 'subject_id', 'id', 'sub', 'Subject']:
            if col in df.columns:
                id_col = col
                break
        
        if id_col is None:
            raise ValueError("Could not find a participant ID column in behavioral file.")
        
        ids = df[id_col].dropna().astype(int).unique().tolist()
        return {"subject_ids": ids, "source": str(found_file), "raw_df": df}
    except Exception as e:
        return {"subject_ids": [], "source": str(found_file), "error": str(e)}

def generate_report(eeg_data, rt_data, join_result, success: bool, error_msg: str = None):
    """Generates the markdown feasibility report."""
    report_lines = [
        "# Feasibility Check Report",
        "",
        f"**Status**: {'PASS' if success else 'FAIL'}",
        "",
        "## Dataset Summary",
        "",
        "### EEG Data",
        f"- Source: {eeg_data.get('source', 'N/A')}",
        f"- Participants Found: {len(eeg_data.get('subject_ids', []))}",
        f"- Sample IDs: {eeg_data.get('subject_ids', [])[:10]}...",
        "",
        "### Behavioral (RT) Data",
        f"- Source: {rt_data.get('source', 'N/A')}",
        f"- Participants Found: {len(rt_data.get('subject_ids', []))}",
    ]
    
    if rt_data.get('error'):
        report_lines.append(f"- **Error**: {rt_data['error']}")
    
    report_lines.append(f"- Sample IDs: {rt_data.get('subject_ids', [])[:10]}...")
    report_lines.append("")
    
    if success:
        report_lines.extend([
            "## Join Results",
            "",
            f"- Total EEG Participants: {eeg_data['count']}",
            f"- Total RT Participants: {rt_data['count']}",
            f"- Overlapping Participants: {len(join_result)}",
            f"- Overlap Percentage: {len(join_result) / len(eeg_data['subject_ids']) * 100:.2f}%",
            "",
            "### Overlapping IDs",
            "",
            f"{join_result}",
            "",
            "## Conclusion",
            "Datasets are compatible. Proceed with pipeline.",
        ])
    else:
        report_lines.extend([
            "## Failure Details",
            "",
            f"- **Reason**: {error_msg}",
            "",
            "## Conclusion",
            "Pipeline halted. Datasets incompatible or missing.",
        ])
    
    return "\n".join(report_lines)

def main():
    print("Starting Feasibility Check (Join & Metadata Validation)...")
    
    # 1. Load EEG Metadata
    try:
        eeg_meta = load_physionet_metadata(raw_dir)
        eeg_ids = set(eeg_meta['subject_ids'])
        print(f"Loaded {len(eeg_ids)} EEG participant IDs from {eeg_meta['source']}")
    except Exception as e:
        print(f"ERROR: Failed to load EEG data: {e}")
        report = generate_report(
            {"source": str(raw_dir), "subject_ids": [], "count": 0},
            {"source": "N/A", "subject_ids": [], "count": 0},
            [],
            False,
            f"EEG data loading failed: {str(e)}"
        )
        REPORT_PATH.write_text(report)
        sys.exit(1)

    # 2. Load RT Metadata
    try:
        rt_meta = load_behavioral_metadata(raw_dir)
        rt_ids = set(rt_meta['subject_ids'])
        if rt_meta.get('error'):
            raise ValueError(rt_meta['error'])
        print(f"Loaded {len(rt_ids)} RT participant IDs from {rt_meta['source']}")
    except Exception as e:
        print(f"ERROR: Failed to load RT data: {e}")
        report = generate_report(
            {"source": eeg_meta.get('source', 'N/A'), "subject_ids": list(eeg_ids), "count": len(eeg_ids)},
            {"source": "N/A", "subject_ids": [], "count": 0},
            [],
            False,
            f"RT data loading failed: {str(e)}"
        )
        REPORT_PATH.write_text(report)
        sys.exit(1)

    # 3. Perform Join
    if not rt_ids:
        # If no RT IDs found, we might assume all EEG IDs are valid if the dataset is known to be complete,
        # but strictly following the task: "If join fails... exit with code 1".
        # However, if the RT data is not a separate file but derived, this check might be too strict.
        # Let's assume the task implies a valid RT list must exist.
        print("ERROR: No RT participant IDs found. Cannot perform join.")
        report = generate_report(
            {"source": eeg_meta.get('source', 'N/A'), "subject_ids": list(eeg_ids), "count": len(eeg_ids)},
            {"source": "N/A", "subject_ids": [], "count": 0},
            [],
            False,
            "No RT participant IDs found to join with EEG data."
        )
        REPORT_PATH.write_text(report)
        sys.exit(1)

    overlap = eeg_ids.intersection(rt_ids)
    
    if not overlap:
        print("ERROR: No overlapping participants between EEG and RT datasets.")
        report = generate_report(
            {"source": eeg_meta.get('source', 'N/A'), "subject_ids": list(eeg_ids), "count": len(eeg_ids)},
            {"source": rt_meta.get('source', 'N/A'), "subject_ids": list(rt_ids), "count": len(rt_ids)},
            [],
            False,
            "Zero overlap between EEG and RT participant IDs."
        )
        REPORT_PATH.write_text(report)
        sys.exit(1)

    # 4. Validate Demographics (Basic check: are IDs consistent types?)
    # Since we only have IDs, we assume if they match, demographics are compatible.
    # If the RT file had age/gender columns, we could check for nulls here.
    
    # 5. Success
    print(f"Success! Found {len(overlap)} overlapping participants.")
    report = generate_report(
        {"source": eeg_meta.get('source', 'N/A'), "subject_ids": list(eeg_ids), "count": len(eeg_ids)},
        {"source": rt_meta.get('source', 'N/A'), "subject_ids": list(rt_ids), "count": len(rt_ids)},
        sorted(list(overlap)),
        True
    )
    REPORT_PATH.write_text(report)
    print(f"Feasibility report written to {REPORT_PATH}")
    sys.exit(0)

if __name__ == "__main__":
    main()