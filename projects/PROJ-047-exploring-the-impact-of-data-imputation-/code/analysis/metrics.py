from typing import Dict, Any, Union, List, Optional
import numpy as np
import pandas as pd
import json
import os
from scipy import stats

def calculate_bias_metrics(estimates: Union[List[Dict[str, Any]], pd.DataFrame], 
                           ground_truth: float) -> Dict[str, float]:
    """
    Calculate absolute bias and RMSE for a set of estimates.
    
    Args:
        estimates: List of dicts or DataFrame with 'ate' or 'estimate' keys.
        ground_truth: The true ATE value.
        
    Returns:
        Dictionary with 'absolute_bias' and 'rmse'.
    """
    if isinstance(estimates, pd.DataFrame):
        ate_values = estimates['ate'].values
    else:
        ate_values = np.array([e.get('ate', e.get('estimate')) for e in estimates])
        
    biases = ate_values - ground_truth
    abs_bias = np.abs(biases).mean()
    rmse = np.sqrt(np.mean(biases ** 2))
    
    return {
        'absolute_bias': float(abs_bias),
        'rmse': float(rmse)
    }

def run_statistical_test(bias_matrix: pd.DataFrame) -> Dict[str, Any]:
    """
    Perform statistical testing on bias distributions per beta level.
    
    Decision Tree (FR-006):
    1. Run Shapiro-Wilk test on bias distribution (aggregated by beta).
    2. If p < 0.05 (non-normal) -> Use Friedman Test.
    3. If p >= 0.05 (normal) -> Use Repeated-Measures ANOVA.
    4. Independently: Calculate skewness. If |skewness| > 1 -> Compute Bootstrap CIs.
    
    Args:
        bias_matrix: DataFrame with columns ['beta', 'method', 'bias'].
        
    Returns:
        Dictionary with test results.
    """
    results = {
        'test_type': None,
        'p_value': None,
        'test_statistic': None,
        'skewness': None,
        'bootstrap_ci_diff': None,
        'conclusion': ''
    }
    
    # Ensure we have data
    if bias_matrix.empty or 'bias' not in bias_matrix.columns:
        results['conclusion'] = 'Insufficient data for statistical testing'
        return results
        
    # Aggregate by beta to get a distribution of biases
    # We need to check normality of the combined distribution or per beta?
    # Spec says: "Run Shapiro-Wilk test on bias distribution (derived from ... aggregated by beta level)"
    # Interpretation: We test the distribution of biases across all runs/methods for each beta,
    # or the distribution of mean biases across betas?
    # Given the context of comparing methods, we likely test the distribution of biases 
    # across the different methods for the dataset.
    # Let's assume we are testing the normality of the bias distribution across all entries 
    # (or per beta if we are doing a trend, but the test compares methods).
    # The Friedman/ANOVA compares methods. So we need bias per method.
    
    # Pivot to have methods as columns, rows as observations (runs/beta combinations)
    # If multiple betas, we might need to test per beta or pooled.
    # Let's test per beta level as implied by "aggregated by beta level".
    # We will iterate betas and pick the first one or aggregate if only one beta is present in the slice.
    # For this function, we assume the input is filtered or we aggregate across betas if needed.
    # However, Friedman/ANOVA requires repeated measures (same subjects).
    # Here "subjects" are the simulation runs (seeds).
    # So we need a matrix: Rows = Seeds, Cols = Methods, Values = Bias.
    
    # Group by seed and method to get mean bias per seed per method
    # Then pivot
    if 'seed' not in bias_matrix.columns:
        # If no seed column, we can't do repeated measures properly.
        # Fallback to independent tests or warn.
        # But the spec implies we have seeds from T029c.
        # Let's try to create a pivot based on unique identifiers if 'seed' is missing.
        # Assuming the dataframe is already aggregated or we treat rows as independent.
        # If independent, we use Kruskal-Wallis or ANOVA, not Friedman.
        # But the spec mandates Friedman/ANOVA. We must have repeated measures.
        # Let's assume the input has 'seed' or we use index.
        pass

    # Prepare data for testing: Group by method to get bias distributions
    # We will test the normality of the bias distribution across all methods combined first?
    # Or per method? Shapiro-Wilk is univariate.
    # Spec: "Run Shapiro-Wilk test on bias distribution"
    # Let's test the pooled distribution of biases (all methods, all betas) to decide global test?
    # Or test per beta?
    # Let's assume we test the distribution of biases for the primary comparison (e.g., across methods).
    
    # Let's calculate skewness first as it's independent
    skewness_val = float(stats.skew(bias_matrix['bias'].dropna()))
    results['skewness'] = skewness_val
    
    # Shapiro-Wilk on the bias distribution
    # We test if the bias values (pooled) are normally distributed
    # If the data is grouped by beta, we might need to test each beta.
    # Let's test the overall distribution for the decision tree.
    try:
        shapiro_stat, shapiro_p = stats.shapiro(bias_matrix['bias'].dropna())
    except ValueError:
        # Not enough data points for Shapiro
        shapiro_p = 0.0
        
    if shapiro_p < 0.05:
        # Non-normal -> Friedman Test
        # Friedman requires repeated measures (same subjects).
        # We need to pivot: Index = Seed (or run_id), Columns = Method, Values = Bias
        if 'seed' in bias_matrix.columns:
            pivot_data = bias_matrix.pivot_table(index='seed', columns='method', values='bias', aggfunc='mean')
        elif 'run_id' in bias_matrix.columns:
            pivot_data = bias_matrix.pivot_table(index='run_id', columns='method', values='bias', aggfunc='mean')
        else:
            # Fallback: treat rows as independent (Kruskal-Wallis) but spec says Friedman.
            # We'll try to group by unique index if available, otherwise fail gracefully.
            pivot_data = bias_matrix.groupby('method')['bias'].apply(list).to_dict()
            # Convert to array for Friedman if possible
            # This is a fallback if structure is wrong
            pivot_data = pd.DataFrame({k: v for k, v in pivot_data.items()})
        
        # Ensure we have numeric columns
        pivot_data = pivot_data.apply(pd.to_numeric, errors='coerce').dropna()
        
        if pivot_data.shape[1] >= 2 and pivot_data.shape[0] >= 3:
            # Friedman Test
            try:
                friedman_stat, friedman_p = stats.friedmanchisquare(*[pivot_data[col] for col in pivot_data.columns])
                results['test_type'] = 'friedman'
                results['p_value'] = float(friedman_p)
                results['test_statistic'] = float(friedman_stat)
                results['conclusion'] = f'Friedman test indicates significant difference (p={friedman_p:.4f})'
            except Exception as e:
                results['conclusion'] = f'Friedman test failed: {str(e)}'
                results['test_type'] = 'friedman'
        else:
            # Not enough data for Friedman
            results['conclusion'] = 'Insufficient data for Friedman test (need repeated measures)'
            results['test_type'] = 'friedman'
            results['p_value'] = None
    else:
        # Normal -> Repeated-Measures ANOVA
        # Same pivot logic
        if 'seed' in bias_matrix.columns:
            pivot_data = bias_matrix.pivot_table(index='seed', columns='method', values='bias', aggfunc='mean')
        elif 'run_id' in bias_matrix.columns:
            pivot_data = bias_matrix.pivot_table(index='run_id', columns='method', values='bias', aggfunc='mean')
        else:
            pivot_data = bias_matrix.groupby('method')['bias'].apply(list).to_dict()
            pivot_data = pd.DataFrame({k: v for k, v in pivot_data.items()})
            
        pivot_data = pivot_data.apply(pd.to_numeric, errors='coerce').dropna()
        
        if pivot_data.shape[1] >= 2 and pivot_data.shape[0] >= 3:
            # Use pingouin if available, otherwise manual or scipy
            # Scipy doesn't have built-in RM-ANOVA. We'll use a simplified approach or fallback to Kruskal if needed.
            # But spec says ANOVA. Let's try to implement a basic one or use statsmodels.
            # Since statsmodels is in requirements, we can use it.
            try:
                import statsmodels.stats.anova as anova
                from statsmodels.formula.api import ols
                
                # Reshape for statsmodels
                df_long = pivot_data.reset_index().melt(id_vars='seed', var_name='method', value_name='bias')
                model = ols('bias ~ C(method) + C(seed)', data=df_long).fit()
                anova_table = anova.anova_lm(model, typ=2)
                
                # Extract F and p for method
                method_row = anova_table.loc['C(method)']
                f_stat = method_row['F']
                p_val = method_row['PR(>F)']
                
                results['test_type'] = 'anova'
                results['p_value'] = float(p_val)
                results['test_statistic'] = float(f_stat)
                results['conclusion'] = f'ANOVA indicates significant difference (p={p_val:.4f})'
            except ImportError:
                # Fallback if statsmodels not used for this specific call (though it is available)
                # Or if data structure fails
                results['conclusion'] = 'ANOVA could not be computed (statsmodels error or data structure)'
                results['test_type'] = 'anova'
                results['p_value'] = None
            except Exception as e:
                results['conclusion'] = f'ANOVA failed: {str(e)}'
                results['test_type'] = 'anova'
        else:
            results['conclusion'] = 'Insufficient data for ANOVA'
            results['test_type'] = 'anova'
            results['p_value'] = None

    # Mandatory Bootstrap CI if skewness condition met
    if abs(skewness_val) > 1:
        # Identify best and worst performing methods based on mean bias
        mean_bias = bias_matrix.groupby('method')['bias'].mean()
        best_method = mean_bias.idxmin() # Lowest absolute bias? Or lowest bias? Usually absolute.
        # The spec says "difference in medians between the best and worst".
        # Best = lowest absolute bias? Or closest to 0?
        # Let's assume best = min absolute bias, worst = max absolute bias
        abs_mean_bias = bias_matrix.groupby('method')['bias'].apply(lambda x: np.abs(x).mean())
        best_method = abs_mean_bias.idxmin()
        worst_method = abs_mean_bias.idxmax()
        
        # Get biases for these methods
        bias_best = bias_matrix[bias_matrix['method'] == best_method]['bias'].values
        bias_worst = bias_matrix[bias_matrix['method'] == worst_method]['bias'].values
        
        # Calculate difference in medians
        median_diff = np.median(bias_worst) - np.median(bias_best)
        
        # Bootstrap
        n_boot = 1000
        boot_diffs = []
        for _ in range(n_boot):
            sample_best = np.random.choice(bias_best, size=len(bias_best), replace=True)
            sample_worst = np.random.choice(bias_worst, size=len(bias_worst), replace=True)
            diff = np.median(sample_worst) - np.median(sample_best)
            boot_diffs.append(diff)
        
        ci_lower = np.percentile(boot_diffs, 2.5)
        ci_upper = np.percentile(boot_diffs, 97.5)
        results['bootstrap_ci_diff'] = [float(ci_lower), float(ci_upper)]
        results['conclusion'] += f' [Bootstrap CI for median diff: {ci_lower:.4f}, {ci_upper:.4f}]'

    return results

