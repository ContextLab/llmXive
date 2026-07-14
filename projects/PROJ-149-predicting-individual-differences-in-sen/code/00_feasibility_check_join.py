import os
import sys
import json
import pandas as pd
from pathlib import Path

# Import from config to ensure paths and seeds are consistent
# We assume config.py is in the code directory or PYTHONPATH includes it
try:
    from config import get_path
except ImportError:
    # Fallback if running directly without full package setup
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_path


def load_physionet_metadata(data_root: Path) -> pd.DataFrame:
    """
    Load participant metadata from the downloaded PhysioNet EEG Motor Movement/Imagery dataset.
    
    The dataset structure after extraction typically contains subject folders.
    We infer participant IDs from the folder names (e.g., '001', '002', ...).
    Since the raw dataset does not contain explicit demographic CSVs, we construct
    a metadata frame based on available subject IDs and verify existence.
    
    Returns:
        pd.DataFrame: Columns ['participant_id', 'source', 'status']
    """
    subjects_dir = data_root / "EEG"
    if not subjects_dir.exists():
        # Try common extraction root
        subjects_dir = data_root / "physionet.org" / "datasets" / "eegmmidb" / "1.0.0" / "EEG"
    
    if not subjects_dir.exists():
        raise FileNotFoundError(f"Subject directory not found at {subjects_dir}")
    
    subject_ids = []
    for item in sorted(subjects_dir.iterdir()):
        if item.is_dir() and item.name.startswith("S"):
            # Extract numeric ID, e.g., S1 -> 1
            try:
                pid = int(item.name[1:])
                subject_ids.append(pid)
            except ValueError:
                continue
    
    if not subject_ids:
        raise ValueError("No valid subject directories found in EEG folder.")
    
    # Construct metadata
    df = pd.DataFrame({
        'participant_id': subject_ids,
        'source': 'physionet_eeg',
        'status': 'available'
    })
    return df


def load_behavioral_metadata(data_root: Path) -> pd.DataFrame:
    """
    Load behavioral (RT) metadata from the downloaded dataset.
    
    The PhysioNet EEGMMIDB dataset includes .mat files for each subject containing
    event information. For the purpose of this feasibility check, we scan for
    the existence of the corresponding .mat files to confirm behavioral data availability.
    We assume the standard naming convention: S<id>.mat exists in the subject folder.
    
    Returns:
        pd.DataFrame: Columns ['participant_id', 'source', 'has_behavioral', 'status']
    """
    subjects_dir = data_root / "EEG"
    if not subjects_dir.exists():
        subjects_dir = data_root / "physionet.org" / "datasets" / "eegmmidb" / "1.0.0" / "EEG"
    
    if not subjects_dir.exists():
        raise FileNotFoundError(f"Subject directory not found at {subjects_dir}")
    
    subject_ids = []
    behavioral_status = []
    
    for item in sorted(subjects_dir.iterdir()):
        if item.is_dir() and item.name.startswith("S"):
            try:
                pid = int(item.name[1:])
                # Check for .mat file (behavioral/event data)
                mat_file = item / f"{item.name}.mat"
                has_mat = mat_file.exists()
                subject_ids.append(pid)
                behavioral_status.append("available" if has_mat else "missing")
            except ValueError:
                continue
    
    if not subject_ids:
        raise ValueError("No valid subject directories found.")
    
    df = pd.DataFrame({
        'participant_id': subject_ids,
        'source': 'physionet_behavioral',
        'has_behavioral': [s == 'available' for s in behavioral_status],
        'status': behavioral_status
    })
    return df


def generate_report(eeg_df: pd.DataFrame, behavioral_df: pd.DataFrame, output_path: Path) -> dict:
    """
    Join EEG and behavioral datasets on participant_id and validate compatibility.
    
    Generates a feasibility report and returns a status dictionary.
    If the join fails or datasets are incompatible, returns a failure status.
    
    Args:
        eeg_df: DataFrame with EEG participant metadata
        behavioral_df: DataFrame with behavioral participant metadata
        output_path: Path to write the feasibility_report.md
    
    Returns:
        dict: Status information including success flag, counts, and errors
    """
    # Ensure participant_id is integer for join
    eeg_df = eeg_df.copy()
    behavioral_df = behavioral_df.copy()
    eeg_df['participant_id'] = eeg_df['participant_id'].astype(int)
    behavioral_df['participant_id'] = behavioral_df['participant_id'].astype(int)
    
    # Perform inner join to find common participants
    joined = pd.merge(
        eeg_df[['participant_id', 'source']], 
        behavioral_df[['participant_id', 'has_behavioral', 'status']], 
        on='participant_id', 
        how='inner',
        suffixes=('_eeg', '_behavioral')
    )
    
    total_eeg = len(eeg_df)
    total_behavioral = len(behavioral_df)
    total_joined = len(joined)
    
    # Validation checks
    errors = []
    if total_joined == 0:
        errors.append("CRITICAL: No common participants found between EEG and behavioral datasets.")
    elif total_joined < total_eeg * 0.5:
        errors.append(f"WARNING: Only {total_joined}/{total_eeg} EEG subjects have behavioral data.")
    
    # Generate Markdown Report
    report_lines = [
        "# Feasibility Check Report: EEG & Behavioral Data Join",
        "",
        "## Summary",
        f"- **Total EEG Subjects**: {total_eeg}",
        f"- **Total Behavioral Subjects**: {total_behavioral}",
        f"- **Joined Participants**: {total_joined}",
        "",
        "## Validation Results",
    ]
    
    if errors:
        report_lines.append("**Status: FAILED**")
        report_lines.append("")
        for err in errors:
            report_lines.append(f"- {err}")
    else:
        report_lines.append("**Status: PASSED**")
        report_lines.append("")
        report_lines.append("Datasets are compatible for analysis.")
    
    report_lines.append("")
    report_lines.append("## Joined Participant IDs")
    report_lines.append("")
    if not joined.empty:
        report_lines.append(f"Participants: {list(joined['participant_id'])}")
    else:
        report_lines.append("No participants found.")
    
    report_content = "\n".join(report_lines)
    
    # Write report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report_content)
    
    return {
        "success": total_joined > 0 and len(errors) == 0,
        "eeg_count": total_eeg,
        "behavioral_count": total_behavioral,
        "joined_count": total_joined,
        "errors": errors,
        "report_path": str(output_path)
    }


def main():
    """
    Main entry point for the feasibility check.
    Loads data, joins on participant_id, validates, and exits with code 1 if failed.
    """
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent
    data_root = project_root / "data" / "raw"
    output_path = project_root / "data" / "processed" / "feasibility_report.md"
    
    print(f"Scanning data root: {data_root}")
    
    try:
        eeg_df = load_physionet_metadata(data_root)
        print(f"Loaded {len(eeg_df)} EEG subjects.")
        
        behavioral_df = load_behavioral_metadata(data_root)
        print(f"Loaded {len(behavioral_df)} behavioral subjects.")
        
        status = generate_report(eeg_df, behavioral_df, output_path)
        
        print(f"Join result: {status['joined_count']} common participants.")
        
        if not status['success']:
            print("Feasibility check FAILED. See report for details.")
            sys.exit(1)
        
        print("Feasibility check PASSED.")
        sys.exit(0)
        
    except Exception as e:
        print(f"CRITICAL ERROR during feasibility check: {e}")
        # Attempt to write a failure report even on exception
        try:
            error_report = f"# Feasibility Check Failed\n\nError: {str(e)}\n"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(error_report)
        except:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()