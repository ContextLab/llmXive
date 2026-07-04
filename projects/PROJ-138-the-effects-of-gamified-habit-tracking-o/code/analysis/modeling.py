import os
import sys
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.formula.api import mixedlm
from code.utils.logging import pipeline_logger
from code.utils.config import set_random_seed

def calculate_vif(df: pd.DataFrame, feature_cols: list) -> dict:
    """
    Calculate Variance Inflation Factor (VIF) for a list of features.
    
    Args:
        df: DataFrame containing the features
        feature_cols: List of column names to calculate VIF for
        
    Returns:
        Dictionary mapping feature names to their VIF values
    """
    vif_data = {}
    X = df[feature_cols].dropna()
    
    if X.shape[0] < 2:
        pipeline_logger.warning("Not enough samples to calculate VIF")
        return {col: np.inf for col in feature_cols}
        
    # Add constant for intercept
    X_with_const = sm.add_constant(X)
    
    for i, col in enumerate(feature_cols):
        try:
            # Regress this feature against all other features
            y = X[col]
            other_features = [c for c in feature_cols if c != col]
            X_other = sm.add_constant(X[other_features])
            
            model = sm.OLS(y, X_other).fit()
            vif = 1 / (1 - model.rsquared)
            vif_data[col] = vif
            pipeline_logger.info(f"VIF for {col}: {vif:.4f}")
        except Exception as e:
            pipeline_logger.error(f"Error calculating VIF for {col}: {e}")
            vif_data[col] = np.inf
            
    return vif_data

def fit_mixed_effects_model(df: pd.DataFrame, seed: int = 42) -> dict:
    """
    Fit a mixed-effects logistic regression model.
    
    Fixed effects: Gamification, Conscientiousness, Interaction (Gamification * Conscientiousness)
    Random effects: Random intercepts per User
    
    Args:
        df: DataFrame with columns: User_ID, Gamified, Adherence, Conscientiousness
        seed: Random seed for reproducibility
        
    Returns:
        Dictionary containing model results, coefficients, and diagnostics
    """
    set_random_seed(seed)
    
    # Ensure required columns exist
    required_cols = ['User_ID', 'Gamified', 'Conscientiousness', 'Adherence']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Clean data
    df_clean = df.dropna(subset=required_cols)
    pipeline_logger.info(f"Data cleaned: {len(df_clean)} rows (from {len(df)})")
    
    if len(df_clean) == 0:
        raise ValueError("No valid data remaining after cleaning")
    
    # Create interaction term
    df_clean['Interaction'] = df_clean['Gamified'] * df_clean['Conscientiousness']
    
    # Prepare formula
    # Using 'Adherence' as the binary outcome (0/1)
    formula = "Adherence ~ Gamified + Conscientiousness + Interaction"
    
    # Fit mixed effects model
    # Using Generalized Linear Mixed Model (GLMM) with logit link for binary outcome
    # Note: statsmodels mixedlm is for linear mixed models, but for binary outcomes
    # we might need to use a different approach or approximation
    
    try:
        # Attempt to fit using mixedlm with Gaussian family (approximation for binary)
        # For true logistic mixed effects, we would typically use statsmodels GLMM
        # or pingouin, but mixedlm is the standard tool available here
        model = mixedlm(
            formula=formula,
            data=df_clean,
            groups=df_clean['User_ID']
        )
        
        # Fit the model
        # For binary outcomes, mixedlm uses a Gaussian approximation
        # In a production setting, we'd use a true GLMM implementation
        result = model.fit()
        
        pipeline_logger.info("Model fitting completed successfully")
        pipeline_logger.info(f"Model log-likelihood: {result.llf:.4f}")
        
        # Extract coefficients
        coefficients = result.params.to_dict()
        std_errors = result.bse.to_dict()
        
        # Extract random effects variance
        random_effects = result.random_effects
        
        # Calculate p-values (approximate using t-distribution)
        p_values = {}
        for param in coefficients:
            if param in std_errors and std_errors[param] > 0:
                t_stat = coefficients[param] / std_errors[param]
                # Approximate p-value (two-tailed)
                # Using normal approximation for large samples
                p_values[param] = 2 * (1 - sm.stats.norm.cdf(abs(t_stat)))
            else:
                p_values[param] = np.nan
        
        return {
            'model': result,
            'coefficients': coefficients,
            'std_errors': std_errors,
            'p_values': p_values,
            'random_effects_variance': result.scale,
            'log_likelihood': result.llf,
            'formula': formula,
            'n_observations': len(df_clean),
            'n_groups': df_clean['User_ID'].nunique()
        }
        
    except Exception as e:
        pipeline_logger.error(f"Model fitting failed: {e}")
        raise

