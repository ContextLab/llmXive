import os
import sys
import time
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from openneuro import client as openneuro_client

from config import get_dataset_ids, get_sample_limit
from models import Subject, BehavioralScore


def get_subject_list(dataset_id: str, sample_limit: int) -> List[str]:
    """
    Retrieve a list of subject IDs from the specified OpenNeuro dataset.
    Uses the OpenNeuro API to fetch subjects.
    """
    try:
        cli = openneuro_client.Client()
        # Fetch subjects for the dataset
        subjects = cli.get_subjects(dataset_id)
        # Filter and limit
        valid_subjects = [s['id'] for s in subjects if 'id' in s]
        return valid_subjects[:sample_limit]
    except Exception as e:
        print(f"Error fetching subjects for {dataset_id}: {e}", file=sys.stderr)
        return []


def download_dataset(dataset_id: str, output_dir: Path, subjects: List[str]) -> List[Subject]:
    """
    Download data for a specific dataset and list of subjects.
    Returns a list of Subject objects representing the successfully downloaded data.
    """
    downloaded_subjects = []
    cli = openneuro_client.Client()

    for subject_id in subjects:
        try:
            # Construct local path for the subject
            subject_path = output_dir / dataset_id / subject_id
            subject_path.mkdir(parents=True, exist_ok=True)

            # Fetch dataset metadata to check for behavioral files
            # OpenNeuro client usually requires downloading the whole dataset or specific files.
            # We'll attempt to download the 'participants.tsv' and 'sub-*/ses-*/sub-*.tsv' files
            # that might contain behavioral scores.

            # For this implementation, we simulate the download process by checking
            # the remote file list if the API supports it, or by attempting a download.
            # Since openneuro-py is a wrapper, we'll assume we can fetch file lists.
            
            # In a real scenario, we would iterate through files.
            # Here we assume the download logic populates the directory.
            # We need to find the behavioral file.
            
            # Attempt to locate behavioral data (Fluid Intelligence)
            # Usually in participants.tsv or sub-XXX/beh/sub-XXX_beh.tsv
            # We will scan the downloaded directory for TSV files after a mock download
            # or attempt to download specific files if the API allows.
            
            # For the purpose of this task, we assume the download function
            # effectively pulls the data. We then scan for the file.
            
            # Note: openneuro-py download command is usually: openneuro download -s dsXXX -t path
            # We invoke it via subprocess if the library doesn't expose a direct download method
            # for specific subjects easily.
            
            import subprocess
            cmd = [
                "openneuro", "download", 
                "--dataset", dataset_id, 
                "--output", str(output_dir),
                "--subject", subject_id
            ]
            # Run the download
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                print(f"Failed to download {subject_id}: {result.stderr}", file=sys.stderr)
                continue

            # Now scan for the behavioral file
            # Expected paths:
            # 1. {dataset_id}/participants.tsv (contains subject-level data)
            # 2. {dataset_id}/sub-{subject_id}/ses-.../sub-{subject_id}_beh.tsv
            
            behavioral_score = None
            score_file = None

            # Check participants.tsv
            participants_file = output_dir / dataset_id / "participants.tsv"
            if participants_file.exists():
                # Parse participants.tsv to find Fluid Intelligence
                import pandas as pd
                df = pd.read_csv(participants_file, sep='\t')
                # Look for columns containing 'Fluid' or 'Intelligence'
                # Common columns: 'FluidIntelligenceScore', 'FluidInt'
                fluid_cols = [c for c in df.columns if 'Fluid' in c or 'Intelligence' in c]
                
                if fluid_cols:
                    # Assume the first match is the score
                    col_name = fluid_cols[0]
                    if subject_id in df['participant_id'].values:
                        row = df[df['participant_id'] == subject_id]
                        if not row[col_name].isna().all():
                            try:
                                val = float(row[col_name].values[0])
                                behavioral_score = BehavioralScore(
                                    value=val,
                                    source=col_name,
                                    subject_id=subject_id
                                )
                                score_file = str(participants_file)
                            except (ValueError, TypeError):
                                pass

            # If not found in participants.tsv, check subject-specific files
            if not behavioral_score:
                # Search for TSV files in the subject directory
                sub_dir = output_dir / dataset_id / subject_id
                if sub_dir.exists():
                    for tsv_file in sub_dir.rglob("*.tsv"):
                        try:
                            df = pd.read_csv(tsv_file, sep='\t')
                            fluid_cols = [c for c in df.columns if 'Fluid' in c or 'Intelligence' in c]
                            if fluid_cols:
                                col_name = fluid_cols[0]
                                # Check if this row corresponds to the subject
                                # Usually subject TSVs have a single row or are indexed
                                if not df[col_name].isna().all():
                                    val = float(df[col_name].iloc[0])
                                    behavioral_score = BehavioralScore(
                                        value=val,
                                        source=col_name,
                                        subject_id=subject_id
                                    )
                                    score_file = str(tsv_file)
                                    break
                        except Exception:
                            continue

            if behavioral_score:
                subj_obj = Subject(
                    id=subject_id,
                    age=None, # Not strictly required for this task but good to have
                    gender=None,
                    raw_data_path=str(sub_dir),
                    behavioral_score=behavioral_score,
                    score_source_file=score_file
                )
                downloaded_subjects.append(subj_obj)
                print(f"Downloaded and validated: {subject_id} (Score: {behavioral_score.value})")
            else:
                # Subject downloaded but no score found
                print(f"Downloaded {subject_id} but no Fluid Intelligence score found. Skipping.", file=sys.stderr)

        except Exception as e:
            print(f"Error processing {subject_id}: {e}", file=sys.stderr)
            continue

    return downloaded_subjects


