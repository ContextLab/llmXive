import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd
import numpy as np

# Import logging utilities from the existing project surface
from utils.logging_init import setup_global_logger, ConfigError
from utils.config_loader import load_config

class DataMissingError(Exception):
    """Raised when a required input file or column is missing."""
    pass

def get_project_root() -> Path:
    """Determine the project root directory."""
    # Assume the script is run from the project root or code/ directory
    current = Path.cwd()
    if current.name == "code":
        return current.parent
    # Fallback: look for 'data' directory
    if (current / "data").exists():
        return current
    # Search up the tree
    for parent in current.parents:
        if (parent / "data").exists() and (parent / "code").exists():
            return parent
    raise FileNotFoundError("Could not determine project root. Ensure 'data' and 'code' directories exist.")

def setup_logger(name: str) -> logging.Logger:
    """Setup a logger using the project's global logging config."""
    try:
        # Ensure global logger is setup if not already
        if not logging.getLogger().handlers:
            config_path = get_project_root() / "code" / "config" / "logging_config.yaml"
            if config_path.exists():
                setup_global_logger(config_path)
            else:
                # Fallback basic config if file missing (should not happen given T008)
                logging.basicConfig(level=logging.INFO)
    except ConfigError as e:
        logging.warning(f"Logging config error: {e}, using default.")
        logging.basicConfig(level=logging.INFO)
    return logging.getLogger(name)

def get_paths(project_root: Path) -> Dict[str, Path]:
    """Return paths to required input and output files."""
    data_derived = project_root / "data" / "derived"
    state = project_root / "state"
    
    return {
        "preprocessed_gaze": data_derived / "preprocessed_gaze.csv",
        "empirical_outcomes": data_derived / "empirical_outcomes.csv",
        "valence_scores": data_derived / "valence_scores.csv",
        "output_merged": data_derived / "merged_dataset_full.csv",
        "state_dir": state
    }

