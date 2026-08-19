import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Set, Any, Optional
import pandas as pd
import numpy as np
from scipy.stats import combine_pvalues

from src.config import get_project_root

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_discovery_results(root: Path) -> Dict[str, pd.DataFrame]:
    """
    Load all {tumor_type}_de_results.csv files from data/processed/.
    Returns a dict mapping tumor_type -> DataFrame.
    """
    processed_dir = root / "data" / "processed"
    results = {}
    
    if not processed_dir.exists():
        logger.error(f"Processed directory not found: {processed_dir}")
        return results

    # Find all de results files
    de_files = list(processed_dir.glob("*_de_results.csv"))
    
    if not de_files:
        logger.warning("No differential expression results files found.")
        return results

    for file_path in de_files:
        # Extract tumor type from filename (e.g., "BRCA_de_results.csv" -> "BRCA")
        tumor_type = file_path.stem.replace("_de_results", "")
        
        try:
            df = pd.read_csv(file_path)
            # Validate required columns
            required_cols = ['gene_symbol', 'pvalue', 'padj', 'log2FoldChange']
            if not all(col in df.columns for col in required_cols):
                logger.warning(f"Skipping {file_path}: missing required columns. Found: {df.columns.tolist()}")
                continue
            
            # Filter for significant genes (FDR < 0.05, |log2FC| > 1.0)
            significant_mask = (df['padj'] < 0.05) & (df['log2FoldChange'].abs() > 1.0)
            significant_df = df[significant_mask].copy()
            
            if significant_df.empty:
                logger.info(f"No significant genes found for {tumor_type} (FDR < 0.05, |log2FC| > 1.0)")
                continue
            
            results[tumor_type] = significant_df
            logger.info(f"Loaded {len(significant_df)} significant genes for {tumor_type}")
            
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            continue

    return results

def compute_intersection(results: Dict[str, pd.DataFrame]) -> Set[str]:
    """
    Compute the intersection of significant gene symbols across all tumor types.
    Returns a set of gene symbols present in ALL tumor types.
    """
    if not results:
        return set()
    
    gene_sets = [set(df['gene_symbol'].tolist()) for df in results.values()]
    if not gene_sets:
        return set()
    
    intersection = gene_sets[0]
    for gene_set in gene_sets[1:]:
        intersection = intersection.intersection(gene_set)
    
    return intersection

def compute_union_top_ranked(results: Dict[str, pd.DataFrame], top_n: int = 100) -> List[str]:
    """
    Compute the union of all significant genes and rank them.
    Ranking criteria:
    1. Descending mean absolute log2FC (across all types where significant)
    2. Ascending meta p-value (calculated via Stouffer's method)
    
    Returns the top_n gene symbols.
    """
    if not results:
        return []
    
    # Collect all unique genes
    all_genes = set()
    for df in results.values():
        all_genes.update(df['gene_symbol'].tolist())
    
    if not all_genes:
        return []
    
    # For each gene, calculate mean log2FC and meta p-value
    gene_stats = []
    
    for gene in all_genes:
        log2fc_values = []
        pvalues = []
        
        for df in results.values():
            gene_row = df[df['gene_symbol'] == gene]
            if not gene_row.empty:
                log2fc_values.append(gene_row['log2FoldChange'].iloc[0])
                pvalues.append(gene_row['pvalue'].iloc[0])
        
        if not log2fc_values:
            continue
        
        mean_log2fc = np.mean(log2fc_values)
        mean_abs_log2fc = np.mean([abs(x) for x in log2fc_values])
        
        # Calculate Stouffer's meta p-value
        # Convert p-values to z-scores (one-sided, assuming effect direction)
        # Using absolute values for ranking, but preserving sign for z-score calculation
        try:
            z_scores = []
            for p in pvalues:
                if p <= 0:
                    p = 1e-16  # Prevent log(0)
                elif p >= 1:
                    p = 1 - 1e-16
                z = np.abs(scipy.stats.norm.ppf(p / 2))  # Two-tailed conversion
                z_scores.append(z)
            
            # Stouffer's method: sum of z-scores / sqrt(k)
            if z_scores:
                z_sum = sum(z_scores)
                k = len(z_scores)
                meta_z = z_sum / np.sqrt(k)
                meta_p = 2 * (1 - scipy.stats.norm.cdf(meta_z))
            else:
                meta_p = 1.0
                
        except Exception as e:
            logger.warning(f"Error calculating meta p-value for {gene}: {e}")
            meta_p = 1.0
        
        gene_stats.append({
            'gene_symbol': gene,
            'mean_abs_log2fc': mean_abs_log2fc,
            'meta_pvalue': meta_p,
            'occurrence_count': len(pvalues)
        })
    
    # Sort by descending mean_abs_log2fc, then ascending meta_pvalue
    gene_stats.sort(key=lambda x: (-x['mean_abs_log2fc'], x['meta_pvalue']))
    
    return [g['gene_symbol'] for g in gene_stats[:top_n]]

