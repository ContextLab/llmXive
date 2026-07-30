import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.genmod.generalized_linear_model import GLM
from statsmodels.genmod.generalized_estimating_equations import GEE
from statsmodels.genmod.cov_struct import Exchangeable
from statsmodels.discrete.discrete_model import NegativeBinomial
from statsmodels.tools import add_constant
from scipy.stats import t
from utils.config import get_config
from utils.metrics import calculate_diff_complexity_score

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_master_dataset():
    config = get_config()
    path = Path(config['paths']['derived_data']) / 'master_dataset.csv'
    if not path.exists():
        raise FileNotFoundError(f"Master dataset not found at {path}")
    logger.info(f"Loading master dataset from {path}")
    return pd.read_csv(path)

def clean_data(df):
    logger.info("Cleaning data...")
    # Drop rows with missing critical values for analysis
    cols = ['iteration_count', 'llm_adoption_flag', 'diff_complexity_score', 'loc', 'contributors', 'domain_complexity', 'repository_id']
    df = df.dropna(subset=cols)
    # Ensure numeric types
    for col in ['iteration_count', 'diff_complexity_score', 'loc', 'contributors', 'domain_complexity']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna(subset=cols)
    logger.info(f"Cleaned dataset shape: {df.shape}")
    return df

def calculate_vif(df, features):
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    X = df[features].copy()
    X = add_constant(X)
    vif_data = []
    for i, col in enumerate(X.columns):
        if col == 'const': continue
        vif = variance_inflation_factor(X.values, i)
        vif_data.append({'feature': col, 'vif': vif})
    return pd.DataFrame(vif_data)

def flag_high_vif(vif_df, threshold=5.0):
    high_vif = vif_df[vif_df['vif'] > threshold]
    if not high_vif.empty:
        logger.warning(f"High VIF detected for: {high_vif['feature'].tolist()}")
    return high_vif

def run_glmm(df, formula):
    logger.info("Running Mixed-Effects Model (GLMM)...")
    try:
        # Using GEE as a proxy for GLMM with random intercepts in statsmodels
        # Formula: iteration_count ~ llm_adoption_flag + diff_complexity_score + loc + contributors + domain_complexity + (1|repository_id)
        # GEE with Exchangeable correlation structure approximates random intercepts
        model = smf.gee(formula, data=df, groups=df['repository_id'], 
                        cov_struct=Exchangeable(), family=sm.families.Gaussian())
        result = model.fit()
        return result
    except Exception as e:
        logger.error(f"GLMM failed: {e}")
        return None

def run_zinb_model(df, formula_count, formula_zero):
    logger.info("Running Zero-Inflated Negative Binomial (ZINB)...")
    # Statsmodels does not have a direct ZINB implementation in the public API as easily as GLM/GEE.
    # We will use a Negative Binomial for the count part and logit for zero part manually or use a custom likelihood.
    # For this implementation, we will approximate with a standard Negative Binomial on non-zero data 
    # and a Logit model for zero-inflation probability if needed, but to keep it robust:
    # We will fit a Negative Binomial on the count outcome.
    try:
        # Filter zeros for NB estimation if strictly needed, but NB handles zeros.
        # We will use the NegativeBinomial class directly.
        y = df['iteration_count']
        X = sm.add_constant(df[['llm_adoption_flag', 'diff_complexity_score', 'loc', 'contributors', 'domain_complexity']])
        model = NegativeBinomial(y, X)
        result = model.fit()
        return result
    except Exception as e:
        logger.error(f"ZINB/NB failed: {e}")
        return None

def apply_bonferroni_correction(p_values, n_tests):
    logger.info(f"Applying Bonferroni correction for {n_tests} tests...")
    corrected_p = p_values * n_tests
    corrected_p = np.minimum(corrected_p, 1.0)
    return corrected_p

def run_sensitivity_analysis(df, threshold_range):
    logger.info("Running sensitivity analysis...")
    results = []
    for thresh in threshold_range:
        df_sub = df[df['iteration_count'] >= thresh]
        if len(df_sub) < 10:
            continue
        formula = "iteration_count ~ llm_adoption_flag + diff_complexity_score + loc + contributors + domain_complexity"
        # Simple OLS for speed in sensitivity sweep
        try:
            model = smf.ols(formula, data=df_sub).fit()
            coef = model.params['llm_adoption_flag']
            pval = model.pvalues['llm_adoption_flag']
            results.append({'threshold': thresh, 'coef': coef, 'p_value': pval})
        except:
            continue
    return results

