"""Schema validation tests for the project.

The tests ensure that the YAML files produced by the pipeline conform to
the expected structure.  Only a minimal subset is required for the current
task – the presence of the keys written by ``code/03_engineer_features.py``
is verified.
"""
import yaml
from pathlib import Path

def test_validity_metrics_schema():
    """Check that ``results/validity_metrics.yaml`` contains the required sections."""
    metrics_path = Path("results") / "validity_metrics.yaml"
    assert metrics_path.is_file(), "Validity metrics file was not created."

    with metrics_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Required top‑level keys
    required_keys = {"cronbach_alpha", "efa", "convergent_validity"}
    assert required_keys.issubset(data.keys()), "Missing top‑level keys in validity metrics."

    # EFA sub‑keys
    assert "n_factors_retained" in data["efa"], "EFA must report number of retained factors."
    assert "loadings" in data["efa"], "EFA must include factor loadings."

    # Convergent validity sub‑keys
    cv = data["convergent_validity"]
    assert "correlation" in cv and "status" in cv, "Convergent validity section incomplete."