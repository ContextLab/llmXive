import argparse
import logging
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
import numpy as np

from src.utils.logger import get_logger

def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parents[2]

def load_association_data(file_path: Path) -> pd.DataFrame:
    """
    Load association results from T021.
    Expected schema: taxon, maaslin2_beta, maaslin2_se, maaslin2_p_value, 
    maaslin2_q_value, spearman_rho, spearman_se, spearman_p_value.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Association data file not found: {file_path}")
    
    df = pd.read_csv(file_path, sep='\t')
    required_cols = ['taxon', 'maaslin2_beta', 'maaslin2_q_value']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Association data missing required columns: {missing}")
    
    # Filter for significant results (q < 0.05) to reduce noise in replication check
    # However, we keep all for the output to show non-significant ones as non-replicated
    return df

def load_diff_abundance_data(file_path: Path) -> pd.DataFrame:
    """
    Load differential abundance results from ANCOM-II or DESeq2 tasks.
    Expected schema: taxon, method, q-value, effect_size, direction.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Differential abundance data file not found: {file_path}")
    
    df = pd.read_csv(file_path, sep='\t')
    # Normalize column names to lowercase for consistency
    df.columns = [c.lower() for c in df.columns]
    
    required_cols = ['taxon', 'q-value', 'effect_size', 'direction']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        # Try alternative naming
        if 'q_value' in df.columns:
            df['q-value'] = df['q_value']
            required_cols.remove('q-value')
            missing = [c for c in required_cols if c not in df.columns]
        if 'effectsize' in df.columns:
            df['effect_size'] = df['effectsize']
            required_cols.remove('effect_size')
            missing = [c for c in required_cols if c not in df.columns]
        if 'direction' not in df.columns and 'sign' in df.columns:
            df['direction'] = df['sign']
            required_cols.remove('direction')
            missing = [c for c in required_cols if c not in df.columns]
        
        if missing:
            raise ValueError(f"Diff abundance data missing required columns: {missing}. Found: {df.columns.tolist()}")
    
    return df

def determine_replication_status(
    agp_beta: float, 
    ukbb_beta: float, 
    agp_q: float, 
    ukbb_q: float,
    q_threshold: float = 0.05
) -> str:
    """
    Determine replication status based on effect direction and significance.
    
    Rules:
    - 'replicated': Both significant (q < threshold) AND same direction of effect.
    - 'cohort-specific': One significant, the other not.
    - 'non-replicable': Both significant but opposite direction.
    - 'non-replicable' (default): If neither is significant, we mark as non-replicable 
      (or 'non-replicable' to indicate no evidence of replication). 
      However, per standard interpretation, if neither is significant, it's often 
      considered 'non-replicable' in the sense of "no replication found".
      Let's follow: 
      - Both sig & same sign -> replicated
      - Both sig & diff sign -> non-replicable
      - One sig -> cohort-specific
      - Neither sig -> non-replicable (no evidence)
    """
    agp_sig = agp_q < q_threshold
    ukbb_sig = ukbb_q < q_threshold

    if agp_sig and ukbb_sig:
        # Check direction (sign of beta)
        if (agp_beta > 0 and ukbb_beta > 0) or (agp_beta < 0 and ukbb_beta < 0):
            return 'replicated'
        else:
            return 'non-replicable'
    elif agp_sig or ukbb_sig:
        return 'cohort-specific'
    else:
        return 'non-replicable'

