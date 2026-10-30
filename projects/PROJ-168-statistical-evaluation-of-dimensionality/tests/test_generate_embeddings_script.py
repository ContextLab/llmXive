"""
Integration test for the generate_embeddings script.

This test runs the script's main entry point and checks that for each
dataset listed in ``data/manifest.json`` an embedding CSV file is created
for PCA, t‑SNE and UMAP, and that the files contain the expected number
of columns and rows (no NaNs).
"""
import os
import json
import pandas as pd
import pytest
from pathlib import Path
from llmxive_toolkit import paths

# Import the script as a module to call its main()
import importlib.util

script_path = Path(__file__).parents[1] / "code" / "generate_embeddings.py"
spec = importlib.util.spec_from_file_location("generate_embeddings", script_path)
generate_embeddings = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generate_embeddings)

@pytest.fixture(scope="module")
def manifest():
    manifest_path = paths.data("manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)

def test_embeddings_created(manifest):
    # Run the script
    exit_code = generate_embeddings.main()
    assert exit_code == 0, "Script should exit with code 0"

    for entry in manifest:
        if entry.get("status") != "Available":
            continue
        ds = entry["dataset_id"]
        for method in ["PCA", "tSNE", "UMAP"]:
            emb_path = paths.data("embeddings", f"{ds}_{method}.csv")
            assert emb_path.is_file(), f"{emb_path} should exist"

            df = pd.read_csv(emb_path)
            # Check cell_id column exists
            assert "cell_id" in df.columns

            # Check column counts
            if method == "PCA":
                # cell_id + 30 PCs
                assert df.shape[1] == 31
            else:
                # cell_id + 2 dimensions
                assert df.shape[1] == 3

            # No NaNs
            assert not df.isnull().any().any(), f"NaNs found in {emb_path}"