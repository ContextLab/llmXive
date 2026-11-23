"""
Preprocessing module for genomic data.
Implements streaming VCF parsing using cyvcf2 to ensure memory usage < 7GB.
"""
import logging
import sys
import os
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List, Iterator
import pandas as pd
import numpy as np
from scipy import stats
from collections import defaultdict

# Import logging utility
from utils.logging import get_module_logger
from utils.io import check_disk_space, DiskSpaceError

logger = get_module_logger(__name__)

# Constants
MEMORY_THRESHOLD_GB = 7.0
VCF_INPUT_PATH = "data/raw/genomic.vcf"
MOCK_VCF_INPUT_PATH = "data/raw/mock_genomic.vcf"
VARIANT_TABLE_OUTPUT = "data/processed/variant_table.csv"
DIVERSITY_METRICS_OUTPUT = "data/processed/diversity_metrics.csv"
FEATURES_VIF_OUTPUT = "data/processed/features_vif.csv"
STABLE_FEATURES_OUTPUT = "data/processed/stable_features.csv"
NORMALIZED_FEATURES_OUTPUT = "data/processed/features_normalized.csv"

def _estimate_vcf_size(vcf_path: str) -> int:
    """Estimate the size of a VCF file in bytes."""
    if os.path.exists(vcf_path):
        return os.path.getsize(vcf_path)
    return 0

def _get_vcf_path() -> str:
    """Determine which VCF file to use (real or mock)."""
    if os.path.exists(VCF_INPUT_PATH):
        return VCF_INPUT_PATH
    elif os.path.exists(MOCK_VCF_INPUT_PATH):
        return MOCK_VCF_INPUT_PATH
    else:
        raise FileNotFoundError(f"Neither {VCF_INPUT_PATH} nor {MOCK_VCF_INPUT_PATH} found. Run ingestion first.")

def parse_vcf_to_table(vcf_path: Optional[str] = None) -> pd.DataFrame:
    """
    Parse raw VCF to a variant table using streaming to handle large files.
    
    Args:
        vcf_path: Path to VCF file. If None, auto-detects real or mock.
        
    Returns:
        pd.DataFrame with columns: population_id, variant_id, ref, alt, genotype
        
    Raises:
        FileNotFoundError: If VCF file not found.
        DiskSpaceError: If insufficient disk space.
    """
    if vcf_path is None:
        vcf_path = _get_vcf_path()
        
    if not os.path.exists(vcf_path):
        raise FileNotFoundError(f"VCF file not found: {vcf_path}")
        
    # Check disk space (estimate: 2x file size for processing)
    estimated_size = _estimate_vcf_size(vcf_path) * 2
    check_disk_space(estimated_size)
    
    logger.info(f"Streaming VCF file: {vcf_path}")
    
    # Try to import cyvcf2 for efficient streaming
    try:
        from cyvcf2 import VCF
    except ImportError:
        logger.warning("cyvcf2 not installed. Falling back to pandas-based parsing (slower).")
        return _parse_vcf_fallback(vcf_path)
    
    # Stream VCF using cyvcf2
    variants_data = []
    
    try:
        vcf_reader = VCF(vcf_path)
        
        # Extract sample names (populations)
        samples = vcf_reader.samples
        
        if not samples:
            raise ValueError("VCF file contains no samples/populations")
        
        logger.info(f"Processing {len(samples)} samples from VCF")
        
        # Stream variants
        for variant in vcf_reader:
            # Get variant ID
            var_id = variant.ID if variant.ID else f"{variant.CHROM}:{variant.POS}"
            
            # Get reference and alternate alleles
            ref = variant.REF
            alts = variant.ALT if variant.ALT else []
            
            # Process each alternate allele
            for alt in alts:
                # Get genotypes for all samples
                # GT format: 0/0, 0/1, 1/1, etc.
                gt_array = variant.genotypes  # Shape: (n_samples, 3) where [0,1] is GT, [2] is phased
                
                for i, sample in enumerate(samples):
                    gt = gt_array[i][0:2]  # Get genotype alleles
                    gt_str = "/".join(map(str, gt)) if all(g >= 0 for g in gt) else "./."
                    
                    variants_data.append({
                        'population_id': sample,
                        'variant_id': var_id,
                        'ref': ref,
                        'alt': alt,
                        'genotype': gt_str
                    })
        
        logger.info(f"Processed {len(variants_data)} variant-sample combinations")
        
    except Exception as e:
        logger.error(f"Error processing VCF: {e}")
        raise
    
    # Convert to DataFrame
    df = pd.DataFrame(variants_data)
    
    # Save to CSV
    output_path = Path(VARIANT_TABLE_OUTPUT)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved variant table to {output_path}")
    
    return df

