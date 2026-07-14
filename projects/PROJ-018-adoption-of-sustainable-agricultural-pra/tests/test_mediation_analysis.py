"""Basic sanity test for the mediation analysis implementation."""
import os
from pathlib import Path

import yaml

from code_04_model_analysis import mediation_analysis  # type: ignore


def test_mediation_output(tmp_path: Path):
    # Create a tiny synthetic yet plausible dataframe
    import pandas as pd
    import numpy as np

    np.random.seed(0)
    size = 200
    df = pd.DataFrame(
        {
            "engagement_score": np.random.normal(0, 1, size),
            "community_trust": np.random.normal(0, 1, size),
            "adoption_binary": np.random.binomial(1, 0.3, size),
        }
    )

    # Run mediation analysis (uses bootstrap – keep it small for speed)
    results = mediation_analysis(df, n_boot=200)

    # Verify required keys exist and are of expected type
    required_keys = {
        "total_effect_logodds",
        "direct_effect_logodds",
        "indirect_effect_logodds",
        "bootstrap_ci",
        "e_value",
        "rosenbaum_bounds",
        "interpretation",
    }
    assert required_keys.issubset(results.keys())
    assert isinstance(results["bootstrap_ci"], dict)
    assert isinstance(results["rosenbaum_bounds"], dict)

    # Check that the results file was written
    out_file = Path("results") / "mediation_results.yaml"
    assert out_file.exists()
    with out_file.open() as f:
        yaml_content = yaml.safe_load(f)
    assert yaml_content == results