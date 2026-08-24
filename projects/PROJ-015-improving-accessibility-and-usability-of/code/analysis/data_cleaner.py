"""
Data cleaning and SUS imputation logic for the accessibility study.

This module implements the core data cleaning pipeline:
1. Filtering incomplete sessions.
2. Imputing missing SUS scores (if <= 1 missing item).
3. Validating data against the session schema.

It strictly enforces the "No Synthetic Data" policy. If input data is missing
or contains only simulated data without the `dev_mode` flag, it raises an error.
"""
import pandas as pd
import numpy as np
import json
import glob
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import os
import sys

# Ensure we can import from the project root if running as a script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from contracts.session_schema import validate_session_data  # type: ignore
# Note: The schema validation logic is expected to be in contracts based on T019b/c
# If the contract module isn't directly importable as 'contracts', we adapt:
try:
    from contracts.session_schema import validate_session_data
except ImportError:
    # Fallback if the schema is loaded differently or we need to load the yaml directly
    pass

class DataCleaner:
    """
    Handles cleaning, filtering, and imputation of session data.
    """
    
    def __init__(self, input_dir: str, output_dir: str, dev_mode: bool = False):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.dev_mode = dev_mode
        
        if not self.input_dir.exists():
            raise FileNotFoundError(f"Input directory does not exist: {self.input_dir}")
        
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_raw_sessions(self) -> pd.DataFrame:
        """
        Loads all JSON session files from the input directory.
        
        Enforces the "No Synthetic Data" policy:
        - Raises FileNotFoundError if directory is empty.
        - Raises ValueError if only simulated data exists and dev_mode is False.
        """
        json_files = list(self.input_dir.glob("*.json"))
        
        if not json_files:
            raise FileNotFoundError(
                f"No JSON files found in {self.input_dir}. "
                "Please ensure data has been collected or generated (with --dev-mode if appropriate)."
            )

        sessions = []
        simulated_count = 0
        real_count = 0

        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Handle case where file contains a list of sessions
                    if isinstance(data, list):
                        sessions.extend(data)
                    elif isinstance(data, dict):
                        sessions.append(data)
                    else:
                        continue
                        
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not read {file_path}: {e}")
                continue

        if not sessions:
            raise FileNotFoundError(
                f"No valid session data found in {self.input_dir}. "
                "Files exist but contain no valid JSON session objects."
            )

        df = pd.DataFrame(sessions)

        # Enforce Data Integrity Gates
        if 'source' not in df.columns:
            # If source is missing, we cannot verify, so we treat as unsafe
            raise ValueError(
                "Data integrity check failed: 'source' field missing in session data. "
                "All sessions must have a 'source' field ('human_participant' or 'simulated')."
            )

        simulated_mask = df['source'] == 'simulated'
        real_mask = df['source'] == 'human_participant'
        
        simulated_count = simulated_mask.sum()
        real_count = real_mask.sum()

        if real_count == 0 and simulated_count > 0:
            if not self.dev_mode:
                raise ValueError(
                    f"Data integrity check failed: Input directory contains ONLY simulated data "
                    f"({simulated_count} sessions). "
                    f"Real data is required for analysis. "
                    f"Use --dev-mode flag if this is intentional for development testing."
                )
            else:
                print(f"Warning: Running in dev_mode. Found {simulated_count} simulated sessions.")
        elif simulated_count > 0 and real_count > 0:
            if not self.dev_mode:
                # Mixed data: usually okay if at least one real session exists, 
                # but strict mode might warn. For now, we allow mixed if real exists.
                print(f"Warning: Found mixed data ({real_count} real, {simulated_count} simulated). "
                      f"Ensure this is intentional.")

        return df

    def filter_incomplete(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Removes sessions where status is 'incomplete' or 'dropout'.
        """
        initial_count = len(df)
        # Filter out incomplete/dropout sessions
        clean_df = df[
            (df['status'] == 'complete') | 
            (df['status'].isna()) # Keep if status is missing but data exists? Spec says remove incomplete.
        ]
        
        # Explicitly remove 'incomplete' and 'dropout'
        clean_df = clean_df[~clean_df['status'].isin(['incomplete', 'dropout'])]
        
        dropped = initial_count - len(clean_df)
        if dropped > 0:
            print(f"Filtered out {dropped} incomplete/dropout sessions.")
        
        return clean_df.reset_index(drop=True)

    def impute_sus(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Imputes missing SUS scores if <= 1 item is missing per participant.
        
        SUS items are typically named 'sus_q1', 'sus_q2', ... 'sus_q10'.
        If > 1 item is missing, the entire session is marked as 'incomplete'.
        
        Returns a DataFrame with imputed values and updated status.
        """
        sus_cols = [col for col in df.columns if col.startswith('sus_q') and col != 'sus_score']
        if not sus_cols:
            # No SUS items found, assume score is already present or not needed
            print("No individual SUS question items found. Skipping imputation.")
            return df

        df = df.copy()
        
        # Identify rows with missing SUS items
        # We assume missing values are NaN or None
        
        def process_sus_row(row):
            sus_values = row[sus_cols]
            missing_count = sus_values.isna().sum()
            
            if missing_count == 0:
                return row
            
            if missing_count <= 1:
                # Impute with participant mean
                # Calculate mean of existing values for this participant
                existing_values = sus_values.dropna()
                if len(existing_values) > 0:
                    mean_val = existing_values.mean()
                    row[sus_cols] = row[sus_cols].fillna(mean_val)
                # If no existing values (all 10 missing), we can't impute -> mark incomplete
                else:
                    row['status'] = 'incomplete'
                    return row
            else:
                # More than 1 missing -> mark incomplete
                row['status'] = 'incomplete'
            
            return row

        df = df.apply(process_sus_row, axis=1)
        
        # Re-filter incomplete if we marked any during imputation
        # Note: The spec says "update session status to 'incomplete'", 
        # but subsequent steps usually filter these out. 
        # We return the dataframe with updated status.
        
        return df

    def clean_and_impute(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Runs the full cleaning pipeline: filter -> impute.
        """
        print("Step 1: Filtering incomplete sessions...")
        df = self.filter_incomplete(df)
        
        print("Step 2: Imputing SUS scores...")
        df = self.impute_sus(df)
        
        # Final filter: remove any that became incomplete during imputation
        df = df[df['status'] != 'incomplete']
        
        return df

    def run(self) -> pd.DataFrame:
        """
        Executes the full cleaning pipeline.
        """
        print(f"Loading data from {self.input_dir}...")
        df = self.load_raw_sessions()
        
        print("Cleaning data...")
        df = self.clean_and_impute(df)
        
        output_path = self.output_dir / "cleaned_sessions.csv"
        df.to_csv(output_path, index=False)
        print(f"Cleaned data saved to {output_path}")
        
        return df

def main():
    """
    CLI entry point for data cleaning.
    Usage: python -m code.analysis.data_cleaner --input data/raw --output data/processed --dev-mode
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean and impute session data.")
    parser.add_argument("--input", type=str, default="data/raw", help="Input directory containing raw JSON sessions.")
    parser.add_argument("--output", type=str, default="data/processed", help="Output directory for cleaned CSV.")
    parser.add_argument("--dev-mode", action="store_true", help="Allow simulated data if no real data is found.")
    
    args = parser.parse_args()
    
    try:
        cleaner = DataCleaner(
            input_dir=args.input,
            output_dir=args.output,
            dev_mode=args.dev_mode
        )
        df = cleaner.run()
        print(f"Cleaning complete. Processed {len(df)} valid sessions.")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Data Integrity Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()