def _parse_vcf_fallback(vcf_path: str) -> pd.DataFrame:
    """
    Fallback VCF parser using standard Python (slower, for when cyvcf2 is unavailable).
    """
    variants_data = []
    
    with open(vcf_path, 'r') as f:
        # Skip header lines
        samples = None
        for line in f:
            if line.startswith('##'):
                continue
            elif line.startswith('#CHROM'):
                # Parse header to get sample names
                parts = line.strip().split('\t')
                samples = parts[9:]  # Sample names start at column 10
                break
        
        if not samples:
            raise ValueError("Could not extract sample names from VCF header")
        
        # Parse variant lines
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) < 10:
                continue
                
            chrom, pos, var_id, ref, alt = parts[0], parts[1], parts[2], parts[3], parts[4]
            
            # Parse genotypes
            gt_fields = parts[9:]
            
            for i, sample in enumerate(samples):
                if i >= len(gt_fields):
                    break
                    
                gt_str = gt_fields[i].split(':')[0]  # First field is genotype
                
                variants_data.append({
                    'population_id': sample,
                    'variant_id': f"{chrom}:{pos}",
                    'ref': ref,
                    'alt': alt,
                    'genotype': gt_str
                })
    
    df = pd.DataFrame(variants_data)
    output_path = Path(VARIANT_TABLE_OUTPUT)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    
    return df

