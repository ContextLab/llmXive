import os
import pandas as pd
from pathlib import Path
from code.correlate_bulk import (
    load_energies_csv,
    load_scaling_results,
    load_bulk_properties,
    merge_data,
    compute_correlations,
    bootstrap_correlation,
    _export_correlation_csv,
)

def test_load_energies(tmp_path):
    # Create a minimal raw energies CSV
    csv_path = tmp_path / "raw_energies.csv"
    df = pd.DataFrame({
        "pair_id": ["EMIM_BF4", "BMIM_TFSI", "HMIM_FAP"],
        "reference_energy": [-15.0, -18.2, -20.5],
        "dft_total_energy": [-15.0, -18.2, -20.5],
        "d3_dispersion_energy": [0.0, 0.0, 0.0],
    })
    df.to_csv(csv_path, index=False)

    loaded = load_energies_csv(str(csv_path))
    assert len(loaded) == 3
    assert "pair_id" in loaded.columns

def test_load_scaling_missing(tmp_path):
    # No scaling file – should return default s=1.0
    result = load_scaling_results(str(tmp_path / "nonexistent.json"))
    assert isinstance(result, dict)
    assert result.get("s") == 1.0

def test_load_bulk_properties(tmp_path):
    csv_path = tmp_path / "bulk.csv"
    df = pd.DataFrame({
        "pair_id": ["EMIM_BF4", "BMIM_TFSI"],
        "density_g_cm3": [1.32, 1.43],
        "viscosity_cP": [45.2, 52.1],
    })
    df.to_csv(csv_path, index=False)

    loaded = load_bulk_properties(str(csv_path))
    assert "density" in loaded.columns
    assert "viscosity_cP" in loaded.columns

def test_merge_and_correlation(tmp_path):
    # Energies
    energies = pd.DataFrame({
        "pair_id": ["EMIM_BF4", "BMIM_TFSI", "HMIM_FAP"],
        "reference_energy": [-15.0, -18.2, -20.5],
        "dft_total_energy": [-14.5, -18.0, -21.0],
        "d3_dispersion_energy": [-0.5, -0.2, -0.5],
    })
    energies_path = tmp_path / "energies.csv"
    energies.to_csv(energies_path, index=False)

    # Bulk properties
    bulk = pd.DataFrame({
        "pair_id": ["EMIM_BF4", "BMIM_TFSI", "HMIM_FAP"],
        "density_g_cm3": [1.32, 1.43, 1.42],
        "viscosity_cP": [45.2, 52.1, 95.4],
    })
    bulk_path = tmp_path / "bulk.csv"
    bulk.to_csv(bulk_path, index=False)

    scaling = {"s": 1.0}

    merged = merge_data(energies, load_bulk_properties(str(bulk_path)), scaling)
    assert "scaled_d3_term" in merged.columns
    assert "signed_error" in merged.columns

    # Compute correlations including the energy‑error test
    corr = compute_correlations(merged, include_energy_error=True)
    # We expect three pairs (raw D3, scaled D3, interaction error)
    assert any("InteractionError_vs_Viscosity_Pearson" in k for k in corr.keys())

    # Bootstrap should run without error
    boot = bootstrap_correlation(merged, n_replicates=10, include_energy_error=True)
    assert isinstance(boot, dict)

    # Export CSV
    out_csv = tmp_path / "correlation_results.csv"
    _export_correlation_csv(corr, boot, merged, out_csv)
    assert out_csv.is_file()
    result_df = pd.read_csv(out_csv)
    # Verify required columns exist
    for col in ["test_name", "coefficient", "r_squared", "raw_p_value",
                "adjusted_p_value", "ci_lower", "ci_upper", "n", "significance"]:
        assert col in result_df.columns

def test_full_workflow(tmp_path):
    # Prepare minimal raw energies CSV
    energies = pd.DataFrame({
        "pair_id": ["EMIM_BF4", "BMIM_TFSI"],
        "reference_energy": [-15.0, -18.2],
        "dft_total_energy": [-15.0, -18.2],
        "d3_dispersion_energy": [0.0, 0.0],
    })
    energies_path = tmp_path / "raw_energies.csv"
    energies.to_csv(energies_path, index=False)

    # Bulk CSV
    bulk = pd.DataFrame({
        "pair_id": ["EMIM_BF4", "BMIM_TFSI"],
        "density_g_cm3": [1.32, 1.43],
        "viscosity_cP": [45.2, 52.1],
    })
    bulk_path = tmp_path / "experimental_bulk_properties.csv"
    bulk.to_csv(bulk_path, index=False)

    # Scaling JSON (optional)
    scaling_path = tmp_path / "scaling_results.json"
    scaling_path.write_text('{"s": 1.0}')

    # Run the analysis function
    from code.correlate_bulk import analyze_and_export

    output_dir = tmp_path / "out"
    output_dir.mkdir()
    csv_path = analyze_and_export(
        str(energies_path),
        str(scaling_path),
        str(bulk_path),
        str(output_dir),
        n_replicates=10,
        include_energy_error=True,
    )
    assert Path(csv_path).is_file()
    df = pd.read_csv(csv_path)
    # Ensure the InteractionError_vs_Viscosity test is present
    assert any(df["test_name"] == "InteractionError_vs_Viscosity")