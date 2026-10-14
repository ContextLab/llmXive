"""
Unit test for the ``src.data.preprocess`` module.

The test uses a tiny synthetic dataset placed under ``tests/data/sample``.
The sample consists of a single 1‑pixel white PNG image and a matching
annotation JSON file.  Because the image is trivial, OCR returns an empty
string – this is acceptable for the purpose of the test.

The test checks that:
  * The script runs without raising.
  * The resulting Parquet file exists.
  * The record complies with the JSON schema.
"""

import pathlib
import json
import shutil

import pandas as pd
import pytest
from jsonschema import Draft7Validator

from src.data import preprocess

SAMPLE_ROOT = pathlib.Path(__file__).parent / "data" / "sample"
OUTPUT_PARQUET = pathlib.Path("data/processed/test_document_pairs.parquet")

@pytest.fixture(scope="module")
def prepare_sample(tmp_path_factory):
    # Copy the tiny sample into a temporary directory to avoid polluting the repo.
    tmp_dir = tmp_path_factory.mktemp("sample_input")
    shutil.copytree(SAMPLE_ROOT, tmp_dir, dirs_exist_ok=True)
    return tmp_dir

def test_preprocess_runs_and_validates(prepare_sample):
    schema_path = pathlib.Path(
        "specs/001-llmxive-follow-up-extending-scalable-vis/contracts/documentpair.schema.yaml"
    )
    # Ensure any previous output is removed.
    if OUTPUT_PARQUET.is_file():
        OUTPUT_PARQUET.unlink()

    # Run the preprocessing function.
    preprocess.preprocess_dataset(
        input_dir=prepare_sample,
        output_parquet=OUTPUT_PARQUET,
        schema_path=schema_path,
    )

    # Verify Parquet file was created.
    assert OUTPUT_PARQUET.is_file(), "Parquet output was not created"

    # Load the Parquet and validate against the schema.
    df = pd.read_parquet(OUTPUT_PARQUET, engine="pyarrow")
    assert not df.empty, "Resulting DataFrame is empty"

    schema = json.loads(schema_path.read_text())
    validator = Draft7Validator(schema)

    for _, row in df.iterrows():
        record = row.to_dict()
        # ``visual_latent`` may be missing – remove it if present for validation.
        record.pop("visual_latent", None)
        validator.validate(record)