def load_gaze_data(path: Path, logger: logging.Logger) -> pd.DataFrame:
    """Load preprocessed gaze data."""
    if not path.exists():
        raise DataMissingError(f"Missing required input file: {path}")
    logger.info(f"Loading gaze data from {path}")
    df = pd.read_csv(path)
    required_cols = ["participant_id", "headline_id", "total_fixation_duration", "roi_type"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise DataMissingError(f"Gaze data missing columns: {missing}")
    return df

def load_empirical_outcomes(path: Path, logger: logging.Logger) -> pd.DataFrame:
    """Load empirical outcomes data."""
    if not path.exists():
        raise DataMissingError(f"Missing required input file: {path}")
    logger.info(f"Loading empirical outcomes from {path}")
    df = pd.read_csv(path)
    required_cols = ["participant_id", "headline_id", "belief_rating", "headline_text"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise DataMissingError(f"Empirical outcomes missing columns: {missing}")
    return df

def load_valence_scores(path: Path, logger: logging.Logger) -> pd.DataFrame:
    """Load valence scores data."""
    if not path.exists():
        raise DataMissingError(f"Missing required input file: {path}")
    logger.info(f"Loading valence scores from {path}")
    df = pd.read_csv(path)
    required_cols = ["headline_id", "valence", "lexicon_used"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise DataMissingError(f"Valence scores missing columns: {missing}")
    return df

def load_crt_scores(gaze_df: pd.DataFrame, outcomes_df: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """
    Derive CRT scores. 
    Assumption: CRT score is associated with participant_id. 
    If present in gaze_df, use that. Otherwise, check outcomes_df.
    If not found, raise error as CRT is critical for the regression.
    """
    logger.info("Extracting/validating Cognitive Reflection Test (CRT) scores")
    
    if "cognitive_reflection_score" in gaze_df.columns:
        logger.info("CRT score found in gaze data")
        # Aggregate to participant level if multiple rows
        crt_df = gaze_df[["participant_id", "cognitive_reflection_score"]].drop_duplicates()
    elif "cognitive_reflection_score" in outcomes_df.columns:
        logger.info("CRT score found in outcomes data")
        crt_df = outcomes_df[["participant_id", "cognitive_reflection_score"]].drop_duplicates()
    else:
        # Try common aliases
        aliases = ["crt_score", "cognitive_reflection", "crt"]
        found_col = None
        for col in gaze_df.columns:
            if col.lower() in [a.lower() for a in aliases]:
                found_col = col
                break
        if not found_col:
            for col in outcomes_df.columns:
                if col.lower() in [a.lower() for a in aliases]:
                    found_col = col
                    break
        
        if found_col:
            logger.info(f"Found CRT score under alias '{found_col}'")
            if found_col in gaze_df.columns:
                crt_df = gaze_df[["participant_id", found_col]].drop_duplicates()
                crt_df.columns = ["participant_id", "cognitive_reflection_score"]
            else:
                crt_df = outcomes_df[["participant_id", found_col]].drop_duplicates()
                crt_df.columns = ["participant_id", "cognitive_reflection_score"]
        else:
            raise DataMissingError("Critical column 'cognitive_reflection_score' (or alias) not found in any input dataset.")
    
    return crt_df

def validate_schema(gaze_df: pd.DataFrame, outcomes_df: pd.DataFrame, valence_df: pd.DataFrame, logger: logging.Logger):
    """Ensure join keys exist and types are compatible."""
    for df, name in [(gaze_df, "gaze"), (outcomes_df, "outcomes"), (valence_df, "valence")]:
        if "participant_id" not in df.columns:
            raise DataMissingError(f"{name} data missing 'participant_id'")
        if "headline_id" not in df.columns:
            raise DataMissingError(f"{name} data missing 'headline_id'")
    
    # Ensure types match for joining
    if gaze_df["participant_id"].dtype != outcomes_df["participant_id"].dtype:
        logger.warning("Participant ID types differ, converting to string for merge")
        gaze_df["participant_id"] = gaze_df["participant_id"].astype(str)
        outcomes_df["participant_id"] = outcomes_df["participant_id"].astype(str)
        valence_df["participant_id"] = valence_df["participant_id"].astype(str) if "participant_id" in valence_df.columns else None

def merge_datasets(gaze_df: pd.DataFrame, outcomes_df: pd.DataFrame, valence_df: pd.DataFrame, 
                   crt_df: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """Perform the multi-step merge."""
    logger.info("Merging datasets on participant_id and headline_id")
    
    # 1. Merge Gaze and Outcomes
    merged = pd.merge(gaze_df, outcomes_df, on=["participant_id", "headline_id"], how="inner")
    logger.info(f"After Gaze+Outcomes merge: {len(merged)} rows")
    
    # 2. Merge Valence (on headline_id only)
    merged = pd.merge(merged, valence_df, on="headline_id", how="left")
    logger.info(f"After Valence merge: {len(merged)} rows")
    
    # 3. Merge CRT (on participant_id only)
    merged = pd.merge(merged, crt_df, on="participant_id", how="left")
    logger.info(f"After CRT merge: {len(merged)} rows")
    
    return merged

def apply_outlier_capping(df: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """Cap cognitive_reflection_score at extreme percentiles (1st and 99th)."""
    col = "cognitive_reflection_score"
    if col not in df.columns:
        logger.warning(f"Column {col} not found, skipping outlier capping")
        return df
    
    lower = df[col].quantile(0.01)
    upper = df[col].quantile(0.99)
    logger.info(f"Capping {col} between {lower:.2f} and {upper:.2f}")
    
    df[col] = df[col].clip(lower=lower, upper=upper)
    
    # Compute headline_length (word count)
    if "headline_text" in df.columns:
        df["headline_length"] = df["headline_text"].apply(lambda x: len(str(x).split()) if pd.notna(x) else 0)
    else:
        df["headline_length"] = 0
        logger.warning("headline_text missing, setting headline_length to 0")
    
    # Compute total_fixation_duration if not already present (should be from gaze)
    if "total_fixation_duration" not in df.columns:
        df["total_fixation_duration"] = 0.0
    
    return df

def main():
    project_root = get_project_root()
    logger = setup_logger("T023_DataMerge")
    paths = get_paths(project_root)
    
    logger.info("Starting T023: Data Merge & Outlier Capping")
    
    try:
        # Load Data
        gaze_df = load_gaze_data(paths["preprocessed_gaze"], logger)
        outcomes_df = load_empirical_outcomes(paths["empirical_outcomes"], logger)
        valence_df = load_valence_scores(paths["valence_scores"], logger)
        
        # Validate and Prepare CRT
        validate_schema(gaze_df, outcomes_df, valence_df, logger)
        crt_df = load_crt_scores(gaze_df, outcomes_df, logger)
        
        # Merge
        merged_df = merge_datasets(gaze_df, outcomes_df, valence_df, crt_df, logger)
        
        # Outlier Capping & Feature Engineering
        final_df = apply_outlier_capping(merged_df, logger)
        
        # Write Output
        output_path = paths["output_merged"]
        final_df.to_csv(output_path, index=False)
        logger.info(f"Successfully wrote merged dataset to {output_path}")
        
        # Log summary stats
        logger.info(f"Total rows: {len(final_df)}")
        logger.info(f"Columns: {list(final_df.columns)}")
        
    except DataMissingError as e:
        logger.error(f"Data error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
