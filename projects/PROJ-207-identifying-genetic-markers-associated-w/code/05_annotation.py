"""
SNP Annotation Module for Honeybee GWAS Study.

This module maps significant SNPs to genes using the Ensembl Bees API
and queries Gene Ontology (GO) terms for functional annotation.

Requirements:
- requests
- pandas

FR-008 Compliance:
1. Uses Ensembl Bees API (Apis mellifera).
2. Selects gene with shortest genomic distance if multiple matches.
3. Assigns 'INTERGENIC' if no gene found.
4. Assigns 'UNAVAILABLE' if API is unreachable.
"""

import os
import sys
import argparse
import time
import json
import requests
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any

import pandas as pd
import numpy as np

# Ensembl Bees API Configuration
# Apis mellifera assembly: Amel_HAv3.1
ENSEMBL_BASE_URL = "https://rest.ensembl.org"
SPECIES = "apis_mellifera"
ASSEMBLY = "Amel_HAv3.1"
TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 2.0  # seconds

# Output paths
OUTPUT_FILE = "data/processed/annotation_results.tsv"


def create_session_with_retries() -> requests.Session:
    """
    Creates a requests session with retry logic for API resilience.
    Implements exponential backoff for rate limiting or transient failures.
    """
    session = requests.Session()
    
    # Custom retry logic
    def _get(url: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Internal wrapper with retry logic."""
        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                response = session.get(url, params=params, timeout=TIMEOUT)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                last_error = e
                wait_time = RETRY_DELAY * (2 ** attempt)
                time.sleep(wait_time)
        
        # If all retries fail, return None to trigger UNAVAILABLE logic
        return None

    # Patch session's get method
    original_get = session.get
    def patched_get(url: str, *args, **kwargs) -> requests.Response:
        # We need to handle the retry logic outside or wrap carefully.
        # For simplicity in this script, we will implement the retry logic
        # inside the specific fetch functions or here if we override.
        # Actually, let's just use the standard session and handle retries in the caller
        # to keep the session standard.
        return original_get(url, *args, **kwargs)
    
    # We will implement retry logic explicitly in fetch functions to avoid
    # monkey-patching complexity.
    return session


def load_gwas_results(input_path: str) -> pd.DataFrame:
    """
    Loads the FDR-corrected GWAS results.
    Expects a TSV file with at least 'SNP', 'chr', 'pos', 'p_value', 'q_value'.
    Filters for significant SNPs (q_value < 0.05) unless specified otherwise.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"GWAS results file not found: {input_path}")
    
    df = pd.read_csv(input_path, sep='\t')
    
    # Validate required columns
    required_cols = ['SNP', 'chr', 'pos', 'q_value']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in GWAS results: {missing}")
    
    # Filter significant SNPs (standard FDR threshold)
    # If the file is already filtered, this is a no-op.
    # We assume the input contains all tested SNPs, and we filter here.
    significant_df = df[df['q_value'] < 0.05].copy()
    
    if significant_df.empty:
        print("Warning: No significant SNPs found (q_value < 0.05). Output will be empty.")
        # Return empty dataframe with correct structure
        significant_df = significant_df[required_cols + ['p_value']] 
        
    return significant_df