def validate_and_aggregate(
    subjects_ds000224: List[Subject],
    subjects_ds000230: List[Subject],
    sample_limit: int
) -> Tuple[List[Subject], Dict[str, Any]]:
    """
    Validates the presence of Fluid Intelligence scores and aggregates subjects.
    Halts with critical error if total N=0.
    Returns the aggregated list and a summary dict.
    """
    # Filter subjects that have a valid behavioral score
    valid_ds000224 = [s for s in subjects_ds000224 if s.behavioral_score is not None]
    valid_ds000230 = [s for s in subjects_ds000230 if s.behavioral_score is not None]

    total_valid = len(valid_ds000224) + len(valid_ds000230)
    
    summary = {
        "ds000224_total_downloaded": len(subjects_ds000224),
        "ds000224_valid_scores": len(valid_ds000224),
        "ds000230_total_downloaded": len(subjects_ds000230),
        "ds000230_valid_scores": len(valid_ds000230),
        "total_valid_subjects": total_valid,
        "status": "ok"
    }

    if total_valid == 0:
        summary["status"] = "critical_error"
        summary["error_message"] = "CRITICAL: No subjects with Fluid Intelligence scores found in either dataset."
        print("CRITICAL ERROR: No subjects with Fluid Intelligence scores found. Halting.", file=sys.stderr)
        # We raise an exception to halt the pipeline as per requirement
        raise ValueError(summary["error_message"])

    # Aggregate
    all_valid = valid_ds000224 + valid_ds000230
    
    # Apply sample limit if necessary (though download logic usually limits)
    if len(all_valid) > sample_limit:
        print(f"Warning: Total valid subjects ({len(all_valid)}) exceeds sample limit ({sample_limit}). Truncating.", file=sys.stderr)
        all_valid = all_valid[:sample_limit]
        summary["truncated_to"] = sample_limit

    return all_valid, summary


def main():
    """
    Main entry point for T014: Validation and Aggregation.
    This function assumes T013 has run and data is available, or it runs the download
    and validation in one go if T013 is integrated. 
    Given the task description, we implement the validation logic here.
    """
    config = get_dataset_ids()
    limit = get_sample_limit()
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Starting T014: Validation and Aggregation...")

    # 1. Fetch subject lists
    subjects_224 = get_subject_list(config[0], limit)
    subjects_230 = get_subject_list(config[1], limit)

    print(f"Found {len(subjects_224)} subjects in ds000224")
    print(f"Found {len(subjects_230)} subjects in ds000230")

    # 2. Download and validate (T013 logic integrated here for completeness of T014 flow)
    # Note: In a real pipeline, T013 might just download. Here we validate immediately.
    try:
        downloaded_224 = download_dataset(config[0], output_dir, subjects_224)
        downloaded_230 = download_dataset(config[1], output_dir, subjects_230)
    except Exception as e:
        print(f"Download failed: {e}", file=sys.stderr)
        sys.exit(1)

    # 3. Validate and Aggregate (The core of T014)
    try:
        final_subjects, summary = validate_and_aggregate(downloaded_224, downloaded_230, limit)
        
        # Write summary to data/processed
        processed_dir = Path("data/processed")
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        summary_path = processed_dir / "validation_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"Validation complete. Total valid subjects: {len(final_subjects)}")
        print(f"Summary written to {summary_path}")

        # Optionally write the list of valid subject IDs for downstream tasks
        subject_ids_path = processed_dir / "valid_subject_ids.txt"
        with open(subject_ids_path, 'w') as f:
            for s in final_subjects:
                f.write(f"{s.id}\n")
        
        return final_subjects, summary

    except ValueError as e:
        print(f"Pipeline halted: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
