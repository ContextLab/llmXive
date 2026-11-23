"""
T051b: Filter genes with missing fold-changes and generate CRE-gene pairs.

This script implements the exclusion mechanism for genes with missing
fold-change values in the eQTL dataset, ensuring that the join with CREs
is performed only after filtering to avoid generating pairs for excluded genes.

Dependencies:
    - code/01_stream_eqtl.py (T045): Provides the eQTL dataset
    - data/processed/cre_filtered.tsv (T04_apply_filters): Provides the filtered CRE list

Output:
    - data/processed/cre_gene_pairs.tsv: Filtered CRE-gene pairs with fold-change data
"""
import os
import sys
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/pipeline.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Required columns in eQTL dataset
REQUIRED_EQTL_COLUMNS = {'gene_id', 'heat_shock_fc', 'osmotic_stress_fc', 'oxidative_stress_fc'}
REQUIRED_CRE_COLUMNS = {'cre_id', 'gene_id'}

def load_eqtl_dataset(eqtl_path: Path) -> pd.DataFrame:
    """
    Load the eQTL dataset from the static file produced by T045.

    Args:
        eqtl_path: Path to the eQTL dataset file (TSV/CSV)

    Returns:
        DataFrame containing the eQTL data

    Raises:
        FileNotFoundError: If the eQTL file does not exist
        ValueError: If required columns are missing
    """
    if not eqtl_path.exists():
        raise FileNotFoundError(f"eQTL dataset not found at: {eqtl_path}")

    logger.info(f"Loading eQTL dataset from: {eqtl_path}")

    # Try to read as TSV first, then CSV
    try:
        df = pd.read_csv(eqtl_path, sep='\t')
    except Exception:
        try:
            df = pd.read_csv(eqtl_path, sep=',')
        except Exception as e:
            raise ValueError(f"Failed to parse eQTL file {eqtl_path}: {e}")

    # Validate required columns
    missing_cols = REQUIRED_EQTL_COLUMNS - set(df.columns)
    if missing_cols:
        raise ValueError(f"eQTL dataset missing required columns: {missing_cols}")

    logger.info(f"Loaded eQTL dataset with {len(df)} rows and {len(df.columns)} columns")
    return df

def load_filtered_cres(cre_path: Path) -> pd.DataFrame:
    """
    Load the filtered CRE list from T04_apply_filters.

    Args:
        cre_path: Path to the filtered CRE file (TSV)

    Returns:
        DataFrame containing the filtered CREs

    Raises:
        FileNotFoundError: If the CRE file does not exist
        ValueError: If required columns are missing
    """
    if not cre_path.exists():
        raise FileNotFoundError(f"Filtered CRE file not found at: {cre_path}")

    logger.info(f"Loading filtered CREs from: {cre_path}")

    df = pd.read_csv(cre_path, sep='\t')

    # Validate required columns
    missing_cols = REQUIRED_CRE_COLUMNS - set(df.columns)
    if missing_cols:
        raise ValueError(f"Filtered CRE file missing required columns: {missing_cols}")

    logger.info(f"Loaded {len(df)} filtered CREs")
    return df

def filter_genes_with_missing_fc(eqtl_df: pd.DataFrame) -> Tuple[pd.DataFrame, int, float]:
    """
    Filter out genes with missing fold-change values in any stress condition.

    Args:
        eqtl_df: DataFrame containing the eQTL data

    Returns:
        Tuple of (filtered DataFrame, number of genes dropped, percentage dropped)
    """
    original_count = len(eqtl_df)
    logger.info(f"Filtering genes with missing fold-changes from {original_count} total genes")

    # Check for missing values in any of the stress condition columns
    # A gene is excluded if ANY of the three stress fold-change columns has a missing value
    mask = eqtl_df[REQUIRED_EQTL_COLUMNS].notna().all(axis=1)
    filtered_df = eqtl_df[mask].copy()

    dropped_count = original_count - len(filtered_df)
    dropped_percentage = (dropped_count / original_count * 100) if original_count > 0 else 0.0

    logger.info(f"Filtered out {dropped_count} genes ({dropped_percentage:.2f}% of cohort)")
    logger.info(f"Remaining genes with complete fold-change data: {len(filtered_df)}")

    return filtered_df, dropped_count, dropped_percentage

