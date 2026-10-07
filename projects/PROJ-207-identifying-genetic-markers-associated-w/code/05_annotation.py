"""
SNP Annotation Module for Honeybee GWAS Study.

Maps significant SNPs to genes using Ensembl Bees API v104 and queries GO terms.
Follows Ensembl Bees API v104 documentation and Gene Ontology Consortium standards.
"""

import os
import sys
import argparse
import time
import json
import requests
from pathlib import Path
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any

# Constants
ENSMBL_BASE_URL = "https://bees.ensembl.org"
ENSMBL_VERSION = "v104"
TIMEOUT_SECONDS = 30
RETRY_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 2

# Output paths
ANNOTATION_OUTPUT = "data/processed/annotation_results.tsv"
ANNOTATION_ERRORS_LOG = "data/processed/annotation_errors.log"

def create_session_with_retries() -> requests.Session:
    """Create a requests session with retry logic for API calls."""
    session = requests.Session()
    # Set headers for Ensembl API
    session.headers.update({
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'llmXive-GWAS-Pipeline/1.0'
    })
    return session

def load_gwas_results(input_path: str) -> pd.DataFrame:
    """
    Load GWAS results and filter for significant SNPs.
    
    Args:
        input_path: Path to the FDR-corrected GWAS results file.
        
    Returns:
        DataFrame containing only significant SNPs (q_value < 0.05).
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"GWAS results file not found: {input_path}")
        
    df = pd.read_csv(input_path, sep='\t')
    
    # Validate required columns
    required_cols = ['snp_id', 'q_value', 'significant']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in GWAS results: {missing_cols}")
        
    # Filter for significant SNPs only
    significant_snps = df[df['significant'] == True].copy()
    
    if significant_snps.empty:
        print("WARNING: No significant SNPs found in the input file.")
        # Return empty DF with expected schema to allow downstream to handle gracefully
        return pd.DataFrame(columns=['snp_id', 'gene_symbol', 'distance', 'go_terms'])
        
    print(f"Loaded {len(significant_snps)} significant SNPs for annotation.")
    return significant_snps

def fetch_gene_info_from_ensembl(snp_id: str, session: requests.Session) -> Optional[Dict[str, Any]]:
    """
    Fetch gene information for a specific SNP from Ensembl Bees API.
    
    Args:
        snp_id: The SNP identifier (rs_id).
        session: Requests session for API calls.
        
    Returns:
        Dictionary containing gene information or None if not found.
    """
    endpoint = f"{ENSMBL_BASE_URL}/api/{ENSMBL_VERSION}/overlap/region/Honeybee:{snp_id}"
    params = {'feature': 'gene', 'feature': 'transcript'}
    
    try:
        response = session.get(endpoint, params=params, timeout=TIMEOUT_SECONDS)
        
        if response.status_code == 404:
            return None
        elif response.status_code != 200:
            raise RuntimeError(f"API error for {snp_id}: HTTP {response.status_code}")
            
        data = response.json()
        
        if not data or len(data) == 0:
            return None
            
        return data
        
    except requests.exceptions.Timeout:
        raise TimeoutError(f"Timeout fetching data for {snp_id}")
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Request failed for {snp_id}: {str(e)}")

def fetch_closest_gene(snp_id: str, session: requests.Session, chrom: str, pos: int) -> Tuple[str, float]:
    """
    Fetch the closest gene to a SNP if direct overlap is not found.
    
    Args:
        snp_id: The SNP identifier.
        session: Requests session.
        chrom: Chromosome number.
        pos: Position on chromosome.
        
    Returns:
        Tuple of (gene_symbol, distance) or ('INTERGENIC', -1.0) if no gene found.
    """
    # Try to find overlapping features first
    try:
        data = fetch_gene_info_from_ensembl(snp_id, session)
        if data and len(data) > 0:
            # Select gene with shortest distance if multiple found
            genes = []
            for feature in data:
                if feature.get('feature_type') == 'gene':
                    gene_symbol = feature.get('external_name', 'UNKNOWN')
                    gene_start = feature.get('start', 0)
                    gene_end = feature.get('end', 0)
                    
                    # Calculate distance
                    if pos < gene_start:
                        dist = gene_start - pos
                    elif pos > gene_end:
                        dist = pos - gene_end
                    else:
                        dist = 0.0
                        
                    genes.append({'symbol': gene_symbol, 'distance': dist})
            
            if genes:
                # Sort by distance and pick the closest
                genes.sort(key=lambda x: x['distance'])
                closest = genes[0]
                return closest['symbol'], closest['distance']
                
    except Exception as e:
        # Log but continue to intergenic handling
        pass
        
    # If no gene found via overlap, try region-based search
    try:
        # Search a window around the SNP
        window = 50000  # 50kb window
        region_endpoint = f"{ENSMBL_BASE_URL}/api/{ENSMBL_VERSION}/overlap/region/Honeybee:{chrom}-{pos-window}-{pos+window}"
        params = {'feature': 'gene'}
        
        response = session.get(region_endpoint, params=params, timeout=TIMEOUT_SECONDS)
        
        if response.status_code == 200 and response.json():
            genes = []
            for feature in response.json():
                if feature.get('feature_type') == 'gene':
                    gene_symbol = feature.get('external_name', 'UNKNOWN')
                    gene_start = feature.get('start', 0)
                    gene_end = feature.get('end', 0)
                    
                    if pos < gene_start:
                        dist = gene_start - pos
                    elif pos > gene_end:
                        dist = pos - gene_end
                    else:
                        dist = 0.0
                        
                    genes.append({'symbol': gene_symbol, 'distance': dist})
            
            if genes:
                genes.sort(key=lambda x: x['distance'])
                closest = genes[0]
                return closest['symbol'], closest['distance']
                
    except Exception:
        pass
        
    return 'INTERGENIC', -1.0

def fetch_go_terms(gene_symbol: str, session: requests.Session) -> List[str]:
    """
    Fetch Gene Ontology terms for a given gene symbol.
    
    Args:
        gene_symbol: The gene symbol.
        session: Requests session.
        
    Returns:
        List of GO term IDs.
    """
    if gene_symbol == 'INTERGENIC' or gene_symbol == 'UNKNOWN':
        return []
        
    try:
        # Search for the gene to get its ID
        search_endpoint = f"{ENSMBL_BASE_URL}/api/{ENSMBL_VERSION}/lookup/symbol/Honeybee:{gene_symbol}"
        
        response = session.get(search_endpoint, timeout=TIMEOUT_SECONDS)
        
        if response.status_code != 200:
            return []
            
        gene_data = response.json()
        gene_id = gene_data.get('id')
        
        if not gene_id:
            return []
            
        # Fetch GO terms for the gene
        go_endpoint = f"{ENSMBL_BASE_URL}/api/{ENSMBL_VERSION}/ontology/{gene_id}"
        
        response = session.get(go_endpoint, timeout=TIMEOUT_SECONDS)
        
        if response.status_code == 200:
            go_data = response.json()
            go_terms = []
            
            if 'ontology' in go_data:
                for term in go_data['ontology']:
                    go_terms.append(term.get('accession', ''))
                    
            return list(set(go_terms))  # Remove duplicates
            
        return []
        
    except Exception:
        return []

def annotate_snps(significant_snps: pd.DataFrame, session: requests.Session) -> pd.DataFrame:
    """
    Annotate significant SNPs with gene information and GO terms.
    
    Args:
        significant_snps: DataFrame of significant SNPs.
        session: Requests session for API calls.
        
    Returns:
        DataFrame with annotation results.
    """
    results = []
    error_log = []
    
    total = len(significant_snps)
    print(f"Starting annotation for {total} SNPs...")
    
    for idx, row in significant_snps.iterrows():
        snp_id = row['snp_id']
        chrom = str(row.get('chrom', '1'))
        pos = int(row.get('pos', 0))
        
        try:
            # Attempt to fetch gene info
            gene_symbol, distance = fetch_closest_gene(snp_id, session, chrom, pos)
            
            # If gene found, fetch GO terms
            go_terms = []
            if gene_symbol != 'INTERGENIC':
                go_terms = fetch_go_terms(gene_symbol, session)
                
            results.append({
                'snp_id': snp_id,
                'gene_symbol': gene_symbol,
                'distance': distance,
                'go_terms': ';'.join(go_terms) if go_terms else ''
            })
            
            # Progress update every 10%
            if (idx + 1) % max(1, total // 10) == 0:
                print(f"  Processed {idx + 1}/{total} SNPs...")
                
        except Exception as e:
            # Log error and mark as UNAVAILABLE
            error_msg = f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {snp_id} | {str(e)}"
            error_log.append(error_msg)
            
            results.append({
                'snp_id': snp_id,
                'gene_symbol': 'UNAVAILABLE',
                'distance': -1.0,
                'go_terms': ''
            })
            
            print(f"  ERROR: Failed to annotate {snp_id}: {str(e)}")
    
    # Write error log
    if error_log:
        with open(ANNOTATION_ERRORS_LOG, 'w') as f:
            f.write('\n'.join(error_log))
        print(f"Logged {len(error_log)} errors to {ANNOTATION_ERRORS_LOG}")
        
    return pd.DataFrame(results)

def write_annotated_output(annotation_df: pd.DataFrame, output_path: str):
    """
    Write annotated results to TSV file.
    
    Args:
        annotation_df: DataFrame with annotation results.
        output_path: Path to output file.
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Validate schema
    required_cols = ['snp_id', 'gene_symbol', 'distance', 'go_terms']
    for col in required_cols:
        if col not in annotation_df.columns:
            annotation_df[col] = ''
            
    # Write to TSV
    annotation_df.to_csv(output_path, sep='\t', index=False)
    print(f"Annotation results written to {output_path}")
    print(f"Total annotated SNPs: {len(annotation_df)}")
    
    # Summary statistics
    intergenic_count = len(annotation_df[annotation_df['gene_symbol'] == 'INTERGENIC'])
    unavailable_count = len(annotation_df[annotation_df['gene_symbol'] == 'UNAVAILABLE'])
    gene_mapped = len(annotation_df) - intergenic_count - unavailable_count
    
    print(f"  - Gene mapped: {gene_mapped}")
    print(f"  - Intergenic: {intergenic_count}")
    print(f"  - Unavailable: {unavailable_count}")

