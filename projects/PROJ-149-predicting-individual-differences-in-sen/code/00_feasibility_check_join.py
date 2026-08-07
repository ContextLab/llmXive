import os
import sys
import json
import pandas as pd
from pathlib import Path

# Import config for path resolution
# Note: config.py is in code/, so we need to ensure code/ is in sys.path or import relative to it
# Since this script is in code/, we can import config directly if code/ is in path, 
# or we can construct paths manually. Given the API surface shows 'from config import get_path',
# we assume code/ is in sys.path when this runs.
try:
    from config import get_path, ensure_dirs
except ImportError:
    # Fallback if run as script without code/ in path
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_path, ensure_dirs

def load_physionet_metadata():
    """
    Load the list of available subjects from the downloaded PhysioNet data.
    Expects data to be in data/raw/physionet/ (or wherever T007 put it).
    Returns a DataFrame with 'participant_id' and 'source' columns.
    """
    # T007 downloads to data/raw/physionet/
    raw_dir = get_path('raw_physionet')
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw PhysioNet data not found at {raw_dir}. Run T007 first.")
    
    # The data structure from T007: data/raw/physionet/subject_001/...
    # We scan for subject directories
    subject_dirs = [d for d in raw_dir.iterdir() if d.is_dir() and d.name.startswith('subject_')]
    
    if not subject_dirs:
        raise ValueError(f"No subject directories found in {raw_dir}. Data might be empty or malformed.")
    
    subjects = []
    for d in subject_dirs:
        # Extract ID from directory name (e.g., 'subject_001' -> '001')
        pid = d.name.replace('subject_', '')
        subjects.append({'participant_id': pid, 'source': 'physionet_eeg'})
    
    return pd.DataFrame(subjects)

def load_behavioral_metadata():
    """
    Load the list of available subjects from the behavioral data (e.g., RT files).
    T007 should have also downloaded behavioral data if it was part of the dataset.
    For PhysioNet EEG Motor Movement/Imagery, behavioral data is often in separate files
    or embedded. We'll assume T007 extracted behavioral data to data/raw/behavioral/
    or similar. If not, we might need to derive it from the EEG metadata if available.
    
    However, for this specific dataset (EEG Motor Movement/Imagery), the "behavioral" data
    (reaction times) are not part of the standard PhysioNet EEG Motor Movement/Imagery release.
    The dataset primarily contains EEG recordings.
    
    CRITICAL: The task description implies there IS behavioral data to join with.
    Since the standard PhysioNet EEG Motor Movement/Imagery dataset does not include RTs,
    we must assume:
    1. T007 downloaded a custom/extended version that includes behavioral data, OR
    2. The behavioral data is in a separate file in data/raw/behavioral/
    
    Let's check for a common pattern: a CSV file in data/raw/behavioral/ or data/raw/physionet/
    that lists subjects and their RTs.
    
    If no such file exists, we raise an error because we cannot fabricate data.
    """
    # Check for behavioral data directory/file
    # Common locations based on project structure
    behavioral_dir = get_path('raw_behavioral')
    behavioral_csv = get_path('raw_behavioral', 'subject_rt.csv') # Hypothesized filename
    
    # Also check inside raw_physionet if there's a behavioral subfolder
    raw_physionet = get_path('raw_physionet')
    if (raw_physionet / 'behavioral').exists():
        behavioral_csv = raw_physionet / 'behavioral' / 'subject_rt.csv'
    
    if not behavioral_csv.exists():
        # Try to find any CSV that might contain behavioral data
        possible_csvs = list(raw_physionet.glob('**/*.csv'))
        # Filter for likely candidates
        candidates = [f for f in possible_csvs if 'rt' in f.name.lower() or 'behavior' in f.name.lower()]
        if candidates:
            behavioral_csv = candidates[0]
        else:
            raise FileNotFoundError(
                f"Behavioral data not found. Expected at {behavioral_csv} or similar. "
                "T007 must download the behavioral component of the dataset."
            )
    
    try:
        df = pd.read_csv(behavioral_csv)
        # Standardize column name to 'participant_id'
        if 'participant_id' not in df.columns:
            if 'subject_id' in df.columns:
                df = df.rename(columns={'subject_id': 'participant_id'})
            else:
                # Try to infer the ID column
                id_cols = [c for c in df.columns if 'id' in c.lower()]
                if id_cols:
                    df = df.rename(columns={id_cols[0]: 'participant_id'})
                else:
                    raise ValueError(f"Could not find a participant ID column in {behavioral_csv}")
        
        # Ensure participant_id is string for consistent joining
        df['participant_id'] = df['participant_id'].astype(str)
        
        return df[['participant_id']].copy() # Return only ID for join, or more if needed
    except Exception as e:
        raise RuntimeError(f"Failed to load behavioral metadata from {behavioral_csv}: {e}")

