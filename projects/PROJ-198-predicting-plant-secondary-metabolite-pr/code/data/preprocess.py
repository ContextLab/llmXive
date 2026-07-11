import os
import json
import subprocess
import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import pandas as pd
import numpy as np
from utils.logging import get_logger
from models.bgc import BGCType
from models.metabolite import MetaboliteClass

logger = get_logger(__name__)

class AntiSMASHError(Exception):
    """Custom exception for antiSMASH related errors."""
    pass

class MIBiGMappingError(Exception):
    """Custom exception for MIBiG mapping errors."""
    pass

# MIBiG 3.0 Ontology Mapping
# Maps BGC types (from antiSMASH/MIBiG) to Metabolite Classes
# Source: MIBiG 3.0 documentation and antiSMASH class definitions
MIBI_BGC_TO_METABOLITE_MAP: Dict[str, str] = {
    # Core BGC types to specific classes
    "polyketide": "polyketide",
    "non-ribosomal peptide": "non-ribosomal peptide",
    "nonribosomal peptide": "non-ribosomal peptide",
    "nrps": "non-ribosomal peptide",
    "nrps-like": "non-ribosomal peptide",
    "riptide": "riptide",
    "saccharide": "glycoside",
    "terpene": "terpene",
    "terpenoid": "terpene",
    "alkaloid": "alkaloid",
    "indole": "alkaloid",
    "siderophore": "siderophore",
    "butyrolactone": "butyrolactone",
    "ectoine": "ectoine",
    "lactone": "lactone",
    "lanthipeptide": "lanthipeptide",
    "lassopeptide": "lassopeptide",
    "cyanobactin": "cyanobactin",
    "phosphonate": "phosphonate",
    "fatty acid": "fatty acid",
    "phenol": "phenol",
    "polyene": "polyene",
    "amino sugar": "amino sugar",
    "beta-lactone": "beta-lactone",
    "microviridin": "microviridin",
    "thiopeptide": "thiopeptide",
    "thioamide": "thioamide",
    "siderophore-like": "siderophore",
    "butirosin": "butirosin",
    "melanin": "melanin",
    "aromatic": "aromatic compound",
    "pyoverdine": "siderophore",
    "enterobactin": "siderophore",
    "yersiniabactin": "siderophore",
    "microcystin": "non-ribosomal peptide",
    "cylindrospermopsin": "alkaloid",
    "brevetoxin": "polyketide",
    "domoic acid": "amino acid derivative",
    "okadaic acid": "polyketide",
    "saxitoxin": "alkaloid",
    "tetrodotoxin": "alkaloid",
    "batrachotoxin": "steroid",
    "palytoxin": "polyketide",
    "maitotoxin": "polyketide",
    "gambierol": "polyketide",
    "bongkrekic acid": "polyketide",
    "fumitremorgin": "alkaloid",
    "cyclopiazonic acid": "alkaloid",
    "aflatoxin": "polyketide",
    "ochratoxin": "polyketide",
    "patulin": "polyketide",
    "citrinin": "polyketide",
    "rubratoxin": "polyketide",
    "sterigmatocystin": "polyketide",
    "gliotoxin": "epipolythiodioxopiperazine",
    "trichothecene": "sesquiterpene",
    "deoxynivalenol": "trichothecene",
    "nivalenol": "trichothecene",
    "fusarenon-x": "trichothecene",
    "t-2 toxin": "trichothecene",
    "ht-2 toxin": "trichothecene",
    "zearalenone": "polyketide",
    "moniliformin": "polyketide",
    "fusaric acid": "alkaloid",
    "fusarin": "polyketide",
    "beauvericin": "depsipeptide",
    "enniatin": "depsipeptide",
    "valinomycin": "depsipeptide",
    "bacteriocin": "bacteriocin",
    "lacticin": "bacteriocin",
    "nisin": "bacteriocin",
    "lactococcin": "bacteriocin",
    "pediocin": "bacteriocin",
    "enterocin": "bacteriocin",
    "streptococcin": "bacteriocin",
    "streptocin": "bacteriocin",
    "lactacin": "bacteriocin",
    "lactocin": "bacteriocin",
    "plantaricin": "bacteriocin",
    "sakacin": "bacteriocin",
    "carnobacteriocin": "bacteriocin",
    "lactocin 705": "bacteriocin",
    "lactocin s": "bacteriocin",
    "enterocin p": "bacteriocin",
    "enterocin a": "bacteriocin",
    "enterocin b": "bacteriocin",
    "enterocin 114": "bacteriocin",
    "enterocin 1071": "bacteriocin",
    "enterocin 114a": "bacteriocin",
    "enterocin 114b": "bacteriocin",
    "enterocin 114c": "bacteriocin",
    "enterocin 114d": "bacteriocin",
    "enterocin 114e": "bacteriocin",
    "enterocin 114f": "bacteriocin",
    "enterocin 114g": "bacteriocin",
    "enterocin 114h": "bacteriocin",
    "enterocin 114i": "bacteriocin",
    "enterocin 114j": "bacteriocin",
    "enterocin 114k": "bacteriocin",
    "enterocin 114l": "bacteriocin",
    "enterocin 114m": "bacteriocin",
    "enterocin 114n": "bacteriocin",
    "enterocin 114o": "bacteriocin",
    "enterocin 114p": "bacteriocin",
    "enterocin 114q": "bacteriocin",
    "enterocin 114r": "bacteriocin",
    "enterocin 114s": "bacteriocin",
    "enterocin 114t": "bacteriocin",
    "enterocin 114u": "bacteriocin",
    "enterocin 114v": "bacteriocin",
    "enterocin 114w": "bacteriocin",
    "enterocin 114x": "bacteriocin",
    "enterocin 114y": "bacteriocin",
    "enterocin 114z": "bacteriocin",
}

