"""
SNP Annotation Module for Honeybee CCD GWAS.

This module maps significant SNPs to genes and retrieves Gene Ontology (GO) terms
using the Ensembl REST API. It implements retry logic with exponential backoff
and graceful degradation if the API is unavailable.

FR-008: Map significant SNPs to genes using Ensembl Bees API and query GO terms.
"""
import os
import sys
import argparse
import time
import json
import requests
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, List, Tuple

# Constants
ENSMBL_BASE_URL = "https://rest.ensembl.org"
MAX_RETRIES = 3
BACKOFF_BASE = 1.0  # Seconds (1s, 2s, 4s)
TIMEOUT = 10  # Seconds per request

# Output path constant
DEFAULT_OUTPUT_PATH = "data/processed/annotated_snps.tsv"


def create_session_with_retries() -> requests.Session:
    """
    Create a requests session with retry logic configuration.
    Implements exponential backoff: 1s, 2s, 4s.
    """
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(
        max_retries=requests.packages.urllib3.util.retry.Retry(
            total=MAX_RETRIES,
            backoff_factor=1.0,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def load_gwas_results(gwas_path: str) -> pd.DataFrame:
    """
    Load GWAS results and filter for significant SNPs (q_value < 0.05).

    Args:
        gwas_path: Path to the FDR-corrected GWAS results TSV.

    Returns:
        DataFrame containing only significant SNPs.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If required columns are missing.
    """
    if not os.path.exists(gwas_path):
        raise FileNotFoundError(f"GWAS results file not found: {gwas_path}")

    df = pd.read_csv(gwas_path, sep='\t')

    required_cols = ['SNP', 'q_value']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in GWAS results: {missing}")

    # Filter for significant SNPs (q_value < 0.05)
    significant_df = df[df['q_value'] < 0.05].copy()

    # If no significant SNPs, return empty dataframe
    if significant_df.empty:
        print("No significant SNPs found (q_value < 0.05). Returning empty annotation.")
        return significant_df

    return significant_df


def fetch_gene_info_from_ensembl(
    session: requests.Session,
    snp_id: str,
    species: str = "apis_mellifera"
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Fetch gene symbol, GO terms, and pathway information for a SNP from Ensembl.

    Args:
        session: Requests session with retry logic.
        snp_id: The SNP ID (e.g., rsID or chromosome_position).
        species: Ensembl species name (default: apis_mellifera).

    Returns:
        Tuple of (gene_symbol, go_terms_str, pathway_str).
        Returns ("UNAVAILABLE", "UNAVAILABLE", "UNAVAILABLE") if fetch fails.
    """
    # Step 1: Map SNP to location (variation endpoint)
    # Note: Ensembl variation API for bees might use specific IDs.
    # We attempt to query by ID first. If that fails, we might need to map by position.
    # For this implementation, we assume the SNP ID is queryable or we try a generic lookup.

    url = f"{ENSMBL_BASE_URL}/variation/{species}/{snp_id}"
    headers = {"Content-Type": "application/json"}

    gene_symbol = None
    go_terms = []
    pathway = []

    try:
        response = session.get(url, headers=headers, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()

        if "mapped" in data and data["mapped"]:
            # Extract location
            location = data["mapped"][0].get("location", "")
            # location format: "Chromosome:Start-End:Strand"
            # We need to extract the region to query the region endpoint
            if location:
                parts = location.split(":")
                if len(parts) >= 2:
                    chr_name = parts[0]
                    coords = parts[1].split("-")
                    if len(coords) >= 2:
                        start = int(coords[0])
                        end = int(coords[1])

                        # Step 2: Query region endpoint for features (genes)
                        region_url = f"{ENSMBL_BASE_URL}/overlap/region/{species}/{chr_name}:{start}-{end}"
                        region_params = {
                            "feature": "gene",
                            "feature": "transcript",
                            "feature": "regulatory_feature",
                            "content_type": "application/json"
                        }
                        region_resp = session.get(region_url, headers=headers, params=region_params, timeout=TIMEOUT)
                        region_resp.raise_for_status()
                        region_data = region_resp.json()

                        for feature in region_data:
                            if feature.get("feature_type") == "gene":
                                gene_symbol = feature.get("external_name") or feature.get("gene_name")
                                # Try to get GO terms via the gene ID
                                gene_id = feature.get("id")
                                if gene_id:
                                    # Query gene ontology
                                    go_url = f"{ENSMBL_BASE_URL}/ontology/{species}/gene/{gene_id}"
                                    go_resp = session.get(go_url, headers=headers, timeout=TIMEOUT)
                                    if go_resp.status_code == 200:
                                        go_data = go_resp.json()
                                        if "ontology" in go_data:
                                            go_terms = [
                                                f"{term.get('term')}"
                                                for term in go_data["ontology"]
                                                if term.get('evidence_code')
                                            ]

                                # Try to get pathway (Reactome/KEGG via external references if available)
                                # Ensembl REST doesn't always have direct pathway links for non-model organisms
                                # We'll check external_refs if available
                                if "external_ref" in feature:
                                    pathway = [ref.get("source", "") + ":" + str(ref.get("id", ""))
                                               for ref in feature.get("external_ref", [])]

                        if not gene_symbol:
                            # Fallback: if we found a region but no specific gene name
                            gene_symbol = f"Region_{chr_name}_{start}"

        if not gene_symbol:
            # If all else fails, mark as unavailable but don't crash
            gene_symbol = "UNAVAILABLE"
            go_terms = ["UNAVAILABLE"]
            pathway = ["UNAVAILABLE"]

    except requests.exceptions.RequestException as e:
        print(f"  Warning: API request failed for {snp_id}: {e}")
        return "UNAVAILABLE", "UNAVAILABLE", "UNAVAILABLE"
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"  Warning: Malformed response for {snp_id}: {e}")
        return "UNAVAILABLE", "UNAVAILABLE", "UNAVAILABLE"

    # Format lists to strings
    go_terms_str = "; ".join(go_terms) if go_terms else "UNAVAILABLE"
    pathway_str = "; ".join(pathway) if pathway else "UNAVAILABLE"

    return gene_symbol, go_terms_str, pathway_str


def annotate_snps(
    significant_df: pd.DataFrame,
    session: requests.Session
) -> pd.DataFrame:
    """
    Annotate a list of SNPs with gene and GO information.

    Args:
        significant_df: DataFrame of significant SNPs.
        session: Requests session.

    Returns:
        DataFrame with added annotation columns.
    """
    annotations = []

    print(f"Annotating {len(significant_df)} significant SNPs...")

    for idx, row in significant_df.iterrows():
        snp_id = str(row['SNP'])
        print(f"  Processing {snp_id}...", end=" ", flush=True)

        gene_sym, go_str, path_str = fetch_gene_info_from_ensembl(session, snp_id)

        if gene_sym == "UNAVAILABLE":
            print("Skipped (API Unavailable)")
        else:
            print("Done")

        annotations.append({
            'rs_id': snp_id,
            'gene_symbol': gene_sym,
            'go_terms': go_str,
            'pathway': path_str
        })

    return pd.DataFrame(annotations)


def write_annotated_output(
    annotated_df: pd.DataFrame,
    output_path: str
) -> None:
    """
    Write the annotated SNP data to a TSV file.

    Args:
        annotated_df: DataFrame with annotation columns.
        output_path: Path to the output TSV file.
    """
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Ensure required columns exist
    required_cols = ['rs_id', 'gene_symbol', 'go_terms', 'pathway']
    for col in required_cols:
        if col not in annotated_df.columns:
            annotated_df[col] = "UNAVAILABLE"

    # Reorder columns
    output_df = annotated_df[required_cols]

    output_df.to_csv(output_path, sep='\t', index=False)
    print(f"Annotation complete. Output written to: {output_path}")


def main():
    """
    Main entry point for the annotation pipeline.
    """
    parser = argparse.ArgumentParser(
        description="Annotate significant GWAS SNPs using Ensembl API."
    )
    parser.add_argument(
        "--gwas",
        type=str,
        required=True,
        help="Path to the FDR-corrected GWAS results TSV (e.g., data/processed/gwas_results_fdr.tsv)."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=DEFAULT_OUTPUT_PATH,
        help=f"Path for the output annotated TSV file (default: {DEFAULT_OUTPUT_PATH})."
    )

    args = parser.parse_args()

    print("Starting SNP Annotation Pipeline...")
    print(f"Input: {args.gwas}")
    print(f"Output: {args.output}")

    # Create session with retry logic
    session = create_session_with_retries()

    try:
        # Load significant SNPs
        significant_snps = load_gwas_results(args.gwas)

        if significant_snps.empty:
            # Create an empty output file with headers if no significant SNPs
            empty_df = pd.DataFrame(columns=['rs_id', 'gene_symbol', 'go_terms', 'pathway'])
            write_annotated_output(empty_df, args.output)
            print("No significant SNPs to annotate. Empty output file created.")
            return

        # Annotate SNPs
        annotated_df = annotate_snps(significant_snps, session)

        # Write output
        write_annotated_output(annotated_df, args.output)

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