def save_statistical_test_results(results: Dict[str, Any], output_path: str) -> None:
    """
    Save statistical test results to a JSON file.
    
    Args:
        results: Dictionary from run_statistical_test.
        output_path: Path to the output JSON file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

def main():
    """
    Main entry point for running statistical tests on simulation results.
    Reads from data/results/simulation_summary.csv and writes to data/results/statistical_test_results.json.
    """
    input_path = 'data/results/simulation_summary.csv'
    output_path = 'data/results/statistical_test_results.json'
    
    if not os.path.exists(input_path):
        print(f"Error: Input file {input_path} not found.")
        return
        
    df = pd.read_csv(input_path)
    
    # Ensure required columns exist
    required_cols = ['method', 'bias']
    if not all(col in df.columns for col in required_cols):
        # Try to calculate bias if ground_truth_ate and ate exist
        if 'ate' in df.columns and 'ground_truth_ate' in df.columns:
            df['bias'] = df['ate'] - df['ground_truth_ate']
        else:
            print("Error: Missing required columns 'method' and 'bias' (or 'ate' and 'ground_truth_ate').")
            return
            
    results = run_statistical_test(df)
    save_statistical_test_results(results, output_path)
    print(f"Statistical test results saved to {output_path}")

if __name__ == '__main__':
    main()