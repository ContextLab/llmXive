"""
Annotation Module for Honeybee CCD GWAS Pipeline.

Maps significant SNPs to genes using Ensembl Bees API and queries Gene Ontology (GO) terms.
Implements retry logic for API resilience.
"""
import os
import sys
import argparse
import time
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configuration
ENSEMBL_BASE_URL = "https://rest.ensembl.org"
MAX_RETRIES = 3
BACKOFF_FACTOR = 2.0
TIMEOUT_SECONDS = 30

def create_session_with_retries() -> requests.Session:
    """Create a requests session with automatic retry logic."""
    session = requests.Session()
    retry_strategy = Retry(
        total=MAX_RETRIES,
        backoff_factor=BACKOFF_FACTOR,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

def load_gwas_results(filepath: str) -> pd.DataFrame:
    """
    Load GWAS results and filter for significant SNPs.
    
    Args:
        filepath: Path to the FDR-corrected GWAS results TSV.
        
    Returns:
        DataFrame containing only SNPs with q_value < 0.05.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"GWAS results file not found: {filepath}")
    
    df = pd.read_csv(filepath, sep='\t')
    
    # Filter for significant SNPs (q < 0.05)
    significant_snps = df[df['q_value'] < 0.05].copy()
    
    if significant_snps.empty:
        print("Warning: No significant SNPs found (q < 0.05). Output will be empty.")
    
    return significant_snps

def fetch_gene_info_from_ensembl(
    session: requests.Session, 
    position: str, 
    species: str = "apis_mellifera"
) -> Dict[str, Any]:
    """
    Fetch gene information for a given genomic position from Ensembl.
    
    Args:
        session: Requests session with retry logic.
        position: Genomic position string (e.g., "1:12345:12345").
        species: Species ID for Ensembl (default: apis_mellifera).
        
    Returns:
        Dictionary containing gene symbol, GO terms, and pathway info.
    """
    # Extract chromosome, start, end from position string
    try:
        parts = position.split(':')
        if len(parts) != 3:
            # Try parsing "chr:start-end" format
            if '-' in parts[1]:
                start_end = parts[1].split('-')
                start = start_end[0]
                end = start_end[1]
                chr_id = parts[0]
            else:
                return {"gene_symbol": "Unknown", "go_terms": [], "pathway": []}
        else:
            chr_id = parts[0]
            start = parts[1]
            end = parts[1]
        
        # Construct Ensembl URL for region lookup
        url = f"{ENSEMBL_BASE_URL}/overlap/region/{species}/{chr_id}:{start}-{end}"
        params = {
            'feature': 'gene',
            'include_gene_symbol': '1',
            'include_go': '1',
        }
        headers = {
            'Content-Type': 'application/json',
            'X-Ensembl-Rest-Version': '10'
        }
        
        response = session.get(url, params=params, headers=headers, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()
        
        if not data:
            return {"gene_symbol": "Unknown", "go_terms": [], "pathway": []}
        
        # Parse response
        gene_symbol = "Unknown"
        go_terms = []
        pathways = []
        
        for item in data:
            if 'external_name' in item:
                gene_symbol = item['external_name']
            
            if 'go' in item:
                for go_entry in item['go']:
                    if 'term' in go_entry:
                        go_terms.append(go_entry['term'])
                    
                    if 'pathway' in go_entry:
                        pathways.append(go_entry['pathway'])
        
        return {
            "gene_symbol": gene_symbol,
            "go_terms": list(set(go_terms)),  # Deduplicate
            "pathway": list(set(pathways))
        }
        
    except (ValueError, KeyError, IndexError):
        return {"gene_symbol": "Unknown", "go_terms": [], "pathway": []}
    except requests.exceptions.RequestException as e:
        print(f"Error fetching gene info for {position}: {e}")
        return {"gene_symbol": "Error", "go_terms": [], "pathway": []}

def annotate_snps(
    session: requests.Session, 
    snp_df: pd.DataFrame, 
    position_col: str = 'POS'
) -> List[Dict[str, Any]]:
    """
    Annotate a list of SNPs with gene and GO information.
    
    Args:
        session: Requests session with retry logic.
        snp_df: DataFrame of significant SNPs.
        position_col: Column name containing genomic position.
        
    Returns:
        List of dictionaries containing annotation results.
    """
    annotations = []
    
    for idx, row in snp_df.iterrows():
        snp_id = row.get('SNP', f"SNP_{idx}")
        position = str(row.get(position_col, ''))
        
        # Skip if position is invalid
        if pd.isna(position) or position == '':
            annotations.append({
                'rs_id': snp_id,
                'gene_symbol': 'Unknown',
                'go_terms': [],
                'pathway': []
            })
            continue
        
        # Fetch gene info
        gene_info = fetch_gene_info_from_ensembl(session, position)
        
        # Format GO terms as semicolon-separated string
        go_str = ";".join(gene_info['go_terms']) if gene_info['go_terms'] else ""
        pathway_str = ";".join(gene_info['pathway']) if gene_info['pathway'] else ""
        
        annotations.append({
            'rs_id': snp_id,
            'gene_symbol': gene_info['gene_symbol'],
            'go_terms': go_str,
            'pathway': pathway_str
        })
        
        # Small delay to be respectful to the API
        time.sleep(0.2)
    
    return annotations

def write_annotated_output(
    annotations: List[Dict[str, Any]], 
    output_path: str
) -> None:
    """
    Write annotated SNPs to a TSV file.
    
    Args:
        annotations: List of annotation dictionaries.
        output_path: Path to output TSV file.
    """
    if not annotations:
        print("Warning: No annotations to write. Creating empty file.")
        df = pd.DataFrame(columns=['rs_id', 'gene_symbol', 'go_terms', 'pathway'])
    else:
        df = pd.DataFrame(annotations)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    df.to_csv(output_path, sep='\t', index=False)
    print(f"Successfully wrote {len(annotations)} annotations to {output_path}")

def main():
    """Main entry point for the annotation pipeline."""
    parser = argparse.ArgumentParser(
        description="Annotate significant SNPs with gene and GO information."
    )
    parser.add_argument(
        "--gwas",
        type=str,
        required=True,
        help="Path to FDR-corrected GWAS results TSV file."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/annotated_snps.tsv",
        help="Path to output annotated SNPS TSV file."
    )
    
    args = parser.parse_args()
    
    # Validate input file exists
    if not os.path.exists(args.gwas):
        print(f"Error: GWAS results file not found: {args.gwas}")
        sys.exit(1)
    
    try:
        # Create session with retry logic
        session = create_session_with_retries()
        
        # Load GWAS results
        print("Loading GWAS results...")
        gwas_df = load_gwas_results(args.gwas)
        
        if gwas_df.empty:
            print("No significant SNPs found. Writing empty output file.")
            write_annotated_output([], args.output)
            return
        
        print(f"Found {len(gwas_df)} significant SNPs to annotate.")
        
        # Annotate SNPs
        print("Fetching gene information from Ensembl...")
        annotations = annotate_snps(session, gwas_df)
        
        # Write output
        write_annotated_output(annotations, args.output)
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"Error: Failed to connect to Ensembl API after retries: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: Unexpected error during annotation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()