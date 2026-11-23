import pytest
import pandas as pd
import numpy as np
from models.baseline import LinearRegressionBaseline

def test_baseline_fit_and_predict():
    """
    Verification for T009: Training on a 10-sample synthetic dataset
    produces a non-empty coefficient vector and a successful fit call.
    """
    # Create a 10-sample synthetic dataset
    data = {
        "smiles": ["C", "CC", "CCC", "CCCC", "CCO", "CCCO", "CCCCO", "C(C)O", "CC(C)O", "CC=O"],
        "viscosity": [0.89, 0.88, 0.87, 0.86, 0.85, 0.84, 0.83, 0.82, 0.81, 0.80],
        "dielectric_constant": [78.4, 78.3, 78.2, 78.1, 78.0, 77.9, 77.8, 77.7, 77.6, 77.5],
        "diffusion_coeff": np.linspace(1e-5, 1e-4, 10)
    }
    df = pd.DataFrame(data)

    # Instantiate and fit
    model = LinearRegressionBaseline(n_bits=2048)
    model.fit(df, target_column="diffusion_coeff")

    # Verify coefficients are produced and non-empty
    coefs = model.get_coefficients()
    assert coefs is not None
    assert len(coefs) > 0
    # Expected size: 2048 (fingerprint) + 2 (viscosity, dielectric) = 2050
    assert len(coefs) == 2050

    # Verify predict call works
    smiles_test = ["C", "CC"]
    solvents_test = [
        {"viscosity": 0.89, "dielectric_constant": 78.4},
        {"viscosity": 0.88, "dielectric_constant": 78.3}
    ]
    preds = model.predict(smiles_test, solvents_test)
    assert len(preds) == 2
    assert not np.isnan(preds).any()

def test_baseline_invalid_smiles():
    """Verify that invalid SMILES raise a ValueError during feature preparation."""
    df = pd.DataFrame({
        "smiles": ["INVALID_SMILES"],
        "viscosity": [0.89],
        "dielectric_constant": [78.4],
        "diffusion_coeff": [1e-5]
    })
    model = LinearRegressionBaseline()
    with pytest.raises(ValueError, match="Invalid SMILES string"):
        model.fit(df)