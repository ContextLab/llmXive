"""
Integration tests for the full llmXive pipeline.
"""
import pytest
import os
import json
from pathlib import Path
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent.parent
import sys
sys.path.insert(0, str(project_root / "code"))

from data.loader import load_all_datasets
from data.processor import process_dataset
from narrative.baseline import generate_baseline_narrative
from config import get_config

@pytest.mark.integration
def test_full_pipeline_sample(temp_dir):
    """
    Integration test: Run the full pipeline on a small sample dataset.
    """
    # Create a small sample CSV with known correlations
    sample_data = temp_dir / "sample.csv"
    n = 100
    x = range(n)
    y = [xi * 2 + 1 for xi in x]  # Perfect linear correlation
    df_sample = pd.DataFrame({
        'id': x,
        'variable_x': x,
        'variable_y': y
    })
    df_sample.to_csv(sample_data, index=False)

    # 1. Load
    datasets = load_all_datasets(
        raw_dir=str(temp_dir),
        processed_dir=str(temp_dir / "processed"),
        output_dir=str(temp_dir / "output"),
        dataset_files=["sample.csv"]
    )

    # 2. Process
    processed = process_dataset(
        datasets["sample"],
        dataset_name="sample",
        output_dir=str(temp_dir / "output")
    )

    # 3. Generate Baseline Narrative
    narrative = generate_baseline_narrative(
        processed,
        dataset_name="sample",
        output_dir=str(temp_dir / "output")
    )

    assert narrative is not None
    assert "primary_narrative" in narrative
    assert "r_value" in narrative
    assert "p_value" in narrative

    # Verify the correlation is detected correctly (r should be ~1.0)
    assert abs(narrative["r_value"]) > 0.99
    assert narrative["p_value"] < 0.05

    # Verify output files exist
    narrative_file = Path(temp_dir / "output" / "baseline_narrative_sample.json")
    assert narrative_file.exists()
