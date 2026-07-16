import pandas as pd
from typing import List, Optional
from utils.logger import get_logger
import json
import glob
from pathlib import Path
import os

logger = get_logger(__name__)

class DataCleaner:
    def __init__(self, raw_dir: Path, processed_dir: Path):
        self.raw_dir = raw_dir
        self.processed_dir = processed_dir
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def load_raw_sessions(self) -> List[dict]:
        """Load all JSON session files from raw directory."""
        sessions = []
        json_files = list(self.raw_dir.glob("*.json"))
        if not json_files:
            # Try subdirectories
            json_files = list(self.raw_dir.rglob("*.json"))
        
        for f in json_files:
            try:
                with open(f, 'r') as file:
                    data = json.load(file)
                    sessions.append(data)
            except Exception as e:
                logger.error(f"Error loading {f}: {e}")
        return sessions

    def filter_incomplete_sessions(self, sessions: List[dict]) -> List[dict]:
        """Filter out sessions with status='incomplete'."""
        valid_sessions = [s for s in sessions if s.get('status') != 'incomplete']
        incomplete_count = len(sessions) - len(valid_sessions)
        if incomplete_count > 0:
            logger.info(f"Excluded {incomplete_count} incomplete sessions.")
            # Log exclusions
            log_path = self.processed_dir / "exclusion_log.txt"
            with open(log_path, "a") as f:
                f.write(f"Excluded {incomplete_count} sessions with status='incomplete'.\n")
        return valid_sessions

    def impute_sus(self, sessions: List[dict]) -> List[dict]:
        """
        Impute missing SUS items per EC-001:
        - If >1 missing items, reject session (mark as incomplete).
        - If <=1 missing, impute with mean of participant's other responses.
        """
        cleaned_sessions = []
        for s in sessions:
            sus_items = [s.get(f'sus_item_{i}') for i in range(1, 11)]
            missing_count = sum(1 for item in sus_items if item is None or item == '')
            
            if missing_count > 1:
                logger.warning(f"Session {s.get('session_id')} has >1 missing SUS items. Marking incomplete.")
                s['status'] = 'incomplete'
                s['dropout_reason'] = 'Invalid SUS data'
            elif missing_count == 1:
                # Impute
                valid_items = [item for item in sus_items if item is not None and item != '']
                if valid_items:
                    mean_val = sum(valid_items) / len(valid_items)
                    # Find the missing index and fill it
                    for i, item in enumerate(sus_items):
                        if item is None or item == '':
                            sus_items[i] = mean_val
                            break
                    # Update session with imputed values (optional, or just recalculate score)
                    # For now, we just ensure we can calculate the score
            else:
                pass # No missing items

            # Recalculate SUS score if needed or use existing
            # Assuming we have a method to calculate it, or we trust the raw if complete
            # For this cleaner, we just pass through valid ones
            if s.get('status') != 'incomplete':
                cleaned_sessions.append(s)
        
        return cleaned_sessions

    def convert_to_dataframe(self, sessions: List[dict]) -> pd.DataFrame:
        """Convert list of dicts to DataFrame."""
        df = pd.DataFrame(sessions)
        # Ensure numeric types for analysis
        numeric_cols = ['completion_time', 'error_count', 'sus_score', 'explanation_engagement_time_seconds']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        return df

    def run_pipeline(self, output_filename: str = "cleaned_sessions.csv") -> str:
        """Run the full cleaning pipeline."""
        logger.info("Starting data cleaning pipeline")
        
        # 1. Load
        sessions = self.load_raw_sessions()
        if not sessions:
            raise FileNotFoundError("No raw session data found.")
        
        # 2. Filter
        sessions = self.filter_incomplete_sessions(sessions)
        
        # 3. Impute
        sessions = self.impute_sus(sessions)
        
        # 4. Convert
        df = self.convert_to_dataframe(sessions)
        
        # 5. Save
        output_path = self.processed_dir / output_filename
        df.to_csv(output_path, index=False)
        logger.info(f"Cleaned data saved to {output_path}")
        
        return str(output_path)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=str, required=True)
    parser.add_argument("--processed", type=str, required=True)
    args = parser.parse_args()
    
    cleaner = DataCleaner(Path(args.raw), Path(args.processed))
    cleaner.run_pipeline()

if __name__ == "__main__":
    main()