def merge_replication_results(
    maaslin2_results: pd.DataFrame,
    ancom_agp: pd.DataFrame,
    ancom_ukbb: pd.DataFrame,
    deseq2_agp: pd.DataFrame,
    deseq2_ukbb: pd.DataFrame,
    q_threshold: float = 0.05
) -> pd.DataFrame:
    """
    Merge results from all methods and calculate replication status.
    
    Returns a DataFrame with schema:
    taxon, method, agp_q_value, ukbb_q_value, agp_effect_size, ukbb_effect_size, 
    replication_status
    """
    results = []

    # 1. MaAsLin2 Results
    # We assume maaslin2_results has 'taxon', 'maaslin2_beta', 'maaslin2_q_value'
    # We need to split by cohort. The input file from T021 might be merged or separate.
    # Assuming T021 output is merged with a 'cohort' column or we have separate files.
    # The task T029 says: "Input: ... association_results.tsv (from T021) for both cohorts"
    # If T021 produced one file for both, we need to filter by cohort.
    # If T021 produced separate files, we load them separately.
    # Let's assume the input to this function is a merged dataframe with a 'cohort' column.
    # If not, we handle the case where we have separate dataframes for AGP and UKBB MaAsLin2.
    
    # For this implementation, we assume the caller passes separate dataframes for AGP and UKBB MaAsLin2
    # if they are separate, or a merged one with a cohort column.
    # Given the task description, let's assume we have a single merged file from T021
    # and we filter by cohort. But the function signature above doesn't support that.
    # Let's adjust: We will assume the `maaslin2_results` passed here is already split 
    # or we need to handle it. 
    # To be safe, let's assume `maaslin2_results` is the merged file and we filter.
    # But the function signature above doesn't take two maaslin2 dataframes.
    # Let's re-read: "Input: ... association_results.tsv (from T021) for both cohorts"
    # This implies one file. So we filter by cohort inside this function if 'cohort' column exists.
    
    if 'cohort' in maaslin2_results.columns:
        agp_maas = maaslin2_results[maaslin2_results['cohort'] == 'AGP'].copy()
        ukbb_maas = maaslin2_results[maaslin2_results['cohort'] == 'UKBB'].copy()
    else:
        # If no cohort column, assume the data is already split or we have two separate inputs.
        # Since the function signature doesn't allow two maaslin2 inputs, we assume the caller
        # has already split them or the data is in a format we can filter.
        # For now, let's assume the data is not split and we cannot proceed without cohort info.
        # But to make it robust, let's assume the caller ensures we have two separate dataframes
        # or the data is in a single dataframe with a cohort column.
        # We'll raise an error if we can't separate.
        raise ValueError("MaAsLin2 results must contain a 'cohort' column to separate AGP and UKBB.")

    # Merge AGP and UKBB MaAsLin2 results on taxon
    maas_merged = pd.merge(
        agp_maas[['taxon', 'maaslin2_beta', 'maaslin2_q_value']],
        ukbb_maas[['taxon', 'maaslin2_beta', 'maaslin2_q_value']],
        on='taxon',
        how='outer',
        suffixes=('_agp', '_ukbb')
    )

    for _, row in maas_merged.iterrows():
        taxon = row['taxon']
        agp_beta = row['maaslin2_beta_agp']
        ukbb_beta = row['maaslin2_beta_ukbb']
        agp_q = row['maaslin2_q_value_agp']
        ukbb_q = row['maaslin2_q_value_ukbb']
        
        status = determine_replication_status(agp_beta, ukbb_beta, agp_q, ukbb_q, q_threshold)
        
        results.append({
            'taxon': taxon,
            'method': 'MaAsLin2',
            'agp_q_value': agp_q,
            'ukbb_q_value': ukbb_q,
            'agp_effect_size': agp_beta,
            'ukbb_effect_size': ukbb_beta,
            'replication_status': status
        })

    # 2. ANCOM-II Results
    # Merge AGP and UKBB ANCOM results
    ancom_merged = pd.merge(
        ancom_agp[['taxon', 'q-value', 'effect_size']],
        ancom_ukbb[['taxon', 'q-value', 'effect_size']],
        on='taxon',
        how='outer',
        suffixes=('_agp', '_ukbb')
    )

    for _, row in ancom_merged.iterrows():
        taxon = row['taxon']
        agp_q = row['q-value_agp']
        ukbb_q = row['q-value_ukbb']
        agp_effect = row['effect_size_agp']
        ukbb_effect = row['effect_size_ukbb']
        
        # For ANCOM, effect_size might be in different units, but we use sign for direction
        status = determine_replication_status(agp_effect, ukbb_effect, agp_q, ukbb_q, q_threshold)
        
        results.append({
            'taxon': taxon,
            'method': 'ANCOM-II',
            'agp_q_value': agp_q,
            'ukbb_q_value': ukbb_q,
            'agp_effect_size': agp_effect,
            'ukbb_effect_size': ukbb_effect,
            'replication_status': status
        })

    # 3. DESeq2 Results
    deseq2_merged = pd.merge(
        deseq2_agp[['taxon', 'q-value', 'effect_size']],
        deseq2_ukbb[['taxon', 'q-value', 'effect_size']],
        on='taxon',
        how='outer',
        suffixes=('_agp', '_ukbb')
    )

    for _, row in deseq2_merged.iterrows():
        taxon = row['taxon']
        agp_q = row['q-value_agp']
        ukbb_q = row['q-value_ukbb']
        agp_effect = row['effect_size_agp']
        ukbb_effect = row['effect_size_ukbb']
        
        status = determine_replication_status(agp_effect, ukbb_effect, agp_q, ukbb_q, q_threshold)
        
        results.append({
            'taxon': taxon,
            'method': 'DESeq2',
            'agp_q_value': agp_q,
            'ukbb_q_value': ukbb_q,
            'agp_effect_size': agp_effect,
            'ukbb_effect_size': ukbb_effect,
            'replication_status': status
        })

    return pd.DataFrame(results)