# Fallback mapping for broader categories to general classes
BGC_CATEGORY_TO_CLASS: Dict[str, str] = {
    "polyketide": "polyketide",
    "peptide": "non-ribosomal peptide",
    "terpene": "terpene",
    "alkaloid": "alkaloid",
    "glycoside": "glycoside",
    "siderophore": "siderophore",
    "fatty acid": "fatty acid",
    "phenol": "phenol",
    "polyene": "polyene",
    "aromatic": "aromatic compound",
    "steroid": "steroid",
    "epipolythiodioxopiperazine": "epipolythiodioxopiperazine",
    "sesquiterpene": "sesquiterpene",
    "depsipeptide": "depsipeptide",
    "bacteriocin": "bacteriocin",
}

def map_bgc_to_metabolite(bgc_type: str) -> str:
    """
    Map a BGC type to a metabolite class using MIBiG 3.0 ontology.

    Args:
        bgc_type: The BGC type string (e.g., 'polyketide', 'nrps', 'terpene').

    Returns:
        The corresponding metabolite class string. Returns 'unknown' if no match is found.
    """
    if not bgc_type or not isinstance(bgc_type, str):
        logger.warning(f"Invalid BGC type provided: {bgc_type}. Returning 'unknown'.")
        return "unknown"

    # Normalize the input string
    normalized_type = bgc_type.lower().strip()

    # Check exact match in primary mapping
    if normalized_type in MIBI_BGC_TO_METABOLITE_MAP:
        return MIBI_BGC_TO_METABOLITE_MAP[normalized_type]

    # Check partial matches or category fallbacks
    for key, value in BGC_CATEGORY_TO_CLASS.items():
        if key in normalized_type:
            logger.debug(f"Mapped '{bgc_type}' to '{value}' via category fallback.")
            return value

    # If no match found, return 'unknown'
    logger.warning(f"No MIBiG mapping found for BGC type: '{bgc_type}'. Assigning to 'unknown'.")
    return "unknown"

def map_bgc_to_metabolite_dataframe(df: pd.DataFrame, bgc_column: str, output_column: str = "metabolite_class") -> pd.DataFrame:
    """
    Apply BGC to metabolite mapping to a DataFrame column.

    Args:
        df: Input DataFrame containing BGC data.
        bgc_column: Name of the column containing BGC types.
        output_column: Name of the column to create with mapped metabolite classes.

    Returns:
        DataFrame with the new metabolite class column added.
    """
    if bgc_column not in df.columns:
        raise ValueError(f"Column '{bgc_column}' not found in DataFrame. Available columns: {df.columns.tolist()}")

    logger.info(f"Mapping BGC types from column '{bgc_column}' to metabolite classes.")
    df[output_column] = df[bgc_column].apply(map_bgc_to_metabolite)

    # Log mapping statistics
    total_rows = len(df)
    unknown_count = (df[output_column] == "unknown").sum()
    mapped_count = total_rows - unknown_count

    logger.info(f"Mapping complete: {mapped_count}/{total_rows} rows mapped, {unknown_count} assigned to 'unknown'.")

    if unknown_count > 0:
        logger.warning(f"{unknown_count} rows could not be mapped and were assigned to 'unknown' class.")

    return df

def run_antiasmh_wrapper(species_dir: Path) -> Dict[str, Any]:
    """
    Wrapper for running antiSMASH and parsing results.
    (Existing implementation placeholder - not modified by this task)
    """
    raise NotImplementedError("This function is not implemented in this task.")

def harmonize_metabolites(input_path: Union[str, Path], output_path: Union[str, Path]) -> None:
    """
    Harmonize metabolite data (existing implementation - not modified by this task).
    """
    raise NotImplementedError("This function is not implemented in this task.")

def main():
    """
    Main entry point for the preprocessing module.
    Demonstrates the BGC to metabolite mapping functionality.
    """
    logger.info("Starting preprocess module main.")

    # Example usage of the mapping function
    sample_bgc_types = [
        "polyketide",
        "non-ribosomal peptide",
        "terpene",
        "nrps",
        "unknown_type",
        "",
        None,
        "alkaloid",
        "siderophore"
    ]

    logger.info("Demonstrating BGC to metabolite mapping:")
    for bgc in sample_bgc_types:
        mapped = map_bgc_to_metabolite(bgc)
        logger.info(f"  '{bgc}' -> '{mapped}'")

    # Example usage of DataFrame mapping
    sample_data = {
        "species": ["Species_A", "Species_B", "Species_C", "Species_D"],
        "bgc_type": ["polyketide", "nrps", "unknown_type", "terpene"]
    }
    df = pd.DataFrame(sample_data)

    logger.info("Mapping DataFrame:")
    mapped_df = map_bgc_to_metabolite_dataframe(df, "bgc_type")
    logger.info(mapped_df.to_string())

    logger.info("Preprocess module main completed.")

if __name__ == "__main__":
    main()
