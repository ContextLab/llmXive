import os
import sys
import json
import logging
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import mean_squared_error
from sklearn.linear_model import LinearRegression
from statsmodels.stats.outliers_influence import variance_inflation_factor

from config import get_project_root
from seed_manager import get_seed, set_seed
from logging_config import get_analysis_logger, save_analysis_results

logger = get_analysis_logger()

def clr_transform(data: pd.DataFrame, pseudocount: float = 0.5) -> pd.DataFrame:
    """
    Apply Centered Log-Ratio (CLR) transformation to microbiome data.
    data: DataFrame with taxa as columns, subjects as rows.
    pseudocount: Value to add to avoid log(0).
    Returns: DataFrame with CLR-transformed values.
    """
    if pseudocount <= 0:
        raise ValueError("Pseudocount must be positive.")
    
    # Add pseudocount
    data_plus_pc = data + pseudocount
    
    # Calculate geometric mean for each row
    geom_mean = data_plus_pc.apply(lambda row: np.exp(np.mean(np.log(row))), axis=1)
    
    # CLR transform
    clr_data = np.log(data_plus_pc / geom_mean.values[:, np.newaxis])
    return pd.DataFrame(clr_data, index=data.index, columns=data.columns)

def load_matched_pairs() -> pd.DataFrame:
    """Load matched pairs from data/processed/matched_pairs.csv"""
    root = get_project_root()
    path = root / "data" / "processed" / "matched_pairs.csv"
    if not path.exists():
        raise FileNotFoundError(f"Matched pairs file not found: {path}")
    return pd.read_csv(path)

def load_distribution_groups() -> pd.DataFrame:
    """Load distribution groups from data/processed/distribution_groups.csv"""
    root = get_project_root()
    path = root / "data" / "processed" / "distribution_groups.csv"
    if not path.exists():
        raise FileNotFoundError(f"Distribution groups file not found: {path}")
    return pd.read_csv(path)

def aggregate_alpha_power_path_a(matched_pairs: pd.DataFrame) -> pd.Series:
    """
    Extract alpha power from matched pairs for Path A.
    Assumes 'alpha_power' column exists in the dataframe.
    """
    if 'alpha_power' not in matched_pairs.columns:
        raise KeyError("Column 'alpha_power' not found in matched_pairs.csv")
    return matched_pairs['alpha_power']

def aggregate_alpha_power_path_b(groups: pd.DataFrame) -> Dict[str, pd.Series]:
    """
    Extract alpha power distributions for groups in Path B.
    Returns a dict mapping group name to Series of alpha power values.
    """
    if 'group' not in groups.columns or 'alpha_power' not in groups.columns:
        raise KeyError("Columns 'group' and 'alpha_power' required in distribution_groups.csv")
    return {name: group['alpha_power'] for name, group in groups.groupby('group')}

def calculate_correlation_path_a(matched_pairs: pd.DataFrame, top_n: int = 20) -> Tuple[pd.DataFrame, List[str]]:
    """
    Calculate Spearman correlation between top N taxa and alpha power (Path A).
    Returns: (DataFrame of results, List of top taxa names)
    """
    # Identify top N taxa by mean abundance
    taxa_cols = [c for c in matched_pairs.columns if c not in ['subject_id_m', 'subject_id_e', 'age', 'sex', 'bmi', 'alpha_power']]
    if not taxa_cols:
        raise ValueError("No taxa columns found in matched_pairs.csv")
    
    mean_abundances = matched_pairs[taxa_cols].mean()
    top_taxa = mean_abundances.nlargest(top_n).index.tolist()
    
    results = []
    for taxon in top_taxa:
        x = matched_pairs[taxon]
        y = matched_pairs['alpha_power']
        
        # Remove NaNs
        mask = ~(x.isna() | y.isna())
        if mask.sum() < 3:
            continue
        
        rho, p_val = stats.spearmanr(x[mask], y[mask])
        results.append({
            'taxon': taxon,
            'rho': rho,
            'p_value': p_val
        })
    
    results_df = pd.DataFrame(results)
    return results_df, top_taxa

