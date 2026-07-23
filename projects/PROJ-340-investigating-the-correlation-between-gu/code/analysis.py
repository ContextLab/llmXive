import os
import random
import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import shapiro

def run_correlation_analysis(df):
    """
    Run correlation analysis based on method selection logic (T021).
    Outputs correlation_matrix.json.
    """
    # Identify columns
    taxa_cols = [c for c in df.columns if c.startswith('Taxon')]
    sleep_cols = ['total_sleep_time', 'sws_duration', 'rem_duration', 'sleep_efficiency']
    
    # Check for zero-inflation (T020)
    zero_inflated = False
    for col in taxa_cols:
        zero_prop = (df[col] == 0).sum() / len(df)
        if zero_prop > 0.30:
            zero_inflated = True
            break
    
    # Check normality (T020)
    normal = True
    for col in sleep_cols:
        if col in df.columns:
            stat, p = shapiro(df[col])
            if p < 0.05:
                normal = False
                break
    
    # Method Selection (T021)
    method = 'pearson'
    if zero_inflated:
        method = 'zinb' # Placeholder for ZINB
    elif not normal:
        method = 'spearman'
    
    results = []
    
    if method == 'pearson':
        for t in taxa_cols:
            for s in sleep_cols:
                if t in df.columns and s in df.columns:
                    corr, pval = stats.pearsonr(df[t], df[s])
                    results.append({
                        "taxon": t,
                        "sleep_metric": s,
                        "method": "pearson",
                        "coefficient": corr,
                        "pvalue": pval,
                        "qvalue": pval # Placeholder for FDR
                    })
    elif method == 'spearman':
        for t in taxa_cols:
            for s in sleep_cols:
                if t in df.columns and s in df.columns:
                    corr, pval = stats.spearmanr(df[t], df[s])
                    results.append({
                        "taxon": t,
                        "sleep_metric": s,
                        "method": "spearman",
                        "coefficient": corr,
                        "pvalue": pval,
                        "qvalue": pval
                    })
    else:
        # ZINB placeholder
        print("ZINB method selected (placeholder).")
        for t in taxa_cols:
            for s in sleep_cols:
                if t in df.columns and s in df.columns:
                    results.append({
                        "taxon": t,
                        "sleep_metric": s,
                        "method": "zinb",
                        "coefficient": 0.0,
                        "pvalue": 1.0,
                        "qvalue": 1.0
                    })
    
    # FDR Correction (T025)
    pvals = [r['pvalue'] for r in results]
    if len(pvals) > 0:
        # Benjamini-Hochberg
        sorted_indices = np.argsort(pvals)
        sorted_pvals = np.array(pvals)[sorted_indices]
        n = len(sorted_pvals)
        corrected = np.zeros(n)
        for i, p in enumerate(sorted_pvals):
            corrected[i] = p * n / (i + 1)
        corrected = np.minimum.accumulate(corrected[::-1])[::-1]
        corrected = np.clip(corrected, 0, 1)
        
        for i, idx in enumerate(sorted_indices):
            results[idx]['qvalue'] = corrected[i]
    
    # Save results
    output_path = 'data/results/correlation_matrix.json'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Correlation analysis complete. Results saved to: {output_path}")
    return results

if __name__ == "__main__":
    pass
