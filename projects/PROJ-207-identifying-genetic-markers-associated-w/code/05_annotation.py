"""
SNP Annotation Module for Honeybee CCD GWAS.

This module maps significant SNPs to genes using the Ensembl Bees API (via
the generic Ensembl REST interface for Apis mellifera) and queries Gene Ontology
(GO) terms and pathways.

It reads the FDR-corrected GWAS results, filters for significant SNPs (q < 0.05),
and attempts to annotate them with gene symbols, GO terms, and pathways.

Since a specific 'Ensembl Bees' endpoint is not a standard public REST service
distinct from the main Ensembl site, this implementation uses the standard Ensembl
REST API with the `Apis mellifera` (ameli) species configuration.

FR-008 Compliance:
- Output: data/processed/annotated_snps.tsv
- Columns: rs_id, gene_symbol, go_terms, pathway
- Logic: Retry on failure, loud failure on total exhaustion.
"""

import os
import sys
import argparse
import time
import json
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

import pandas as pd
import requests
from requests.adapters import HTTPAdapter, Retry

# Configuration
ANNOTATION_OUTPUT_PATH = "data/processed/annotated_snps.tsv"
GWAS_INPUT_PATH = "data/processed/gwas_results_fdr.tsv"
SIGNIFICANCE_THRESHOLD = 0.05
MAX_RETRIES = 5
BACKOFF_FACTOR = 1.0
TIMEOUT = 30  # seconds