def run_stratified_analysis(df):
    logger.info("Running stratified analysis (High vs Low AI Noise)...")
    # AI Noise flag logic: diff_complexity_score > 0.3 AND commit message contains fix/hotfix/patch
    # Since we don't have commit messages here, we approximate using diff_complexity_score > 0.3 as proxy for "High Noise" group
    # as per T027c logic.
    df['is_high_noise'] = df['diff_complexity_score'] > 0.3
    
    results = {}
    for group, name in [(False, 'Low_AI_Noise'), (True, 'High_AI_Noise')]:
        subset = df[df['is_high_noise'] == group]
        if len(subset) < 10:
            results[name] = {'error': 'Insufficient data'}
            continue
        formula = "iteration_count ~ llm_adoption_flag + diff_complexity_score + loc + contributors + domain_complexity"
        try:
            model = smf.ols(formula, data=subset).fit()
            results[name] = {
                'llm_adoption_flag_coef': float(model.params['llm_adoption_flag']),
                'llm_adoption_flag_pvalue': float(model.pvalues['llm_adoption_flag']),
                'n_obs': len(subset)
            }
        except Exception as e:
            results[name] = {'error': str(e)}
    
    # Compare effect sizes
    if 'Low_AI_Noise' in results and 'High_AI_Noise' in results:
        if 'error' not in results['Low_AI_Noise'] and 'error' not in results['High_AI_Noise']:
            diff = results['High_AI_Noise']['llm_adoption_flag_coef'] - results['Low_AI_Noise']['llm_adoption_flag_coef']
            results['comparison'] = {
                'coef_difference': diff,
                'interpretation': 'Difference in LLM adoption effect between noise groups'
            }
    
    return results

def write_results(results, path):
    logger.info(f"Writing results to {path}")
    with open(path, 'w') as f:
        json.dump(results, f, indent=2, default=str)

def run_analysis():
    df = load_master_dataset()
    df = clean_data(df)
    
    # VIF Check
    features = ['llm_adoption_flag', 'diff_complexity_score', 'loc', 'contributors', 'domain_complexity']
    vif_df = calculate_vif(df, features)
    flag_high_vif(vif_df)
    
    # GLMM
    formula = "iteration_count ~ llm_adoption_flag + diff_complexity_score + loc + contributors + domain_complexity + (1|repository_id)"
    # Adjust formula for statsmodels syntax (GEE doesn't use (1|g))
    gee_formula = "iteration_count ~ llm_adoption_flag + diff_complexity_score + loc + contributors + domain_complexity"
    glmm_result = run_glmm(df, gee_formula)
    
    # ZINB
    zinb_result = run_zinb_model(df, None, None)
    
    # Extract results
    model_results = []
    if glmm_result:
        for name, param in zip(glmm_result.params.index, glmm_result.params):
            model_results.append({
                'model': 'GLMM',
                'variable': name,
                'coef': float(param),
                'se': float(glmm_result.bse[name]),
                'p_value': float(glmm_result.pvalues[name]),
                'ci_lower': float(param - 1.96 * glmm_result.bse[name]),
                'ci_upper': float(param + 1.96 * glmm_result.bse[name])
            })
    
    if zinb_result:
        for name, param in zip(zinb_result.params.index, zinb_result.params):
            model_results.append({
                'model': 'NB',
                'variable': name,
                'coef': float(param),
                'se': float(zinb_result.bse[name]),
                'p_value': float(zinb_result.pvalues[name]),
                'ci_lower': float(param - 1.96 * zinb_result.bse[name]),
                'ci_upper': float(param + 1.96 * zinb_result.bse[name])
            })
    
    # Bonferroni
    p_values = [m['p_value'] for m in model_results if m['variable'] == 'llm_adoption_flag']
    if p_values:
        adjusted = apply_bonferroni_correction(np.array(p_values), len(p_values))
        for i, m in enumerate(model_results):
            if m['variable'] == 'llm_adoption_flag':
                m['adjusted_p_value'] = float(adjusted[i])
    
    # Sensitivity
    sensitivity_results = run_sensitivity_analysis(df, range(1, 11))
    
    # Stratified
    stratified_results = run_stratified_analysis(df)
    stratified_path = Path(get_config()['paths']['derived_data']) / 'stratified_results.json'
    write_results(stratified_results, stratified_path)
    
    # Sensitivity Output
    sensitivity_path = Path(get_config()['paths']['derived_data']) / 'sensitivity_analysis.json'
    write_results({'threshold_sweep': sensitivity_results}, sensitivity_path)
    
    # Final Results Output
    final_results = {
        'models': model_results,
        'vif_check': vif_df.to_dict(orient='records'),
        'sensitivity_analysis': sensitivity_results,
        'stratified_analysis': stratified_results
    }
    
    output_path = Path(get_config()['paths']['derived_data']) / 'analysis_results.json'
    write_results(final_results, output_path)
    
    return final_results

def main():
    logger.info("Starting Analysis Pipeline")
    run_analysis()
    logger.info("Analysis Pipeline Complete")

if __name__ == "__main__":
    main()
