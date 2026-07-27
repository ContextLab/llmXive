"""
Feature Engineering Module for Plant Defense Allocation Prediction.

This module provides functions to filter gene lists to prevent data leakage
from trait-synthesis genes (e.g., CYP enzymes directly involved in defense
compound production) which would bias the predictive models.
"""

from typing import List, Set


# Comprehensive list of trait-synthesis genes to exclude from predictor sets.
# These genes are directly involved in the biosynthesis of defense compounds
# and their inclusion would create circular logic (predicting defense allocation
# using genes that *are* the allocation).
#
# Source: FR-005 and T004 configuration definition.
TRAIT_SYNTHESIS_GENES: Set[str] = {
    # CYP79D family (cyanogenic glucoside biosynthesis)
    "CYP79D16",
    "CYP79D15",
    "CYP79D17",
    # CYP83 family (cyanogenic glucoside biosynthesis)
    "CYP83A1",
    "CYP83B1",
    # CYP96 family (alkaloid biosynthesis)
    "CYP96A1",
    "CYP96A2",
    "CYP96A3",
    # CYP71A family (diverse secondary metabolites)
    "CYP71A1",
    "CYP71A2",
    "CYP71A3",
    "CYP71A4",
    "CYP71A5",
    "CYP71A6",
    "CYP71A7",
    "CYP71A8",
    "CYP71A9",
    "CYP71A10",
    "CYP71A11",
    "CYP71A12",
    "CYP71A13",
    "CYP71A14",
    "CYP71A15",
    "CYP71A16",
    "CYP71A17",
    "CYP71A18",
    "CYP71A19",
    "CYP71A20",
    "CYP71A21",
    "CYP71A22",
    "CYP71A23",
    "CYP71A24",
    "CYP71A25",
    "CYP71A26",
    "CYP71A27",
    "CYP71A28",
    "CYP71A29",
    "CYP71A30",
    "CYP71A31",
    "CYP71A32",
}


def get_trait_synthesis_exclusion_list(gene_list: List[str]) -> List[str]:
    """
    Filter a list of gene IDs to exclude trait-synthesis genes.

    This function is critical for preventing data leakage in the predictive
    modeling pipeline (T027). It ensures that genes directly involved in
    the biosynthesis of defense compounds are not used as predictors for
    the Defense Allocation Index (DAI).

    Args:
        gene_list: A list of gene IDs (strings) from the differential
                   expression analysis or pathway aggregation.

    Returns:
        A filtered list of gene IDs with all trait-synthesis genes removed.
        The order of the remaining genes is preserved.

    Example:
        >>> genes = ["ACT2", "CYP79D16", "GAPDH", "CYP71A1", "UBQ10"]
        >>> clean_genes = get_trait_synthesis_exclusion_list(genes)
        >>> assert "CYP79D16" not in clean_genes
        >>> assert "CYP71A1" not in clean_genes
        >>> assert "ACT2" in clean_genes
    """
    if not gene_list:
        return []

    filtered_genes = [
        gene for gene in gene_list
        if gene not in TRAIT_SYNTHESIS_GENES
    ]

    return filtered_genes
