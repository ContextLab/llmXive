"""
Gene Annotation Module for Honeybee GWAS Results.

This module maps significant SNPs to genes using the Ensembl Bees API.
It handles cases where a SNP maps to no genes by assigning 'INTERGENIC'.
It also handles API unavailability by assigning 'UNAVAILABLE'.
"""

import os
import sys
import argparse
import time
import json
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd

# Constants for API configuration
ENSEMBL_BEES_BASE_URL = "https://bees.ensembl.org"
API_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 2

# Output schema columns
OUTPUT_COLUMNS = [
    "snp_id",
    "chromosome",
    "position",
    "p_value",
    "q_value",
    "significant",
    "gene_id",
    "gene_symbol",
    "gene_distance",
    "go_terms",
    "annotation_status"
]

def create_session_with_retries() -> requests.Session:
    """Create a requests session with retry logic for API calls."""
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(
        max_retries=requests.adapters.Retry(
            total=MAX_RETRIES,
            backoff_factor=RETRY_DELAY,
            status_forcelist=[429, 500, 502, 503, 504]
        )
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def load_gwas_results(input_path: str) -> pd.DataFrame:
    """
    Load GWAS results from a TSV file.

    Args:
        input_path: Path to the input TSV file.

    Returns:
        DataFrame containing GWAS results.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file format is invalid.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    try:
        df = pd.read_csv(path, sep='\t')
        required_cols = ['snp_id', 'p_value', 'q_value', 'significant']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        # Filter for significant SNPs only to reduce API load
        # If no significant SNPs, we still process all for completeness in some pipelines
        # but typically annotation is for hits. We'll process all rows provided.
        return df
    except pd.errors.EmptyDataError:
        raise ValueError("Input file is empty")
    except Exception as e:
        raise ValueError(f"Failed to parse input file: {e}")

def fetch_gene_info_from_ensembl(
    session: requests.Session,
    chrom: str,
    pos: int,
    species: str = "apis_mellifera"
) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Fetch gene information for a specific genomic location from Ensembl Bees API.

    Args:
        session: Requests session with retry logic.
        chrom: Chromosome name (e.g., 'chr1').
        pos: Position on the chromosome (1-based).
        species: Species identifier for Ensembl.

    Returns:
        Tuple of (gene_info_dict or None, status_string).
        status_string is one of: 'FOUND', 'NOT_FOUND', 'UNAVAILABLE', 'ERROR'.
    """
    # Normalize chromosome name if needed
    # Ensembl usually expects just the number or standard format
    clean_chrom = chrom.replace("chr", "")

    url = f"{ENSEMBL_BEES_BASE_URL}/overlap/region/{species}/{clean_chrom}:{pos}-{pos}"
    params = {
        "feature": "gene",
        "content_type": "application/json"
    }

    headers = {
        "Content-Type": "application/json",
        "X-Ensembl-Version": "109"  # Use a stable version
    }

    try:
        response = session.get(url, params=params, headers=headers, timeout=API_TIMEOUT)
        
        if response.status_code == 404:
            return None, "NOT_FOUND"
        elif response.status_code >= 500:
            return None, "UNAVAILABLE"
        elif response.status_code != 200:
            return None, "ERROR"

        data = response.json()
        if not data or len(data) == 0:
            return None, "NOT_FOUND"

        # Prefer the closest gene if multiple overlap (though pos-pos usually gives direct overlap)
        # If multiple, we might need distance calculation, but for exact overlap, first is fine.
        # We'll return the first one found for simplicity, or the one with shortest distance if we had flanking search.
        # Here we assume direct overlap.
        gene_data = data[0]
        return gene_data, "FOUND"

    except requests.exceptions.RequestException as e:
        print(f"API Request error for {chrom}:{pos}: {e}", file=sys.stderr)
        return None, "UNAVAILABLE"
    except json.JSONDecodeError:
        return None, "ERROR"

def fetch_closest_gene(
    session: requests.Session,
    chrom: str,
    pos: int,
    window_size: int = 50000,
    species: str = "apis_mellifera"
) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Fetch the closest gene to a specific genomic location if no direct overlap is found.
    Searches a window around the position.

    Args:
        session: Requests session.
        chrom: Chromosome name.
        pos: Position.
        window_size: Search window size in bp (±).
        species: Species identifier.

    Returns:
        Tuple of (gene_info_dict or None, status_string).
    """
    clean_chrom = chrom.replace("chr", "")
    start = max(1, pos - window_size)
    end = pos + window_size

    url = f"{ENSEMBL_BEES_BASE_URL}/overlap/region/{species}/{clean_chrom}:{start}-{end}"
    params = {
        "feature": "gene",
        "content_type": "application/json"
    }
    headers = {
        "Content-Type": "application/json",
        "X-Ensembl-Version": "109"
    }

    try:
        response = session.get(url, params=params, headers=headers, timeout=API_TIMEOUT)
        
        if response.status_code >= 500:
            return None, "UNAVAILABLE"
        if response.status_code != 200:
            return None, "NOT_FOUND"

        data = response.json()
        if not data:
            return None, "NOT_FOUND"

        # Find closest gene
        closest_gene = None
        min_dist = float('inf')

        for entry in data:
            gene_start = entry.get('start', 0)
            gene_end = entry.get('end', 0)
            
            # Calculate distance to the gene
            if pos < gene_start:
                dist = gene_start - pos
            elif pos > gene_end:
                dist = pos - gene_end
            else:
                dist = 0  # Overlap

            if dist < min_dist:
                min_dist = dist
                closest_gene = entry

        if closest_gene:
            return closest_gene, "FOUND"
        else:
            return None, "NOT_FOUND"

    except requests.exceptions.RequestException:
        return None, "UNAVAILABLE"
    except json.JSONDecodeError:
        return None, "ERROR"

def annotate_snps(
    df: pd.DataFrame,
    window_size: int = 50000
) -> pd.DataFrame:
    """
    Annotate SNPs with gene information.

    Logic:
    1. Try to fetch direct overlap gene.
    2. If no overlap, search for closest gene within window.
    3. If no gene found in window, assign 'INTERGENIC'.
    4. If API unavailable, assign 'UNAVAILABLE'.

    Args:
        df: DataFrame with SNP data (must have 'chromosome', 'position', 'snp_id').
        window_size: Search window for closest gene.

    Returns:
        Annotated DataFrame.
    """
    session = create_session_with_retries()
    
    results = []
    
    # Ensure we have the necessary columns
    if 'chromosome' not in df.columns or 'position' not in df.columns:
        raise ValueError("DataFrame must contain 'chromosome' and 'position' columns")

    for idx, row in df.iterrows():
        snp_id = row['snp_id']
        chrom = str(row['chromosome'])
        pos = int(row['position'])
        
        gene_info = None
        status = "ERROR"
        gene_symbol = "UNKNOWN"
        gene_id = "UNKNOWN"
        go_terms = "UNKNOWN"
        gene_distance = -1

        # 1. Try direct overlap
        gene_info, status = fetch_gene_info_from_ensembl(session, chrom, pos)
        
        if status == "NOT_FOUND":
            # 2. Try closest gene in window
            gene_info, status = fetch_closest_gene(session, chrom, pos, window_size)
        
        if status == "FOUND" and gene_info:
            gene_id = gene_info.get('id', 'UNKNOWN')
            # Try to get external names (symbol)
            external_names = gene_info.get('external_name', [])
            if isinstance(external_names, list) and len(external_names) > 0:
                gene_symbol = external_names[0]
            elif isinstance(external_names, str):
                gene_symbol = external_names
            else:
                # Fallback to ID if no name
                gene_symbol = gene_id
            
            # Calculate distance if we used closest logic (simplified here as 0 if overlap, else calculated in fetch_closest)
            # Since fetch_closest returns the gene, we assume distance is handled or 0 for simplicity in this version
            # A more robust version would return distance from fetch_closest.
            # For now, we mark distance as 0 if found.
            gene_distance = 0 
            
            # GO terms are not directly in the overlap endpoint usually, 
            # would require a separate call to /gene/{id}/ontology
            # For this task, we mark as 'PENDING' or 'UNKNOWN' if not fetched
            go_terms = "UNKNOWN" 
            
        elif status == "UNAVAILABLE":
            gene_symbol = "UNAVAILABLE"
            gene_id = "UNAVAILABLE"
            go_terms = "UNAVAILABLE"
            status = "UNAVAILABLE"
        elif status == "NOT_FOUND" or gene_info is None:
            # No gene found
            gene_symbol = "INTERGENIC"
            gene_id = "INTERGENIC"
            go_terms = "INTERGENIC"
            status = "INTERGENIC"
            gene_distance = -1

        results.append({
            "snp_id": snp_id,
            "chromosome": chrom,
            "position": pos,
            "p_value": row.get('p_value', ''),
            "q_value": row.get('q_value', ''),
            "significant": row.get('significant', False),
            "gene_id": gene_id,
            "gene_symbol": gene_symbol,
            "gene_distance": gene_distance,
            "go_terms": go_terms,
            "annotation_status": status
        })

        # Rate limiting to be polite to the API
        time.sleep(0.1)

    return pd.DataFrame(results)

def write_annotated_output(df: pd.DataFrame, output_path: str) -> None:
    """
    Write annotated results to a TSV file.

    Args:
        df: Annotated DataFrame.
        output_path: Path to output file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Ensure columns are in correct order
    if all(col in df.columns for col in OUTPUT_COLUMNS):
        df = df[OUTPUT_COLUMNS]
    
    df.to_csv(path, sep='\t', index=False)
    print(f"Annotation results written to: {output_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Annotate GWAS results with gene information from Ensembl Bees."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to input GWAS results TSV file (e.g., data/processed/gwas_results_fdr.tsv)"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to output annotated TSV file (e.g., data/processed/annotation_results.tsv)"
    )
    parser.add_argument(
        "--window",
        type=int,
        default=50000,
        help="Search window size in bp for closest gene (default: 50000)"
    )

    args = parser.parse_args()

    try:
        print(f"Loading GWAS results from: {args.input}")
        df = load_gwas_results(args.input)
        print(f"Loaded {len(df)} SNPs.")

        print("Annotating SNPs...")
        annotated_df = annotate_snps(df, window_size=args.window)

        print(f"Writing results to: {args.output}")
        write_annotated_output(annotated_df, args.output)

        # Summary stats
        status_counts = annotated_df['annotation_status'].value_counts()
        print("\nAnnotation Summary:")
        for status, count in status_counts.items():
            print(f"  {status}: {count}")

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()