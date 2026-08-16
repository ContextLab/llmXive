import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
import numpy as np

# Import pingouin for Mixed-Model Repeated-Measures ANOVA
try:
    import pingouin as pg
except ImportError:
    raise ImportError(
        "pingouin is required for statistical analysis. "
        "Please install it via: pip install pingouin"
    )

from utils.config import get_project_root, get_artifacts_dir
from utils.logging import setup_logging, get_logger

# Ensure project root is in path for relative imports if running as script
PROJECT_ROOT = get_project_root()
if str(PROJECT_ROOT / "code") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "code"))

logger = setup_logging()

def load_training_logs(log_file_path: Optional[str] = None) -> pd.DataFrame:
    """
    Loads the training logs CSV file.
    
    Args:
        log_file_path: Optional path to the CSV. If None, uses default path.
        
    Returns:
        DataFrame with columns: epoch, model_type, train_loss, val_loss, gap, seed_id
        
    Raises:
        FileNotFoundError: If the log file does not exist.
        ValueError: If required columns are missing.
    """
    if log_file_path is None:
        artifacts_dir = get_artifacts_dir()
        log_file_path = str(artifacts_dir / "training_logs.csv")
    
    path = Path(log_file_path)
    if not path.exists():
        raise FileNotFoundError(f"Training logs file not found at: {log_file_path}")
    
    logger.info(f"Loading training logs from {log_file_path}")
    df = pd.read_csv(log_file_path)
    
    required_cols = ['epoch', 'model_type', 'train_loss', 'val_loss', 'gap', 'seed_id']
    missing_cols = [c for c in required_cols if c not in df.columns]
    
    if missing_cols:
        raise ValueError(f"Missing required columns in training logs: {missing_cols}")
    
    logger.info(f"Loaded {len(df)} rows of training data")
    return df

