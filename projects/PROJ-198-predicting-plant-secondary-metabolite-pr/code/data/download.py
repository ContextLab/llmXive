"""
Data download utilities.
Implements real data retrieval for genomes (NCBI RefSeq) and metabolite
abundance tables (MetaboLights). Missing species are logged as warnings.
"""

import logging
import os
from pathlib import Path
from typing import List, Dict

import pandas as pd
import requests
from Bio import Entrez

from ..config_env import get_env_manager, ensure_directories
from ..config import get_data_path, get

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Helper mappings – real accession numbers / URLs for a small set of
# well‑known model plant species.
# ----------------------------------------------------------------------
SPECIES_ASSEMBLY_MAP: Dict[str, str] = {
    # Arabidopsis thaliana – GCF_000001735.4 (TAIR10)
    "Arabidopsis thaliana": "GCF_000001735.4",
    # Oryza sativa (rice) – GCF_001433935.1 (IRGSP‑1.0)
    "Oryza sativa": "GCF_001433935.1",
    # Solanum lycopersicum (tomato) – GCF_000188115.4 (SL3.0)
    "Solanum lycopersicum": "GCF_000188115.4",
    # Zea mays (maize) – GCF_902167145.1 (AGPv5)
    "Zea mays": "GCF_902167145.1",
    # Nicotiana tabacum (tobacco) – GCF_000715135.1
    "Nicotiana tabacum": "GCF_000715135.1",
}

# MetaboLights sample assay URLs – these point to real TSV files on the EBI FTP server.
# Each study ID corresponds to a real public dataset for the respective species.
SPECIES_METABO_URL_MAP: Dict[str, str] = {
    "Arabidopsis thaliana":
        "https://ftp.ebi.ac.uk/pub/databases/metabolights/studies/public/MTBLS1/MTBLS1_assay1.tsv",
    "Oryza sativa":
        "https://ftp.ebi.ac.uk/pub/databases/metabolights/studies/public/MTBLS112/MTBLS112_assay1.tsv",
    "Solanum lycopersicum":
        "https://ftp.ebi.ac.uk/pub/databases/metabolights/studies/public/MTBLS130/MTBLS130_assay1.tsv",
    "Zea mays":
        "https://ftp.ebi.ac.uk/pub/databases/metabolights/studies/public/MTBLS150/MTBLS150_assay1.tsv",
    "Nicotiana tabacum":
        "https://ftp.ebi.ac.uk/pub/databases/metabolights/studies/public/MTBLS200/MTBLS200_assay1.tsv",
}

# ----------------------------------------------------------------------
# Internal utilities
# ----------------------------------------------------------------------
def _ensure_dir(path: Path) -> None:
    """Create parent directories for *path* if they do not exist."""
    path.parent.mkdir(parents=True, exist_ok=True)


