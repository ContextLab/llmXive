"""
Data cleaning module for the accessibility research pipeline.

This module handles the cleaning of raw session data, including:
1. Filtering out incomplete sessions
2. Imputing missing SUS items (max 1 allowed)
3. Validating data types and schema compliance

CRITICAL: This module must NOT generate synthetic data. It processes
real data collected from participants or CI simulation runs (dev mode).
"""

import pandas as pd
from typing import List, Optional, Tuple, Dict, Any
from utils.logger import get_logger
import json
import glob
from pathlib import Path
import sys

logger = get_logger(__name__)

# SUS item indices (1-10 in the questionnaire, 0-9 in list)
SUS_ITEMS = [
    'sus_q1', 'sus_q2', 'sus_q3', 'sus_q4', 'sus_q5',
    'sus_q6', 'sus_q7', 'sus_q8', 'sus_q9', 'sus_q10'
]

class DataCleaner:
    """
    Handles cleaning of session data according to research protocol.
    
    Rules:
    1. Filter out sessions with status='incomplete' (unless explicitly kept for dropout analysis)
    2. If <=1 SUS item is missing, impute with participant mean
    3. If >1 SUS items are missing, reject the session
    4. Validate explanation_engagement_time is non-zero for Explainable interfaces
    """
    
    def __init__(self, raw_data_path: str, output_path: str, log_path: str = None):
        """
        Initialize the DataCleaner.
        
        Args:
            raw_data_path: Path to directory containing raw session JSON files
            output_path: Path for the cleaned CSV output
            log_path: Optional path for cleaning log
        """
        self.raw_data_path = Path(raw_data_path)
        self.output_path = Path(output_path)
        self.log_path = Path(log_path) if log_path else self.output_path.parent / "cleaning_log.txt"
        self.log_entries: List[str] = []
        
        # Ensure output directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"DataCleaner initialized. Raw: {self.raw_data_path}, Output: {self.output_path}")
    
    def load_raw_sessions(self) -> List[Dict[str, Any]]:
        """
        Load all raw session JSON files from the data directory.
        
        Returns:
            List of session dictionaries
        """
        sessions = []
        json_files = list(self.raw_data_path.glob("*.json"))
        
        if not json_files:
            logger.warning(f"No JSON files found in {self.raw_data_path}")
            return sessions
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    sessions.append(data)
                    logger.debug(f"Loaded session from {json_file.name}")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse {json_file.name}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error loading {json_file.name}: {e}")
        
        return sessions
    
    def filter_incomplete(self, sessions: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Filter out sessions with status='incomplete'.
        
        Args:
            sessions: List of session dictionaries
        
        Returns:
            Tuple of (kept_sessions, dropped_sessions)
        """
        kept = []
        dropped = []
        
        for session in sessions:
            status = session.get('status', 'unknown')
            if status == 'incomplete':
                dropped.append(session)
                self.log_entries.append(f"DROPPED: Session {session.get('session_id', 'unknown')} - status=incomplete")
                logger.info(f"Dropped incomplete session: {session.get('session_id')}")
            else:
                kept.append(session)
                self.log_entries.append(f"KEPT: Session {session.get('session_id', 'unknown')} - status={status}")
        
        logger.info(f"Filtered sessions: {len(kept)} kept, {len(dropped)} dropped")
        return kept, dropped
    
    def _count_missing_sus_items(self, session: Dict[str, Any]) -> int:
        """Count how many SUS items are missing or null."""
        missing = 0
        for item in SUS_ITEMS:
            value = session.get(item)
            if value is None or (isinstance(value, float) and pd.isna(value)):
                missing += 1
        return missing
    
    def _impute_sus_items(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """
        Impute missing SUS items with participant mean (if <=1 missing).
        
        Args:
            session: Session dictionary
        
        Returns:
            Updated session dictionary
        """
        missing_count = self._count_missing_sus_items(session)
        
        if missing_count == 0:
            return session
        
        if missing_count > 1:
            self.log_entries.append(f"REJECTED: Session {session.get('session_id')} - {missing_count} SUS items missing")
            logger.warning(f"Session {session.get('session_id')} has {missing_count} missing SUS items - rejecting")
            return None  # Signal rejection
        
        # Exactly 1 missing - impute with mean of present items
        present_values = []
        for item in SUS_ITEMS:
            value = session.get(item)
            if value is not None and not (isinstance(value, float) and pd.isna(value)):
                present_values.append(float(value))
        
        if present_values:
            mean_val = sum(present_values) / len(present_values)
            # Find which item is missing
            for item in SUS_ITEMS:
                value = session.get(item)
                if value is None or (isinstance(value, float) and pd.isna(value)):
                    session[item] = mean_val
                    self.log_entries.append(f"IMPUTED: Session {session.get('session_id')} - {item} = {mean_val:.2f}")
                    logger.debug(f"Imputed {item} for session {session.get('session_id')} with mean {mean_val:.2f}")
        else:
            # All items missing - this shouldn't happen if missing_count == 1
            self.log_entries.append(f"REJECTED: Session {session.get('session_id')} - all SUS items missing")
            return None
        
        return session
    
    def impute_sus(self, sessions: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Apply SUS imputation logic to sessions.
        
        Args:
            sessions: List of session dictionaries
        
        Returns:
            Tuple of (imputed_sessions, rejected_sessions)
        """
        imputed = []
        rejected = []
        
        for session in sessions:
            result = self._impute_sus_items(session)
            if result is not None:
                imputed.append(result)
            else:
                rejected.append(session)
        
        logger.info(f"SUS imputation: {len(imputed)} processed, {len(rejected)} rejected")
        return imputed, rejected
    
    def validate_xai_engagement(self, sessions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate explanation_engagement_time for XAI interfaces.
        
        Args:
            sessions: List of session dictionaries
        
        Returns:
            Sessions with warnings logged but not rejected
        """
        valid_sessions = []
        
        for session in sessions:
            interface_type = session.get('interface_type', '')
            engagement_time = session.get('explanation_engagement_time_seconds', 0)
            
            if interface_type == 'Explainable':
                if engagement_time is None or engagement_time == 0:
                    self.log_entries.append(
                        f"WARNING: Session {session.get('session_id')} - Explainable interface "
                        f"but explanation_engagement_time is {engagement_time}"
                    )
                    logger.warning(f"Session {session.get('session_id')}: Zero engagement time for Explainable interface")
            
            valid_sessions.append(session)
        
        return valid_sessions
    
    def sessions_to_dataframe(self, sessions: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Convert list of session dictionaries to a pandas DataFrame.
        
        Args:
            sessions: List of session dictionaries
        
        Returns:
            pandas DataFrame with cleaned data
        """
        if not sessions:
            return pd.DataFrame()
        
        df = pd.DataFrame(sessions)
        
        # Ensure required columns exist
        required_cols = [
            'participant_id', 'session_id', 'interface_type', 'completion_time',
            'error_count', 'status', 'sus_score'
        ] + SUS_ITEMS
        
        for col in required_cols:
            if col not in df.columns:
                df[col] = None
        
        # Convert numeric columns
        numeric_cols = ['completion_time', 'error_count', 'sus_score'] + SUS_ITEMS
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
    def write_log(self):
        """Write cleaning log to file."""
        with open(self.log_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(self.log_entries))
        logger.info(f"Cleaning log written to {self.log_path}")
    
    def run(self) -> pd.DataFrame:
        """
        Execute the full cleaning pipeline.
        
        Returns:
            Cleaned pandas DataFrame
        """
        logger.info("Starting data cleaning pipeline")
        
        # Step 1: Load raw sessions
        sessions = self.load_raw_sessions()
        if not sessions:
            logger.error("No sessions loaded. Cannot proceed with cleaning.")
            return pd.DataFrame()
        
        logger.info(f"Loaded {len(sessions)} raw sessions")
        
        # Step 2: Filter incomplete sessions
        kept_sessions, _ = self.filter_incomplete(sessions)
        
        # Step 3: Impute SUS items
        cleaned_sessions, rejected = self.impute_sus(kept_sessions)
        
        # Step 4: Validate XAI engagement (log warnings only)
        validated_sessions = self.validate_xai_engagement(cleaned_sessions)
        
        # Step 5: Convert to DataFrame
        df = self.sessions_to_dataframe(validated_sessions)
        
        # Step 6: Write output
        if not df.empty:
            df.to_csv(self.output_path, index=False)
            logger.info(f"Cleaned data written to {self.output_path} ({len(df)} rows)")
        else:
            logger.warning("No data to write after cleaning")
            # Still create an empty file with headers
            df.to_csv(self.output_path, index=False)
        
        # Step 7: Write log
        self.write_log()
        
        logger.info("Data cleaning pipeline completed")
        return df

def main():
    """CLI entry point for data cleaning."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean raw session data")
    parser.add_argument("--input", type=str, required=True, help="Path to raw data directory")
    parser.add_argument("--output", type=str, required=True, help="Path for cleaned CSV output")
    parser.add_argument("--log", type=str, default=None, help="Path for cleaning log")
    parser.add_argument("--simulate", action="store_true", help="Allow simulation mode (dev only)")
    
    args = parser.parse_args()
    
    # Check for real data
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input directory does not exist: {input_path}")
        sys.exit(1)
    
    json_files = list(input_path.glob("*.json"))
    if not json_files and not args.simulate:
        logger.error(
            "Production mode: No real data found in " + str(input_path) + 
            ". Please run the simulator with real participants or use --simulate for dev mode only."
        )
        sys.exit(1)
    
    if not json_files and args.simulate:
        logger.warning("Running in simulate mode with no data. This is for dev testing only.")
    
    cleaner = DataCleaner(
        raw_data_path=args.input,
        output_path=args.output,
        log_path=args.log
    )
    
    df = cleaner.run()
    
    if df.empty:
        logger.warning("Cleaning resulted in empty dataset")
        sys.exit(0)  # Not an error, just no data
    
    logger.info(f"Successfully cleaned {len(df)} sessions")
    sys.exit(0)

if __name__ == "__main__":
    main()