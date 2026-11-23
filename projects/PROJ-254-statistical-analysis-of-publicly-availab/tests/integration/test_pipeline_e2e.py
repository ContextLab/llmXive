import os
import sys
import unittest
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.ingest import ingest_mpd
from code.embeddings import train_global_word2vec, aggregate_yearly_embeddings
from code.regression import fit_linear_regression

class TestPipelineE2E(unittest.TestCase):
    def test_e2e_pipeline(self):
        # Define paths for data and outputs
        raw_data_dir = Path("data/raw")
        derived_data_dir = Path("data/derived")
        yearly_embeddings_dir = Path("yearly_embeddings")

        # Ensure output directories exist (or create them if they don't)
        if not derived_data_dir.exists():
            derived_data_dir.mkdir(parents=True)
        if not yearly_embeddings_dir.exists():
            yearly_embeddings_dir.mkdir(parents=True)

        # Ingest MPD data (using a small sample for testing)
        try:
            ingest_mpd()  # No arguments needed, uses default parameters
        except Exception as e:
            self.fail(f"Ingestion failed: {e}")

        # Train global Word2Vec model and aggregate yearly embeddings
        try:
            train_global_word2vec()
            aggregate_yearly_embeddings()
        except Exception as e:
            self.fail(f"Embedding training/aggregation failed: {e}")

        # Fit linear regression model
        try:
            fit_linear_regression()
        except Exception as e:
            self.fail(f"Regression fitting failed: {e}")

        # Verify output files exist (basic check)
        self.assertTrue(Path("data/derived/metadata_mpd.parquet").exists())
        self.assertTrue(yearly_embeddings_dir.glob("*").__len__() > 0)
        self.assertTrue(Path("data/derived/yearly_similarity.csv").exists())
        self.assertTrue(Path("data/derived/regression_results.json").exists())
