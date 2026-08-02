"""
Reproducibility analysis module.

Calculates Jaccard similarity between raw DE results and a published herbivory response gene list.
Strictly enforces real data usage; fails loudly if no published list is found in real mode.
"""
import os
import sys
import json
import logging
import requests
from pathlib import Path
from typing import Set, List, Dict, Optional, Tuple
from urllib.parse import urljoin

# Import from existing project utilities
from src.utils.config import get_data_path, get_seed

# Configure logging
logger = logging.getLogger(__name__)

# Constants
PUBLISHED_GENE_LIST_URL = "https://raw.githubusercontent.com/Plant-Response-Data/herbivory_genes/main/published_list.json"
LOCAL_BACKUP_PATH = "data/processed/published_gene_list_backup.json"

def load_de_results(de_results_path: Path) -> Set[str]:
    """
    Load DE results from a CSV file and return the set of gene IDs.

    Args:
        de_results_path: Path to the DE results CSV file.

    Returns:
        Set of gene IDs from the DE results.

    Raises:
        FileNotFoundError: If the DE results file does not exist.
        ValueError: If the file is empty or malformed.
    """
    import pandas as pd

    if not de_results_path.exists():
        raise FileNotFoundError(f"DE results file not found: {de_results_path}")

    try:
        df = pd.read_csv(de_results_path)
        # Expecting a column named 'gene_id' or 'gene'
        gene_col = None
        for col in ['gene_id', 'gene', 'GeneID', 'Gene']:
            if col in df.columns:
                gene_col = col
                break

        if gene_col is None:
            raise ValueError(f"DE results file must contain a 'gene_id' or 'gene' column. Found columns: {df.columns.tolist()}")

        genes = set(df[gene_col].dropna().astype(str).unique())
        if not genes:
            raise ValueError("DE results file contains no gene IDs.")

        logger.info(f"Loaded {len(genes)} genes from {de_results_path}")
        return genes
    except Exception as e:
        logger.error(f"Failed to load DE results: {e}")
        raise

def fetch_published_gene_list(url: str, timeout: int = 30) -> Set[str]:
    """
    Fetch a published gene list from a public URL.

    Args:
        url: The URL to fetch the gene list from.
        timeout: Request timeout in seconds.

    Returns:
        Set of gene IDs from the published list.

    Raises:
        RuntimeError: If the fetch fails or the response is invalid.
    """
    logger.info(f"Fetching published gene list from {url}")
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()

        data = response.json()
        if isinstance(data, list):
            genes = set(str(g).strip() for g in data if g)
        elif isinstance(data, dict) and 'genes' in data:
            genes = set(str(g).strip() for g in data['genes'] if g)
        elif isinstance(data, dict) and 'gene_list' in data:
            genes = set(str(g).strip() for g in data['gene_list'] if g)
        else:
            raise ValueError(f"Unexpected JSON structure: {type(data)}")

        if not genes:
            raise ValueError("Published gene list is empty.")

        logger.info(f"Successfully fetched {len(genes)} genes from {url}")
        return genes
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch published gene list: {e}")
        raise RuntimeError(f"Failed to fetch published gene list from {url}: {e}")
    except ValueError as e:
        logger.error(f"Invalid published gene list format: {e}")
        raise RuntimeError(f"Invalid published gene list format: {e}")

def load_local_backup(backup_path: Path) -> Optional[Set[str]]:
    """
    Load a locally cached backup of the published gene list.

    Args:
        backup_path: Path to the backup JSON file.

    Returns:
        Set of gene IDs if found, None otherwise.
    """
    if not backup_path.exists():
        return None

    try:
        with open(backup_path, 'r') as f:
            data = json.load(f)

        if isinstance(data, list):
            genes = set(str(g).strip() for g in data if g)
        elif isinstance(data, dict) and 'genes' in data:
            genes = set(str(g).strip() for g in data['genes'] if g)
        else:
            logger.warning(f"Invalid backup format at {backup_path}")
            return None

        logger.info(f"Loaded {len(genes)} genes from local backup")
        return genes
    except Exception as e:
        logger.warning(f"Failed to load local backup: {e}")
        return None

def calculate_jaccard_similarity(set_a: Set[str], set_b: Set[str]) -> float:
    """
    Calculate the Jaccard similarity coefficient between two sets.

    Jaccard = |A ∩ B| / |A ∪ B|

    Args:
        set_a: First set of gene IDs.
        set_b: Second set of gene IDs.

    Returns:
        Jaccard similarity score between 0.0 and 1.0.
    """
    if not set_a or not set_b:
        return 0.0

    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))

    if union == 0:
        return 0.0

    return intersection / union

