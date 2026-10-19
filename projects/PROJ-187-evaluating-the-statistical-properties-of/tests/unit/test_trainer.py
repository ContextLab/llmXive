"""Unit tests for SDV trainer and synthesis.

Verifies that CTGAN can fit on a small dataset and produce a synthetic
CSV and JSON side-car with correct properties.
"""
import json
import pandas as pd
import pytest
from pathlib import Path
from llmxive_toolkit import paths
from src.models.synthesize import generate_and_save

@pytest.fixture
def sample_data():
    """Create a small, simple dataframe for fast testing."""
    return pd.DataFrame({
        "age": [25, 30, 45, 50, 22, 35, 40, 60, 28, 33],
        "workclass": ["Private", "Private", "Self-emp", "Private", "Private", "Gov", "Private", "Private", "Self-emp", "Private"],
        "education": ["Bachelors", "HS-grad", "Masters", "Bachelors", "HS-grad", "Bachelors", "Masters", "HS-grad", "Bachelors", "HS-grad"],
        "income": [0, 0, 1, 1, 0, 1, 1, 0, 0, 0]
    })

def test_ctgan_fit_and_save(sample_data):
    """Verify CTGAN fit for 2 epochs produces correct artifacts (T003)."""
    dataset_name = "test_adult"
    model_name = "CTGAN"
    seed = 42
    
    # Run synthesis with very few epochs for speed.
    csv_path = generate_and_save(
        dataset_name=dataset_name,
        model_name=model_name,
        seed=seed,
        train_df=sample_data,
        max_epochs=2
    )
    
    # Check CSV existence and row count.
    assert csv_path.is_file()
    synth_df = pd.read_csv(csv_path)
    assert len(synth_df) == len(sample_data)
    assert list(synth_df.columns) == list(sample_data.columns)
    
    # Check JSON side-car existence and fields.
    json_path = csv_path.with_suffix(".json")
    assert json_path.is_file()
    with open(json_path, "r") as f:
        meta = json.load(f)
    
    assert meta["dataset"] == dataset_name
    assert meta["model"] == model_name
    assert meta["seed"] == seed
    assert meta["status"] == "success"
    assert meta["row_count"] == len(sample_data)

def test_trainer_failure_handling(sample_data):
    """Verify that an unsupported model name raises ValueError."""
    with pytest.raises(ValueError):
        generate_and_save(
            dataset_name="test",
            model_name="InvalidModel", # type: ignore
            seed=42,
            train_df=sample_data
        )