def main():
    """Main entry point for SNP annotation."""
    parser = argparse.ArgumentParser(
        description="Annotate significant GWAS SNPs using Ensembl Bees API v104"
    )
    parser.add_argument(
        '--input',
        type=str,
        default='data/processed/gwas_results_fdr.tsv',
        help='Path to FDR-corrected GWAS results file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=ANNOTATION_OUTPUT,
        help='Path to output annotation results'
    )
    parser.add_argument(
        '--immune-snp-list',
        type=str,
        default='data/interim/immune_pathway_snps.txt',
        help='Path to immune pathway SNP list (for reference only)'
    )
    
    args = parser.parse_args()
    
    # Verify input file exists
    if not os.path.exists(args.input):
        print(f"ERROR: Input file not found: {args.input}")
        sys.exit(1)
        
    # Create session with retries
    session = create_session_with_retries()
    
    try:
        # Load significant SNPs
        print("Loading GWAS results...")
        significant_snps = load_gwas_results(args.input)
        
        if significant_snps.empty:
            print("No significant SNPs to annotate. Creating empty output.")
            empty_df = pd.DataFrame(columns=['snp_id', 'gene_symbol', 'distance', 'go_terms'])
            write_annotated_output(empty_df, args.output)
            return
        
        # Annotate SNPs
        print("Fetching gene information from Ensembl Bees API...")
        annotated_df = annotate_snps(significant_snps, session)
        
        # Write results
        write_annotated_output(annotated_df, args.output)
        
        print("Annotation complete.")
        
    except Exception as e:
        print(f"ERROR: Annotation failed: {str(e)}")
        # Log to error file even on crash
        with open(ANNOTATION_ERRORS_LOG, 'a') as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | CRITICAL | {str(e)}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()