"""
Reproducibility analysis module for T040.
Calculates Jaccard similarity between raw DE results and a published herbivory response gene list.
Implements fallback strategy: Primary URL -> Local Backup -> Synthetic (structural validation only).
"""
import os
import sys
import json
import logging
import requests
from pathlib import Path
from typing import List, Set, Dict, Any, Optional
from datetime import datetime

# Add project root to path for imports if running as script
if "code" in os.getcwd():
    sys.path.insert(0, os.path.abspath(os.path.join(os.getcwd(), "..")))
else:
    sys.path.insert(0, os.path.abspath(os.getcwd()))

from src.utils.logger import get_logger
from src.utils.schemas import DEGResult

logger = get_logger(__name__)

# Constants
PRIMARY_SOURCES = [
    "https://raw.githubusercontent.com/Plant-Defense-Project/herbivory-genes/main/gene_list.json",
    "https://raw.githubusercontent.com/Arabidopsis-Herbivory/consensus/main/list.json"
]
LOCAL_BACKUP_PATH = Path("data/processed/curated_gene_list.json")
OUTPUT_PATH = Path("data/processed/reproducibility_report.json")
SYNTHETIC_WARNING = "Synthetic gene list used for structural validation only"

def fetch_published_gene_list() -> Optional[Set[str]]:
    """
    Attempt to fetch the published herbivory response gene list from primary sources.
    Returns a set of gene IDs if successful, None otherwise.
    """
    for url in PRIMARY_SOURCES:
        try:
            logger.info(f"Attempting to fetch gene list from: {url}")
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                # Handle both list of strings and list of dicts with 'gene_id'
                if isinstance(data, list):
                    if isinstance(data[0], str):
                        return set(data)
                    elif isinstance(data[0], dict) and 'gene_id' in data[0]:
                        return {item['gene_id'] for item in data}
                logger.warning(f"Unexpected format from {url}, skipping.")
            else:
                logger.warning(f"Failed to fetch from {url}: HTTP {response.status_code}")
        except Exception as e:
            logger.warning(f"Error fetching from {url}: {e}")
    return None

def load_local_backup() -> Optional[Set[str]]:
    """
    Attempt to load the local curated backup file.
    """
    if LOCAL_BACKUP_PATH.exists():
        try:
            with open(LOCAL_BACKUP_PATH, 'r') as f:
                data = json.load(f)
            if isinstance(data, list):
                return set(data)
            elif isinstance(data, dict) and 'genes' in data:
                return set(data['genes'])
            logger.warning("Local backup found but invalid format.")
        except Exception as e:
            logger.warning(f"Error loading local backup: {e}")
    return None

def generate_synthetic_list(de_results_genes: Set[str]) -> Set[str]:
    """
    Generate a small synthetic list for structural validation only.
    Uses a deterministic subset of the input DE genes to ensure reproducibility.
    """
    logger.warning(SYNTHETIC_WARNING)
    sorted_genes = sorted(list(de_results_genes))
    # Take top 10 genes as synthetic "published" list
    return set(sorted_genes[:10]) if len(sorted_genes) >= 10 else set(sorted_genes)

def calculate_jaccard_similarity(set_a: Set[str], set_b: Set[str]) -> float:
    """
    Calculate Jaccard similarity coefficient between two sets.
    J = |A ∩ B| / |A ∪ B|
    """
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0

def load_de_results() -> Set[str]:
    """
    Load raw DE results from T018 output.
    Expects a CSV file with a 'gene_id' column.
    """
    # Look for DE results in data/processed (common location after T018)
    # The exact filename might vary, so we search for a pattern
    de_dir = Path("data/processed")
    if not de_dir.exists():
        raise FileNotFoundError("data/processed directory not found. T018 may not have completed.")
    
    # Try common filenames
    candidate_files = [
        de_dir / "de_results.csv",
        de_dir / "deseq2_results.csv",
        de_dir / "herbivore_response_vectors.csv"
    ]
    
    de_file = None
    for candidate in candidate_files:
        if candidate.exists():
            de_file = candidate
            break
    
    if not de_file:
        # Fallback: look for any CSV in the directory
        csv_files = list(de_dir.glob("*.csv"))
        if csv_files:
            de_file = csv_files[0]
            logger.warning(f"Using first available CSV: {de_file.name} for DE results")
        else:
            raise FileNotFoundError("No DE results CSV found in data/processed. T018 output missing.")
    
    import pandas as pd
    df = pd.read_csv(de_file)
    
    # Identify gene ID column
    gene_col = None
    possible_cols = ['gene_id', 'gene', 'GeneID', 'id']
    for col in possible_cols:
        if col in df.columns:
            gene_col = col
            break
    
    if not gene_col:
        # Assume first column is gene ID
        gene_col = df.columns[0]
        logger.warning(f"Could not find standard gene ID column, using first column: {gene_col}")
    
    return set(df[gene_col].astype(str).unique())

def main():
    """
    Main execution function for T040.
    """
    logger.info("Starting T040: Reproducibility Analysis")
    
    # Step 1: Load DE results from T018
    try:
        de_gene_set = load_de_results()
        logger.info(f"Loaded {len(de_gene_set)} genes from DE results")
    except Exception as e:
        logger.error(f"Failed to load DE results: {e}")
        # Create error report and exit gracefully
        report = {
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_PATH, 'w') as f:
            json.dump(report, f, indent=2)
        return 1
    
    # Step 2: Fetch published gene list with fallbacks
    published_list = None
    source_used = None
    
    # Try primary sources
    published_list = fetch_published_gene_list()
    if published_list:
        source_used = "primary_url"
        logger.info(f"Successfully fetched published list from primary source ({len(published_list)} genes)")
    else:
        # Try local backup
        published_list = load_local_backup()
        if published_list:
            source_used = "local_backup"
            logger.info(f"Loaded published list from local backup ({len(published_list)} genes)")
        else:
            # Generate synthetic
            published_list = generate_synthetic_list(de_gene_set)
            source_used = "synthetic"
            logger.warning(f"Using synthetic gene list for structural validation ({len(published_list)} genes)")
    
    # Step 3: Calculate Jaccard similarity
    jaccard_score = calculate_jaccard_similarity(de_gene_set, published_list)
    intersection_genes = list(de_gene_set & published_list)
    union_genes = list(de_gene_set | published_list)
    
    # Step 4: Generate report
    report = {
        "status": "completed",
        "timestamp": datetime.now().isoformat(),
        "source_used": source_used,
        "de_results_count": len(de_gene_set),
        "published_list_count": len(published_list),
        "jaccard_similarity": jaccard_score,
        "intersection_count": len(intersection_genes),
        "union_count": len(union_genes),
        "intersection_genes": intersection_genes[:20],  # Limit to first 20 for readability
        "notes": SYNTHETIC_WARNING if source_used == "synthetic" else "Real data source used"
    }
    
    # Step 5: Write output
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Reproducibility report written to {OUTPUT_PATH}")
    logger.info(f"Jaccard Similarity: {jaccard_score:.4f} (Source: {source_used})")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
