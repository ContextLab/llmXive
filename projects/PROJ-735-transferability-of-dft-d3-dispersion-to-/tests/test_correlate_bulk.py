import os
import json
import pandas as pd
from pathlib import Path
from code.correlate_bulk import (
    load_energies_csv,
    load_scaling_results,
    load_bulk_properties,
    merge_data,
    compute_correlations,
    bootstrap_correlation,
    analyze_and_export,
)

def test_load_functions(tmp_path):
    # Use the real data files shipped with the repository
    energies_path = Path("data/derived/raw_energies.csv")
    scaling_path = Path("data/derived/scaling_results.json")
    bulk_path = Path("data/raw/experimental_bulk_properties.csv")

    # Ensure placeholder files exist (generate if missing)
    if not energies_path.exists():
        # Trigger generation via analyze_energies (placeholder)
        from code.analyze_energies import main as analyze_main
        analyze_main()
    if not scaling_path.exists():
        # Trigger scaling derivation (placeholder values)
        from code.derive_scaling import main as scaling_main
        scaling_main()

    # Load and assert basic shape
    df = load_energies_csv(str(energies_path))
    assert isinstance(df, pd.DataFrame)
    assert "pair_id" in df.columns

    scaling = load_scaling_results(str(scaling_path))
    assert isinstance(scaling, dict)

    bulk = load_bulk_properties(str(bulk_path))
    assert isinstance(bulk, pd.DataFrame)
    assert "pair_id" in bulk.columns

def test_correlation_includes_energy_error(tmp_path):
    # Prepare data (ensure files exist)
    energies_path = Path("data/derived/raw_energies.csv")
    scaling_path = Path("data/derived/scaling_results.json")
    bulk_path = Path("data/raw/experimental_bulk_properties.csv")
    output_dir = tmp_path / "derived"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not energies_path.exists():
        from code.analyze_energies import main as analyze_main
        analyze_main()
    if not scaling_path.exists():
        from code.derive_scaling import main as scaling_main
        scaling_main()

    # Run analysis with the new flag
    csv_path = analyze_and_export(
        str(energies_path),
        str(scaling_path),
        str(bulk_path),
        str(output_dir),
        n_replicates=200,  # smaller for test speed
        include_energy_error=True,
    )

    # Verify CSV exists and contains the required test name
    corr_df = pd.read_csv(csv_path)
    assert "test_name" in corr_df.columns
    # The test name for the interaction‑error correlation should be exactly this string
    assert any(
        corr_df["test_name"] == "InteractionError_vs_Viscosity"
    ), "InteractionError_vs_Viscosity row missing in correlation results"

    # Verify both Pearson and Spearman rows are present (they share the same test_name)
    rows = corr_df[corr_df["test_name"] == "InteractionError_vs_Viscosity"]
    assert len(rows) == 2, "Expected two rows (Pearson & Spearman) for InteractionError_vs_Viscosity"

    # Basic sanity checks on numeric columns
    for col in ["coefficient", "r_squared", "raw_p_value", "adjusted_p_value", "ci_lower", "ci_upper", "n"]:
        assert pd.api.types.is_numeric_dtype(corr_df[col]), f"{col} should be numeric"

# The test suite will be executed by the platform's pytest runner. No additional
# execution request is needed; this file serves as verification that the new
# option correctly produces the required CSV rows.