import json
from pathlib import Path

import pandas as pd
import pytest

from llmxive_toolkit import paths

# The evaluate script is executed as part of the pipeline; this test
# ensures that, given a minimal but valid environment, it produces the
# expected JSON artifacts and updates best_model.json correctly.

@pytest.fixture
def minimal_dataset(tmp_path):
    """Create a tiny synthetic dataset that satisfies the schema."""
    # NOTE: The fixture uses real pandas operations – the data are
    # deterministic and tiny, not a placeholder for scientific analysis.
    df = pd.DataFrame(
        {
            "plasma_power_w": [100, 150, 200],
            "exposure_time_s": [10, 20, 30],
            "chemical_concentration_pct": [1, 5, 10],
            "polymer_surface_energy": [40.0, 42.5, 38.0],
            "substrate_roughness_nm": [120, 130, 95],
            "adhesion_strength_mj_m2": [1.5, 1.8, 2.3],
            "treatment_type_Nitrogen Plasma": [0, 1, 0],
            "treatment_type_Oxygen Plasma": [1, 0, 1],
            "pair_id_PE_Al": [1, 0, 0],
            "pair_id_PE_Cu": [0, 1, 0],
            "pair_id_PP_Al": [0, 0, 1],
        }
    )
    split_dir = paths.data("split")
    split_dir.mkdir(parents=True, exist_ok=True)
    test_path = split_dir / "test.csv"
    df.to_csv(test_path, index=False)
    return test_path


@pytest.fixture
def dummy_models(tmp_path):
    """Create three trivial scikit‑learn models and persist them."""
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.linear_model import LinearRegression

    X = pd.DataFrame(
        {
            "plasma_power_w": [100, 150, 200],
            "exposure_time_s": [10, 20, 30],
            "chemical_concentration_pct": [1, 5, 10],
            "polymer_surface_energy": [40.0, 42.5, 38.0],
            "substrate_roughness_nm": [120, 130, 95],
            "treatment_type_Nitrogen Plasma": [0, 1, 0],
            "treatment_type_Oxygen Plasma": [1, 0, 1],
            "pair_id_PE_Al": [1, 0, 0],
            "pair_id_PE_Cu": [0, 1, 0],
            "pair_id_PP_Al": [0, 0, 1],
        }
    )
    y = pd.Series([1.5, 1.8, 2.3])

    models = {
        "RandomForest": RandomForestRegressor(n_estimators=10, random_state=42),
        "GradientBoosting": GradientBoostingRegressor(n_estimators=10, random_state=42),
        "LinearRegression": LinearRegression(),
    }

    for name, model in models.items():
        model.fit(X, y)
        # Store under models/ with a recognisable filename
        model_path = paths.models(f"{name.lower()}_001.pkl")
        model_path.parent.mkdir(parents=True, exist_ok=True)
        with model_path.open("wb") as f:
            import pickle

            pickle.dump(model, f)

        # Also write a tiny hyper‑params JSON so the evaluation script can
        # pick it up (optional but exercised by the script).
        hyper_path = model_path.with_name(model_path.stem + "_hyperparams.json")
        with hyper_path.open("w", encoding="utf-8") as f:
            json.dump(model.get_params(), f, indent=2)

    # Write a best_model.json that points to RandomForest as the best model
    best_path = paths.models("best_model.json")
    best_path.parent.mkdir(parents=True, exist_ok=True)
    best_path.write_text(
        json.dumps(
            {
                "best_model_type": "RandomForest",
                "cv_r2_mean": None,
                "cv_r2_std": None,
                "hyperparameters": {},
                "null_result": False,
                "timestamp": "2026-10-15T12:11:42.364334Z",
                "validation_r2": None,
                "validation_rmse": None,
            },
            indent=2,
        )
    )
    return models


def test_evaluate_creates_artifacts(minimal_dataset, dummy_models):
    """Run the evaluate script and verify output artifacts."""
    # Import the script as a module and invoke its main()
    import importlib.util
    import sys

    script_path = Path(__file__).parents[1] / "code" / "evaluate.py"
    spec = importlib.util.spec_from_file_location("evaluate", script_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["evaluate"] = module
    spec.loader.exec_module(module)

    # Execute the main function
    module.main()

    # Check that three artifact JSONs exist
    for model_name in ["randomforest", "gradientboosting", "linearregression"]:
        artifact_path = paths.models(f"{model_name}_artifact.json")
        assert artifact_path.is_file(), f"{artifact_path} missing"
        data = json.loads(artifact_path.read_text())
        # Basic schema checks
        assert data["model_type"] in ["RandomForest", "GradientBoosting", "LinearRegression"]
        for metric in ["test_r2", "test_rmse", "test_mae"]:
            assert isinstance(data[metric], float)

    # Verify that best_model.json was updated with test metrics
    best_path = paths.models("best_model.json")
    best_data = json.loads(best_path.read_text())
    for field in ["final_r2", "final_rmse", "final_mae"]:
        assert isinstance(best_data[field], float)