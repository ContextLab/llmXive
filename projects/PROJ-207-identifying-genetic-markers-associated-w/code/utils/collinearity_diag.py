import os
import sys
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor

def calculate_vif(df):
    """
    Calculate Variance Inflation Factor (VIF) for each column in the DataFrame.
    Returns a Series with variable names as index and VIF values as values.
    """
    # Add a constant for the intercept if not present (VIF calculation requires it)
    # However, statsmodels VIF function expects the design matrix X
    # We assume df contains the features (covariates)
    
    # Handle categorical variables encoded as dummy variables (already done by get_dummies usually)
    # If there are non-numeric columns, VIF cannot be calculated directly
    numeric_df = df.select_dtypes(include=[np.number])
    
    if numeric_df.empty:
        return pd.Series(dtype=float)

    # Calculate VIF for each feature
    vif_data = pd.Series(index=numeric_df.columns, dtype=float)
    
    for i, col in enumerate(numeric_df.columns):
        try:
            vif = variance_inflation_factor(numeric_df.values, i)
            vif_data[col] = vif
        except Exception:
            vif_data[col] = np.nan
    
    return vif_data

def calculate_correlation_matrix(df):
    """
    Calculate the correlation matrix for the DataFrame.
    Returns a DataFrame with correlations.
    """
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.empty:
        return pd.DataFrame()
    
    # Calculate Pearson correlation
    corr = numeric_df.corr()
    
    # Convert to r-squared (r²) as requested in task description for flagging
    # Note: Task says "flag relationships where r² > 0.8". 
    # Usually correlation is r, so we square it.
    r_squared = corr ** 2
    return r_squared

def run_collinearity_diagnostics(df, threshold=0.8):
    """
    Run full collinearity diagnostics: VIF and Correlation Matrix.
    Flags pairs with r² > threshold.
    """
    vif = calculate_vif(df)
    corr = calculate_correlation_matrix(df)
    
    flagged_pairs = []
    for i in range(len(corr)):
        for j in range(i + 1, len(corr)):
            val = corr.iloc[i, j]
            if val > threshold:
                flagged_pairs.append({
                    'var1': corr.index[i],
                    'var2': corr.columns[j],
                    'r_squared': val
                })
    
    return {
        'vif': vif,
        'correlation_matrix': corr,
        'flagged_pairs': flagged_pairs
    }

def main():
    parser = argparse.ArgumentParser(description="Collinearity Diagnostics Tool")
    parser.add_argument("--input", type=str, required=True, help="Input TSV file with covariates")
    parser.add_argument("--output", type=str, required=True, help="Output TSV report file")
    parser.add_argument("--threshold", type=float, default=0.8, help="Threshold for r² flagging")
    args = parser.parse_args()

    df = pd.read_csv(args.input, sep='\t')
    
    # Run diagnostics
    results = run_collinearity_diagnostics(df, args.threshold)
    
    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write("VIF Results\n")
        f.write("Variable\tVIF\n")
        for var, val in results['vif'].items():
            f.write(f"{var}\t{val:.4f}\n")
        
        f.write("\nCorrelation Matrix (r²)\n")
        f.write(results['correlation_matrix'].to_csv(sep='\t'))
        
        f.write("\nFlagged Pairs (r² > " + str(args.threshold) + ")\n")
        if not results['flagged_pairs']:
            f.write("None\n")
        else:
            for pair in results['flagged_pairs']:
                f.write(f"{pair['var1']} <-> {pair['var2']}: {pair['r_squared']:.4f}\n")
    
    print(f"Report written to {args.output}")

if __name__ == "__main__":
    main()
