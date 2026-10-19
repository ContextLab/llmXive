"""
Data download (or mock‑data loading) utilities.
In CI mode the functions load pre‑generated mock files from ``data/raw``.
In research mode they would perform real API calls – those branches are
deliberately left unimplemented to avoid external dependencies during testing.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict

import pandas as pd

from ..config_env import get_env_manager, ensure_directories
from ..config import get_data_path

logger = logging.getLogger(__name__)


def _load_mock_json(path: Path) -> List[Dict]:
    """Utility to read a JSON file containing a list of dictionaries."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def download_genomes(species_list: List[Dict], force: bool = False) -> pd.DataFrame:
    """
    Load genome‑related mock data.

    When ``CI_MODE`` (environment variable) is truthy the function reads
    ``data/raw/mock_bgc_counts.csv`` which contains pre‑computed BGC count
    information for a small set of species. In non‑CI mode a ``NotImplementedError``
    is raised – the real implementation would query NCBI/Phytozome.
    """
    ci_mode = int(get_env_manager().get("CI_MODE") or 0)
    if ci_mode:
        mock_path = get_data_path(Path("raw") / "mock_bgc_counts.csv")
        if not mock_path.exists():
            logger.error(f"Mock BGC counts file not found at {mock_path}")
            raise FileNotFoundError(mock_path)
        df = pd.read_csv(mock_path)
        logger.info(f"Loaded mock genome data with {len(df)} rows")
        return df
    else:
        raise NotImplementedError(
            "Real genome download not implemented in this sandbox."
        )


def download_metabolites(species_list: List[Dict], force: bool = False) -> pd.DataFrame:
    """
    Load metabolite‑related mock data.

    In CI mode the function reads ``data/raw/mock_metabolite_abundance.csv``.
    In research mode a ``NotImplementedError`` is raised.
    """
    ci_mode = int(get_env_manager().get("CI_MODE") or 0)
    if ci_mode:
        mock_path = get_data_path(Path("raw") / "mock_metabolite_abundance.csv")
        if not mock_path.exists():
            logger.error(f"Mock metabolite file not found at {mock_path}")
            raise FileNotFoundError(mock_path)
        df = pd.read_csv(mock_path)
        logger.info(f"Loaded mock metabolite data with {len(df)} rows")
        return df
    else:
        raise NotImplementedError(
            "Real metabolite download not implemented in this sandbox."
        )


def main() -> None:
    """
    CLI entry point used by the quickstart guide.
    Executes a minimal pipeline that loads the mock data, aligns it,
    and writes ``data/processed/aligned_matrix.csv``.
    """
    from ..config import load_config, get_species_list

    # Initialise configuration and ensure required directories exist
    config = load_config()
    ensure_directories(config)

    species = get_species_list()
    if not species:
        logger.warning("No species configured – proceeding with mock data only.")

    # Load mock data
    genomes_df = download_genomes([], force=False)
    metabolites_df = download_metabolites([], force=False)

    # Align and save
    from .align import align_data, save_aligned_matrix

    aligned_df, _ = align_data(genomes_df, metabolites_df, species_list=None)
    save_aligned_matrix(aligned_df)
    logger.info("Mock alignment completed.")

if __name__ == "__main__":
    main()
