"""
Annotation module for mapping significant SNPs to genes and GO terms.

This module implements FR-008: Map significant SNPs to genes using Ensembl Bees API
and query Gene Ontology (GO) terms for functional annotation.
"""
import os
import sys
import argparse
import time
from pathlib import Path
import pandas as pd
import requests
from typing import List, Dict, Optional, Tuple

# Constants
ENSEMBL_BEES_URL = "https://bees.ensembl.org"
ENSEMBL_REST_URL = "https://rest.ensembl.org"
ANNOTATED_OUTPUT_PATH = "data/processed/annotated_snps.tsv"
MIN_Q_VALUE = 0.05

def load_gwas_results(input_path: str) -> pd.DataFrame:
    """
    Load GWAS results and filter for significant SNPs.
    
    Args:
        input_path: Path to the GWAS results TSV file (typically data/processed/gwas_results_fdr.tsv)
        
    Returns:
        DataFrame containing only significant SNPs (q-value < 0.05)
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"GWAS results file not found: {input_path}")
    
    df = pd.read_csv(input_path, sep='\t')
    
    # Ensure q-value column exists
    if 'q_value' not in df.columns:
        # Try alternative column names
        q_cols = [c for c in df.columns if 'q' in c.lower() or 'fdr' in c.lower()]
        if q_cols:
            df.rename(columns={q_cols[0]: 'q_value'}, inplace=True)
        else:
            raise ValueError("No q-value column found in GWAS results")
    
    # Filter significant SNPs
    significant_df = df[df['q_value'] < MIN_Q_VALUE].copy()
    
    if significant_df.empty:
        print(f"Warning: No significant SNPs found with q-value < {MIN_Q_VALUE}")
        # Return empty DF with expected columns to avoid downstream errors
        significant_df = pd.DataFrame(columns=['rs_id', 'gene_symbol', 'go_terms', 'pathway'])
    
    return significant_df

def fetch_gene_info_from_ensembl(snp_id: str, species: str = "apis_mellifera") -> Dict:
    """
    Fetch gene information for a SNP using Ensembl REST API.
    
    Args:
        snp_id: The SNP identifier (rs_id)
        species: Species name for Ensembl (default: apis_mellifera)
        
    Returns:
        Dictionary containing gene symbol, coordinates, and associated GO terms
    """
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    # First, get variant location
    variant_url = f"{ENSEMBL_REST_URL}/variation/{species}/{snp_id}"
    
    try:
        response = requests.get(variant_url, headers=headers, timeout=10)
        response.raise_for_status()
        variant_data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching variant info for {snp_id}: {e}")
        return {'gene_symbol': 'Unknown', 'go_terms': [], 'pathway': 'Unknown'}
    
    # Extract location and surrounding genes
    location = variant_data.get('location', '')
    chrom = None
    pos = None
    
    if location:
        parts = location.split(':')
        if len(parts) >= 2:
            chrom = parts[0]
            pos = int(parts[1].split('-')[0])
    
    if not chrom or not pos:
        return {'gene_symbol': 'Unknown', 'go_terms': [], 'pathway': 'Unknown'}
    
    # Get overlapping genes
    genes_url = f"{ENSEMBL_REST_URL}/overlap/region/{species}/{chrom}:{pos}-{pos}"
    genes_url += "?feature=gene;content_type=application/json"
    
    try:
        response = requests.get(genes_url, headers=headers, timeout=10)
        response.raise_for_status()
        overlap_data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching gene overlap for {snp_id}: {e}")
        return {'gene_symbol': 'Unknown', 'go_terms': [], 'pathway': 'Unknown'}
    
    gene_symbol = 'Unknown'
    gene_id = None
    
    if overlap_data:
        gene_symbol = overlap_data[0].get('external_name', 'Unknown')
        gene_id = overlap_data[0].get('id')
    
    # Fetch GO terms if we have a gene ID
    go_terms = []
    pathway = 'Unknown'
    
    if gene_id and gene_id != 'Unknown':
        # Get GO terms for this gene
        go_url = f"{ENSEMBL_REST_URL}/ontology/{species}/gene/{gene_id}"
        go_url += "?content_type=application/json"
        
        try:
            response = requests.get(go_url, headers=headers, timeout=10)
            if response.status_code == 200:
                go_data = response.json()
                if 'ontology' in go_data:
                    go_terms = [term.get('term', '') for term in go_data['ontology'] if term.get('term')]
                    # Extract pathway if available
                    for term in go_data['ontology']:
                        if 'pathway' in term.get('term', '').lower():
                            pathway = term.get('term', 'Unknown')
                            break
        except requests.exceptions.RequestException as e:
            print(f"Error fetching GO terms for gene {gene_id}: {e}")
    
    return {
        'gene_symbol': gene_symbol,
        'go_terms': ';'.join(go_terms) if go_terms else 'No GO terms found',
        'pathway': pathway
    }

def annotate_snps(snp_list: List[str]) -> List[Dict]:
    """
    Annotate a list of SNPs with gene and GO term information.
    
    Args:
        snp_list: List of SNP identifiers (rs_ids)
        
    Returns:
        List of dictionaries containing annotation data
    """
    annotations = []
    
    print(f"Starting annotation for {len(snp_list)} SNPs...")
    
    for i, snp_id in enumerate(snp_list):
        if i % 10 == 0:
            print(f"Progress: {i}/{len(snp_list)} SNPs processed")
        
        # Rate limiting to avoid API throttling
        if i > 0 and i % 5 == 0:
            time.sleep(1)
        
        info = fetch_gene_info_from_ensembl(snp_id)
        annotations.append({
            'rs_id': snp_id,
            'gene_symbol': info['gene_symbol'],
            'go_terms': info['go_terms'],
            'pathway': info['pathway']
        })
    
    return annotations

def write_annotated_output(annotations: List[Dict], output_path: str) -> None:
    """
    Write annotated SNP data to TSV file.
    
    Args:
        annotations: List of annotation dictionaries
        output_path: Path for the output TSV file
    """
    if not annotations:
        print("No annotations to write.")
        # Create empty file with headers
        df = pd.DataFrame(columns=['rs_id', 'gene_symbol', 'go_terms', 'pathway'])
    else:
        df = pd.DataFrame(annotations)
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    df.to_csv(output_path, sep='\t', index=False)
    print(f"Annotated SNPs written to {output_path}")

def main():
    """Main entry point for SNP annotation pipeline."""
    parser = argparse.ArgumentParser(
        description="Annotate significant SNPs with gene and GO term information"
    )
    parser.add_argument(
        '--input',
        type=str,
        default='data/processed/gwas_results_fdr.tsv',
        help='Path to GWAS results file with q-values'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=ANNOTATED_OUTPUT_PATH,
        help='Path for annotated output TSV'
    )
    
    args = parser.parse_args()
    
    try:
        # Load and filter significant SNPs
        gwas_df = load_gwas_results(args.input)
        
        if gwas_df.empty:
            print("No significant SNPs to annotate. Creating empty output file.")
            write_annotated_output([], args.output)
            return
        
        # Extract SNP IDs
        snp_ids = gwas_df['rs_id'].tolist()
        
        # Annotate SNPs
        annotations = annotate_snps(snp_ids)
        
        # Write output
        write_annotated_output(annotations, args.output)
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during annotation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
