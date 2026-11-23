import os
import sys
import json
import logging
import warnings
from pathlib import Path

import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.genmod.generalized_linear_model import GLM
from statsmodels.genmod.families import NegativeBinomial

# Import from sibling module if needed, though we implement logic here
from config import ensure_directories

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/entropy_glm.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def calculate_author_entropy(author_contributions: pd.Series) -> float:
    """
    Calculate Shannon entropy of author contributions.
    
    Args:
        author_contributions: Series of contribution counts (e.g., lines of code) per author.
        
    Returns:
        Shannon entropy value. Returns 0.0 if sum is 0 or only one non-zero contributor.
    """
    if author_contributions is None or len(author_contributions) == 0:
        return 0.0
    
    # Filter out zero contributions
    contributions = author_contributions[author_contributions > 0]
    
    if len(contributions) == 0:
        return 0.0
    
    total = contributions.sum()
    if total == 0:
        return 0.0
    
    # Calculate probabilities
    probs = contributions / total
    
    # Calculate entropy: -sum(p * log(p))
    # Avoid log(0) by filtering out zero probabilities (already done above)
    entropy = -np.sum(probs * np.log(probs))
    
    return float(entropy)

def prepare_data_with_entropy(input_path: str, output_path: str) -> pd.DataFrame:
    """
    Load repo metrics, calculate Shannon entropy per repo, and save to new CSV.
    
    This function expects the input CSV to have a column 'author_contributions' 
    (or similar structure) containing a JSON string or list of contributions per author.
    If that column is missing, it attempts to derive entropy from existing data 
    or assumes a placeholder if the data structure allows.
    
    For this implementation, we assume the input `repo_metrics.csv` has a column 
    `author_contributions` which is a JSON string of lists or a list of numbers 
    representing lines of code per author. If not present, we fallback to 
    calculating entropy based on the assumption that contributions are evenly 
    distributed if only `unique_authors` is known (which is a weak proxy but 
    necessary if raw data is missing).
    
    However, strictly following the task: we need real author contribution data.
    If the previous pipeline (T008) did not save per-author lines, we must 
    rely on the `unique_authors` and `kloc` to estimate or assume a distribution.
    
    Given the constraints of T008 output (url, unique_authors, raw_line_count, kloc),
    we do NOT have per-author line counts. To calculate REAL Shannon entropy, 
    we would need the raw git log parsed to per-author lines.
    
    Since T008 output does not contain per-author breakdown, we must check if 
    there is a way to get it. If not, we cannot calculate REAL entropy.
    
    WAIT: The task T022 says "Implement Shannon entropy calculation for author contributions".
    If the data doesn't exist, we cannot calculate it.
    
    Let's re-read T008: "parse git log for unique authors (with >= 1 line of code committed)".
    It does NOT say it saves per-author lines.
    
    If the data is missing, we must fail loudly or estimate. The prompt says "Real data only".
    We cannot fabricate per-author lines.
    
    However, often in these pipelines, the `author_contributions` column might be 
    expected to be added by T008 or T009. If T008 only counted unique authors, 
    we are stuck without raw data.
    
    Let's assume for the sake of the pipeline that T008/T009 *should* have produced 
    a column `author_contributions` (JSON string) or that we can derive it.
    If the column is missing in `repo_metrics.csv`, we will raise an error 
    because we cannot fabricate the data.
    
    Alternative: If the task implies using `unique_authors` as a proxy for a uniform distribution,
    the entropy would be log(unique_authors). But that is not "Shannon entropy of contributions".
    
    Decision: We will look for a column `author_contributions` in the input.
    If it exists, we calculate entropy.
    If it does NOT exist, we check if we can fetch it. If not, we raise a ValueError
    stating that the required data for entropy calculation is missing from the input.
    
    However, to make the code runnable for the "real" scenario where the data *might* 
    be present (perhaps T008 was updated to save it, or T009 added it), we implement the logic.
    If the column is missing, the script will fail loudly, which is the correct behavior 
    for "Fail loudly, never silently".
    """
    logger.info(f"Loading data from {input_path}")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    required_cols = ['url', 'unique_authors', 'kloc', 'cve_count']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' missing in {input_path}")
    
    # Check for author contributions data
    if 'author_contributions' in df.columns:
        logger.info("Found 'author_contributions' column. Calculating entropy.")
        entropy_values = []
        for idx, row in df.iterrows():
            try:
                # Expecting a JSON string or a list
                if isinstance(row['author_contributions'], str):
                    import json
                    contribs = json.loads(row['author_contributions'])
                else:
                    contribs = row['author_contributions']
                
                entropy = calculate_author_entropy(pd.Series(contribs))
                entropy_values.append(entropy)
            except Exception as e:
                logger.warning(f"Error calculating entropy for {row['url']}: {e}")
                entropy_values.append(np.nan)
        
        df['author_entropy'] = entropy_values
    else:
        # Fallback: If we only have unique_authors, we cannot calculate real entropy of contributions.
        # We must fail loudly as per constraints.
        raise ValueError(
            f"Column 'author_contributions' is missing from {input_path}. "
            "Cannot calculate Shannon entropy of author contributions without per-author contribution data. "
            "Please ensure T008/T009 outputs include this data or fetch it from source."
        )
    
    logger.info(f"Saving entropy data to {output_path}")
    ensure_directories(output_path)
    df.to_csv(output_path, index=False)
    return df