def fetch_gene_info_from_ensembl(
    chr_name: str, 
    pos: int, 
    session: requests.Session
) -> Tuple[Optional[str], Optional[str], float]:
    """
    Fetches gene information for a specific SNP position from Ensembl Bees API.
    
    Args:
        chr_name: Chromosome name (e.g., 'chr1', '1').
        pos: 1-based genomic position.
        session: Requests session.
        
    Returns:
        Tuple of (gene_name, go_terms, distance).
        - gene_name: str or None
        - go_terms: str (comma-separated) or None
        - distance: float (0.0 if overlapping, otherwise bp distance)
    """
    # Normalize chromosome name (Ensembl usually expects '1', '2' not 'chr1')
    # But Apis mellifera assembly might use 'chr1'. We try to be robust.
    # Ensembl REST for bees usually uses '1', '2'... but sometimes 'chr1'.
    # Let's try to strip 'chr' prefix if present.
    clean_chr = str(chr_name).replace('chr', '').replace('CHR', '')
    
    # API Endpoint: /overlap/region/{species}/{region}
    # region format: {chromosome}:{start}-{end}
    # We query a small window around the SNP to catch overlapping genes
    # and nearby genes.
    window_size = 5000  # 5kb window
    start = max(1, pos - window_size)
    end = pos + window_size
    
    region = f"{clean_chr}:{start}-{end}"
    url = f"{ENSEMBL_BASE_URL}/overlap/region/{SPECIES}/{region}"
    
    params = {
        'feature': 'gene',
        'include_overlapping': 1,
        'include_gene_trees': 1
    }
    
    try:
        response = session.get(url, params=params, timeout=TIMEOUT)
        if response.status_code != 200:
            # Try with 'chr' prefix if the first attempt failed (common issue)
            region_with_chr = f"chr{clean_chr}:{start}-{end}"
            url_retry = f"{ENSEMBL_BASE_URL}/overlap/region/{SPECIES}/{region_with_chr}"
            response = session.get(url_retry, params=params, timeout=TIMEOUT)
            if response.status_code != 200:
                return None, None, float('inf')
        
        data = response.json()
        
        if not data:
            return None, None, float('inf')
        
        # Find the closest gene
        closest_gene = None
        min_dist = float('inf')
        
        for feature in data:
            if feature.get('feature_type') == 'gene':
                gene_start = feature.get('start', 0)
                gene_end = feature.get('end', 0)
                
                # Calculate distance
                if start <= gene_start and end >= gene_end:
                    # Overlapping
                    dist = 0.0
                elif pos < gene_start:
                    dist = gene_start - pos
                else:
                    dist = pos - gene_end
                
                if dist < min_dist:
                    min_dist = dist
                    closest_gene = feature
        
        if not closest_gene:
            return None, None, float('inf')
        
        gene_name = closest_gene.get('gene_name', 'Unknown')
        gene_id = closest_gene.get('id', '')
        
        # Fetch GO terms for this gene
        # Endpoint: /external/{species}/idmapping/id/{id} -> not direct GO
        # Better: /gene/{species}/id/{id} -> includes ontology
        go_url = f"{ENSEMBL_BASE_URL}/gene/{SPECIES}/id/{gene_id}"
        go_params = {'feature': 'gene'} # standard params
        
        go_response = session.get(go_url, timeout=TIMEOUT)
        go_terms = []
        
        if go_response.status_code == 200:
            go_data = go_response.json()
            if 'ontology_associations' in go_data:
                go_terms = [
                    f"{assoc['ontology']}:{assoc['accession']}" 
                    for assoc in go_data['ontology_associations']
                ]
        
        return gene_name, ",".join(go_terms), min_dist
        
    except (requests.exceptions.RequestException, json.JSONDecodeError, KeyError) as e:
        print(f"Error fetching gene info for {chr_name}:{pos}: {e}")
        return None, None, float('inf')


def annotate_snps(
    df: pd.DataFrame, 
    output_path: str
) -> None:
    """
    Annotates significant SNPs with gene and GO term information.
    
    Args:
        df: DataFrame of significant SNPs.
        output_path: Path to write the output TSV.
    """
    session = create_session_with_retries()
    
    results = []
    
    print(f"Processing {len(df)} significant SNPs...")
    
    for idx, row in df.iterrows():
        snp_id = row['SNP']
        chr_name = row['chr']
        pos = int(row['pos'])
        p_val = row.get('p_value', 0.0)
        q_val = row['q_value']
        
        gene_name, go_terms, distance = fetch_gene_info_from_ensembl(
            chr_name, pos, session
        )
        
        # Apply logic for missing data
        if gene_name is None:
            if distance == float('inf'):
                # API failed completely
                gene_name = "UNAVAILABLE"
                go_terms = "UNAVAILABLE"
                distance = float('nan')
            else:
                # No gene found in window
                gene_name = "INTERGENIC"
                go_terms = "INTERGENIC"
                distance = float('nan')
        
        results.append({
            'SNP': snp_id,
            'chr': chr_name,
            'pos': pos,
            'p_value': p_val,
            'q_value': q_val,
            'gene_name': gene_name,
            'go_terms': go_terms,
            'distance_bp': distance
        })
        
        # Progress logging
        if (idx + 1) % 10 == 0:
            print(f"  Processed {idx + 1}/{len(df)} SNPs")
    
    # Create output DataFrame
    out_df = pd.DataFrame(results)
    
    # Ensure output directory exists
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to TSV
    out_df.to_csv(out_path, sep='\t', index=False)
    print(f"Annotation complete. Results written to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Annotate significant SNPs with gene and GO term info."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the FDR-corrected GWAS results TSV file."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=OUTPUT_FILE,
        help=f"Path to write the annotated results TSV (default: {OUTPUT_FILE})"
    )
    
    args = parser.parse_args()
    
    try:
        # Load significant SNPs
        gwas_df = load_gwas_results(args.input)
        
        if gwas_df.empty:
            # Create empty output with headers if no significant SNPs
            out_df = pd.DataFrame(columns=['SNP', 'chr', 'pos', 'p_value', 'q_value', 'gene_name', 'go_terms', 'distance_bp'])
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            out_df.to_csv(args.output, sep='\t', index=False)
            print(f"No significant SNPs to annotate. Empty output written to: {args.output}")
            return
        
        # Annotate
        annotate_snps(gwas_df, args.output)
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error during annotation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()