def create_cre_gene_pairs(
    filtered_eqtl_df: pd.DataFrame,
    filtered_cre_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Create CRE-gene pairs by joining filtered eQTL data with filtered CREs.

    The join is performed AFTER gene filtering to ensure no pairs are generated
    for excluded genes.

    Args:
        filtered_eqtl_df: DataFrame containing eQTL data with complete fold-changes
        filtered_cre_df: DataFrame containing filtered CREs

    Returns:
        DataFrame containing CRE-gene pairs with fold-change data
    """
    logger.info("Performing join between filtered eQTL data and filtered CREs")

    # Ensure gene_id is consistent for joining
    # The eQTL dataset should have gene_id, and CREs should have gene_id
    # We join on gene_id to get the fold-change for each CRE-gene pair

    # First, identify unique genes in filtered CREs
    cre_genes = set(filtered_cre_df['gene_id'].unique())
    eqtl_genes = set(filtered_eqtl_df['gene_id'].unique())

    logger.info(f"Genes in filtered CREs: {len(cre_genes)}")
    logger.info(f"Genes in filtered eQTL: {len(eqt_genes)}")

    # Find genes that are in both sets
    common_genes = cre_genes.intersection(eqt_genes)
    missing_genes = cre_genes - eqtl_genes

    if missing_genes:
        logger.warning(f"Genes in CREs but not in eQTL (will be excluded): {len(missing_genes)}")

    # Filter eQTL to only include genes that are in the CREs
    eqtl_for_join = filtered_eqtl_df[filtered_eqtl_df['gene_id'].isin(common_genes)]

    # Perform the join: merge CREs with eQTL data on gene_id
    # This creates one row per CRE-gene pair with all fold-change columns
    pairs_df = pd.merge(
        filtered_cre_df,
        eqtl_for_join,
        on='gene_id',
        how='inner',
        suffixes=('_cre', '_eqtl')
    )

    # Select and order columns for output
    # We want: cre_id, gene_id, fold_change columns, and any other relevant CRE info
    output_columns = ['cre_id', 'gene_id']

    # Add fold-change columns
    fc_columns = ['heat_shock_fc', 'osmotic_stress_fc', 'oxidative_stress_fc']
    for col in fc_columns:
        if col in pairs_df.columns:
            output_columns.append(col)

    # Add other CRE columns if they exist
    cre_cols = [col for col in filtered_cre_df.columns if col not in ['cre_id', 'gene_id']]
    for col in cre_cols:
        if col in pairs_df.columns:
            output_columns.append(col)

    # Filter to only existing columns
    output_columns = [col for col in output_columns if col in pairs_df.columns]

    result_df = pairs_df[output_columns].copy()

    logger.info(f"Created {len(result_df)} CRE-gene pairs")

    return result_df

def write_output(pairs_df: pd.DataFrame, output_path: Path) -> None:
    """
    Write the CRE-gene pairs to the output file.

    Args:
        pairs_df: DataFrame containing the CRE-gene pairs
        output_path: Path to the output file
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Writing output to: {output_path}")
    pairs_df.to_csv(output_path, sep='\t', index=False)
    logger.info(f"Successfully wrote {len(pairs_df)} rows to {output_path}")

def main():
    """Main entry point for T051b."""
    parser = argparse.ArgumentParser(
        description='Filter genes with missing fold-changes and generate CRE-gene pairs'
    )
    parser.add_argument(
        '--eqtl-path',
        type=str,
        default='data/raw/eqtl_dataset.tsv',
        help='Path to the eQTL dataset file (from T045)'
    )
    parser.add_argument(
        '--cre-path',
        type=str,
        default='data/processed/cre_filtered.tsv',
        help='Path to the filtered CRE file (from T04_apply_filters)'
    )
    parser.add_argument(
        '--output-path',
        type=str,
        default='data/processed/cre_gene_pairs.tsv',
        help='Path to the output CRE-gene pairs file'
    )

    args = parser.parse_args()

    try:
        # Load inputs
        eqtl_df = load_eqtl_dataset(Path(args.eqtl_path))
        cre_df = load_filtered_cres(Path(args.cre_path))

        # Filter genes with missing fold-changes
        filtered_eqtl_df, dropped_count, dropped_pct = filter_genes_with_missing_fc(eqtl_df)

        # Create CRE-gene pairs
        pairs_df = create_cre_gene_pairs(filtered_eqtl_df, cre_df)

        # Write output
        write_output(pairs_df, Path(args.output_path))

        logger.info("T051b completed successfully")
        logger.info(f"Summary: Dropped {dropped_count} genes ({dropped_pct:.2f}% of cohort)")
        logger.info(f"Generated {len(pairs_df)} CRE-gene pairs")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()