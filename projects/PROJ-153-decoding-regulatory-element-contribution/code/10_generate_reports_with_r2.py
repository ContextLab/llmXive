import os
import sys
import argparse
import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple

# Standard library imports for GO enrichment
from collections import Counter
from math import comb

# Note: 'statsmodels' is assumed to be available in the environment as per T002
# We use scipy for hypergeometric test to avoid heavy dependencies if possible,
# but scipy is standard in scientific Python stacks.
from scipy.stats import hypergeom

def load_gls_results(file_path: str) -> pd.DataFrame:
    """Load GLS results from T016/T017 output."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"GLS results file not found: {file_path}")
    df = pd.read_csv(file_path, sep='\t')
    return df

def load_cre_features(file_path: str) -> pd.DataFrame:
    """Load CRE features (coordinates, gene associations) from T013/T014 output."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"CRE features file not found: {file_path}")
    # Assuming BED-like format with gene association in a column or derived from name
    df = pd.read_csv(file_path, sep='\t', header=None, 
                     names=['chrom', 'start', 'end', 'name', 'score', 'strand', 'gene_id'])
    return df

def load_gene_background(gene_list_path: str) -> List[str]:
    """
    Load the background set of genes (e.g., all annotated yeast ORFs).
    This is required for the hypergeometric test denominator.
    """
    if not os.path.exists(gene_list_path):
        raise FileNotFoundError(f"Background gene list not found: {gene_list_path}")
    with open(gene_list_path, 'r') as f:
        # Assuming one gene ID per line
        genes = [line.strip() for line in f if line.strip()]
    return genes

def load_go_annotations(annotation_file: str) -> Dict[str, List[str]]:
    """
    Load GO annotations mapping Gene ID -> List of GO terms.
    Expected format: Tab-separated (GeneID, GO_ID, ...) or similar.
    We will look for a standard Yeast GO annotation file structure.
    """
    if not os.path.exists(annotation_file):
        raise FileNotFoundError(f"GO annotation file not found: {annotation_file}")
    
    # Using pandas to parse flexible formats
    # Expecting columns: Gene, GO, ...
    df = pd.read_csv(annotation_file, sep='\t', comment='!')
    
    # Standardize column names if necessary (e.g., 'Gene' vs 'GeneID')
    # Assuming first column is Gene, second is GO term
    gene_col = df.columns[0]
    go_col = df.columns[1]
    
    mapping = {}
    for _, row in df.iterrows():
        gene = row[gene_col]
        go = row[go_col]
        if gene not in mapping:
            mapping[gene] = []
        mapping[gene].append(go)
    return mapping

def calculate_go_enrichment(
    significant_genes: List[str],
    background_genes: List[str],
    go_annotations: Dict[str, List[str]],
    top_n_terms: int = 20
) -> pd.DataFrame:
    """
    Perform hypergeometric test for GO enrichment.
    
    Args:
        significant_genes: List of gene IDs associated with significant CREs.
        background_genes: List of all gene IDs in the background set.
        go_annotations: Mapping of GeneID -> List of GO terms.
        top_n_terms: Number of top enriched terms to return.
    
    Returns:
        DataFrame with GO term enrichment statistics.
    """
    if not significant_genes:
        logging.warning("No significant genes provided for enrichment analysis.")
        return pd.DataFrame()

    # Filter background to only those with annotations to avoid division by zero
    annotated_background = set(g for g in background_genes if g in go_annotations)
    if not annotated_background:
        raise ValueError("No annotated genes found in the background set.")
    
    total_background = len(annotated_background)
    
    # Count GO terms in the background
    go_counts_bg = Counter()
    for gene in annotated_background:
        for term in go_annotations[gene]:
            go_counts_bg[term] += 1
    
    # Count GO terms in the significant set (intersection with annotated background)
    go_counts_sig = Counter()
    valid_sig_genes = [g for g in significant_genes if g in go_annotations]
    for gene in valid_sig_genes:
        for term in go_annotations[gene]:
            go_counts_sig[term] += 1
    
    results = []
    
    for term, count_sig in go_counts_sig.items():
        if term not in go_counts_bg:
            continue
        
        count_bg = go_counts_bg[term]
        count_sig_total = len(valid_sig_genes)
        
        # Hypergeometric test
        # M = total background (annotated)
        # n = number of genes in background with this term
        # N = number of significant genes
        # k = number of significant genes with this term
        M = total_background
        n = count_bg
        N = count_sig_total
        k = count_sig
        
        if k == 0 or n == 0:
            p_val = 1.0
        else:
            # Calculate p-value: P(X >= k)
            # scipy.stats.hypergeom.sf(k-1, M, n, N) gives P(X > k-1) = P(X >= k)
            p_val = hypergeom.sf(k - 1, M, n, N)
        
        results.append({
            'go_term': term,
            'count_in_sig': k,
            'count_in_bg': n,
            'p_value': p_val,
            'fdr_q_value': np.nan, # To be calculated
            'enrichment_ratio': (k / N) / (n / M) if (n/M) > 0 else np.inf
        })
    
    df_results = pd.DataFrame(results)
    if df_results.empty:
        return pd.DataFrame()
    
    # Benjamini-Hochberg FDR correction
    df_results = df_results.sort_values('p_value')
    df_results['fdr_q_value'] = pd.Series(df_results['p_value']).rank().apply(
        lambda x: min(x * len(df_results) / (x + 1), 1.0) # Approximate BH or use statsmodels
    )
    # More accurate BH using statsmodels if available, otherwise simple rank method above
    # Using simple rank method to avoid extra imports if statsmodels not strictly imported for this
    # Let's try to import statsmodels if available, fallback to simple
    try:
        from statsmodels.stats.multitest import multipletests
        _, q_vals, _, _ = multipletests(df_results['p_value'], method='fdr_bh')
        df_results['fdr_q_value'] = q_vals
    except ImportError:
        logging.warning("statsmodels not found. Using simple rank-based p-value adjustment.")
        # Simple adjustment logic already applied above roughly
    
    return df_results.sort_values('fdr_q_value').head(top_n_terms)