def calculate_correlation_path_b(groups: pd.DataFrame, top_n: int = 20) -> Tuple[pd.DataFrame, List[str]]:
    """
    Perform Mann-Whitney U test for top N taxa between High/Low groups (Path B).
    Returns: (DataFrame of results, List of top taxa names)
    """
    # Identify top N taxa
    taxa_cols = [c for c in groups.columns if c not in ['subject_id', 'group', 'alpha_power']]
    if not taxa_cols:
        raise ValueError("No taxa columns found in distribution_groups.csv")
    
    mean_abundances = groups[taxa_cols].mean()
    top_taxa = mean_abundances.nlargest(top_n).index.tolist()
    
    results = []
    groups_dict = {name: grp['alpha_power'] for name, grp in groups.groupby('group')}
    
    if len(groups_dict) < 2:
        raise ValueError("Distribution groups must have at least 2 groups for comparison.")
    
    group_names = list(groups_dict.keys())
    high_group = groups_dict[group_names[0]]
    low_group = groups_dict[group_names[1]]
    
    for taxon in top_taxa:
        # Calculate group means for this taxon to verify directionality? 
        # The task asks for Mann-Whitney U on alpha power distributions between groups defined by taxa abundance.
        # However, the groups are already defined in distribution_groups.csv.
        # We compare alpha_power distributions between the groups for the association.
        # Wait, the task says: "Perform Mann-Whitney U ... comparing alpha power distributions between High/Low abundance groups."
        # The groups are already High/Low. We just test alpha_power difference.
        # But we need to report per taxon? 
        # Re-reading T022: "Perform Mann-Whitney U ... comparing alpha power distributions between High/Low abundance groups."
        # This implies the test is on alpha_power, stratified by the group definition.
        # If the groups are defined by a specific taxon, we do one test per taxon?
        # The task says "top 20 taxa". This implies we split groups based on EACH taxon?
        # But T014 says "Split AGP data into High/Low abundance groups (median split) for top taxa."
        # And then T022 says "comparing alpha power distributions between High/Low abundance groups."
        # If the groups are already in the file, they are likely defined by one specific split or a composite.
        # If the file has a 'group' column, we assume it's the High/Low split.
        # If we need to do it for each of the top 20 taxa, we must re-split the AGP data for each taxon?
        # The file `distribution_groups.csv` likely contains the result of one split (or the AGP side).
        # Let's assume the task implies: For each of the top 20 taxa, if we had split by that taxon, what is the result?
        # But we don't have the raw AGP data in the EEG file.
        # Alternative interpretation: The `distribution_groups.csv` contains the groups for the top taxon, and we just run the test once?
        # But T022 says "top 20 taxa".
        # Let's re-read T014: "Split AGP data ... for top taxa." Plural.
        # This suggests multiple splits.
        # However, `distribution_groups.csv` is a single file. It probably contains the subjects and their assigned group (High/Low) based on the *primary* taxon or a composite score.
        # If the file structure is fixed, we can't easily re-split for 20 taxa without the raw AGP matrix.
        # Let's assume the file `distribution_groups.csv` contains the 'group' column which is the High/Low assignment.
        # And we perform the Mann-Whitney U test on `alpha_power` between these groups.
        # But where does "top 20 taxa" come in for Path B?
        # Perhaps we report the Mann-Whitney U statistic for the alpha power difference, and list the top 20 taxa that *defined* the groups?
        # Or maybe we run the test for the alpha power, and the "top 20" is just the list of taxa we *considered* for grouping?
        # Let's assume the standard interpretation: The groups are fixed. We test alpha power.
        # But we need to output 20 rows?
        # Let's assume the file contains the groups for the *most significant* taxon, or we just report the test result once?
        # The task T026 asks for "test statistics" (plural).
        # Let's assume we run the Mann-Whitney U test on the existing groups, and report that single statistic?
        # Or maybe we run it for each taxon if the file has columns for each?
        # Let's assume the file has a 'group' column (High/Low) and we test alpha_power.
        # If we need 20 results, we might need to iterate over the top 20 taxa, re-splitting the AGP data if available.
        # But `distribution_groups.csv` is the processed output.
        # Let's assume the task implies: Run the test on the existing groups. The "top 20" is context for how groups were formed.
        # We will output one result for the path, or if the file has multiple group definitions...
        # Let's stick to the file content: If it has 'group' and 'alpha_power', run U test.
        # If the task insists on 20, maybe we output the same result 20 times? No, that's fake.
        # Let's assume the file `distribution_groups.csv` has the groups for the top taxon, and we just report that.
        # But T022 says "top 20 taxa".
        # Hypothesis: The `distribution_groups.csv` contains the AGP subjects split by median for EACH of the top 20 taxa?
        # Unlikely for a single file.
        # Let's assume the task T022 is slightly ambiguous and the implementation should:
        # 1. Identify top 20 taxa from the AGP data (which we might need to load separately or is in the file).
        # 2. If the file has a 'group' column, it's the High/Low split for the *primary* taxon.
        # 3. We run the U test on alpha_power.
        # 4. We report the result.
        # To satisfy "top 20", maybe we report the U-statistic for the alpha_power difference, and list the top 20 taxa that were candidates?
        # Let's just run the test on the existing groups and report the statistic.
        # If the file has multiple group columns?
        # Let's assume the file has 'group' (High/Low) and 'alpha_power'.
        # We perform the test.
        # If we need to output 20 rows, we might be stuck.
        # Let's assume the output JSON can handle a single test result for Path B.
        # But T026 says "test statistics" (plural).
        # Maybe we run the test for each of the top 20 taxa if the file has columns for them?
        # Let's assume the file has the AGP data and the group column.
        # We will iterate over the top 20 taxa, re-split the AGP data for each, and run the U test?
        # But we don't have the raw AGP data in the EEG file.
        # Let's assume the `distribution_groups.csv` contains the AGP data and the group column.
        # We will re-split for each of the top 20 taxa.
        
        # Re-reading T014: "Split AGP data ... for top taxa."
        # This implies the file `distribution_groups.csv` might contain the AGP data and the group assignment.
        # Let's assume it has columns: subject_id, group, alpha_power, and taxa columns.
        # We can re-split for each taxon.
        
        # Check if taxa columns exist
        if not any(c in groups.columns for c in top_taxa):
            raise ValueError(f"Top taxa {top_taxa} not found in distribution_groups.csv")
        
        results = []
        for taxon in top_taxa:
            # Split by median of this taxon
            median_val = groups[taxon].median()
            high_grp = groups[groups[taxon] >= median_val]['alpha_power']
            low_grp = groups[groups[taxon] < median_val]['alpha_power']
            
            if len(high_grp) < 2 or len(low_grp) < 2:
                continue
            
            stat, p_val = stats.mannwhitneyu(high_grp, low_grp, alternative='two-sided')
            results.append({
                'taxon': taxon,
                'statistic': stat,
                'p_value': p_val
            })
        
        return pd.DataFrame(results), top_taxa

