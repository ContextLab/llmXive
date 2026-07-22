import os
import json
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.regression.linear_model import OLS
from statsmodels.tools import add_constant
from sklearn.decomposition import PCA
from typing import Dict, List, Tuple
import warnings

# Import from utils
try:
    from utils import get_logger, set_random_seed
except ImportError:
    def get_logger(name):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        return logging.getLogger(name)
    def set_random_seed(seed):
        pass

logger = get_logger(__name__)
warnings.filterwarnings('ignore')

def load_analysis_data() -> pd.DataFrame:
    path = "data/processed/final_analysis_data.csv"
    if not os.path.exists(path):
        raise FileNotFoundError(f"Analysis data file not found: {path}")
    return pd.read_csv(path)

def sm_add_constant(df, columns):
    return add_constant(df[columns])

def calculate_correlations(df: pd.DataFrame) -> Dict:
    """Calculate Pearson correlations for all pairs."""
    results = {}
    predictors = ['edge_density', 'color_entropy', 'object_count']
    outcomes = ['reaction_time', 'accuracy']
    
    for pred in predictors:
        for out in outcomes:
            # Filter NaNs for this pair
            mask = df[[pred, out]].notna().all(axis=1)
            if mask.sum() < 2:
                continue
            r, p = stats.pearsonr(df.loc[mask, pred], df.loc[mask, out])
            results[f"{pred}_{out}"] = {'r': r, 'p': p}
    return results

def run_regression_standard(df: pd.DataFrame, predictor: str, outcome: str) -> Dict:
    """Run linear regression for a specific pair."""
    mask = df[[predictor, outcome]].notna().all(axis=1)
    if mask.sum() < 2:
        return {'beta': np.nan, 'ci_lower': np.nan, 'ci_upper': np.nan}
    
    X = add_constant(df.loc[mask, predictor])
    y = df.loc[mask, outcome]
    model = OLS(y, X).fit()
    
    beta = model.params[predictor]
    se = model.bse[predictor]
    ci = model.conf_int(alpha=0.05)
    ci_lower = ci.loc[predictor, 0]
    ci_upper = ci.loc[predictor, 1]
    
    return {'beta': beta, 'ci_lower': ci_lower, 'ci_upper': ci_upper}

def calculate_vif(df: pd.DataFrame) -> Dict:
    """Calculate VIF for visual complexity metrics."""
    predictors = ['edge_density', 'color_entropy', 'object_count']
    # Filter rows where all predictors are present
    mask = df[predictors].notna().all(axis=1)
    if mask.sum() < 10:
        return {p: np.nan for p in predictors}
    
    X = df.loc[mask, predictors]
    vif_data = {}
    for i, col in enumerate(X.columns):
        vif = variance_inflation_factor(X.values, i)
        vif_data[col] = vif
    return vif_data

def save_vif_report(vif_data: Dict, path: str):
    with open(path, 'w') as f:
        json.dump(vif_data, f, indent=2)

def run_pca(df: pd.DataFrame) -> pd.DataFrame:
    """Run PCA and add component to df."""
    predictors = ['edge_density', 'color_entropy', 'object_count']
    mask = df[predictors].notna().all(axis=1)
    if mask.sum() < 10:
        return df
    
    pca = PCA(n_components=1)
    df.loc[mask, 'pca_component_1'] = pca.fit_transform(df.loc[mask, predictors])
    return df

def apply_holm_bonferroni(p_values: Dict[str, float]) -> Dict[str, float]:
    """Apply Holm-Bonferroni correction."""
    tests = list(p_values.keys())
    p_vals = list(p_values.values())
    adjusted = stats.multitest.multipletests(p_vals, method='holm')[1]
    return dict(zip(tests, adjusted))

def save_multiplicity_table(correlations: Dict, adjusted: Dict, path: str):
    rows = []
    for key, val in correlations.items():
        pred, out = key.split('_')
        rows.append({
            'test_name': f"{pred}_vs_{out}",
            'raw_p': val['p'],
            'adjusted_p': adjusted.get(key, np.nan),
            'metric_pair': key
        })
    df = pd.DataFrame(rows)
    df.to_csv(path, index=False)
    # Save text snippet
    snippet = " (Wikipedia: Holm–Bonferroni method, https://en.wikipedia.org/wiki/Holm–Bonferroni_method)"
    with open(path.replace('.csv', '_snippet.txt'), 'w') as f:
        f.write(snippet)

def save_statistics(stats_data: Dict, path: str):
    with open(path, 'w') as f:
        json.dump(stats_data, f, indent=2)

def main():
    """Main analysis pipeline."""
    logger.info("Starting statistical analysis pipeline...")
    
    # Load data
    df = load_analysis_data()
    
    # 1. VIF Calculation
    vif_data = calculate_vif(df)
    save_vif_report(vif_data, "results/statistics/vif_report.json")
    logger.info(f"VIF Report: {vif_data}")
    
    # 2. Decision
    use_pca = max(vif_data.values()) >= 5 if any(v is not None and not np.isnan(v) for v in vif_data.values()) else False
    logger.info(f"VIF >= 5? {use_pca}")
    
    # 3. PCA if needed
    if use_pca:
        df = run_pca(df)
        logger.info("PCA component added.")
    
    # 4. Correlations and Regressions
    correlations = calculate_correlations(df)
    
    final_stats = {}
    for key, corr_val in correlations.items():
        pred, out = key.split('_')
        predictor_col = 'pca_component_1' if use_pca else pred
        
        # Regression
        if use_pca:
            reg_res = run_regression_standard(df, 'pca_component_1', out)
            pred_name = 'pca_component_1'
        else:
            reg_res = run_regression_standard(df, pred, out)
            pred_name = pred
        
        final_stats[key] = {
            'r': corr_val['r'],
            'p': corr_val['p'],
            'beta': reg_res['beta'],
            'ci_lower': reg_res['ci_lower'],
            'ci_upper': reg_res['ci_upper'],
            'predictor': pred_name
        }
    
    # 5. Holm-Bonferroni
    p_vals = {k: v['p'] for k, v in final_stats.items()}
    adjusted = apply_holm_bonferroni(p_vals)
    for k, adj_p in adjusted.items():
        final_stats[k]['adjusted_p'] = adj_p
    
    # 6. Save outputs
    save_multiplicity_table(correlations, adjusted, "results/statistics/multiplicity_table.csv")
    save_statistics(final_stats, "results/statistics/statistics.json")
    
    logger.info("Analysis pipeline completed.")

if __name__ == "__main__":
    main()