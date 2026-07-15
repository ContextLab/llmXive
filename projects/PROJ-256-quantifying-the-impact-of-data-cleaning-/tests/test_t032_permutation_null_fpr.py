import json
import os
from pathlib import Path

from t032_permutation_null_fpr import generate_null_fpr_metrics

def test_generate_null_fpr_metrics_creates_file(tmp_path):
    # Use a temporary directory for raw data to avoid side‑effects.
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    # Create a tiny synthetic CSV (real data not required for the test logic)
    csv_path = raw_dir / "sample.csv"
    csv_path.write_text(
        "target,feat1,feat2\n"
        "1,0.1,0.2\n"
        "0,0.3,0.4\n"
        "1,0.5,0.6\n"
    )
    output_file = tmp_path / "null_fpr.json"

    result = generate_null_fpr_metrics(
        raw_dir=str(raw_dir),
        outcome="target",
        predictors=["feat1", "feat2"],
        n_permutations=200,
        output_file=str(output_file),
    )

    # Verify the function returns a dictionary with expected keys
    assert isinstance(result, dict)
    assert set(result.keys()) == {"total_permutations", "false_positive_rate", "p_value_threshold"}

    # Verify the output file exists and contains valid JSON
    assert output_file.is_file()
    data = json.loads(output_file.read_text())
    assert data["total_permutations"] == 200
    assert 0.0 <= data["false_positive_rate"] <= 1.0
    assert data["p_value_threshold"] == 0.05

    # Clean‑up is handled by the pytest tmp_path fixture.