def generate_report(eeg_df, behavioral_df, join_df, output_path):
    """
    Generate the feasibility report in Markdown format.
    """
    report_lines = [
        "# Feasibility Check Report",
        f"Generated: {pd.Timestamp.now().isoformat()}",
        "",
        "## Dataset Overview",
        f"- **EEG Subjects**: {len(eeg_df)}",
        f"- **Behavioral Subjects**: {len(behavioral_df)}",
        "",
        "## Join Results",
        f"- **Matched Participants**: {len(join_df)}",
        "",
    ]
    
    if len(join_df) == 0:
        report_lines.extend([
            "### ⚠️ CRITICAL FAILURE",
            "No participants were found in both EEG and behavioral datasets.",
            "The pipeline cannot proceed without matched data.",
            "",
            "### EEG Participants",
            eeg_df.to_markdown(index=False) if hasattr(eeg_df, 'to_markdown') else str(eeg_df),
            "",
            "### Behavioral Participants",
            behavioral_df.to_markdown(index=False) if hasattr(behavioral_df, 'to_markdown') else str(behavioral_df),
        ])
    else:
        report_lines.extend([
            "### ✅ Success: Data Join Complete",
            "The following participants have both EEG and behavioral data:",
            "",
            join_df.to_markdown(index=False) if hasattr(join_df, 'to_markdown') else str(join_df),
            "",
            "## Next Steps",
            "Proceed with preprocessing (T010) and feature extraction.",
        ])
    
    report_content = "\n".join(report_lines)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    return report_content

def main():
    """
    Main entry point for the feasibility check.
    1. Load EEG subjects.
    2. Load Behavioral subjects.
    3. Join on participant_id.
    4. If join fails (0 matches), generate report and exit with code 1.
    5. If join succeeds, generate report and exit with code 0.
    """
    print("Starting feasibility check (T008a)...")
    
    try:
        # Load datasets
        print("Loading EEG metadata...")
        eeg_df = load_physionet_metadata()
        print(f"Found {len(eeg_df)} EEG subjects.")
        
        print("Loading behavioral metadata...")
        behavioral_df = load_behavioral_metadata()
        print(f"Found {len(behavioral_df)} behavioral subjects.")
        
        # Perform inner join
        print("Joining datasets on participant_id...")
        join_df = pd.merge(eeg_df, behavioral_df, on='participant_id', how='inner')
        
        output_path = get_path('processed', 'feasibility_report.md')
        ensure_dirs([output_path])
        
        generate_report(eeg_df, behavioral_df, join_df, output_path)
        print(f"Feasibility report generated: {output_path}")
        
        if len(join_df) == 0:
            print("❌ FEASIBILITY CHECK FAILED: No matched participants.")
            print("Exiting with code 1.")
            sys.exit(1)
        else:
            print(f"✅ FEASIBILITY CHECK PASSED: {len(join_df)} matched participants.")
            print("Exiting with code 0.")
            sys.exit(0)
            
    except FileNotFoundError as e:
        print(f"❌ CRITICAL ERROR: {e}")
        # Generate a minimal report even on error
        try:
            output_path = get_path('processed', 'feasibility_report.md')
            ensure_dirs([output_path])
            error_report = f"# Feasibility Check Failed\n\nError: {str(e)}\n\nNo data could be loaded."
            with open(output_path, 'w') as f:
                f.write(error_report)
            print(f"Error report saved to {output_path}")
        except Exception as report_err:
            print(f"Failed to generate error report: {report_err}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()