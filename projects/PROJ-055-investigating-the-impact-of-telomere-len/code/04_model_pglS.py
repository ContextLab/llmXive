import os
import sys
import logging
import csv
from pathlib import Path
from typing import Dict, Any, Optional, List

import pandas as pd

# rpy2 is optional at import time – we will handle missing dependency gracefully
try:
    import rpy2.robjects as ro
    from rpy2.robjects import pandas2ri
    from rpy2.robjects.conversion import localconverter
except ImportError:
    ro = None

# Ensure local imports work if running as script or module
try:
    from config import get_config
    from logging_config import init_project_logging, handle_memory_pressure, log_memory_status
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_config
    from logging_config import init_project_logging, handle_memory_pressure, log_memory_status

logger = logging.getLogger(__name__)

def check_species_power(species_count: int, threshold: int = 15) -> bool:
    if species_count < threshold:
        logger.warning(f"Low Power: Phylogenetic inference unreliable (n={species_count} < {threshold})")
        return False
    return True

def extract_unique_species(data_path: str) -> List[str]:
    df = pd.read_csv(data_path)
    if 'species' not in df.columns:
        raise ValueError(f"Column 'species' not found in {data_path}")
    return df['species'].dropna().unique().tolist()

def fetch_phylogenetic_tree(species_list: List[str], output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    tree_path = os.path.join(output_dir, "bird_phylogeny.nwk")
    if os.path.exists(tree_path):
        logger.info(f"Phylogenetic tree already exists at {tree_path}")
        return tree_path

    if ro is None:
        raise ImportError("rpy2 is required to fetch the phylogenetic tree via rotl.")

    logger.info(f"Fetching phylogenetic tree for {len(species_list)} species via rotl...")
    ro.r('library(rotl)')
    ro.r('library(ape)')

    species_names_r = ro.StrVector(species_list)
    r_code = f'''
    species <- {species_names_r}
    matched <- tnrs(species)
    tree <- tol_tree(matched$unique_name)
    write.tree(tree, file="{tree_path}")
    '''
    ro.r(r_code)
    logger.info(f"Successfully saved phylogenetic tree to {tree_path}")
    return tree_path

def run_r_pglS_model(data_path: str, tree_path: str, output_dir: str) -> Dict[str, Any]:
    if ro is None:
        raise ImportError("rpy2 is required to run the PGLS model.")

    os.makedirs(output_dir, exist_ok=True)
    r_script_path = os.path.join(Path(__file__).parent, "R", "01_fit_pglS.R")
    if not os.path.exists(r_script_path):
        raise FileNotFoundError(f"R script not found: {r_script_path}")

    args = ["--data", data_path, "--tree", tree_path, "--output_dir", output_dir]

    import subprocess
    result = subprocess.run(
        ["Rscript", r_script_path] + args,
        check=True,
        capture_output=True,
        text=True,
    )
    logger.info(f"R script stdout: {result.stdout}")
    if result.stderr:
        logger.warning(f"R script stderr: {result.stderr}")

    results_file = os.path.join(output_dir, "pgls_results.csv")
    if not os.path.exists(results_file):
        raise FileNotFoundError(f"R script did not produce results file at {results_file}")

    df_res = pd.read_csv(results_file)
    if df_res.empty:
        raise ValueError("R script produced an empty results file.")
    row = df_res.iloc[0]
    return {
        "coefficient": float(row.get("coefficient", 0)),
        "se": float(row.get("se", 0)),
        "p_value": float(row.get("p_value", 1.0)),
        "lambda": float(row.get("lambda", 0.0)),
    }

def save_model_results(results: Dict[str, Any], output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    pd.DataFrame([results]).to_csv(output_path, index=False)
    logger.info(f"Saved model results to {output_path}")

def main():
    config = get_config()
    init_project_logging(config)

    # Properly pass the logger to memory‑status helper
    logger = logging.getLogger(__name__)
    handle_memory_pressure(logger)
    log_memory_status(logger)

    merged_data_path = config.get("paths", {}).get("merged_data", "data/processed/merged_analysis.csv")
    phylogeny_dir = config.get("paths", {}).get("phylogeny", "data/phylogeny")
    results_dir = config.get("paths", {}).get("results", "results")
    output_csv_path = os.path.join(results_dir, "model_summary.csv")

    if not os.path.exists(merged_data_path):
        logger.error(f"Merged data file not found: {merged_data_path}")
        sys.exit(1)

    species_list = extract_unique_species(merged_data_path)
    if not species_list:
        logger.error("No species found in merged data.")
        sys.exit(1)

    if not check_species_power(len(species_list)):
        skipped = {
            "coefficient": None,
            "se": None,
            "p_value": None,
            "lambda": None,
            "status": "skipped_low_power",
        }
        save_model_results(skipped, output_csv_path)
        logger.info("Modeling skipped due to low power.")
        return

    tree_path = fetch_phylogenetic_tree(species_list, phylogeny_dir)
    model_results = run_r_pglS_model(merged_data_path, tree_path, results_dir)
    save_model_results(model_results, output_csv_path)
    logger.info("PGLS modeling completed successfully.")

if __name__ == "__main__":
    main()
