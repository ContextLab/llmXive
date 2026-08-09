"""
Modeling Module.
Implements Ordinal Logistic Regression for severity analysis.
"""
import pandas as pd
import numpy as np
import logging
from statsmodels.miscmodels.ordinal_model import OrderedModel
from config import PROCESSED_DATA_DIR, RANDOM_SEED

logger = logging.getLogger(__name__)

def load_data(filepath: str = None) -> pd.DataFrame:
    """Load the merged dataset."""
    if filepath is None:
        filepath = PROCESSED_DATA_DIR / "merged_dataset.csv"
    
    logger.info(f"Loading data from {filepath}")
    df = pd.read_csv(filepath)
    return df

def prepare_model_data(df: pd.DataFrame) -> tuple:
    """Prepare features and target for the ordinal model."""
    logger.info("Preparing model data...")
    
    # Target: Severity (Ordinal: 0=Property, 1=Injury, 2=Fatality)
    # Ensure it's encoded as integer
    if 'SEVERITY_CODE' not in df.columns:
        # Fallback if not pre-encoded
        df['SEVERITY_CODE'] = df['SEVERITY'].apply(lambda x: 0 if x == 'Property' else (1 if x == 'Injury' else 2))
    
    y = df['SEVERITY_CODE']
    
    # Features: Weather + Controls
    features = ['precipitation', 'visibility', 'temperature', 'HOUR', 'MONTH']
    # Filter to existing columns
    X_cols = [c for c in features if c in df.columns]
    
    if not X_cols:
        raise ValueError("No feature columns found in dataset.")
        
    X = df[X_cols]
    
    # Fill missing values
    X = X.fillna(X.median())
    
    return X, y

def fit_ordinal_model(X: pd.DataFrame, y: pd.Series) -> OrderedModel:
    """Fit the Ordinal Logistic Regression model."""
    logger.info("Fitting OrderedModel...")
    
    model = OrderedModel(y, X, distr='logit')
    try:
        result = model.fit(method='bfgs', maxiter=100)
        logger.info("Model fitting successful.")
        return result
    except Exception as e:
        logger.error(f"Model fitting failed: {e}")
        raise

def extract_odds_ratios(result: OrderedModel) -> pd.DataFrame:
    """Extract coefficients and odds ratios."""
    logger.info("Extracting odds ratios...")
    
    coefs = result.params
    odds_ratios = np.exp(coefs)
    conf_int = result.conf_int()
    
    df_results = pd.DataFrame({
        'coefficient': coefs,
        'odds_ratio': odds_ratios,
        'ci_lower': conf_int[0],
        'ci_upper': conf_int[1]
    })
    
    return df_results

def run_modeling() -> dict:
    """Execute the full modeling pipeline."""
    df = load_data()
    X, y = prepare_model_data(df)
    result = fit_ordinal_model(X, y)
    odds_ratios = extract_odds_ratios(result)
    
    output = {
        'model_results': result,
        'odds_ratios': odds_ratios,
        'aic': result.aic,
        'bic': result.bic
    }
    
    # Save results
    odds_ratios.to_csv(PROCESSED_DATA_DIR / "model_odds_ratios.csv")
    logger.info("Modeling pipeline complete.")
    
    return output
