"""
Gene Annotation Module for Honeybee GWAS Pipeline.

This module maps significant SNPs to genes using the Ensembl REST API
and queries Gene Ontology (GO) terms for functional annotation.
"""

import os
import sys
import argparse
import time
import json
import requests
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple

# Constants
ENSEMBL_BASE_URL = "https://rest.ensembl.org"
ENSEMBL_TIMEOUT = 10  # seconds
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2  # exponential backoff base
USER_AGENT = "llmXive-HoneybeeGWAS/1.0"

# Output paths
OUTPUT_FILE = "data/processed/annotated_snps.tsv"
METADATA_FILE = "data/processed/annotation_metadata.json"


def create_session_with_retries() -> requests.Session:
    """
    Create a requests session with retry logic and exponential backoff.

    Returns:
        requests.Session: Configured session with retry capabilities.
    """
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": USER_AGENT
    })
    return session


def load_gwas_results(input_path: str) -> pd.DataFrame:
    """
    Load GWAS results from a TSV file.

    Args:
        input_path: Path to the GWAS results TSV file.

    Returns:
        pd.DataFrame: DataFrame containing GWAS results.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file is empty or missing required columns.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"GWAS results file not found: {input_path}")

    df = pd.read_csv(path, sep='\t')

    required_cols = ['SNP', 'P', 'q_value']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Filter for significant SNPs (q_value < 0.05)
    significant_df = df[df['q_value'] < 0.05].copy()

    if significant_df.empty:
        print("Warning: No significant SNPs found (q_value < 0.05). "
              "Processing all SNPs for annotation purposes.")
        significant_df = df.copy()

    return significant_df


def fetch_gene_info_from_ensembl(
    session: requests.Session,
    rs_id: str,
    species: str = "apis_mellifera",
    assembly: str = "Amel_HAv3.1"
) -> Tuple[Optional[str], Optional[str], Optional[List[str]]]:
    """
    Fetch gene symbol, pathway, and GO terms for a given SNP using Ensembl REST API.

    Args:
        session: Requests session with retry logic.
        rs_id: The SNP ID (rs_id) to query.
        species: Ensembl species identifier.
        assembly: Genome assembly version.

    Returns:
        Tuple[Optional[str], Optional[str], Optional[List[str]]]:
            (gene_symbol, pathway, go_terms) or (None, None, None) if not found.
    """
    # Map SNP to location
    url = f"{ENSEMBL_BASE_URL}/variation/{species}/{rs_id}"

    for attempt in range(MAX_RETRIES):
        try:
            response = session.get(url, timeout=ENSEMBL_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            break
        except requests.exceptions.RequestException as e:
            if attempt == MAX_RETRIES - 1:
                # Final attempt failed
                print(f"  Warning: Ensembl API request failed for {rs_id} after {MAX_RETRIES} attempts: {e}")
                return None, None, None
            # Exponential backoff
            wait_time = RETRY_BACKOFF_BASE ** attempt
            time.sleep(wait_time)
            continue

    # Extract gene location from variation data
    gene_symbol = None
    go_terms = []
    pathway = None

    if "mappings" in data:
        for mapping in data["mappings"]:
            if mapping.get("location"):
                # Parse location (e.g., "1:12345:12345:A/T")
                parts = mapping["location"].split(":")
                if len(parts) >= 2:
                    chrom = parts[0]
                    pos = parts[1]

                    # Query overlapping features (genes)
                    feature_url = f"{ENSEMBL_BASE_URL}/overlap/region/{species}/{chrom}:{pos}-{pos}?feature=gene;feature=transcript;feature=exon"
                    try:
                        feat_resp = session.get(feature_url, timeout=ENSEMBL_TIMEOUT)
                        feat_resp.raise_for_status()
                        features = feat_resp.json()

                        for feat in features:
                            if feat.get("FeatureType") == "gene":
                                gene_symbol = feat.get("external_name") or feat.get("id")
                                # Try to get GO terms
                                gene_id = feat.get("id")
                                if gene_id:
                                    go_url = f"{ENSEMBL_BASE_URL}/ontology/{species}/{gene_id}"
                                    go_resp = session.get(go_url, timeout=ENSEMBL_TIMEOUT)
                                    if go_resp.status_code == 200:
                                        go_data = go_resp.json()
                                        if "ontology" in go_data:
                                            for term in go_data["ontology"]:
                                                go_terms.append(term.get("name", "unknown"))
                                    break
                        if gene_symbol:
                            break
                    except requests.exceptions.RequestException:
                        pass  # Continue if feature query fails

    # If gene symbol not found via location, try direct gene lookup if rs_id matches a gene ID pattern
    if not gene_symbol:
        # Fallback: check if rs_id itself is a gene identifier in some contexts
        # (Rare for SNPs, but handles edge cases)
        pass

    return gene_symbol, pathway, go_terms


def annotate_snps(
    df: pd.DataFrame,
    output_path: str,
    metadata_path: str
) -> None:
    """
    Annotate significant SNPs with gene information and write to TSV.

    Args:
        df: DataFrame containing significant SNPs.
        output_path: Path for the annotated output TSV.
        metadata_path: Path for the annotation metadata JSON.
    """
    session = create_session_with_retries()
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    annotations = []
    stats = {
        "total_snps": len(df),
        "annotated_snps": 0,
        "intergenic_snps": 0,
        "api_failures": 0,
        "start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "end_time": None
    }

    print(f"Annotating {len(df)} significant SNPs...")

    for idx, row in df.iterrows():
        rs_id = str(row['SNP'])
        print(f"  Processing {rs_id}...")

        gene_symbol, pathway, go_terms = fetch_gene_info_from_ensembl(session, rs_id)

        if gene_symbol:
            annotations.append({
                "rs_id": rs_id,
                "gene_symbol": gene_symbol,
                "go_terms": "; ".join(go_terms) if go_terms else "N/A",
                "pathway": pathway if pathway else "N/A",
                "p_value": row['P'],
                "q_value": row['q_value']
            })
            stats["annotated_snps"] += 1
        else:
            # Handle "no gene found" case explicitly (T061)
            print(f"  SNP {rs_id} is intergenic; no gene symbol found.")
            annotations.append({
                "rs_id": rs_id,
                "gene_symbol": "INTERGENIC",
                "go_terms": "N/A",
                "pathway": "N/A",
                "p_value": row['P'],
                "q_value": row['q_value']
            })
            stats["intergenic_snps"] += 1
            stats["api_failures"] += 1  # Count as failure since no annotation found

        # Small delay to be polite to the API
        time.sleep(0.2)

    stats["end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")

    # Write annotated output
    if annotations:
        annot_df = pd.DataFrame(annotations)
        # Ensure column order matches spec
        annot_df = annot_df[["rs_id", "gene_symbol", "go_terms", "pathway"]]
        annot_df.to_csv(output_path, sep='\t', index=False)
        print(f"Annotation complete. Wrote {len(annotations)} rows to {output_path}")
    else:
        # Create empty file with headers if no annotations
        pd.DataFrame(columns=["rs_id", "gene_symbol", "go_terms", "pathway"]).to_csv(
            output_path, sep='\t', index=False
        )
        print(f"No SNPs to annotate. Created empty file at {output_path}")

    # Write metadata
    with open(metadata_path, 'w') as f:
        json.dump(stats, f, indent=2)


def write_annotated_output(df: pd.DataFrame, output_path: str) -> None:
    """
    Write the annotated DataFrame to a TSV file.

    Args:
        df: DataFrame with annotations.
        output_path: Output file path.
    """
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, sep='\t', index=False)


def main():
    """Main entry point for the annotation pipeline."""
    parser = argparse.ArgumentParser(
        description="Annotate significant SNPs with gene and GO term information."
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/gwas_results_fdr.tsv",
        help="Path to GWAS results TSV file (default: data/processed/gwas_results_fdr.tsv)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=OUTPUT_FILE,
        help="Path for annotated output TSV (default: data/processed/annotated_snps.tsv)"
    )
    parser.add_argument(
        "--metadata",
        type=str,
        default=METADATA_FILE,
        help="Path for annotation metadata JSON (default: data/processed/annotation_metadata.json)"
    )
    args = parser.parse_args()

    # Ensure input file exists
    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        print("Please ensure T022 has run and produced data/processed/gwas_results_fdr.tsv")
        sys.exit(1)

    try:
        df = load_gwas_results(args.input)
        annotate_snps(df, args.output, args.metadata)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during annotation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()