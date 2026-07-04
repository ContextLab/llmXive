import pandas as pd
from typing import List, Optional
from utils.logger import get_logger
import json
import glob
from pathlib import Path

class DataCleaner:
    def __init__(self):
        self.logger = get_logger("data_cleaner")

    def load_raw_sessions(self, raw_dir: str) -> pd.DataFrame:
        """
        Load all JSON session files from the raw directory into a single DataFrame.
        Expects files matching 'session_*.json' pattern.
        """
        raw_path = Path(raw_dir)
        if not raw_path.exists():
            self.logger.error(f"Raw directory does not exist: {raw_dir}")
            return pd.DataFrame()

        json_files = list(raw_path.glob("session_*.json"))
        if not json_files:
            self.logger.warning(f"No session files found in {raw_dir}")
            return pd.DataFrame()

        records = []
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Flatten specific nested fields if necessary, or keep as is
                    # Based on T019, we expect specific top-level keys
                    records.append(data)
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse {file_path}: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error reading {file_path}: {e}")

        df = pd.DataFrame(records)
        self.logger.info(f"Loaded {len(df)} sessions from {raw_dir}")
        return df

    def filter_incomplete(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter out sessions where status is not 'complete'.
        Logs the count of dropped sessions and their reasons if available.
        """
        if df.empty:
            return df

        initial_count = len(df)
        # Keep only rows where status is explicitly 'complete'
        # T020 ensures 'dropout_reason' is logged for incomplete
        complete_df = df[df['status'] == 'complete'].copy()
        dropped_count = initial_count - len(complete_df)

        if dropped_count > 0:
            dropped_sessions = df[df['status'] != 'complete']
            reasons = dropped_sessions['dropout_reason'].tolist()
            self.logger.info(f"Filtered {dropped_count} incomplete sessions. Reasons: {reasons}")
        
        return complete_df

    def impute_sus(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply SUS imputation logic per EC-001:
        - If > 1 missing items in SUS questions (1-10), reject the session (drop row).
        - If <= 1 missing items, impute the missing value with the mean of the participant's other responses.
        
        Assumes columns: sus_1, sus_2, ..., sus_10.
        """
        if df.empty:
            return df

        sus_columns = [f'sus_{i}' for i in range(1, 11)]
        missing_cols = [col for col in sus_columns if col not in df.columns]
        
        if missing_cols:
            self.logger.warning(f"Expected SUS columns missing from data: {missing_cols}. Skipping imputation.")
            return df

        rows_to_drop = []
        
        for idx, row in df.iterrows():
            sus_values = row[sus_columns]
            # Check for NaN (missing) values
            is_missing = sus_values.isna()
            missing_count = is_missing.sum()

            if missing_count > 1:
                self.logger.warning(f"Session {row.get('session_id', idx)} has {missing_count} missing SUS values (>1). Dropping session.")
                rows_to_drop.append(idx)
            elif missing_count == 1:
                # Impute: mean of non-missing values for this participant
                valid_values = sus_values[~is_missing]
                if len(valid_values) > 0:
                    mean_val = valid_values.mean()
                    df.at[idx, sus_columns[is_missing][0]] = mean_val
                    self.logger.info(f"Session {row.get('session_id', idx)}: Imputed 1 missing SUS value with mean {mean_val:.2f}")
                else:
                    # All missing? Technically >1 missing logic applies if we consider 0 valid as >1 missing relative to 10, 
                    # but strictly 10 missing is >1. If only 1 is missing and 9 are present, we impute.
                    # If 10 are missing, missing_count is 10, handled above.
                    pass

        if rows_to_drop:
            df = df.drop(index=rows_to_drop)
            self.logger.info(f"Dropped {len(rows_to_drop)} sessions due to excessive missing SUS data.")

        return df

def main():
    """
    Entry point for the data cleaner script.
    Loads raw data, filters incomplete sessions, imputes SUS, and saves to processed.
    """
    logger = get_logger("data_cleaner_main")
    raw_dir = "data/raw"
    processed_dir = "data/processed"
    
    # Ensure processed directory exists
    Path(processed_dir).mkdir(parents=True, exist_ok=True)
    
    cleaner = DataCleaner()
    
    logger.info("Starting data cleaning pipeline...")
    df = cleaner.load_raw_sessions(raw_dir)
    
    if df.empty:
        logger.warning("No data loaded. Exiting.")
        return

    logger.info(f"Initial dataset size: {len(df)}")
    
    df_clean = cleaner.filter_incomplete(df)
    logger.info(f"After filtering incomplete: {len(df_clean)}")
    
    df_final = cleaner.impute_sus(df_clean)
    logger.info(f"After SUS imputation: {len(df_final)}")
    
    output_path = Path(processed_dir) / "cleaned_sessions.csv"
    df_final.to_csv(output_path, index=False)
    logger.info(f"Cleaned data saved to {output_path}")

if __name__ == "__main__":
    main()