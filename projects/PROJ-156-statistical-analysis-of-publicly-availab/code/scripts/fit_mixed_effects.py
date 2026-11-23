"""
Fit mixed-effects models to speedrun data to quantify learning curves.

Model: log(Time) ~ log(Attempt Number) + Game Difficulty + Lagged Pressure + (1 | RunnerID)

Outputs:
  - data/processed/model_results.csv: Model coefficients, p-values, VIFs, and fit statistics.
"""
import csv
import json
import logging
import os
import sys
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Import utilities from project
from scripts.utils.checkpoint import ensure_checkpoint_dir, save_checkpoint, load_checkpoint, get_checkpoint_path
from scripts.preprocess import load_config, load_schema, validate_record

# Statistical libraries
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.outliers_influence import variance_inflation_factor
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def load_processed_data(config: Dict) -> pd.DataFrame:
    """Load the preprocessed run records."""
    data_path = Path(config['data']['processed']) / 'run_records.csv'
    if not data_path.exists():
        raise FileNotFoundError(f"Processed data not found at {data_path}. Run US1 tasks first.")
    
    logger.info(f"Loading processed data from {data_path}")
    df = pd.read_csv(data_path)
    
    # Validate required columns
    required_cols = [
        'run_time_seconds', 'attempt_number', 'game_id', 'runner_id', 
        'difficulty_label', 'lagged_competitive_pressure', 'submission_date'
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in run_records.csv: {missing}")
    
    # Filter out records with missing critical values
    df = df.dropna(subset=required_cols)
    logger.info(f"Loaded {len(df)} valid records")
    return df

def calculate_vif(df: pd.DataFrame, formula: str) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factors for fixed effects.
    
    Args:
        df: DataFrame with model data.
        formula: Statsmodels formula string.
        
    Returns:
        Dict mapping feature names to VIF values.
    """
    # Parse formula to get fixed effect terms (excluding random effects)
    # Formula format: "y ~ x1 + x2 + (1 | g)"
    # We need to extract the right-hand side fixed effects
    rhs = formula.split('~')[1].strip()
    # Remove random effects part
    if '(1 |' in rhs:
        rhs = rhs.split('(1 |')[0].strip()
    
    # Create design matrix
    # Use statsmodels to get the design matrix for fixed effects
    # We need to handle categorical variables (game_id, difficulty_label)
    
    # Create a temporary model to get the design matrix
    # Note: We use a simple OLS just to get the design matrix, not the model itself
    try:
        # Add a dummy response to get design matrix
        y = np.ones(len(df))
        X = smf.ols(f"{y.name} ~ {rhs}", data=df).fit().model.exog
        
        # Intercept is usually the first column
        vifs = {}
        feature_names = [f"Intercept"] + [col for col in df.columns if col in rhs.split('+')]
        
        # Actually, let's do it properly by parsing the formula
        # For simplicity, we'll use the columns that end up in the design matrix
        # statsmodels adds dummy variables for categorical columns
        
        # Re-do: get the actual feature names from the fitted model
        # We need to fit a temporary OLS to get the design matrix column names
        temp_model = smf.ols(f"run_time_seconds ~ {rhs}", data=df).fit()
        feature_names = temp_model.model.exog_names[1:]  # Skip intercept
        
        # Calculate VIF for each feature
        for i, name in enumerate(feature_names):
            vif = variance_inflation_factor(temp_model.model.exog, i + 1)  # +1 to skip intercept
            vifs[name] = vif
            
    except Exception as e:
        logger.warning(f"Could not calculate VIFs: {e}")
        return {}
        
    return vifs

def fit_model_for_game(df: pd.DataFrame, game_id: str) -> Optional[Dict]:
    """
    Fit the mixed-effects model for a single game.
    
    Model: log(Time) ~ log(Attempt Number) + Game Difficulty + Lagged Pressure + (1 | RunnerID)
    """
    game_df = df[df['game_id'] == game_id].copy()
    
    if len(game_df) < 10:  # Minimum samples for fitting
        logger.warning(f"Skipping {game_id}: only {len(game_df)} runs")
        return None
    
    try:
        # Prepare features
        game_df['log_time'] = np.log(game_df['run_time_seconds'])
        game_df['log_attempt'] = np.log(game_df['attempt_number'])
        
        # Filter out any remaining NaNs after log transform
        game_df = game_df.dropna(subset=['log_time', 'log_attempt'])
        
        if len(game_df) < 10:
            logger.warning(f"Skipping {game_id} after filtering: only {len(game_df)} runs")
            return None
        
        # Define formula
        # Note: difficulty_label and lagged_competitive_pressure are fixed effects
        # runner_id is the random effect grouping variable
        formula = "log_time ~ log_attempt + difficulty_label + lagged_competitive_pressure + (1 | runner_id)"
        
        # Fit the mixed-effects model
        # Using REML=False for likelihood ratio tests compatibility
        model = smf.mixedlm(formula, game_df, groups=game_df["runner_id"])
        result = model.fit(reml=False)
        
        if not result.converged:
            logger.warning(f"Model for {game_id} did not converge")
            # Still return results but flag as non-converged
        
        # Extract coefficients and p-values
        coef_dict = result.params.to_dict()
        p_values = result.pvalues.to_dict()
        
        # Calculate VIFs
        vifs = calculate_vif(game_df, formula)
        
        # Check for multicollinearity
        high_vif_features = {k: v for k, v in vifs.items() if v > 5}
        
        # Likelihood ratio test (simplified: compare to intercept-only model)
        # Fit intercept-only model
        intercept_formula = "log_time ~ 1 + (1 | runner_id)"
        try:
            intercept_model = smf.mixedlm(intercept_formula, game_df, groups=game_df["runner_id"])
            intercept_result = intercept_model.fit(reml=False)
            
            # Likelihood ratio test
            lr_stat = 2 * (result.llf - intercept_result.llf)
            # Degrees of freedom = difference in number of parameters
            df_diff = len(result.params) - len(intercept_result.params)
            lr_pvalue = 1 - stats.chi2.cdf(lr_stat, df_diff)
        except Exception as e:
            logger.warning(f"Could not perform likelihood ratio test for {game_id}: {e}")
            lr_stat = None
            lr_pvalue = None
        
        return {
            'game_id': game_id,
            'n_runs': len(game_df),
            'n_runners': game_df['runner_id'].nunique(),
            'converged': result.converged,
            'log_likelihood': result.llf,
            'aic': result.aic,
            'bic': result.bic,
            'log_attempt_coef': coef_dict.get('log_attempt'),
            'log_attempt_pvalue': p_values.get('log_attempt'),
            'difficulty_label_coef': coef_dict.get('difficulty_label'),  # This might be a dict if categorical
            'lagged_pressure_coef': coef_dict.get('lagged_competitive_pressure'),
            'lagged_pressure_pvalue': p_values.get('lagged_competitive_pressure'),
            'lr_statistic': lr_stat,
            'lr_pvalue': lr_pvalue,
            'vif_log_attempt': vifs.get('log_attempt'),
            'vif_lagged_pressure': vifs.get('lagged_competitive_pressure'),
            'high_vif_features': json.dumps(high_vif_features) if high_vif_features else None
        }
        
    except Exception as e:
        logger.error(f"Failed to fit model for {game_id}: {e}")
        return None

def save_results(results: List[Dict], config: Dict) -> None:
    """Save model results to CSV."""
    output_path = Path(config['data']['processed']) / 'model_results.csv'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not results:
        logger.warning("No results to save")
        return
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Saved {len(results)} model results to {output_path}")

def main():
    """Main entry point for mixed-effects model fitting."""
    logger.info("Starting mixed-effects model fitting (T027)")
    
    # Load configuration
    config = load_config()
    games = config.get('games', [])
    
    if not games:
        logger.error("No games specified in config.yaml")
        sys.exit(1)
    
    # Load processed data
    df = load_processed_data(config)
    
    # Setup checkpointing
    checkpoint_dir = Path(config.get('checkpoint_dir', 'data/checkpoints'))
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = get_checkpoint_path(checkpoint_dir, 'fit_mixed_effects')
    
    # Load checkpoint if exists
    start_index = 0
    if checkpoint_path.exists():
        checkpoint = load_checkpoint(checkpoint_path)
        start_index = checkpoint.get('last_game_index', 0)
        logger.info(f"Resuming from game index {start_index}")
    
    results = []
    
    for i, game_id in enumerate(games):
        if i < start_index:
            continue
          
        logger.info(f"Fitting model for game: {game_id} (index {i}/{len(games)})")
        
        result = fit_model_for_game(df, game_id)
        if result:
            results.append(result)
        
        # Save checkpoint after each game
        save_checkpoint(
            checkpoint_path,
            {
                'last_game_index': i + 1,
                'games_processed': len(results),
                'timestamp': pd.Timestamp.now().isoformat()
            }
        )
    
    # Save final results
    save_results(results, config)
    
    # Clean up checkpoint
    if checkpoint_path.exists():
        os.remove(checkpoint_path)
    
    logger.info("Mixed-effects model fitting completed successfully")

if __name__ == "__main__":
    main()