def run_validation_cross_cohort(
    association_file: Path,
    ancom_agp_file: Path,
    ancom_ukbb_file: Path,
    deseq2_agp_file: Path,
    deseq2_ukbb_file: Path,
    output_file: Path,
    q_threshold: float = 0.05
) -> None:
    """
    Main function to run the cross-cohort validation.
    """
    logger = get_logger(__name__)
    logger.info("Starting cross-cohort validation (T029)")

    # Load data
    logger.info(f"Loading association data from {association_file}")
    assoc_df = load_association_data(association_file)

    logger.info(f"Loading ANCOM-II AGP data from {ancom_agp_file}")
    ancom_agp = load_diff_abundance_data(ancom_agp_file)
    logger.info(f"Loading ANCOM-II UKBB data from {ancom_ukbb_file}")
    ancom_ukbb = load_diff_abundance_data(ancom_ukbb_file)

    logger.info(f"Loading DESeq2 AGP data from {deseq2_agp_file}")
    deseq2_agp = load_diff_abundance_data(deseq2_agp_file)
    logger.info(f"Loading DESeq2 UKBB data from {deseq2_ukbb_file}")
    deseq2_ukbb = load_diff_abundance_data(deseq2_ukbb_file)

    # Merge and calculate replication
    logger.info("Merging results and calculating replication status")
    replication_df = merge_replication_results(
        assoc_df,
        ancom_agp,
        ancom_ukbb,
        deseq2_agp,
        deseq2_ukbb,
        q_threshold
    )

    # Write output
    output_file.parent.mkdir(parents=True, exist_ok=True)
    replication_df.to_csv(output_file, sep='\t', index=False)
    logger.info(f"Replication status written to {output_file}")
    logger.info(f"Total taxa analyzed: {len(replication_df)}")
    logger.info(f"Replicated: {len(replication_df[replication_df['replication_status'] == 'replicated'])}")
    logger.info(f"Non-replicable: {len(replication_df[replication_df['replication_status'] == 'non-replicable'])}")
    logger.info(f"Cohort-specific: {len(replication_df[replication_df['replication_status'] == 'cohort-specific'])}")

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Cross-cohort validation for fiber-microbiome associations"
    )
    parser.add_argument(
        "--association-file",
        type=Path,
        required=True,
        help="Path to association_results.tsv from T021"
    )
    parser.add_argument(
        "--ancom-agp",
        type=Path,
        required=True,
        help="Path to diff_abundance_agp_ancom.tsv"
    )
    parser.add_argument(
        "--ancom-ukbb",
        type=Path,
        required=True,
        help="Path to diff_abundance_ukbb_ancom.tsv"
    )
    parser.add_argument(
        "--deseq2-agp",
        type=Path,
        required=True,
        help="Path to diff_abundance_agp_deseq2.tsv"
    )
    parser.add_argument(
        "--deseq2-ukbb",
        type=Path,
        required=True,
        help="Path to diff_abundance_ukbb_deseq2.tsv"
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=Path("data/processed/results/replication_status.tsv"),
        help="Path for output replication_status.tsv"
    )
    parser.add_argument(
        "--q-threshold",
        type=float,
        default=0.05,
        help="Q-value threshold for significance"
    )
    return parser

def main():
    parser = build_arg_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    run_validation_cross_cohort(
        association_file=args.association_file,
        ancom_agp_file=args.ancom_agp,
        ancom_ukbb_file=args.ancom_ukbb,
        deseq2_agp_file=args.deseq2_agp,
        deseq2_ukbb_file=args.deseq2_ukbb,
        output_file=args.output_file,
        q_threshold=args.q_threshold
    )

if __name__ == "__main__":
    main()