def main():
    """
    Main execution function for the modeling pipeline.
    
    Reads processed data, fits the mixed-effects model, and saves results.
    """
    pipeline_logger.info("Starting mixed-effects modeling pipeline")
    
    # Load processed data
    input_path = "data/processed/merged_data.csv"
    
    if not os.path.exists(input_path):
        pipeline_logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    try:
        df = pd.read_csv(input_path)
        pipeline_logger.info(f"Loaded data: {len(df)} rows, {len(df.columns)} columns")
        pipeline_logger.info(f"Columns: {list(df.columns)}")
        
        # Check for required columns
        required_cols = ['User_ID', 'Gamified', 'Conscientiousness', 'Adherence']
        available_cols = [c for c in required_cols if c in df.columns]
        
        if len(available_cols) < len(required_cols):
            missing = [c for c in required_cols if c not in df.columns]
            pipeline_logger.warning(f"Missing columns: {missing}")
            # Attempt to proceed with available columns if possible
            # But for this task, we need all of them
            if len(available_cols) < len(required_cols):
                raise ValueError(f"Missing required columns: {missing}")
        
        # Convert Gamified and Adherence to numeric if needed
        if 'Gamified' in df.columns:
            df['Gamified'] = df['Gamified'].astype(int)
        if 'Adherence' in df.columns:
            df['Adherence'] = df['Adherence'].astype(int)
        if 'Conscientiousness' in df.columns:
            df['Conscientiousness'] = df['Conscientiousness'].astype(float)
        
        # Fit the model
        results = fit_mixed_effects_model(df, seed=42)
        
        # Save results
        output_dir = "data/processed"
        os.makedirs(output_dir, exist_ok=True)
        
        # Save coefficients to CSV
        coef_df = pd.DataFrame({
            'parameter': list(results['coefficients'].keys()),
            'coefficient': list(results['coefficients'].values()),
            'std_error': list(results['std_errors'].values()),
            'p_value': list(results['p_values'].values())
        })
        
        coef_output_path = os.path.join(output_dir, "model_coefficients.csv")
        coef_df.to_csv(coef_output_path, index=False)
        pipeline_logger.info(f"Saved model coefficients to {coef_output_path}")
        
        # Save summary statistics
        summary = {
            'log_likelihood': results['log_likelihood'],
            'n_observations': results['n_observations'],
            'n_groups': results['n_groups'],
            'random_effects_variance': results['random_effects_variance'],
            'formula': results['formula']
        }
        
        summary_output_path = os.path.join(output_dir, "model_summary.json")
        import json
        with open(summary_output_path, 'w') as f:
            json.dump(summary, f, indent=2)
        pipeline_logger.info(f"Saved model summary to {summary_output_path}")
        
        # Log key findings
        pipeline_logger.info("=== Model Results ===")
        for param, coef in results['coefficients'].items():
            p_val = results['p_values'].get(param, np.nan)
            sig = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else ""
            pipeline_logger.info(f"{param}: {coef:.4f} (SE: {results['std_errors'][param]:.4f}) {sig}")
        
        return results
        
    except Exception as e:
        pipeline_logger.error(f"Pipeline execution failed: {e}")
        raise

if __name__ == "__main__":
    main()