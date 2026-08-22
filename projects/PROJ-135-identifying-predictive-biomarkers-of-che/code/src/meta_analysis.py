import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Set, Any, Optional

from src.config import get_project_root, ensure_directories

# Ensure logger is configured
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_discovery_results(results_dir: Path) -> Dict[str, pd.DataFrame]:
    """
    Load differential expression results for each tumor type from the results directory.
    Expects files named like: <tumor_type>_de_results.csv
    """
    results = {}
    if not results_dir.exists():
        logger.warning(f"Results directory {results_dir} does not exist.")
        return results

    for file_path in results_dir.glob("*_de_results.csv"):
        tumor_type = file_path.stem.replace("_de_results", "")
        try:
            df = pd.read_csv(file_path)
            # Ensure required columns exist
            required_cols = ['gene_symbol', 'pvalue', 'log2FC']
            if not all(col in df.columns for col in required_cols):
                logger.warning(f"Skipping {file_path}: missing required columns. Found: {df.columns.tolist()}")
                continue
            results[tumor_type] = df
            logger.info(f"Loaded DE results for {tumor_type} from {file_path}")
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
    return results

def compute_intersection(results: Dict[str, pd.DataFrame], fdr_threshold: float = 0.05, log2fc_threshold: float = 1.0) -> Set[str]:
    """
    Compute the intersection of significant genes across tumor types.
    Significant: FDR < threshold AND |log2FC| > threshold.
    Since we only have pvalues here, we assume the input DE results are already FDR corrected
    or we treat pvalue as the adjusted p-value for this step if 'padj' is missing.
    """
    significant_genes_sets: List[Set[str]] = []

    for tumor_type, df in results.items():
        # Determine p-value column (padj or pvalue)
        p_col = 'padj' if 'padj' in df.columns else 'pvalue'
        
        mask = (df[p_col] < fdr_threshold) & (df['log2FC'].abs() > log2fc_threshold)
        sig_genes = set(df.loc[mask, 'gene_symbol'].dropna().unique())
        significant_genes_sets.append(sig_genes)
        logger.info(f"Tumor type {tumor_type}: {len(sig_genes)} significant genes")

    if not significant_genes_sets:
        return set()

    # Intersection of all sets
    intersection = significant_genes_sets[0]
    for s in significant_genes_sets[1:]:
        intersection = intersection.intersection(s)
    
    logger.info(f"Intersection size: {len(intersection)}")
    return intersection

def compute_union_top_ranked(results: Dict[str, pd.DataFrame], max_genes: int = 50, fdr_threshold: float = 0.05, log2fc_threshold: float = 1.0) -> List[str]:
    """
    Compute the union of top-ranked genes if intersection is empty.
    Ranking: descending mean log2FC, then ascending meta-p-value.
    """
    all_genes = {} # gene_symbol -> {'mean_log2fc': float, 'meta_pvalue': float, 'count': int}

    for tumor_type, df in results.items():
        p_col = 'padj' if 'padj' in df.columns else 'pvalue'
        
        # Filter significant first
        mask = (df[p_col] < fdr_threshold) & (df['log2FC'].abs() > log2fc_threshold)
        sig_df = df.loc[mask]
        
        for _, row in sig_df.iterrows():
            gene = row['gene_symbol']
            if pd.isna(gene): continue
            
            if gene not in all_genes:
                all_genes[gene] = {'mean_log2fc': 0.0, 'sum_log2fc': 0.0, 'count': 0, 'meta_pvalue': 1.0}
            
            all_genes[gene]['sum_log2fc'] += row['log2FC']
            all_genes[gene]['count'] += 1
            # For meta_pvalue, we might need to aggregate later, but for top-ranking by log2FC, mean is key.
            # We'll update meta_pvalue in the next step if meta-analysis was run.
            # For now, we just use mean log2FC for ranking.

    # Calculate mean log2FC
    for gene, data in all_genes.items():
        data['mean_log2fc'] = data['sum_log2fc'] / data['count']

    # Sort by mean log2FC descending, then by meta_pvalue (if available) ascending
    # Since meta_pvalue might not be fully computed here or we use pvalue as proxy,
    # we sort primarily by mean_log2FC.
    sorted_genes = sorted(
        all_genes.keys(),
        key=lambda g: (-all_genes[g]['mean_log2fc'], all_genes[g].get('meta_pvalue', 1.0))
    )

    return sorted_genes[:max_genes]

