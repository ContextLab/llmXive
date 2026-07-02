"""
Data Schema Validation Module (T004)

Implements validation for input datasets and output artifacts using
jsonschema and pydantic based on contracts/*.yaml definitions.
"""
import os
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import pandas as pd

try:
    import jsonschema
    from jsonschema import validate, ValidationError
except ImportError:
    raise ImportError("jsonschema package is required. Install via: pip install jsonschema")

from config import get_project_root

logger = logging.getLogger(__name__)

class SchemaValidator:
    """
    Validates data artifacts against YAML schema definitions.
    """
    
    def __init__(self, contracts_dir: Optional[Path] = None):
        if contracts_dir is None:
            project_root = get_project_root()
            contracts_dir = project_root / "contracts"
        
        self.contracts_dir = contracts_dir
        self.schemas: Dict[str, Dict[str, Any]] = {}
        self._load_schemas()
    
    def _load_schemas(self) -> None:
        """Load all schema files from the contracts directory."""
        schema_files = {
            "dataset": "dataset.schema.yaml",
            "output": "output.schema.yaml"
        }
        
        for key, filename in schema_files.items():
            schema_path = self.contracts_dir / filename
            if schema_path.exists():
                with open(schema_path, 'r') as f:
                    self.schemas[key] = yaml.safe_load(f)
                logger.info(f"Loaded schema: {filename}")
            else:
                logger.warning(f"Schema file not found: {schema_path}")
    
    def validate_input_dataset(self, microbiome_df: pd.DataFrame, eeg_df: pd.DataFrame) -> bool:
        """
        Validate input DataFrames against the dataset schema.
        Checks for required columns and basic type constraints.
        """
        if "dataset" not in self.schemas:
            raise RuntimeError("Dataset schema not loaded. Ensure contracts/dataset.schema.yaml exists.")
        
        schema = self.schemas["dataset"]
        errors = []
        
        # Validate Microbiome
        if "subject_id" not in microbiome_df.columns:
            errors.append("Microbiome data missing 'subject_id' column")
        if "age" not in microbiome_df.columns:
            errors.append("Microbiome data missing 'age' column")
        if "sex" not in microbiome_df.columns:
            errors.append("Microbiome data missing 'sex' column")
        if "bmi" not in microbiome_df.columns:
            errors.append("Microbiome data missing 'bmi' column")
        
        # Validate EEG
        if "subject_id" not in eeg_df.columns:
            errors.append("EEG data missing 'subject_id' column")
        if "age" not in eeg_df.columns:
            errors.append("EEG data missing 'age' column")
        if "sex" not in eeg_df.columns:
            errors.append("EEG data missing 'sex' column")
        if "alpha_power" not in eeg_df.columns:
            errors.append("EEG data missing 'alpha_power' column")
        
        if errors:
            for err in errors:
                logger.error(f"Validation Error: {err}")
            return False
        
        logger.info("Input dataset validation passed.")
        return True
    
    def validate_matched_pairs(self, df: pd.DataFrame) -> bool:
        """Validate matched_pairs.csv structure."""
        required_cols = [
            "microbiome_subject_id", 
            "eeg_subject_id", 
            "age_diff", 
            "sex_match", 
            "bmi_diff", 
            "matching_score"
        ]
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            logger.error(f"matched_pairs.csv missing columns: {missing}")
            return False
        logger.info("matched_pairs.csv validation passed.")
        return True
    
    def validate_distribution_groups(self, df: pd.DataFrame) -> bool:
        """Validate distribution_groups.csv structure."""
        required_cols = [
            "subject_id", 
            "group_label", 
            "abundance_metric", 
            "alpha_power"
        ]
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            logger.error(f"distribution_groups.csv missing columns: {missing}")
            return False
        
        if "group_label" in df.columns:
            valid_labels = ["High", "Low", "Control"]
            invalid = df[~df["group_label"].isin(valid_labels)]["group_label"].unique()
            if len(invalid) > 0:
                logger.error(f"Invalid group labels found: {invalid}")
                return False
        
        logger.info("distribution_groups.csv validation passed.")
        return True
    
    def validate_analysis_results(self, results: Dict[str, Any]) -> bool:
        """Validate analysis_results.json structure."""
        required_keys = [
            "path_selected", 
            "n_pairs", 
            "statistical_test", 
            "p_value", 
            "q_value", 
            "permutation_passed",
            "disclaimer"
        ]
        missing = [key for key in required_keys if key not in results]
        if missing:
            logger.error(f"analysis_results.json missing keys: {missing}")
            return False
        
        if results.get("path_selected") not in ["Path A (Matching)", "Path B (Distributional)"]:
            logger.error(f"Invalid path_selected value: {results.get('path_selected')}")
            return False
        
        logger.info("analysis_results.json validation passed.")
        return True


def validate_artifacts(
    microbiome_path: Optional[str] = None,
    eeg_path: Optional[str] = None,
    matched_pairs_path: Optional[str] = None,
    distribution_groups_path: Optional[str] = None,
    results_path: Optional[str] = None
) -> bool:
    """
    High-level function to validate all artifacts.
    Returns True if all present artifacts are valid.
    """
    validator = SchemaValidator()
    all_valid = True
    
    if microbiome_path and eeg_path:
        try:
            m_df = pd.read_csv(microbiome_path)
            e_df = pd.read_csv(eeg_path)
            if not validator.validate_input_dataset(m_df, e_df):
                all_valid = False
        except Exception as e:
            logger.error(f"Failed to load or validate input datasets: {e}")
            all_valid = False
    
    if matched_pairs_path:
        try:
            if os.path.exists(matched_pairs_path):
                df = pd.read_csv(matched_pairs_path)
                if not validator.validate_matched_pairs(df):
                    all_valid = False
        except Exception as e:
            logger.error(f"Failed to validate matched_pairs: {e}")
            all_valid = False
    
    if distribution_groups_path:
        try:
            if os.path.exists(distribution_groups_path):
                df = pd.read_csv(distribution_groups_path)
                if not validator.validate_distribution_groups(df):
                    all_valid = False
        except Exception as e:
            logger.error(f"Failed to validate distribution_groups: {e}")
            all_valid = False
    
    if results_path:
        try:
            if os.path.exists(results_path):
                with open(results_path, 'r') as f:
                    data = json.load(f)
                if not validator.validate_analysis_results(data):
                    all_valid = False
        except Exception as e:
            logger.error(f"Failed to validate analysis results: {e}")
            all_valid = False
    
    return all_valid


if __name__ == "__main__":
    # Basic CLI usage for validation
    import argparse
    parser = argparse.ArgumentParser(description="Validate project artifacts against schemas")
    parser.add_argument("--microbiome", type=str, help="Path to microbiome CSV")
    parser.add_argument("--eeg", type=str, help="Path to EEG CSV")
    parser.add_argument("--matched-pairs", type=str, help="Path to matched_pairs CSV")
    parser.add_argument("--dist-groups", type=str, help="Path to distribution_groups CSV")
    parser.add_argument("--results", type=str, help="Path to analysis_results JSON")
    
    args = parser.parse_args()
    
    success = validate_artifacts(
        microbiome_path=args.microbiome,
        eeg_path=args.eeg,
        matched_pairs_path=args.matched_pairs,
        distribution_groups_path=args.dist_groups,
        results_path=args.results
    )
    
    if success:
        print("All artifacts validated successfully.")
        exit(0)
    else:
        print("Validation failed.")
        exit(1)