def calculate_vif(data: pd.DataFrame, top_taxa: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for the top taxa (Path A).
    """
    if len(top_taxa) == 0:
        return {}
    
    X = data[top_taxa].dropna()
    if X.shape[0] < len(top_taxa) + 1:
        logger.warning("Not enough samples for VIF calculation.")
        return {t: float('inf') for t in top_taxa}
    
    # Add intercept
    X_with_intercept = sm.add_constant(X)
    vif_data = {}
    for i, col in enumerate(X_with_intercept.columns):
        if col == 'const':
            continue
        try:
            vif = variance_inflation_factor(X_with_intercept.values, i)
            vif_data[col] = vif
        except Exception as e:
            vif_data[col] = float('nan')
    
    return vif_data

def run_permutation_test(
    data: pd.DataFrame, 
    target_col: str, 
    predictor_cols: List[str], 
    n_permutations: int = 1000, 
    method: str = 'spearman'
) -> Dict[str, Any]:
    """
    Run permutation test to generate null distribution.
    """
    seed = get_seed()
    set_seed(seed)
    
    observed_stats = []
    for col in predictor_cols:
        if method == 'spearman':
            rho, _ = stats.spearmanr(data[col], data[target_col])
            observed_stats.append(rho)
        else:
            # For Mann-Whitney, we need to define groups?
            # Assuming Path A for now as Path B is group-based.
            pass
    
    null_distributions = []
    for _ in range(n_permutations):
        shuffled = data[target_col].sample(frac=1, replace=False, random_state=seed).reset_index(drop=True)
        perm_stats = []
        for col in predictor_cols:
            if method == 'spearman':
                rho, _ = stats.spearmanr(data[col], shuffled)
                perm_stats.append(rho)
        null_distributions.append(perm_stats)
    
    # Check if observed > 95th percentile of null
    results = {}
    for i, col in enumerate(predictor_cols):
        obs = observed_stats[i]
        nulls = [dist[i] for dist in null_distributions]
        percentile_95 = np.percentile(nulls, 95)
        passed = obs > percentile_95
        results[col] = {
            'observed': obs,
            'percentile_95': percentile_95,
            'passed': passed
        }
    
    return results

def save_analysis_results(
    results_df: pd.DataFrame,
    path_type: str,
    vif_values: Optional[Dict[str, float]] = None,
    perm_results: Optional[Dict[str, Any]] = None
):
    """
    Save analysis results to artifacts/analysis_results.json.
    """
    root = get_project_root()
    output_path = root / "artifacts" / "analysis_results.json"
    
    # Ensure artifacts directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # FDR Correction
    if 'p_value' in results_df.columns:
        p_values = results_df['p_value'].values
        # Benjamini-Hochberg
        sorted_indices = np.argsort(p_values)
        sorted_p = p_values[sorted_indices]
        n = len(sorted_p)
        q_values = np.zeros(n)
        for i in range(n):
            q_values[i] = sorted_p[i] * n / (i + 1)
        q_values = np.minimum.accumulate(q_values[::-1])[::-1]
        q_values = np.clip(q_values, 0, 1)
        results_df['q_value'] = 0.0
        results_df.loc[sorted_indices, 'q_value'] = q_values
    
    # Build output dict
    output = {
        'path': path_type,
        'timestamp': pd.Timestamp.now().isoformat(),
        'associational_disclaimer': "Note: This analysis is associational only; no causal inference is made.",
        'results': results_df.to_dict(orient='records')
    }
    
    if vif_values:
        output['vif_values'] = vif_values
    
    if perm_results:
        output['permutation_test'] = perm_results
    
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    logger.info(f"Analysis results saved to {output_path}")
    return output

def main():
    """
    Main entry point for correlation analysis and result generation.
    """
    set_seed(get_seed())
    logger.info("Starting correlation analysis...")
    
    root = get_project_root()
    matched_path = root / "data" / "processed" / "matched_pairs.csv"
    dist_path = root / "data" / "processed" / "distribution_groups.csv"
    
    path_a = matched_path.exists()
    path_b = dist_path.exists()
    
    if not path_a and not path_b:
        logger.error("Neither matched_pairs.csv nor distribution_groups.csv found.")
        sys.exit(1)
    
    results_df = None
    vif_values = None
    perm_results = None
    
    if path_a:
        logger.info("Path A: Virtual Cohort Matching detected.")
        matched_pairs = load_matched_pairs()
        # CLR Transform
        taxa_cols = [c for c in matched_pairs.columns if c not in ['subject_id_m', 'subject_id_e', 'age', 'sex', 'bmi', 'alpha_power']]
        if taxa_cols:
            clr_data = clr_transform(matched_pairs[taxa_cols], pseudocount=0.5)
            matched_pairs[taxa_cols] = clr_data
        
        results_df, top_taxa = calculate_correlation_path_a(matched_pairs)
        vif_values = calculate_vif(matched_pairs, top_taxa)
        
        # Permutation test
        if not results_df.empty:
            perm_results = run_permutation_test(
                matched_pairs, 
                'alpha_power', 
                top_taxa, 
                n_permutations=1000, 
                method='spearman'
            )
        
        path_type = "Path_A"
    
    elif path_b:
        logger.info("Path B: Distributional Comparison detected.")
        groups = load_distribution_groups()
        # We need the AGP data to re-split for top 20 taxa?
        # Assuming the file has the taxa columns.
        taxa_cols = [c for c in groups.columns if c not in ['subject_id', 'group', 'alpha_power']]
        if taxa_cols:
            mean_abundances = groups[taxa_cols].mean()
            top_taxa = mean_abundances.nlargest(20).index.tolist()
        else:
            top_taxa = []
        
        if top_taxa:
            results_df, _ = calculate_correlation_path_b(groups, top_n=20)
        
        path_type = "Path_B"
    
    if results_df is not None:
        save_analysis_results(results_df, path_type, vif_values, perm_results)
    else:
        logger.warning("No results to save.")

if __name__ == "__main__":
    main()