def compute_generalization_gap(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes the generalization gap if not already present.
    Gap = val_loss - train_loss.
    
    Args:
        df: DataFrame with train_loss and val_loss columns.
        
    Returns:
        DataFrame with an additional 'gap' column.
    """
    if 'gap' not in df.columns:
        logger.info("Computing generalization gap (val_loss - train_loss)")
        df['gap'] = df['val_loss'] - df['train_loss']
    else:
        logger.info("Generalization gap column already present, verifying...")
        # Optional: verify existing gap matches calculation
        expected_gap = df['val_loss'] - df['train_loss']
        if not np.allclose(df['gap'], expected_gap, rtol=1e-5):
            logger.warning("Existing 'gap' column does not match calculated values. Overwriting.")
            df['gap'] = expected_gap
    
    return df

def run_anova_analysis(df: pd.DataFrame, result_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Runs Mixed-Model Repeated-Measures ANOVA on the Generalization Gap.
    
    Model Formula: gap ~ model_type * epoch + (1|seed_id)
    This treats 'seed_id' as the subject (random effect) and 'model_type' and 'epoch'
    as within-subject factors (or fixed effects in the mixed model context).
    
    Args:
        df: DataFrame containing 'gap', 'model_type', 'epoch', 'seed_id'.
        result_path: Optional path to save JSON results.
        
    Returns:
        Dictionary containing ANOVA results, p-values, and effect sizes.
    """
    logger.info("Running Mixed-Model Repeated-Measures ANOVA")
    
    # Prepare data for Pingouin
    # Pingouin's mixed_anova expects 'subject', 'dv', 'between', 'within'
    # However, for a formula-like approach or complex mixed models, we might need
    # to use statsmodels or specific pingouin configurations.
    # Given the spec asks for Mixed-Model Repeated-Measures ANOVA with formula:
    # gap ~ model_type * epoch + (1|seed_id)
    #
    # Pingouin's `mixed_anova` is suitable if we treat 'seed_id' as subject,
    # and 'model_type' and 'epoch' as within-subject factors.
    # Note: 'model_type' might vary between seeds in some designs, but here
    # we assume each seed has both models (AR and Diffusion) or we are comparing
    # the trajectories. If 'model_type' is a between-subject factor (different seeds for each),
    # the formula changes.
    #
    # Assumption based on typical "Repeated Measures": Each seed trains both models?
    # Or we treat 'model_type' as a within-subject factor if the same seed ID
    # appears for multiple model types (which implies multiple runs per seed).
    #
    # If 'seed_id' is the subject, and we have multiple measurements per subject
    # across 'model_type' and 'epoch', we can use mixed_anova.
    
    # Check data structure
    subjects = df['seed_id'].unique()
    conditions = df.groupby('seed_id')['model_type'].nunique()
    
    # If every subject has all model types, it's within-subject for model_type.
    # If not, it's between-subject.
    # Let's assume the design allows for mixed ANOVA where:
    # DV = gap
    # Subject = seed_id
    # Within = ['model_type', 'epoch'] IF every seed has every model_type
    # Otherwise, we might need to treat 'model_type' as 'between'.
    
    # To be robust, we will check uniqueness.
    # If a seed_id only appears for one model_type, 'model_type' is between.
    # If a seed_id appears for multiple model_types, it's within.
    
    model_type_per_seed = df.groupby('seed_id')['model_type'].apply(lambda x: set(x)).unique()
    unique_sets = set(frozenset(x) for x in model_type_per_seed)
    
    is_model_within = len(unique_sets) == 1 and len(list(unique_sets)[0]) > 1
    
    if is_model_within:
        within_factors = ['model_type', 'epoch']
        between_factors = []
        logger.info("Design: model_type and epoch are within-subject factors.")
    else:
        # If model_type varies between seeds, it's a between factor
        # Epoch is always within (repeated over time)
        within_factors = ['epoch']
        between_factors = ['model_type']
        logger.info("Design: model_type is a between-subject factor, epoch is within-subject.")
    
    # Pingouin mixed_anova signature:
    # mixed_anova(dv, between, within, subject, data, detailed=False, effsize='np2')
    # If we have both between and within, we need to be careful.
    # Actually, `mixed_anova` in pingouin handles one between and one within usually.
    # For complex designs, we might need `statsmodels`.
    # However, the spec asks for `pingouin`. Let's try to fit it.
    # If we have 2 within factors (model_type, epoch), pingouin supports that.
    # If we have 1 between (model_type) and 1 within (epoch), pingouin supports that.
    
    try:
        if is_model_within:
            # Both within
            aov = pg.mixed_anova(
                dv='gap',
                within=['model_type', 'epoch'],
                subject='seed_id',
                data=df,
                detailed=True
            )
        else:
            # model_type is between, epoch is within
            aov = pg.mixed_anova(
                dv='gap',
                between='model_type',
                within='epoch',
                subject='seed_id',
                data=df,
                detailed=True
            )
    except Exception as e:
        logger.error(f"Failed to run mixed_anova: {e}")
        # Fallback to standard repeated measures if mixed fails (e.g. unbalanced)
        # Or raise a clear error.
        raise RuntimeError(f"ANOVA failed. Check data balance: {e}")
    
    # Extract key results
    # The result is a DataFrame. We need the interaction term if applicable.
    # Interaction term is usually 'model_type:epoch' or similar.
    
    results_dict = {
        "anova_table": aov.to_dict(orient='records'),
        "model_design": "within" if is_model_within else "mixed",
        "interaction_term": None,
        "interaction_p": None,
        "interaction_f": None,
        "effect_size": None
    }
    
    # Look for interaction in the table
    # Columns usually: Source, SS, DF, F, p-unc, np2 (partial eta squared)
    interaction_row = aov[aov['Source'].str.contains('model_type.*epoch') | 
                          aov['Source'].str.contains('epoch.*model_type')]
    
    if not interaction_row.empty:
        row = interaction_row.iloc[0]
        results_dict["interaction_term"] = row['Source']
        results_dict["interaction_p"] = float(row['p-unc'])
        results_dict["interaction_f"] = float(row['F'])
        results_dict["effect_size"] = float(row['np2'])
        logger.info(f"Interaction found: {row['Source']}, p={row['p-unc']:.4f}, F={row['F']:.4f}")
    else:
        logger.warning("No interaction term found in ANOVA table.")
        
    # Save results if path provided
    if result_path:
        with open(result_path, 'w') as f:
            json.dump(results_dict, f, indent=2)
        logger.info(f"ANOVA results saved to {result_path}")
        
    return results_dict

def main():
    """
    Main entry point for the statistical test task.
    """
    logger.info("Starting Statistical Test (ANOVA) Task")
    
    artifacts_dir = get_artifacts_dir()
    log_file = artifacts_dir / "training_logs.csv"
    output_file = artifacts_dir / "anova_results.json"
    
    try:
        # 1. Load Data
        df = load_training_logs(str(log_file))
        
        # 2. Compute Gap (if needed)
        df = compute_generalization_gap(df)
        
        # 3. Run ANOVA
        results = run_anova_analysis(df, str(output_file))
        
        logger.info("ANOVA analysis completed successfully.")
        print(f"Results written to {output_file}")
        
    except FileNotFoundError as e:
        logger.error(f"Data not found: {e}")
        print(f"ERROR: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during ANOVA: {e}")
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()