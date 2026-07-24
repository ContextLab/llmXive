import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from scipy.stats import entropy
from skbio.diversity import alpha_diversity, beta_diversity
from skbio.stats.distance import permanova
from statsmodels.stats.power import FTestAnovaPower
from statsmodels.stats.multitest import multipletests

# Import shared utilities from existing project API
from utils import log_underpowered_flag, benjamini_hochberg_fdr, generate_checksum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/diversity_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_processed_data(processed_dir: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load processed feature table and metadata from data/processed directory.
    
    Args:
        processed_dir: Path to the processed data directory
        
    Returns:
        Tuple of (feature_table, metadata) DataFrames
    """
    feature_table_path = Path(processed_dir) / 'feature_table_filtered.csv'
    metadata_path = Path(processed_dir) / 'metadata_filtered.csv'
    
    if not feature_table_path.exists():
        logger.error(f"Feature table not found at {feature_table_path}")
        sys.exit(1)
        
    if not metadata_path.exists():
        logger.error(f"Metadata not found at {metadata_path}")
        sys.exit(1)
        
    feature_table = pd.read_csv(feature_table_path, index_col=0)
    metadata = pd.read_csv(metadata_path, index_col=0)
    
    logger.info(f"Loaded feature table with shape: {feature_table.shape}")
    logger.info(f"Loaded metadata with shape: {metadata.shape}")
    
    return feature_table, metadata

def calculate_alpha_metrics(feature_table: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate alpha diversity metrics (Shannon and Simpson) for each sample.
    
    Args:
        feature_table: DataFrame with taxa as columns and samples as rows
        
    Returns:
        DataFrame with alpha diversity metrics
    """
    logger.info("Calculating alpha diversity metrics...")
    
    # Calculate Shannon diversity
    shannon = alpha_diversity('shannon', feature_table.values, ids=feature_table.index)
    
    # Calculate Simpson diversity
    simpson = alpha_diversity('simpson', feature_table.values, ids=feature_table.index)
    
    alpha_df = pd.DataFrame({
        'sample_id': feature_table.index,
        'shannon': shannon,
        'simpson': simpson
    }).set_index('sample_id')
    
    logger.info(f"Alpha diversity calculated for {len(alpha_df)} samples")
    return alpha_df

def calculate_beta_metrics(feature_table: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate beta diversity (Bray-Curtis) between all sample pairs.
    
    Args:
        feature_table: DataFrame with taxa as columns and samples as rows
        
    Returns:
        Distance matrix as a DataFrame
    """
    logger.info("Calculating beta diversity metrics...")
    
    # Calculate Bray-Curtis distance
    bc_dist = beta_diversity('braycurtis', feature_table.values, ids=feature_table.index)
    
    # Convert to DataFrame for easier handling
    bc_df = pd.DataFrame(
        bc_dist.to_data_frame(),
        index=feature_table.index,
        columns=feature_table.index
    )
    
    logger.info(f"Beta diversity calculated for {len(feature_table)} samples")
    return bc_df

def estimate_permanova_power(n_groups: int, n_per_group: int, effect_size: float = 0.15) -> Dict[str, Any]:
    """
    Estimate statistical power for PERMANOVA test.
    
    Args:
        n_groups: Number of groups being compared
        n_per_group: Number of samples per group
        effect_size: Expected effect size (R²)
        
    Returns:
        Dictionary with power analysis results
    """
    logger.info(f"Estimating PERMANOVA power: {n_groups} groups, {n_per_group} per group")
    
    # Total sample size
    n_total = n_groups * n_per_group
    
    # Degrees of freedom
    df1 = n_groups - 1
    df2 = n_total - n_groups
    
    # Use FTestAnovaPower for estimation
    power_analyzer = FTestAnovaPower()
    
    try:
        # Calculate power
        power = power_analyzer.solve_power(
            effect_size=effect_size,
            nobs1=n_total,
            alpha=0.05,
            power=None,
            ratio=1.0
        )
        
        # If power calculation fails or returns NaN, use a fallback
        if pd.isna(power) or power < 0:
            power = 0.0
            
    except Exception as e:
        logger.warning(f"Power calculation failed: {e}. Using conservative estimate.")
        power = 0.0
    
    return {
        'power': float(power),
        'n_per_group': n_per_group,
        'n_total': n_total,
        'effect_size': effect_size,
        'df1': df1,
        'df2': df2
    }

def validate_power_requirements(power_result: Dict[str, Any]) -> str:
    """
    Validate if power analysis meets requirements.
    
    Args:
        power_result: Dictionary with power analysis results
        
    Returns:
        Status string: "PASS" or "UNDERPOWERED"
    """
    power = power_result['power']
    n_per_group = power_result['n_per_group']
    
    if power < 0.8 or n_per_group < 10:
        return "UNDERPOWERED"
    return "PASS"

def save_power_analysis_report(power_result: Dict[str, Any], output_path: str) -> None:
    """
    Save power analysis report to JSON file.
    
    Args:
        power_result: Dictionary with power analysis results
        output_path: Path to save the report
    """
    status = validate_power_requirements(power_result)
    
    report = {
        'power': power_result['power'],
        'n_per_group': power_result['n_per_group'],
        'effect_size': power_result['effect_size'],
        'flag': status,
        'details': {
            'n_total': power_result['n_total'],
            'df1': power_result['df1'],
            'df2': power_result['df2']
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Power analysis report saved to {output_path}")
    
    if status == "UNDERPOWERED":
        log_underpowered_flag()
        logger.error("UNDERPOWERED: Insufficient statistical power. Halting pipeline.")
        sys.exit(1)

def run_permanova_test(beta_dist: pd.DataFrame, metadata: pd.DataFrame, grouping_col: str = 'stage') -> Dict[str, Any]:
    """
    Run PERMANOVA test to compare community composition between groups.
    
    Args:
        beta_dist: Beta diversity distance matrix as DataFrame
        metadata: Metadata DataFrame with grouping information
        grouping_col: Column name in metadata for grouping
        
    Returns:
        Dictionary with PERMANOVA results
    """
    logger.info(f"Running PERMANOVA test with grouping variable: {grouping_col}")
    
    # Ensure metadata index matches distance matrix index
    common_samples = list(set(beta_dist.index) & set(metadata.index))
    
    if len(common_samples) < 3:
        logger.error("Insufficient common samples between distance matrix and metadata")
        sys.exit(1)
    
    # Filter to common samples
    dist_filtered = beta_dist.loc[common_samples, common_samples]
    meta_filtered = metadata.loc[common_samples]
    
    # Convert to skbio DistanceMatrix
    from skbio.stats.distance import DistanceMatrix
    dist_matrix = DistanceMatrix(dist_filtered.values)
    
    # Run PERMANOVA
    result = permanova(
        distance_matrix=dist_matrix,
        metadata=meta_filtered,
        column=grouping_col,
        permutations=999
    )
    
    return {
        'pseudo_f': float(result['test statistic']),
        'r_squared': float(result['R2']),
        'p_value': float(result['p-value']),
        'n_permutations': 999,
        'groups': list(meta_filtered[grouping_col].unique())
    }

def apply_fdr_correction(p_values: List[float], alpha: float = 0.05) -> List[Dict[str, Any]]:
    """
    Apply Benjamini-Hochberg FDR correction to p-values.
    
    Args:
        p_values: List of raw p-values
        alpha: Significance threshold
        
    Returns:
        List of dictionaries with corrected results
    """
    logger.info(f"Applying FDR correction to {len(p_values)} p-values")
    
    if len(p_values) == 0:
        return []
    
    # Use statsmodels for FDR correction
    reject, pvals_corrected, _, _ = multipletests(p_values, alpha=alpha, method='fdr_bh')
    
    results = []
    for i, (p_raw, p_corr, rej) in enumerate(zip(p_values, pvals_corrected, reject)):
        results.append({
            'comparison_id': i,
            'p_raw': float(p_raw),
            'p_corrected': float(p_corr),
            'significant': bool(rej)
        })
    
    return results

def save_results(alpha_metrics: pd.DataFrame, beta_metrics: pd.DataFrame, 
                permanova_results: Dict[str, Any], fdr_results: List[Dict[str, Any]],
                power_result: Dict[str, Any], output_path: str) -> None:
    """
    Save all diversity metrics and analysis results to a single JSON file.
    
    Args:
        alpha_metrics: Alpha diversity metrics DataFrame
        beta_metrics: Beta diversity metrics DataFrame
        permanova_results: PERMANOVA test results
        fdr_results: FDR corrected results
        power_result: Power analysis results
        output_path: Path to save the results
    """
    logger.info("Compiling diversity metrics report...")
    
    # Convert DataFrames to dictionaries for JSON serialization
    alpha_dict = alpha_metrics.to_dict(orient='index')
    
    # For beta metrics, we'll store summary statistics instead of full matrix
    beta_summary = {
        'num_samples': len(beta_metrics),
        'distance_type': 'braycurtis',
        'mean_distance': float(beta_metrics.values[np.triu_indices_from(beta_metrics.values, k=1)].mean())
    }
    
    report = {
        'alpha_diversity': alpha_dict,
        'beta_diversity_summary': beta_summary,
        'permanova': permanova_results,
        'fdr_correction': fdr_results,
        'power_analysis': {
            'power': power_result['power'],
            'n_per_group': power_result['n_per_group'],
            'effect_size': power_result['effect_size'],
            'flag': validate_power_requirements(power_result)
        },
        'metadata': {
            'generated_at': pd.Timestamp.now().isoformat(),
            'sample_count': len(alpha_metrics),
            'taxon_count': 0  # Will be updated if needed
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Generate and record checksum
    checksum = generate_checksum(output_path)
    report['checksum'] = checksum
    
    # Rewrite with checksum
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Diversity metrics report saved to {output_path}")
    logger.info(f"Checksum: {checksum}")

def main():
    """Main execution function for diversity analysis pipeline."""
    logger.info("Starting diversity metrics analysis pipeline...")
    
    # Define paths
    project_root = Path(__file__).parent.parent
    processed_dir = project_root / 'data' / 'processed'
    output_dir = project_root / 'data' / 'processed'
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load processed data
    feature_table, metadata = load_processed_data(str(processed_dir))
    
    # Calculate alpha diversity
    alpha_metrics = calculate_alpha_metrics(feature_table)
    
    # Calculate beta diversity
    beta_metrics = calculate_beta_metrics(feature_table)
    
    # Determine groups for PERMANOVA
    if 'stage' not in metadata.columns:
        logger.error("Metadata must contain 'stage' column for PERMANOVA")
        sys.exit(1)
    
    groups = metadata['stage'].unique()
    n_groups = len(groups)
    n_per_group = len(metadata) // n_groups
    
    # Estimate power
    power_result = estimate_permanova_power(n_groups, n_per_group)
    
    # Save power analysis report (will exit if underpowered)
    power_report_path = output_dir / 'power_analysis_report.json'
    save_power_analysis_report(power_result, str(power_report_path))
    
    # Run PERMANOVA
    permanova_results = run_permanova_test(beta_metrics, metadata)
    
    # Prepare FDR correction (for pairwise comparisons if multiple groups)
    # For now, we have one PERMANOVA test, so we'll just wrap it
    if n_groups > 2:
        # In a real scenario, we'd run pairwise PERMANOVA tests
        # For this implementation, we'll use the single test result
        fdr_results = apply_fdr_correction([permanova_results['p_value']])
    else:
        fdr_results = apply_fdr_correction([permanova_results['p_value']])
    
    # Save comprehensive results
    output_path = output_dir / 'diversity_metrics.json'
    save_results(
        alpha_metrics, 
        beta_metrics, 
        permanova_results, 
        fdr_results, 
        power_result, 
        str(output_path)
    )
    
    logger.info("Diversity metrics analysis completed successfully!")

if __name__ == "__main__":
    main()
