"""
Integration test for the static model training pipeline (T019).
Verifies that the training script runs end-to-end and produces valid artifacts.
"""
import os
import sys
import tempfile
import shutil
import pickle
import json
import pandas as pd
import numpy as np
import pytest

# Add project root to path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, ROOT_DIR)

from models.train_static import run_training_pipeline, load_data, preprocess_data

class TestStaticTrainingPipeline:
    """Integration tests for T019."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup a temporary directory for test artifacts."""
        self.temp_dir = tempfile.mkdtemp()
        self.input_csv = os.path.join(self.temp_dir, "merged_dataset.csv")
        self.output_dir = os.path.join(self.temp_dir, "models", "seeds")
        self.anomalies_csv = os.path.join(self.temp_dir, "anomalies.csv")
        
        # Create a dummy anomalies file to test filtering
        pd.DataFrame({"doc_id": ["doc_001"]}).to_csv(self.anomalies_csv, index=False)
        
        # Create a dummy merged dataset with realistic-ish data
        n_samples = 100
        data = {
            "doc_id": [f"doc_{i:03d}" for i in range(n_samples)],
            "text": ["sample text"] * n_samples,
            "rtpurbo_label": np.random.randint(0, 2, n_samples),
            "entropy": np.random.rand(n_samples) * 10,
            "position": np.random.rand(n_samples) * 100,
            "kenlm_perplexity": np.random.rand(n_samples) * 50,
            "is_ambiguous": np.random.randint(0, 2, n_samples)
        }
        df = pd.DataFrame(data)
        # Ensure the anomaly doc is in the dataset so it gets filtered
        df.loc[0, "doc_id"] = "doc_001" 
        df.to_csv(self.input_csv, index=False)
        
        yield
        
        # Teardown
        shutil.rmtree(self.temp_dir)

    def test_run_pipeline_produces_models(self, setup_and_teardown):
        """Test that the pipeline runs and saves model files."""
        # Run the pipeline
        summary = run_training_pipeline(
            input_path=self.input_csv,
            output_dir=self.output_dir,
            n_seeds=2,  # Small number for speed
            test_size=0.2
        )
        
        # Assertions
        assert os.path.exists(self.output_dir), "Output directory was not created."
        assert summary["n_samples"] == 99, "Anomaly filtering should have removed 1 row (100-1=99)."
        assert len(summary["models_trained"]) == 4, "Should train 2 models (LR, DT) x 2 seeds."
        
        # Check for summary file
        summary_path = os.path.join(self.output_dir, "training_summary.json")
        assert os.path.exists(summary_path), "Summary JSON not found."
        
        # Check model files
        model_files = [f for f in os.listdir(self.output_dir) if f.endswith(".pkl")]
        assert len(model_files) == 4, f"Expected 4 model files, found {len(model_files)}"
        
        # Verify one model can be loaded
        sample_model_path = os.path.join(self.output_dir, model_files[0])
        with open(sample_model_path, 'rb') as f:
            model = pickle.load(f)
        assert model is not None

    def test_load_data_filters_anomalies(self, setup_and_teardown):
        """Test that load_data correctly filters out anomalous documents."""
        df = load_data(self.input_csv)
        # We created 100 rows, 1 is anomalous (doc_001)
        assert len(df) == 99, "Anomaly filtering failed."
        assert "doc_001" not in df["doc_id"].values, "Anomalous doc_id still present."

    def test_preprocess_data_format(self, setup_and_teardown):
        """Test that preprocess_data returns correct shapes and types."""
        df = load_data(self.input_csv)
        X, y, feature_names = preprocess_data(df)
        
        assert X.shape[0] == len(df), "X rows mismatch."
        assert y.shape[0] == len(df), "y rows mismatch."
        assert isinstance(X, np.ndarray), "X is not a numpy array."
        assert isinstance(y, np.ndarray), "y is not a numpy array."
        assert len(feature_names) > 0, "No feature names returned."
        assert "entropy" in feature_names, "Entropy feature missing."