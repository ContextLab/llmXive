"""
Statistical analysis module for User Story 3.

Implements Mixed-Model Repeated-Measures ANOVA on Generalization Gap curves
using seed_id as subjects, as required by T030.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np
from statsmodels.stats.anova import AnovaRM
from statsmodels.stats.power import FTestAnovaPower

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import get_logger, info, error, warning
from utils.config import get_artifacts_dir, get_processed_dir

logger = get_logger(__name__)


def load_training_logs(logs_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load training logs from CSV file.
    
    Args:
        logs_path: Path to training_logs.csv. If None, uses default artifacts path.
        
    Returns:
        DataFrame with training metrics including seed_id, epoch, train_loss, val_loss
    """
    if logs_path is None:
        logs_path = str(get_artifacts_dir() / "training_logs.csv")
    
    logs_path = Path(logs_path)
    if not logs_path.exists():
        raise FileNotFoundError(f"Training logs not found at {logs_path}")
    
    logger.info(f"Loading training logs from {logs_path}")
    df = pd.read_csv(logs_path)
    
    required_cols = ['seed_id', 'epoch', 'train_loss', 'val_loss', 'model_type']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in training logs: {missing}")
    
    return df


def compute_generalization_gap(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute generalization gap (val_loss - train_loss) for each record.
    
    Args:
        df: DataFrame with train_loss and val_loss columns
        
    Returns:
        DataFrame with added 'gap' column
    """
    df = df.copy()
    df['gap'] = df['val_loss'] - df['train_loss']
    return df


def run_anova_analysis(
    logs_path: Optional[str] = None,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run Mixed-Model Repeated-Measures ANOVA on Generalization Gap.
    
    This implements T030: Statistical test for ANOVA output schema.
    Uses seed_id as subjects, epoch as within-subject factor, 
    model_type as between-subject factor.
    
    Args:
        logs_path: Path to training logs CSV
        output_path: Path to save results JSON. If None, uses default.
        
    Returns:
        Dictionary containing ANOVA results and statistics
    """
    logger.info("Starting Mixed-Model Repeated-Measures ANOVA analysis")
    
    # Load and prepare data
    df = load_training_logs(logs_path)
    df = compute_generalization_gap(df)
    
    # Ensure seed_id is treated as subject identifier
    df['seed_id'] = df['seed_id'].astype(str)
    df['epoch'] = df['epoch'].astype(int)
    
    info(f"Data loaded: {len(df)} records, {df['seed_id'].nunique()} subjects, "
         f"{df['model_type'].nunique()} model types")
    
    # Run Repeated Measures ANOVA
    # Formula: gap ~ model_type + epoch + model_type:epoch
    # subject: seed_id, within: epoch, between: model_type
    try:
        anova = AnovaRM(
            df, 
            depvar='gap', 
            subject='seed_id', 
            within=['epoch'], 
            between=['model_type']
        )
        result = anova.fit()
        
        logger.info("ANOVA completed successfully")
        info(f"ANOVA F-statistics:\n{result}")
        
    except Exception as e:
        error(f"ANOVA analysis failed: {str(e)}")
        raise
    
    # Extract key statistics
    results = {
        "method": "Mixed-Model Repeated-Measures ANOVA",
        "dependent_variable": "generalization_gap",
        "subject_variable": "seed_id",
        "within_subject_factor": "epoch",
        "between_subject_factor": "model_type",
        "sample_size": len(df),
        "num_subjects": int(df['seed_id'].nunique()),
        "num_model_types": int(df['model_type'].nunique()),
        "num_epochs": int(df['epoch'].nunique()),
        "anova_table": str(result),
        "summary": {
            "model_type_effect": {
                "f_statistic": float(result.anova_table.loc['model_type', 'F value']) if 'model_type' in result.anova_table.index else None,
                "p_value": float(result.anova_table.loc['model_type', 'Pr > F']) if 'model_type' in result.anova_table.index else None
            },
            "epoch_effect": {
                "f_statistic": float(result.anova_table.loc['epoch', 'F value']) if 'epoch' in result.anova_table.index else None,
                "p_value": float(result.anova_table.loc['epoch', 'Pr > F']) if 'epoch' in result.anova_table.index else None
            },
            "interaction_effect": {
                "f_statistic": float(result.anova_table.loc['model_type:epoch', 'F value']) if 'model_type:epoch' in result.anova_table.index else None,
                "p_value": float(result.anova_table.loc['model_type:epoch', 'Pr > F']) if 'model_type:epoch' in result.anova_table.index else None
            }
        },
        "interaction_significant": False
    }
    
    # Check if interaction term is significant (p < 0.05)
    if results["summary"]["interaction_effect"]["p_value"] is not None:
        results["interaction_significant"] = results["summary"]["interaction_effect"]["p_value"] < 0.05
    
    # Save results
    if output_path is None:
        output_path = str(get_artifacts_dir() / "statistical_results.json")
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    info(f"ANOVA results saved to {output_path}")
    
    return results


def main():
    """Main entry point for statistical test script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Mixed-Model Repeated-Measures ANOVA on training data")
    parser.add_argument("--logs", type=str, help="Path to training_logs.csv")
    parser.add_argument("--output", type=str, help="Path to output JSON file")
    
    args = parser.parse_args()
    
    try:
        results = run_anova_analysis(
            logs_path=args.logs,
            output_path=args.output
        )
        
        info("ANOVA analysis completed successfully")
        info(f"Interaction effect significant: {results['interaction_significant']}")
        
    except Exception as e:
        error(f"ANOVA analysis failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