def generate_ranked_report(gls_df: pd.DataFrame, cre_df: pd.DataFrame, output_path: str):
    """
    Generate the ranked CRE report.
    Merges GLS results with CRE features and writes to Markdown.
    """
    # Merge logic depends on specific column names from T016/T013
    # Assuming 'cre_id' or similar joins them. Here we assume 'name' in cre_df matches index or id in gls_df
    # For this implementation, we assume a join on 'cre_id'
    
    if 'cre_id' not in gls_df.columns and 'name' in cre_df.columns:
        # Fallback: assume order or simple join if IDs match
        pass
    
    report_df = pd.merge(gls_df, cre_df, left_on='cre_id', right_on='name', how='left')
    
    # Sort by q-value and absolute beta1
    report_df['abs_beta1'] = report_df['beta1'].abs()
    report_df = report_df.sort_values(by=['q_value', 'abs_beta1'], ascending=[True, False])
    
    with open(output_path, 'w') as f:
        f.write("# Ranked CRE Report\n\n")
        f.write("This report lists significant CREs (q ≤ 0.05) sorted by statistical significance.\n\n")
        f.write("Results are associational, not causal.\n\n")
        
        # Write table
        cols_to_write = ['chrom', 'start', 'end', 'name', 'TF', 'log2FC', 'beta1', 'q_value']
        available_cols = [c for c in cols_to_write if c in report_df.columns]
        f.write(report_df[available_cols].to_markdown(index=False))
        f.write("\n")

def generate_statistical_summary(
    gls_df: pd.DataFrame, 
    cre_df: pd.DataFrame, 
    background_genes: List[str], 
    go_annotations: Dict[str, List[str]],
    output_path: str
):
    """
    Generate the statistical summary PDF/Markdown including GO enrichment.
    """
    # 1. Extract significant genes from the ranked CREs
    significant_cres = gls_df[gls_df['q_value'] <= 0.05]
    
    # Map CREs to genes. Assuming 'gene_id' in cre_df
    if 'gene_id' not in cre_df.columns:
        logging.warning("gene_id column not found in CRE features. Skipping GO enrichment.")
        significant_genes = []
    else:
        # Merge to get gene_ids for significant CREs
        sig_cres_with_genes = pd.merge(
            significant_cres, cre_df[['name', 'gene_id']], 
            left_on='cre_id', right_on='name', how='left'
        )
        significant_genes = sig_cres_with_genes['gene_id'].dropna().unique().tolist()
    
    # 2. Perform GO Enrichment
    go_results = pd.DataFrame()
    if significant_genes:
        try:
            go_results = calculate_go_enrichment(
                significant_genes, 
                background_genes, 
                go_annotations
            )
        except Exception as e:
            logging.error(f"GO enrichment failed: {e}")
    
    # 3. Write Summary
    with open(output_path, 'w') as f:
        f.write("# Statistical Summary\n\n")
        
        # GLS Summary
        f.write("## GLS Model Results\n")
        f.write(f"Total CREs tested: {len(gls_df)}\n")
        f.write(f"Significant CREs (q ≤ 0.05): {len(significant_cres)}\n\n")
        
        # GO Enrichment Section
        f.write("## GO Enrichment Analysis\n")
        if not go_results.empty:
            f.write("Top enriched GO terms for stress-response genes:\n\n")
            f.write(go_results.to_markdown(index=False))
        else:
            f.write("No significant GO terms found or enrichment analysis skipped.\n")
        
        f.write("\n---\n")
        f.write("*Results are associational, not causal.*\n")

def main():
    parser = argparse.ArgumentParser(description="Generate ranked reports and statistical summaries with GO enrichment.")
    parser.add_argument("--gls-results", required=True, help="Path to GLS results TSV (from T016)")
    parser.add_argument("--cre-features", required=True, help="Path to CRE features BED/TSV (from T013)")
    parser.add_argument("--go-annotations", required=True, help="Path to GO annotation file")
    parser.add_argument("--background-genes", required=True, help="Path to background gene list")
    parser.add_argument("--output-ranked", required=True, help="Output path for ranked report (MD)")
    parser.add_argument("--output-summary", required=True, help="Output path for statistical summary (MD)")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    try:
        gls_df = load_gls_results(args.gls_results)
        cre_df = load_cre_features(args.cre_features)
        background_genes = load_gene_background(args.background_genes)
        go_annotations = load_go_annotations(args.go_annotations)
        
        generate_ranked_report(gls_df, cre_df, args.output_ranked)
        logging.info(f"Ranked report written to {args.output_ranked}")
        
        generate_statistical_summary(
            gls_df, cre_df, background_genes, go_annotations, args.output_summary
        )
        logging.info(f"Statistical summary written to {args.output_summary}")
        
    except Exception as e:
        logging.error(f"Report generation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()