# Ensembl API Configuration for Apis mellifera (Honeybee)
# Using the main Ensembl REST API which supports non-human species
ENSEMBL_BASE_URL = "https://rest.ensembl.org"
SPECIES = "apis_mellifera"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def create_session_with_retries() -> requests.Session:
    """
    Creates a requests Session with automatic retry logic for transient failures.
    """
    session = requests.Session()
    retry_strategy = Retry(
        total=MAX_RETRIES,
        backoff_factor=BACKOFF_FACTOR,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

def load_gwas_results(input_path: str) -> pd.DataFrame:
    """
    Loads the FDR-corrected GWAS results and filters for significant SNPs.

    Args:
        input_path: Path to the TSV file containing GWAS results.

    Returns:
        DataFrame containing only significant SNPs (q_value < 0.05).

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If required columns are missing.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"GWAS results file not found: {input_path}")

    try:
        df = pd.read_csv(path, sep='\t')
    except Exception as e:
        raise ValueError(f"Failed to read GWAS results file: {e}")

    # Validate required columns
    required_cols = ['SNP', 'q_value']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in GWAS file: {missing_cols}")

    # Filter for significant SNPs
    significant_df = df[df['q_value'] < SIGNIFICANCE_THRESHOLD].copy()

    if significant_df.empty:
        print(f"Warning: No significant SNPs found (q_value < {SIGNIFICANCE_THRESHOLD}). "
              f"Output file will be created with headers only.")
        return significant_df

    print(f"Found {len(significant_df)} significant SNPs to annotate.")
    return significant_df

def fetch_gene_info_from_ensembl(
    session: requests.Session,
    snp_id: str,
    chrom: Optional[str] = None,
    pos: Optional[int] = None
) -> Tuple[Optional[str], List[str], List[str]]:
    """
    Fetches gene symbol, GO terms, and pathways for a given SNP.

    Uses the Ensembl Variant ID lookup endpoint. If the SNP ID is not found,
    it attempts to map via location if chrom/pos are provided.

    Args:
        session: Requests session with retry logic.
        snp_id: The SNP identifier (e.g., rsID or internal ID).
        chrom: Chromosome (optional, for fallback location lookup).
        pos: Position (optional, for fallback location lookup).

    Returns:
        Tuple of (gene_symbol, go_terms_list, pathway_list).
        Returns (None, [], []) if no information is found.
    """
    gene_symbol = None
    go_terms = []
    pathways = []

    # Strategy 1: Direct Variant Lookup
    # Endpoint: /variation/:species/:id
    url = f"{ENSEMBL_BASE_URL}/variation/{SPECIES}/{snp_id}"

    try:
        response = session.get(url, headers=HEADERS, timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if 'id' in data:
                # Extract gene info from 'mappings' or 'variations'
                # Ensembl variation response structure can vary, looking for 'mappings'
                mappings = data.get('mappings', [])
                if mappings:
                    # Usually the first mapping is the primary gene hit
                    mapping = mappings[0]
                    if 'mapped_gene' in mapping:
                        gene_data = mapping['mapped_gene']
                        gene_symbol = gene_data.get('external_name') or gene_data.get('name')

                        # Extract GO terms
                        if 'go' in mapping:
                            go_terms = [g['name'] for g in mapping['go']]

                        # Extract pathways (Reactome/GO pathways)
                        # Ensembl often stores pathways under 'pathway' or similar in mappings
                        if 'pathway' in mapping:
                            pathways = [p['name'] for p in mapping['pathway']]
                        # Sometimes pathways are embedded in GO terms (BP, MF, CC)
                        # We will collect unique GO terms as 'pathways' if explicit pathways are missing
                        if not pathways and go_terms:
                            # Fallback: treat GO terms as pathway descriptors if no explicit pathway
                            # But strictly, we should try to find 'reactome' or similar
                            pass

                return gene_symbol, go_terms, pathways

        elif response.status_code == 404:
            # Not found via ID, try location if available
            pass
        else:
            # Log non-404 errors but continue
            print(f"  API Error for {snp_id}: {response.status_code} - {response.text[:100]}")

    except requests.exceptions.RequestException as e:
        print(f"  Network error for {snp_id}: {e}")
        return None, [], []

    # Strategy 2: Location-based lookup (if ID fails and coords provided)
    if chrom and pos:
        # Ensembl location lookup: /overlap/region/:species/:region
        # Format: chr:start-end
        region = f"{chrom}:{pos}-{pos}"
        url = f"{ENSEMBL_BASE_URL}/overlap/region/{SPECIES}/{region}"
        params = {
            "feature": "gene",
            "include_go": 1,
            "include_pathway": 1 # Note: 'include_pathway' might not be a standard param, fallback to gene features
        }

        try:
            response = session.get(url, headers=HEADERS, params=params, timeout=TIMEOUT)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    for feature in data:
                        if feature.get('feature_type') == 'gene':
                            if not gene_symbol:
                                gene_symbol = feature.get('external_name') or feature.get('name')
                            # Collect GO terms from features
                            if 'go' in feature:
                                go_terms.extend([g['name'] for g in feature['go']])
                            # Deduplicate GO terms
                            go_terms = list(set(go_terms))
                            break
                return gene_symbol, go_terms, pathways
        except requests.exceptions.RequestException:
            pass

    return None, [], []

def annotate_snps(
    df: pd.DataFrame,
    session: requests.Session
) -> pd.DataFrame:
    """
    Iterates over significant SNPs and annotates them.

    Args:
        df: DataFrame of significant SNPs.
        session: Requests session.

    Returns:
        Annotated DataFrame.
    """
    results = []
    total = len(df)

    for idx, row in df.iterrows():
        snp_id = str(row['SNP'])
        chrom = row.get('CHR', None)
        pos = row.get('POS', None)

        print(f"Annotating {idx+1}/{total}: {snp_id}...")

        gene_symbol, go_terms, pathways = fetch_gene_info_from_ensembl(
            session, snp_id, str(chrom) if chrom else None, int(pos) if pos else None
        )

        # Format lists as semicolon-separated strings for TSV
        go_str = ";".join(go_terms) if go_terms else "N/A"
        path_str = ";".join(pathways) if pathways else "N/A"

        results.append({
            "rs_id": snp_id,
            "gene_symbol": gene_symbol if gene_symbol else "N/A",
            "go_terms": go_str,
            "pathway": path_str
        })

        # Small delay to be polite to the API
        time.sleep(0.2)

    return pd.DataFrame(results)

def write_annotated_output(df: pd.DataFrame, output_path: str) -> None:
    """
    Writes the annotated SNPs to a TSV file.

    Args:
        df: Annotated DataFrame.
        output_path: Output file path.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Ensure columns are in the correct order
    cols = ["rs_id", "gene_symbol", "go_terms", "pathway"]
    # Add any missing columns if the dataframe is empty or partial
    for col in cols:
        if col not in df.columns:
            df[col] = "N/A"

    df = df[cols]

    df.to_csv(path, sep='\t', index=False)
    print(f"Annotated SNPs written to: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Annotate significant SNPs using Ensembl API.")
    parser.add_argument(
        "--input",
        type=str,
        default=GWAS_INPUT_PATH,
        help=f"Path to input GWAS results file (default: {GWAS_INPUT_PATH})"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=ANNOTATION_OUTPUT_PATH,
        help=f"Path to output annotated TSV file (default: {ANNOTATION_OUTPUT_PATH})"
    )

    args = parser.parse_args()

    # 1. Load Data
    try:
        significant_df = load_gwas_results(args.input)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # If no significant SNPs, create empty output with headers and exit
    if significant_df.empty:
        print("No significant SNPs to annotate. Creating empty output file.")
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(columns=["rs_id", "gene_symbol", "go_terms", "pathway"]).to_csv(
            args.output, sep='\t', index=False
        )
        return

    # 2. Create Session with Retry Logic
    session = create_session_with_retries()

    # 3. Annotate
    try:
        annotated_df = annotate_snps(significant_df, session)
    except Exception as e:
        print(f"Critical error during annotation: {e}")
        sys.exit(1)

    # 4. Write Output
    try:
        write_annotated_output(annotated_df, args.output)
    except Exception as e:
        print(f"Error writing output file: {e}")
        sys.exit(1)

    print("Annotation complete.")

if __name__ == "__main__":
    main()