def run_stouffers_meta_analysis(results: Dict[str, pd.DataFrame], output_path: Path) -> pd.DataFrame:
    """
    Run Stouffer's meta-analysis on p-values across tumor types.
    Requires 'pvalue' or 'padj' column.
    """
    from scipy.stats import combine_pvalues
    
    # Collect all unique genes
    all_genes = set()
    for df in results.values():
        all_genes.update(df['gene_symbol'].dropna().unique())
    
    meta_results = []
    
    for gene in all_genes:
        p_values = []
        weights = [] # Default weight = 1 for each study
        
        for tumor_type, df in results.items():
            gene_row = df[df['gene_symbol'] == gene]
            if not gene_row.empty:
                p_val = gene_row.iloc[0]['pvalue'] # Use raw pvalue for Stouffer usually
                if not pd.isna(p_val):
                    p_values.append(p_val)
                    weights.append(1.0)
        
        if len(p_values) >= 2:
            # Stouffer's method
            combined = combine_pvalues(p_values, weights=weights, method='stouffer')
            combined_pval = combined.pvalue
        elif len(p_values) == 1:
            combined_pval = p_values[0]
        else:
            combined_pval = 1.0 # No data
        
        # Calculate mean log2FC for this gene across available studies
        log2fc_values = []
        for tumor_type, df in results.items():
            gene_row = df[df['gene_symbol'] == gene]
            if not gene_row.empty:
                log2fc_values.append(gene_row.iloc[0]['log2FC'])
        
        mean_log2fc = np.mean(log2fc_values) if log2fc_values else 0.0
        
        meta_results.append({
            'gene_symbol': gene,
            'meta_pvalue': combined_pval,
            'log2FC_mean': mean_log2fc,
            'n_studies': len(p_values)
        })
    
    meta_df = pd.DataFrame(meta_results)
    meta_df.to_csv(output_path, index=False)
    logger.info(f"Stouffer's meta-analysis results saved to {output_path}")
    return meta_df

def update_summary_with_fallback(intersection: Set[str], union_list: List[str], status_path: Path, reason: str):
    """
    Update the panel status JSON with fallback information.
    """
    status_data = {'status': 'completed'}
    if reason:
        status_data['fallback_reason'] = reason
        status_data['intersection_size'] = len(intersection)
        status_data['union_size'] = len(union_list)
    
    with open(status_path, 'w') as f:
        json.dump(status_data, f, indent=2)
    logger.info(f"Panel status updated at {status_path}")

def save_gene_panel(final_genes: List[str], meta_results: pd.DataFrame, output_path: Path):
    """
    Save the final gene panel to a JSON file.
    """
    panel_data = []
    for gene in final_genes:
        row = meta_results[meta_results['gene_symbol'] == gene]
        if not row.empty:
            panel_data.append({
                'gene_symbol': gene,
                'meta_p_value': row.iloc[0]['meta_pvalue'],
                'log2FC_mean': row.iloc[0]['log2FC_mean'],
                'selected': True
            })
        else:
            # Should not happen if final_genes comes from meta_results
            panel_data.append({
                'gene_symbol': gene,
                'meta_p_value': 1.0,
                'log2FC_mean': 0.0,
                'selected': True
            })
    
    with open(output_path, 'w') as f:
        json.dump(panel_data, f, indent=2)
    logger.info(f"Final gene panel saved to {output_path}")

def aggregate_and_select_panel(results_dir: Path, meta_output: Path, panel_output: Path, status_output: Path):
    """
    Main logic for T024c: Finalize Gene Panel.
    1. Load DE results.
    2. Compute intersection.
    3. If empty, compute union of top-ranked.
    4. Save panel and status.
    """
    logger.info("Starting Gene Panel Finalization (T024c)")
    
    # 1. Load DE results
    results = load_discovery_results(results_dir)
    if not results:
        logger.error("No DE results found. Cannot finalize panel.")
        # Create empty status
        with open(status_output, 'w') as f:
            json.dump({'status': 'failed', 'reason': 'no_data'}, f)
        return

    # 2. Compute Intersection
    intersection = compute_intersection(results)
    
    final_genes = []
    fallback_reason = None

    if len(intersection) > 0:
        final_genes = list(intersection)
        logger.info(f"Using intersection of {len(final_genes)} genes.")
    else:
        logger.info("Intersection is empty. Falling back to union of top-ranked genes.")
        # Ensure meta-analysis is run first to get proper ranking if needed
        # T024b should have produced meta_output. If not, we run it here or assume it exists.
        if not meta_output.exists():
            logger.warning("Meta-analysis output not found. Running Stouffer's now.")
            run_stouffers_meta_analysis(results, meta_output)
        
        meta_df = pd.read_csv(meta_output)
        # Re-run union logic with meta_pvalues if available
        # We reuse compute_union_top_ranked but we need to inject meta_pvalues into the results dict?
        # Simpler: Just rank by mean_log2FC from the meta_df if we have it, or re-calculate from results.
        # Let's assume we use the meta_df for ranking now.
        # Sort meta_df by log2FC_mean desc, meta_pvalue asc
        sorted_meta = meta_df.sort_values(by=['log2FC_mean', 'meta_pvalue'], ascending=[False, True])
        final_genes = sorted_meta['gene_symbol'].head(50).tolist()
        fallback_reason = "intersection_empty"
        update_summary_with_fallback(intersection, final_genes, status_output, fallback_reason)
    
    # If we used intersection, we still need to ensure we have meta_pvalues for the output.
    # Run Stouffer if not done or if we used intersection and meta file is missing.
    if not meta_output.exists():
        run_stouffers_meta_analysis(results, meta_output)
    
    meta_df = pd.read_csv(meta_output)
    
    # 3. Save Panel
    save_gene_panel(final_genes, meta_df, panel_output)
    
    # Update status if we didn't do it in the fallback block
    if not fallback_reason:
        update_summary_with_fallback(intersection, final_genes, status_output, None)

def main():
    root = get_project_root()
    results_dir = root / "results" / "meta_analysis"
    ensure_directories([results_dir])

    meta_output = results_dir / "stouffer_meta.csv"
    panel_output = results_dir / "gene_panel.json"
    status_output = results_dir / "panel_status.json"

    aggregate_and_select_panel(results_dir, meta_output, panel_output, status_output)

if __name__ == "__main__":
    main()