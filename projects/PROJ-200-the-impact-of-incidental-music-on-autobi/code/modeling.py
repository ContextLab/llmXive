import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.regression.mixed_linear_model import MixedLM
from statsmodels.tools import add_constant
from pathlib import Path
from config import get_project_root
from utils import get_logger

log = get_logger(__name__)

def calculate_vif(df, cols):
    X = df[cols]
    X = add_constant(X)
    vifs = []
    for i in range(1, X.shape[1]):
        y = X.iloc[:, i]
        X_others = X.drop(columns=X.columns[i])
        model = sm.OLS(y, X_others).fit()
        r2 = model.rsquared
        vifs.append(1 / (1 - r2) if r2 < 1 else np.inf)
    return vifs

def main():
    log.info("Running modeling (Thin Pipeline)...")
    root = get_project_root()
    in_path = root / "data" / "processed" / "user_track_pairs.parquet"
    
    if not in_path.exists():
        raise FileNotFoundError(f"Input missing: {in_path}")
    
    df = pd.read_parquet(in_path)
    
    # Fit Linear Mixed Model: mean_vividness ~ adolescent_exposure_ratio + popularity + (1|user_id)
    # statsmodels MixedLM syntax: MixedLM(endog, exog, groups)
    exog_cols = ['adolescent_exposure_ratio', 'popularity']
    X = sm.add_constant(df[exog_cols])
    y = df['mean_vividness']
    groups = df['user_id']
    
    model = MixedLM(y, X, groups=groups).fit()
    
    # Calculate VIF
    vifs = calculate_vif(df, exog_cols)
    vif_map = dict(zip(exog_cols, vifs))
    
    # Prepare summary CSV
    results = []
    for col in X.columns:
        term = col if col != 'const' else 'Intercept'
        estimate = model.params[col]
        std_err = model.bse[col]
        t_val = model.tvalues[col]
        p_val = model.pvalues[col]
        vif = vif_map.get(col, np.nan)
        
        results.append({
            'term': term,
            'estimate': estimate,
            'std_error': std_err,
            't_value': t_val,
            'p_value': p_val,
            'vif': vif
        })
    
    summary_df = pd.DataFrame(results)
    out_path = root / "data" / "final" / "regression_summary.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(out_path, index=False)
    log.info(f"Regression summary written to {out_path}")

if __name__ == "__main__":
    main()