def main(mode: str = "real", de_results_path: Optional[str] = None) -> None:
    """
    Main entry point for reproducibility analysis.

    Args:
        mode: 'real' or 'synthetic'. In 'real' mode, fails if no published list is found.
        de_results_path: Optional path to DE results. If not provided, uses default path.
    """
    data_path = get_data_path()
    manifests_path = data_path / "manifests"
    processed_path = data_path / "processed"

    # Ensure output directory exists
    manifests_path.mkdir(parents=True, exist_ok=True)

    # Determine DE results path
    if de_results_path is None:
        # Default path based on project structure
        de_results_path = processed_path / "de_results.csv"
    else:
        de_results_path = Path(de_results_path)

    output_report_path = manifests_path / "reproducibility_report.json"

    logger.info(f"Starting reproducibility analysis in '{mode}' mode")
    logger.info(f"DE results path: {de_results_path}")
    logger.info(f"Output report path: {output_report_path}")

    # Load DE results
    try:
        de_genes = load_de_results(de_results_path)
    except Exception as e:
        logger.error(f"Failed to load DE results: {e}")
        # Write a failure report
        report = {
            "jaccard_similarity": None,
            "source_url": None,
            "used_fallback": False,
            "error": str(e),
            "mode": mode
        }
        with open(output_report_path, 'w') as f:
            json.dump(report, f, indent=2)
        raise

    published_genes = None
    source_url = None
    used_fallback = False

    if mode == "real":
        # Try to fetch from primary source
        try:
            published_genes = fetch_published_gene_list(PUBLISHED_GENE_LIST_URL)
            source_url = PUBLISHED_GENE_LIST_URL
        except RuntimeError as e:
            logger.warning(f"Primary source failed: {e}")
            # Try local backup
            backup_path = processed_path / "published_gene_list_backup.json"
            published_genes = load_local_backup(backup_path)

            if published_genes is None:
                logger.error("No published gene list found in primary source or local backup.")
                # Write failure report and raise
                report = {
                    "jaccard_similarity": None,
                    "source_url": None,
                    "used_fallback": False,
                    "error": "No published gene list found in real mode",
                    "mode": "real"
                }
                with open(output_report_path, 'w') as f:
                    json.dump(report, f, indent=2)
                raise RuntimeError("No published gene list found in real mode. Cannot proceed with reproducibility analysis.")
            else:
                source_url = "local_backup"
                used_fallback = True
                logger.info("Using local backup for published gene list")
    else:
        # Synthetic mode: Use a predefined small list for structural validation only
        # This is NOT a real measurement, just for pipeline structure validation
        logger.warning("Running in synthetic mode. Using a small predefined list for structural validation only.")
        published_genes = {"AT1G01010", "AT1G01020", "AT1G01030", "AT1G01040", "AT1G01050"}
        source_url = "synthetic_predefined"
        used_fallback = True

    # Calculate Jaccard similarity
    jaccard_score = calculate_jaccard_similarity(de_genes, published_genes)

    logger.info(f"Jaccard similarity: {jaccard_score:.4f}")
    logger.info(f"DE genes: {len(de_genes)}, Published genes: {len(published_genes)}")
    logger.info(f"Intersection: {len(de_genes.intersection(published_genes))}, Union: {len(de_genes.union(published_genes))}")

    # Prepare report
    report = {
        "jaccard_similarity": jaccard_score,
        "source_url": source_url,
        "used_fallback": used_fallback,
        "de_gene_count": len(de_genes),
        "published_gene_count": len(published_genes),
        "intersection_count": len(de_genes.intersection(published_genes)),
        "union_count": len(de_genes.union(published_genes)),
        "mode": mode
    }

    # Write report
    with open(output_report_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Reproducibility report written to {output_report_path}")

    # Gate: If using fallback in real mode, halt with a warning
    if mode == "real" and used_fallback:
        logger.warning("Reproducibility analysis used a fallback source. Results may be less reliable.")
        # Do not raise, but log the warning. The task specification says "halt" if fallback is true in real mode,
        # but since we successfully computed a score, we just warn. If the task strictly requires halting,
        # we would raise SystemExit here. Based on the spec: "Gate: If used_fallback is true and mode is real, halt."
        # We interpret "halt" as stopping further pipeline execution, which is handled by the caller.
        # We raise a warning that can be caught by the pipeline orchestrator.
        # For strict compliance, we raise SystemExit if fallback was used in real mode.
        # However, the spec also says "raise RuntimeError" if no list is found. Since we found a list (via backup),
        # we proceed but warn. The "halt" might refer to not continuing to model training if the score is poor,
        # but the task only asks to calculate and report. We'll log the warning and let the pipeline decide.
        # Re-reading: "Gate: If used_fallback is true and mode is real, halt." -> This likely means stop the pipeline.
        # We'll raise SystemExit to comply.
        logger.error("HALTING: Reproducibility analysis used a fallback source in real mode.")
        raise SystemExit("Reproducibility analysis used a fallback source in real mode. Pipeline halted.")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Calculate Jaccard similarity for reproducibility analysis.")
    parser.add_argument("--mode", choices=["real", "synthetic"], default="real", help="Data mode (real or synthetic)")
    parser.add_argument("--de_results", type=str, default=None, help="Path to DE results CSV file")

    args = parser.parse_args()

    main(mode=args.mode, de_results_path=args.de_results)