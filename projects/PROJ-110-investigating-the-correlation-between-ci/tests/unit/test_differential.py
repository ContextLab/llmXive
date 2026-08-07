import json
from pathlib import Path

import numpy as np
import pandas as pd

from analysis.differential import (
    stratify_by_tissue,
    filter_underpowered_tissues,
)


def _create_synthetic_dataset():
    """
    Build a tiny synthetic expression and phenotype dataset with two tissues:
    - 'LowPower': 10 MetS + 10 Control samples (below the 20‑per‑group threshold)
    - 'Sufficient': 30 MetS + 30 Control samples (meets the threshold)
    """
    rng = np.random.default_rng(0)

    # Helper to generate expression values for a single gene
    def expr_vals(n):
        return rng.normal(loc=5.0, scale=1.0, size=n)

    # Low‑power tissue
    low_power_ids = [f"LP_M{i}" for i in range(10)] + [f"LP_C{i}" for i in range(10)]
    low_power_expr = pd.Series(expr_vals(20), index=low_power_ids, name="GENE_X")

    # Sufficient tissue
    sufficient_ids = [f"SP_M{i}" for i in range(30)] + [f"SP_C{i}" for i in range(30)]
    sufficient_expr = pd.Series(expr_vals(60), index=sufficient_ids, name="GENE_X")

    # Combine expression into a DataFrame (single gene)
    expression_df = pd.concat([low_power_expr, sufficient_expr], axis=0).to_frame()

    # Phenotype dataframe
    phenotype_records = []

    # Low‑power tissue records
    for i in range(10):
        phenotype_records.append(
            {"sample_id": f"LP_M{i}", "MetS_status": "MetS", "tissue": "LowPower"}
        )
    for i in range(10):
        phenotype_records.append(
            {"sample_id": f"LP_C{i}", "MetS_status": "Control", "tissue": "LowPower"}
        )

    # Sufficient tissue records
    for i in range(30):
        phenotype_records.append(
            {"sample_id": f"SP_M{i}", "MetS_status": "MetS", "tissue": "Sufficient"}
        )
    for i in range(30):
        phenotype_records.append(
            {"sample_id": f"SP_C{i}", "MetS_status": "Control", "tissue": "Sufficient"}
        )

    phenotype_df = pd.DataFrame(phenotype_records).set_index("sample_id")

    return expression_df, phenotype_df


def test_tissue_stratification_low_power(tmp_path):
    """
    Verify that tissues with fewer than 20 samples per phenotype group are
    excluded by ``filter_underpowered_tissues``.
    """
    expression_df, phenotype_df = _create_synthetic_dataset()

    # Step 1 – stratify samples by tissue
    tissue_groups = stratify_by_tissue(expression_df, phenotype_df)

    # Step 2 – filter out under‑powered tissues
    filtered_groups = filter_underpowered_tissues(
        tissue_groups,
        phenotype_df,
        min_per_group=20,
        output_path=Path(tmp_path) / "excluded_tissues.json",
    )

    # The low‑power tissue must be excluded
    assert "LowPower" not in filtered_groups
    # The sufficient tissue must remain
    assert "Sufficient" in filtered_groups

    # The JSON exclusion report should contain the low‑power tissue entry
    excl_path = Path(tmp_path) / "excluded_tissues.json"
    with excl_path.open("r", encoding="utf-8") as f:
        excl_data = json.load(f)

    tissues_in_report = {entry["tissue"] for entry in excl_data}
    assert "LowPower" in tissues_in_report
    assert "Sufficient" not in tissues_in_report