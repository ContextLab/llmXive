import importlib.util
import pathlib
import numpy as np
import pandas as pd
from rdkit import Chem

# Load the feature engineering module dynamically (its name starts with a digit)
module_path = pathlib.Path(__file__).parents[2] / "code" / "02_feature_engineering.py"
spec = importlib.util.spec_from_file_location("feature_engineering", module_path)
feature_engineering = importlib.util.module_from_spec(spec)
assert spec.loader is not None, "Failed to load feature_engineering module"
spec.loader.exec_module(feature_engineering)

def test_descriptor_generation(tmp_path):
    """
    Verify that the feature engineering pipeline computes correct RDKit descriptors
    for known molecules and writes the expected output CSV.
    """
    # Prepare a small input CSV with two molecules (ethanol and benzene)
    input_df = pd.DataFrame({
        "host_id": [1, 2],
        "smiles": ["CCO", "c1ccccc1"],  # ethanol, benzene
        "halide_identity": ["Cl", "Cl"],
        "binding_constant": [1.0, 2.0],
        "solvent": ["acetonitrile", "acetonitrile"],
        "source": ["simulated", "simulated"]
    })
    input_csv = tmp_path / "hosts.csv"
    input_df.to_csv(input_csv, index=False)

    # Define output path
    output_csv = tmp_path / "descriptors_added.csv"

    # Run the pipeline
    result_df = feature_engineering.run_feature_engineering_pipeline(
        input_path=str(input_csv),
        output_path=str(output_csv)
    )

    # The script should have written the file
    assert output_csv.exists(), "Descriptor CSV was not created"

    # Expected descriptor columns (standard RDKit descriptors + custom proxies)
    expected_cols = {
        "MolWt", "LogP", "NumHDonors", "NumHAcceptors",
        "TPSA", "NumRotatableBonds", "NumAromaticRings",
        "NumAliphaticRings", "charge_density", "cavity_volume"
    }
    missing = expected_cols - set(result_df.columns)
    assert not missing, f"Missing descriptor columns: {missing}"

    # Compute reference descriptors for ethanol using the same helper functions
    mol_ethanol = Chem.MolFromSmiles("CCO")
    mol_ethanol = Chem.AddHs(mol_ethanol)
    ref_desc = feature_engineering.calculate_rdkit_descriptors(mol_ethanol)

    # Compare a selection of values (allow small numerical tolerance)
    row_ethanol = result_df.iloc[0]
    assert np.isclose(row_ethanol["MolWt"], ref_desc["MolWt"], atol=1e-3)
    assert np.isclose(row_ethanol["LogP"], ref_desc["LogP"], atol=1e-3)
    assert row_ethanol["NumHDonors"] == ref_desc["NumHDonors"]
    assert np.isclose(row_ethanol["charge_density"], ref_desc["charge_density"], atol=1e-6)
    assert np.isclose(row_ethanol["cavity_volume"], ref_desc["cavity_volume"], atol=1e-3)