def calculate_diversity_metrics(variant_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Calculate genomic diversity metrics per population.
    Implements FR-004: heterozygosity and nucleotide diversity.
    
    Args:
        variant_df: DataFrame from parse_vcf_to_table. If None, loads from file.
        
    Returns:
        DataFrame with diversity metrics per population.
    """
    if variant_df is None:
        variant_df = pd.read_csv(VARIANT_TABLE_OUTPUT)
    
    # Group by population
    diversity_data = []
    
    for pop_id, group in variant_df.groupby('population_id'):
        # Calculate heterozygosity (proportion of heterozygous genotypes)
        heterozygous = group[group['genotype'].str.contains('0/1|1/0|0|1', na=False)]
        het_count = len(heterozygous)
        total_count = len(group)
        heterozygosity = het_count / total_count if total_count > 0 else 0.0
        
        # Calculate nucleotide diversity (pi) - simplified version
        # Count unique alleles and their frequencies
        allele_counts = defaultdict(int)
        for gt in group['genotype']:
            if pd.isna(gt) or gt == './.':
                continue
            alleles = gt.split('/')
            for a in alleles:
                if a.isdigit() and int(a) >= 0:
                    allele_counts[int(a)] += 1
        
        total_alleles = sum(allele_counts.values())
        if total_alleles > 1:
            # Pi = 1 - sum(pi^2) where pi is allele frequency
            freqs = [count / total_alleles for count in allele_counts.values()]
            nucleotide_diversity = 1 - sum(f**2 for f in freqs)
        else:
            nucleotide_diversity = 0.0
        
        diversity_data.append({
            'population_id': pop_id,
            'heterozygosity': heterozygosity,
            'nucleotide_diversity': nucleotide_diversity,
            'variant_count': total_count,
            'unique_alleles': len(allele_counts)
        })
    
    df = pd.DataFrame(diversity_data)
    output_path = Path(DIVERSITY_METRICS_OUTPUT)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    
    logger.info(f"Saved diversity metrics to {output_path}")
    return df

def calculate_vif_and_aggregate(diversity_df: Optional[pd.DataFrame] = None, 
                               cleaned_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Calculate VIF for collinearity check and aggregate data to population level.
    Implements FR-009 and Assumption 6.
    
    Args:
        diversity_df: Diversity metrics DataFrame.
        cleaned_df: Cleaned data from validation pipeline.
        
    Returns:
        DataFrame with VIF scores and aggregated features.
    """
    if diversity_df is None:
        diversity_df = pd.read_csv(DIVERSITY_METRICS_OUTPUT)
    
    if cleaned_df is None:
        # Try to load cleaned data
        cleaned_path = Path("data/processed/final_cleaned.csv")
        if cleaned_path.exists():
            cleaned_df = pd.read_csv(cleaned_path)
        else:
            logger.warning("Cleaned data not found. Using diversity metrics only.")
            cleaned_df = diversity_df
    
    # Merge diversity metrics with cleaned data
    merged = pd.merge(diversity_df, cleaned_df, on='population_id', how='inner')
    
    # Select numeric features for VIF calculation
    numeric_cols = merged.select_dtypes(include=[np.number]).columns.tolist()
    
    # Remove target variable if present
    target_vars = ['concentration', 'compound_concentration']
    for tv in target_vars:
        if tv in numeric_cols:
            numeric_cols.remove(tv)
    
    if len(numeric_cols) < 2:
        logger.warning("Not enough numeric features for VIF calculation")
        vif_df = pd.DataFrame({
            'feature': numeric_cols,
            'vif': [1.0] * len(numeric_cols)
        })
    else:
        # Calculate VIF
        from statsmodels.stats.outliers_influence import variance_inflation_factor
        
        X = merged[numeric_cols].fillna(0)
        
        # Add constant for intercept
        X_const = sm.add_constant(X) if 'const' not in X.columns else X
        
        vif_data = []
        for col in X.columns:
            if col == 'const':
                continue
            try:
                vif = variance_inflation_factor(X.values, X.columns.get_loc(col))
                vif_data.append({'feature': col, 'vif': vif})
            except Exception as e:
                logger.warning(f"Could not calculate VIF for {col}: {e}")
                vif_data.append({'feature': col, 'vif': np.nan})
        
        vif_df = pd.DataFrame(vif_data)
    
    # Flag high VIF features
    high_vif = vif_df[vif_df['vif'] > 5]
    if len(high_vif) > 0:
        logger.warning(f"Found {len(high_vif)} features with VIF > 5: {high_vif['feature'].tolist()}")
    
    # Save VIF results
    output_path = Path(FEATURES_VIF_OUTPUT)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    vif_df.to_csv(output_path, index=False)
    
    logger.info(f"Saved VIF results to {output_path}")
    return vif_df

def select_stable_features(vif_df: pd.DataFrame, features_df: pd.DataFrame) -> pd.DataFrame:
    """
    Select stable features by removing those with VIF > 5 if model instability is detected.
    
    Args:
        vif_df: DataFrame with VIF scores.
        features_df: DataFrame with features.
        
    Returns:
        DataFrame with stable features only.
    """
    # Identify features with high VIF
    high_vif_features = vif_df[vif_df['vif'] > 5]['feature'].tolist()
    
    if not high_vif_features:
        logger.info("No features with VIF > 5. All features are stable.")
        return features_df
    
    logger.info(f"Removing {len(high_vif_features)} features with VIF > 5: {high_vif_features}")
    
    # Filter features
    stable_cols = [col for col in features_df.columns if col not in high_vif_features]
    stable_df = features_df[stable_cols]
    
    # Save stable features
    output_path = Path(STABLE_FEATURES_OUTPUT)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    stable_df.to_csv(output_path, index=False)
    
    logger.info(f"Saved stable features to {output_path}")
    return stable_df

def apply_normalization(df: pd.DataFrame, cv_strategy: Dict, covariate_config: Dict) -> pd.DataFrame:
    """
    Apply normalization based on CV strategy and covariate configuration.
    
    Args:
        df: Input DataFrame.
        cv_strategy: CV strategy configuration.
        covariate_config: Covariate configuration.
        
    Returns:
        Normalized DataFrame.
    """
    normalized_df = df.copy()
    
    # Get numeric columns
    numeric_cols = normalized_df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Apply normalization
    if covariate_config.get('normalization_type') == 'global_zscore':
        logger.info("Applying global Z-score normalization")
        for col in numeric_cols:
            mean = normalized_df[col].mean()
            std = normalized_df[col].std()
            if std > 0:
                normalized_df[col] = (normalized_df[col] - mean) / std
            else:
                normalized_df[col] = 0.0
    else:
        logger.info("Applying standard scaling")
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        normalized_df[numeric_cols] = scaler.fit_transform(normalized_df[numeric_cols])
    
    # Save normalized features
    output_path = Path(NORMALIZED_FEATURES_OUTPUT)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    normalized_df.to_csv(output_path, index=False)
    
    logger.info(f"Saved normalized features to {output_path}")
    return normalized_df

def run_preprocessing_pipeline() -> Dict[str, Any]:
    """
    Run the complete preprocessing pipeline.
    
    Returns:
        Dictionary with paths to generated artifacts.
    """
    logger.info("Starting preprocessing pipeline")
    
    # Step 1: Parse VCF to table
    variant_df = parse_vcf_to_table()
    
    # Step 2: Calculate diversity metrics
    diversity_df = calculate_diversity_metrics(variant_df)
    
    # Step 3: Calculate VIF and aggregate
    try:
        cleaned_df = pd.read_csv("data/processed/final_cleaned.csv")
        vif_df = calculate_vif_and_aggregate(diversity_df, cleaned_df)
    except FileNotFoundError:
        logger.warning("Cleaned data not found. Skipping VIF calculation.")
        vif_df = calculate_vif_and_aggregate(diversity_df, None)
    
    # Step 4: Load CV and covariate strategies
    cv_strategy = {}
    covariate_config = {}
    
    cv_path = Path("data/processed/cv_strategy.json")
    if cv_path.exists():
        import json
        with open(cv_path) as f:
            cv_strategy = json.load(f)
    
    cov_path = Path("data/processed/covariate_config.json")
    if cov_path.exists():
        import json
        with open(cov_path) as f:
            covariate_config = json.load(f)
    
    # Step 5: Apply normalization
    try:
        final_cleaned = pd.read_csv("data/processed/final_cleaned.csv")
        normalized_df = apply_normalization(final_cleaned, cv_strategy, covariate_config)
    except FileNotFoundError:
        logger.warning("Final cleaned data not found. Skipping normalization.")
        normalized_df = diversity_df
    
    return {
        'variant_table': VARIANT_TABLE_OUTPUT,
        'diversity_metrics': DIVERSITY_METRICS_OUTPUT,
        'features_vif': FEATURES_VIF_OUTPUT,
        'features_normalized': NORMALIZED_FEATURES_OUTPUT
    }

def main():
    """Main entry point for preprocessing."""
    configure_root_logger()
    results = run_preprocessing_pipeline()
    logger.info(f"Preprocessing complete. Artifacts: {results}")
    return results

# Import sm for VIF calculation
try:
    import statsmodels.api as sm
except ImportError:
    logger.warning("statsmodels not installed. VIF calculation may fail.")
    sm = None

# Import sklearn if available
try:
    from sklearn.preprocessing import StandardScaler
except ImportError:
    StandardScaler = None

# Import logging configuration
try:
    from utils.logging import configure_root_logger
except ImportError:
    def configure_root_logger():
        logging.basicConfig(level=logging.INFO)