def run_reml_meta_analysis(results: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Run meta-analysis using Stouffer's method on p-values.
    Returns a DataFrame with gene_symbol, meta_pvalue, mean_log2FC.
    Note: This task specifically requires Stouffer's method via scipy.stats.combine_pvalues.
    """
    if not results:
        return pd.DataFrame(columns=['gene_symbol', 'meta_pvalue', 'mean_log2FC'])
    
    # Collect all unique genes
    all_genes = set()
    for df in results.values():
        all_genes.update(df['gene_symbol'].tolist())
    
    gene_stats = []
    
    for gene in all_genes:
        pvalues = []
        log2fc_values = []
        
        for df in results.values():
            gene_row = df[df['gene_symbol'] == gene]
            if not gene_row.empty:
                pvalues.append(gene_row['pvalue'].iloc[0])
                log2fc_values.append(gene_row['log2FoldChange'].iloc[0])
        
        if not pvalues:
            continue
        
        # Calculate mean log2FC
        mean_log2fc = np.mean(log2fc_values)
        
        # Stouffer's method using scipy.stats.combine_pvalues
        # Method: 'stouffer' combines p-values using weighted Z-score method
        try:
            # Ensure p-values are within valid range
            pvalues_clipped = [max(1e-16, min(1 - 1e-16, p)) for p in pvalues]
            
            # Use combine_pvalues with Stouffer's method
            # weights=None gives equal weight to all studies
            result = combine_pvalues(pvalues_clipped, method='stouffer', weights=None)
            meta_pvalue = result.pvalue
            
        except Exception as e:
            logger.warning(f"Error running Stouffer's meta-analysis for {gene}: {e}")
            meta_pvalue = 1.0
        
        gene_stats.append({
            'gene_symbol': gene,
            'meta_pvalue': meta_pvalue,
            'mean_log2FC': mean_log2fc
        })
    
    return pd.DataFrame(gene_stats)

def aggregate_and_select_panel(
    root: Path,
    intersection_threshold: int = 2
) -> Dict[str, Any]:
    """
    Main logic to generate the static gene panel.
    1. Load DE results for all tumor types.
    2. Compute intersection of significant genes.
    3. If intersection is empty, fallback to union top-ranked.
    4. Perform Stouffer's meta-analysis on the selected genes.
    5. Return the panel and status.
    """
    results = load_discovery_results(root)
    
    if not results:
        logger.error("No discovery results found. Cannot generate gene panel.")
        return {
            'panel': [],
            'status': 'error',
            'reason': 'no_discovery_results'
        }
    
    # Step 1: Compute intersection
    intersection_genes = compute_intersection(results)
    
    fallback_reason = None
    selected_genes = []
    
    if len(intersection_genes) >= intersection_threshold:
        selected_genes = list(intersection_genes)
        logger.info(f"Intersection found with {len(selected_genes)} genes.")
    else:
        # Step 2: Fallback to union top-ranked
        logger.info("Intersection is empty or insufficient. Falling back to union top-ranked.")
        fallback_reason = "intersection_empty"
        # Select top 100 genes by mean log2FC and meta p-value
        selected_genes = compute_union_top_ranked(results, top_n=100)
        logger.info(f"Selected {len(selected_genes)} genes from union (top-ranked).")
    
    # Step 3: Run Stouffer's meta-analysis on selected genes
    meta_results = run_reML_meta_analysis(results)
    
    # Filter meta_results to only selected genes
    panel_df = meta_results[meta_results['gene_symbol'].isin(selected_genes)].copy()
    
    # Sort by meta_pvalue
    panel_df = panel_df.sort_values('meta_pvalue')
    
    panel = panel_df['gene_symbol'].tolist()
    
    return {
        'panel': panel,
        'panel_size': len(panel),
        'status': 'completed',
        'fallback_reason': fallback_reason,
        'intersection_size': len(intersection_genes),
        'meta_analysis_method': 'Stouffer'
    }

def update_summary_with_fallback(root: Path, fallback_reason: Optional[str]) -> None:
    """
    Update results/summary.md with fallback reason if applicable.
    """
    summary_path = root / "results" / "summary.md"
    
    # Ensure results directory exists
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    
    note = ""
    if fallback_reason:
        note = f"\n# Fallback Status\n- **Fallback Reason**: {fallback_reason}\n"
    
    # Append to summary if it exists, otherwise create
    mode = 'a' if summary_path.exists() else 'w'
    with open(summary_path, mode) as f:
        f.write(note)

def write_override_note(root: Path, method: str) -> None:
    """
    Write override note to panel_status.json to satisfy Spec FR-006.
    """
    status_path = root / "results" / "meta_analysis" / "panel_status.json"
    
    # Ensure directory exists
    status_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing status or create new
    status = {}
    if status_path.exists():
        try:
            with open(status_path, 'r') as f:
                status = json.load(f)
        except json.JSONDecodeError:
            status = {}
    
    status['override_note'] = f"{method} used as per Spec FR-006"
    
    with open(status_path, 'w') as f:
        json.dump(status, f, indent=2)

def save_gene_panel(root: Path, panel_data: Dict[str, Any]) -> None:
    """
    Save the final gene panel to results/meta_analysis/gene_panel.json.
    Conforms to gene_panel.schema.yaml structure.
    """
    panel_path = root / "results" / "meta_analysis" / "gene_panel.json"
    
    # Ensure directory exists
    panel_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Format output according to schema
    output = {
        'genes': panel_data['panel'],
        'panel_size': panel_data['panel_size'],
        'selection_method': 'intersection' if not panel_data.get('fallback_reason') else 'union_top_ranked',
        'meta_analysis_method': panel_data.get('meta_analysis_method', 'Stouffer'),
        'selected': panel_data['panel']
    }
    
    # Add fallback reason if applicable
    if panel_data.get('fallback_reason'):
        output['fallback_reason'] = panel_data['fallback_reason']
    
    with open(panel_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    logger.info(f"Gene panel saved to {panel_path}")

def main():
    """
    Entry point for generating the static gene panel (T024).
    """
    root = get_project_root()
    logger.info(f"Starting gene panel generation. Project root: {root}")
    
    # Ensure output directories exist
    (root / "results" / "meta_analysis").mkdir(parents=True, exist_ok=True)
    
    # Generate panel
    panel_data = aggregate_and_select_panel(root)
    
    if panel_data['status'] == 'error':
        logger.error(f"Panel generation failed: {panel_data.get('reason')}")
        sys.exit(1)
    
    # Save panel
    save_gene_panel(root, panel_data)
    
    # Write fallback reason to panel_status.json
    status_path = root / "results" / "meta_analysis" / "panel_status.json"
    status_path.parent.mkdir(parents=True, exist_ok=True)
    
    status = {
        'panel_size': panel_data['panel_size'],
        'selection_method': 'intersection' if not panel_data.get('fallback_reason') else 'union_top_ranked',
        'intersection_size': panel_data.get('intersection_size', 0)
    }
    
    if panel_data.get('fallback_reason'):
        status['fallback_reason'] = panel_data['fallback_reason']
        status['override_note'] = "Stouffer's method used as per Spec FR-006"
        # Also write to summary
        update_summary_with_fallback(root, panel_data['fallback_reason'])
    else:
        status['override_note'] = "Stouffer's method used as per Spec FR-006"
    
    with open(status_path, 'w') as f:
        json.dump(status, f, indent=2)
    
    logger.info(f"Gene panel generation completed. Panel size: {panel_data['panel_size']}")
    logger.info(f"Status saved to {status_path}")

if __name__ == "__main__":
    main()
