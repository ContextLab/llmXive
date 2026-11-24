"""
Unit test for the alignment success‑rate enforcement and statistics generation.
The test creates a minimal in‑memory dataset, runs the alignment utilities,
and checks that ``alignment_stats.json`` is written and that the success
rate meets the required 80 % threshold.
"""

import json
from pathlib import Path

import pandas as pd

from code.data.align import align_data, save_aligned_matrix
from code.config import get_data_path


def test_alignment_success_and_stats(tmp_path):
    """
    Create a tiny aligned dataset where all species have complete data.
    Verify that the statistics file is produced and that the success rate
    is 1.0 (100 %), satisfying the ≥ 80 % requirement.
    """
    # ---- Prepare mock BGC and metabolite tables ---------------------------------
    species = [f"sp{i}" for i in range(1, 6)]

    # BGC table – includes the required ``total_bgc_count`` column
    genomes_df = pd.DataFrame(
        {
            "species": species,
            "total_bgc_count": [1, 0, 2, 3, 0],
        }
    )

    # Metabolite table – includes the required ``log_abundance`` column
    metabolites_df = pd.DataFrame(
        {
            "species": species,
            "log_abundance": [0.1, 0.2, 0.3, 0.4, 0.5],
        }
    )

    # ---- Run the alignment -------------------------------------------------------
    aligned_df, rate = align_data(genomes_df, metabolites_df)

    # Use a temporary file for the aligned matrix to avoid polluting the repo
    aligned_path = tmp_path / "aligned_matrix.csv"
    save_aligned_matrix(aligned_df, output_path=aligned_path)

    # ---- Verify the success rate -------------------------------------------------
    assert rate == 1.0, "All species have data, so success rate must be 100 %"

    # ---- Verify the statistics JSON file -----------------------------------------
    stats_path = get_data_path(Path("processed") / "alignment_stats.json")
    assert stats_path.is_file(), "alignment_stats.json should have been created"

    with stats_path.open("r", encoding="utf-8") as f:
        stats = json.load(f)

    # The JSON should contain the same rate we computed
    assert abs(stats["success_rate"] - rate) < 1e-9
    assert stats["total_species"] == len(species)
    assert stats["valid_species"] == len(species)

    # The enforcement threshold (≥ 80 %) is already validated by the
    # ``save_aligned_matrix`` implementation – no exception should have been raised.