def fit_entropy_glm(data_path: str, output_path: str) -> dict:
    """
    Fit a Negative Binomial GLM with author_entropy as the primary predictor.
    
    Model: cve_count ~ author_entropy + controls, with log(kloc) as offset.
    """
    logger.info(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)
    
    # Filter zero kloc as per T017
    df = df[df['kloc'] > 0]
    if len(df) == 0:
        raise ValueError("No data remaining after filtering zero kloc.")
    
    # Prepare features
    # Primary predictor: author_entropy
    # Controls: language (one-hot), project_age, release_count (if available)
    # Offset: log(kloc)
    
    predictors = ['author_entropy']
    controls = []
    
    # Add controls if they exist
    if 'project_age' in df.columns:
        controls.append('project_age')
    if 'release_count' in df.columns:
        controls.append('release_count')
    if 'language' in df.columns:
        # One-hot encode language
        dummies = pd.get_dummies(df['language'], prefix='lang', drop_first=True)
        df = pd.concat([df, dummies], axis=1)
        for col in dummies.columns:
            predictors.append(col)
    
    # Combine predictors
    X_cols = predictors + controls
    X = df[X_cols].fillna(0)
    
    # Add constant for intercept? GLM with offset usually doesn't need constant if we want rate, 
    # but NegativeBinomial usually includes intercept.
    X = sm.add_constant(X)
    
    y = df['cve_count']
    offset = np.log(df['kloc'])
    
    logger.info(f"Fitting Negative Binomial GLM with predictors: {X.columns.tolist()}")
    
    try:
        model = GLM(y, X, family=NegativeBinomial(), offset=offset)
        results = model.fit()
        
        logger.info(f"Model converged: {results.converged}")
        logger.info(f"AIC: {results.aic}")
        logger.info(f"BIC: {results.bic}")
        
    except Exception as e:
        logger.error(f"GLM fitting failed: {e}")
        raise
    
    # Extract results
    results_dict = {
        'model_type': 'NegativeBinomial_GLM_Entropy',
        'converged': bool(results.converged),
        'aic': float(results.aic),
        'bic': float(results.bic),
        'coefficients': {},
        'pvalues': {},
        'std_errors': {},
        'conf_int_95': {}
    }
    
    for i, param in enumerate(results.params.index):
        results_dict['coefficients'][param] = float(results.params.iloc[i])
        results_dict['pvalues'][param] = float(results.pvalues.iloc[i])
        results_dict['std_errors'][param] = float(results.bse.iloc[i])
        conf_int = results.conf_int()
        results_dict['conf_int_95'][param] = [float(conf_int.iloc[i, 0]), float(conf_int.iloc[i, 1])]
    
    logger.info(f"Saving results to {output_path}")
    ensure_directories(output_path)
    
    with open(output_path, 'w') as f:
        json.dump(results_dict, f, indent=2)
    
    return results_dict

def extract_results(results_path: str) -> dict:
    """Load and return the results from the entropy GLM."""
    with open(results_path, 'r') as f:
        return json.load(f)

def main():
    """Main entry point for the entropy GLM analysis."""
    input_data = "data/processed/repo_metrics_with_entropy.csv"
    output_data = "data/processed/entropy_model_data.csv"
    output_results = "data/processed/entropy_model_results.json"
    
    # Ensure directories exist
    ensure_directories(output_data)
    ensure_directories(output_results)
    
    try:
        # Step 1: Prepare data with entropy
        df = prepare_data_with_entropy(input_data, output_data)
        
        # Step 2: Fit GLM
        results = fit_entropy_glm(output_data, output_results)
        
        logger.info("Entropy GLM analysis completed successfully.")
        logger.info(f"Results saved to {output_results}")
        
        # Print summary
        print(f"Primary Predictor (Entropy) Coefficient: {results['coefficients'].get('author_entropy', 'N/A')}")
        print(f"P-value: {results['pvalues'].get('author_entropy', 'N/A')}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
