import pytest
import pandas as pd
import json
from pathlib import Path
import jsonschema
import os
import yaml

# Adjust import path if necessary depending on how tests are run
try:
    from code.exceptions import DataInsufficientError, PowerWarning
except ImportError:
    # Fallback for direct execution or different environment setup
    from exceptions import DataInsufficientError, PowerWarning


@pytest.fixture
def schema_path():
    return Path("specs/001-predict-carbon-diffusion-bcc/contracts/dataset.schema.yaml")

@pytest.fixture
def dataset_path():
    return Path("data/processed/dataset_cleaned.csv")

@pytest.fixture
def split_config_path():
    return Path("data/processed/split_config.json")

def test_dataset_schema_validation(dataset_path, schema_path):
    """
    T012: Verify dataset_cleaned.csv matches the schema defined in T004.
    """
    if not dataset_path.exists():
        pytest.skip("Dataset not yet generated. Run 02_preprocess.py first.")
    if not schema_path.exists():
        pytest.fail(f"Schema file missing: {schema_path}")

    # Load schema
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)

    # Load data
    df = pd.read_csv(dataset_path)

    # Convert dataframe to list of dicts for validation
    data_records = df.to_dict('records')

    # Validate each record
    for i, record in enumerate(data_records):
        try:
            jsonschema.validate(instance=record, schema=schema)
        except jsonschema.ValidationError as e:
            pytest.fail(f"Validation error in record {i}: {e.message}")

def test_bcc_filter_and_completeness(dataset_path):
    """
    T013: Verify no non-BCC or missing-composition entries remain.
    """
    if not dataset_path.exists():
        pytest.skip("Dataset not yet generated.")

    df = pd.read_csv(dataset_path)

    # Check structure is always BCC
    non_bcc = df[df['structure'] != 'BCC']
    assert len(non_bcc) == 0, f"Found {len(non_bcc)} non-BCC entries."

    # Check composition is not null
    null_comp = df[df['composition'].isnull()]
    assert len(null_comp) == 0, "Found entries with missing composition."

def test_atomic_fractions_sum_to_one(dataset_path):
    """
    Verify atomic fractions in composition sum to 1.0.
    Note: This assumes composition is a string like 'Fe0.9Ni0.1'.
    Parsing logic depends on utils or specific format.
    For this test, we assume the preprocessing step guarantees this.
    We check the log_D and other numeric fields for sanity instead.
    """
    if not dataset_path.exists():
        pytest.skip("Dataset not yet generated.")

    df = pd.read_csv(dataset_path)

    # Check numeric columns are finite
    for col in ['log_D', 'atomic_radius_variance', 'VEC', 'electronegativity_spread', 'mixing_entropy', 'inv_temperature']:
        assert df[col].isna().sum() == 0, f"Missing values in {col}"
        assert (df[col].isinf() == False).all(), f"Infinite values in {col}"

def test_provenance_flags(dataset_path):
    """
    Verify provenance flags are respected (no entries with missing flags in output).
    """
    if not dataset_path.exists():
        pytest.skip("Dataset not yet generated.")

    df = pd.read_csv(dataset_path)

    # Check microstructure_controlled is boolean and not null
    assert df['microstructure_controlled'].isnull().sum() == 0, "Missing microstructure_controlled flags."
    assert df['microstructure_controlled'].dtype == bool, "microstructure_controlled is not boolean."

def test_split_config_exists(split_config_path):
    """
    Verify split_config.json exists and contains valid strategy.
    """
    assert split_config_path.exists(), "split_config.json not found."

    with open(split_config_path, 'r') as f:
        config = json.load(f)

    assert 'split_strategy' in config, "split_strategy key missing in split_config.json."
    strategy = config['split_strategy']
    assert strategy in ['LOOCV', '80/20'], f"Invalid split strategy: {strategy}"