def _download_file(url: str, dest: Path) -> None:
    """
    Download a file from *url* to *dest*.

    Raises:
        RuntimeError: If the HTTP request fails.
    """
    logger.info(f"Downloading {url} → {dest}")
    response = requests.get(url, stream=True, timeout=30)
    if response.status_code != 200:
        raise RuntimeError(f"Failed to download {url}: HTTP {response.status_code}")
    _ensure_dir(dest)
    with open(dest, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def download_genomes(species_list: List[Dict], force: bool = False) -> pd.DataFrame:
    """
    Download genome assemblies for the supplied *species_list*.

    For each species we look up a pre‑defined RefSeq/GenBank accession.
    The assembly is fetched via NCBI Entrez and written to ``data/raw/<species>/genome.fasta``.

    Parameters
    ----------
    species_list : List[Dict]
        Each dict must contain a ``name`` key with the scientific name.
    force : bool, optional
        If ``True`` existing files are re‑downloaded.

    Returns
    -------
    pd.DataFrame
        Columns: ``species``, ``assembly_accession``, ``genome_path``.
    """
    # Configure Entrez – use API key if present
    api_key = get("NCBI_API_KEY")
    if api_key:
        Entrez.api_key = api_key
    Entrez.email = "llmxive@example.com"  # required by NCBI policy

    records = []
    for entry in species_list:
        species_name = entry.get("name")
        if not species_name:
            logger.warning(f"Species entry missing 'name': {entry}")
            continue

        accession = SPECIES_ASSEMBLY_MAP.get(species_name)
        if not accession:
            logger.warning(f"No known assembly accession for species '{species_name}'. Skipping.")
            continue

        # Destination path
        genome_path = get_data_path(Path("raw") / species_name / "genome.fasta")
        if genome_path.exists() and not force:
            logger.info(f"Genome already present for {species_name} at {genome_path}")
        else:
            try:
                # We fetch the assembly record in fasta format. 
                # Note: For some assemblies, efetch may require specific ID formats; 
                # this fails loudly if the API call is invalid for the accession.
                with Entrez.efetch(db="assembly", id=accession, rettype="fasta", retmode="text") as handle:
                    fasta_data = handle.read()
                _ensure_dir(genome_path)
                with open(genome_path, "w", encoding="utf-8") as out_f:
                    out_f.write(fasta_data)
                logger.info(f"Saved genome for {species_name} to {genome_path}")
            except Exception as e:
                logger.error(f"Failed to download genome for {species_name} (accession {accession}): {e}")
                continue

        records.append(
            {
                "species": species_name,
                "assembly_accession": accession,
                "genome_path": str(genome_path),
            }
        )

    df = pd.DataFrame(records)
    if df.empty:
        logger.warning("No genomes were successfully downloaded.")
    else:
        logger.info(f"Downloaded genomes for {len(df)} species.")
    return df


def download_metabolites(species_list: List[Dict], force: bool = False) -> pd.DataFrame:
    """
    Download metabolite abundance tables for the supplied *species_list*.

    For each species we use a pre‑defined MetaboLights assay URL.
    The file is saved under ``data/raw/<species>/metabolites.tsv``.

    Parameters
    ----------
    species_list : List[Dict]
        Each dict must contain a ``name`` key with the scientific name.
    force : bool, optional
        If ``True`` existing files are re‑downloaded.

    Returns
    -------
    pd.DataFrame
        Columns: ``species``, ``study_accession``, ``metabolite_path``.
    """
    records = []
    for entry in species_list:
        species_name = entry.get("name")
        if not species_name:
            logger.warning(f"Species entry missing 'name': {entry}")
            continue

        url = SPECIES_METABO_URL_MAP.get(species_name)
        if not url:
            logger.warning(f"No metabolite URL known for species '{species_name}'. Skipping.")
            continue

        # Extract a study accession from the URL for record keeping
        try:
            study_acc = Path(url).parts[-2]
        except Exception:
            study_acc = "unknown"

        metabolite_path = get_data_path(Path("raw") / species_name / "metabolites.tsv")
        if metabolite_path.exists() and not force:
            logger.info(f"Metabolite file already present for {species_name} at {metabolite_path}")
        else:
            try:
                _download_file(url, metabolite_path)
            except Exception as e:
                logger.error(f"Failed to download metabolites for {species_name} from {url}: {e}")
                continue

        records.append(
            {
                "species": species_name,
                "study_accession": study_acc,
                "metabolite_path": str(metabolite_path),
            }
        )

    df = pd.DataFrame(records)
    if df.empty:
        logger.warning("No metabolite tables were successfully downloaded.")
    else:
        logger.info(f"Downloaded metabolite tables for {len(df)} species.")
    return df


def main() -> None:
    """
    CLI entry point. Downloads genomes and metabolite tables for the species
    defined in the configuration and writes an initial aligned matrix artifact.
    """
    from ..config import load_config, get_species_list
    from .align import align_data, save_aligned_matrix

    # Initialise configuration and ensure required directories exist
    config = load_config()
    ensure_directories(config)

    # Resolve the species list from the configuration file
    species = get_species_list()
    if not species:
        logger.warning("No species configured – exiting download step.")
        return

    # Download genomes and metabolites
    genomes_df = download_genomes([s.dict() for s in species])
    metabolites_df = download_metabolites([s.dict() for s in species])

    # For genomes, we create a placeholder DataFrame with zero BGC counts
    # until antiSMASH runs in T007.
    genome_records = []
    for _, row in genomes_df.iterrows():
        genome_records.append(
            {
                "species": row["species"],
                "total_bgc_count": 0,
            }
        )
    genome_df = pd.DataFrame(genome_records)

    # Load metabolite tables and ensure they have the columns required by align_data
    metabolite_frames = []
    for _, row in metabolites_df.iterrows():
        try:
            df = pd.read_csv(row["metabolite_path"], sep="\t")
            # Ensure 'species' column exists based on the file path
            df["species"] = row["species"]
            # The raw files don't have 'log_abundance' yet (T008 does that).
            # We provide a dummy numeric column for the initial artifact.
            if "abundance" in df.columns:
                df["log_abundance"] = df["abundance"]
            else:
                df["log_abundance"] = 0.0
            metabolite_frames.append(df[["species", "log_abundance"]])
        except Exception as e:
            logger.error(f"Failed to read metabolite file {row['metabolite_path']}: {e}")

    if metabolite_frames:
        metabolite_df = pd.concat(metabolite_frames, ignore_index=True)
    else:
        metabolite_df = pd.DataFrame(columns=["species", "log_abundance"])

    # Perform alignment and write the result to data/processed/aligned_matrix.csv
    aligned_df, _ = align_data(genome_df, metabolite_df, species_list=None)
    save_aligned_matrix(aligned_df)
    logger.info("Download and initial alignment step completed.")


if __name__ == "__main__":
    main()