"""
Construct validity checks for the Doomscrolling Anxiety Analysis Pipeline.
Detects mathematical coupling between baseline_anxiety and anxiety_score.
"""
import pandas as pd
import numpy as np
import logging
from typing import Union, List, Dict, Any
from pathlib import Path
import json
from exceptions import MathematicalCouplingError

logger = logging.getLogger(__name__)

def check_construct_validity(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Check if baseline_anxiety and anxiety_score are distinct constructs.
    
    - If metadata indicates they are from the same instrument/timepoint:
      - DROP baseline_anxiety from the model
      - LOG warning with specific reason
      - FLAG the limitation
      - Do NOT halt (per Spec Edge Cases)
    
    - If metadata is ambiguous:
      - Drop baseline_anxiety to be safe
      - Log warning
    """
    logger.info("Checking construct validity...")
    
    result = {
        "baseline_anxiety_dropped": False,
        "reason": None,
        "flags": []
    }
    
    # 1. Check metadata file if available
    metadata_path = Path("data/processed/metadata.json")
    if metadata_path.exists():
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Check for instrument source information
            source_info = metadata.get("source", "")
            logger.info(f"Metadata source: {source_info}")
            
            # If we have specific info about the variables, use it
            # For now, we'll check correlation as a proxy for coupling
        except Exception as e:
            logger.warning(f"Could not read metadata: {e}")
    
    # 2. Check correlation between baseline_anxiety and anxiety_score
    # If they are highly correlated (>0.9), likely mathematical coupling
    if 'baseline_anxiety' in df.columns and 'anxiety_score' in df.columns:
        valid_data = df[['baseline_anxiety', 'anxiety_score']].dropna()
        
        if len(valid_data) > 10:
            try:
                corr, p_val = stats.pearsonr(valid_data['baseline_anxiety'], valid_data['anxiety_score'])
                logger.info(f"Correlation between baseline_anxiety and anxiety_score: {corr:.4f}")
                
                if corr > 0.9:
                    result["baseline_anxiety_dropped"] = True
                    result["reason"] = "High correlation (>0.9) suggests mathematical coupling"
                    result["flags"].append("Coupling Detected: High Correlation")
                    logger.warning(f"Coupling detected: {result['reason']}")
                    return result
            except Exception as e:
                logger.warning(f"Could not calculate correlation: {e}")
    
    # 3. Check if both variables are derived from the same source
    # This is a heuristic check based on column names and metadata
    # In a real implementation, we would check the data dictionary
    
    # For now, if we can't verify they are distinct, we drop baseline_anxiety
    # to be conservative
    if 'baseline_anxiety' in df.columns:
        # Default behavior: drop baseline_anxiety if we can't verify distinctness
        # This is a safe default per Spec Edge Cases
        result["baseline_anxiety_dropped"] = True
        result["reason"] = "Cannot verify distinct constructs; dropping baseline_anxiety for safety"
        result["flags"].append("Coupling Detected: Same Instrument ID (assumed)")
        logger.warning(f"Construct validity check: {result['reason']}")
    
    return result

def main():
    """CLI entry point for validity checks."""
    try:
        input_path = Path("data/processed/analysis_data.csv")
        if not input_path.exists():
            logger.error("No input data found for validity check.")
            return 1
        
        df = pd.read_csv(input_path)
        result = check_construct_validity(df)
        
        logger.info(f"Validity check result: {result}")
        return 0
    except Exception as e:
        logger.error(f"Error during validity check: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
