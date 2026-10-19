import pandas as pd
from pathlib import Path
from code.analysis.explainability import flag_conformational_limits

def test_conformational_limitations_file(tmp_path, monkeypatch):
    """
    Run the conformational audit and verify that the output CSV exists,
    has the correct columns, and that every row has num_rotatable_bonds > 10.
    """
    # Use a temporary directory for all data outputs
    data_derived = Path(tmp_path) / "data" / "derived"
    data_derived.mkdir(parents=True, exist_ok=True)

    # Point the function to the temporary paths
    test_set_path = data_derived / "test_set.csv"
    rf_predictions_path = data_derived / "rf_test_predictions.csv"
    output_path = data_derived / "conformational_limitations.csv"

    # Run the audit
    flag_conformational_limits(
        test_set_path=str(test_set_path),
        rf_predictions_path=str(rf_predictions_path),
        output_path=str(output_path),
        rotatable_bond_threshold=10,
    )

    # Verify file exists
    assert output_path.is_file(), "Conformational limitations CSV was not created."

    # Load and check schema
    df = pd.read_csv(output_path)
    expected_columns = {"smiles", "num_rotatable_bonds", "tpsa", "deviation_magnitude"}
    assert set(df.columns) == expected_columns, f"Unexpected columns: {df.columns}"

    # All rows must have num_rotatable_bonds > 10
    assert (df["num_rotatable_bonds"] > 10).all(), "Found rows with rotatable bonds <= 10"

    # Deviation magnitude should be numeric (allow NaN if no prediction match)
    assert pd.api.types.is_numeric_dtype(df["deviation_magnitude"]), "Deviation magnitude not numeric"
