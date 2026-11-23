import json
from pathlib import Path

import pytest
from llmxive_toolkit import paths

# Load the schema to ensure the analysis output conforms.
schema_path = Path(__file__).parents[2] / "specs" / "001-llmxive-cognitive-load" / "contracts" / "analysis_result.schema.yaml"
with schema_path.open("r", encoding="utf-8") as f:
    schema = json.load(f)

def test_analysis_output_schema():
    results_path = paths.outputs("analysis_results.jsonl")
    assert results_path.is_file(), "Analysis results file not found."

    with results_path.open("r", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            # Simple schema validation – will raise if invalid.
            jsonschema.validate(instance=record, schema=schema)

def test_wilcoxon_detects_known_difference():
    """
    Synthetic sanity‑check: create a tiny dataset where the structured
    interface is consistently faster. The analysis script should report
    a significant (p < 0.05) result for ``time_to_success_ms``.
    """
    import pandas as pd
    from src.analysis.wilcoxon_analysis import _analyze_metric

    # Construct a minimal wide‑format DataFrame
    data = {
        "time_to_success_ms_structured": [100, 120, 110],
        "time_to_success_ms_chat": [200, 220, 210],
        "iteration_count_structured": [2, 2, 2],
        "iteration_count_chat": [3, 3, 3],
        "subjective_load_structured": [30, 35, 32],
        "subjective_load_chat": [60, 65, 62],
    }
    df_wide = pd.DataFrame(data, index=["p1", "p2", "p3"])

    res = _analyze_metric(df_wide, "time_to_success_ms")
    assert res["p_value_corrected"] < 0.05, "Expected a significant difference."
    assert res["test_used"] in {"wilcoxon", "paired_t"}