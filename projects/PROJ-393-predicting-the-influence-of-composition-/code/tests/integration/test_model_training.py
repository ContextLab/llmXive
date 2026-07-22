"""
Integration test for the model training pipeline (T030).
Verifies k-fold cross-validation, model training, and metric generation.
"""
import pytest
import json
import os
import sys
from pathlib import Path
import tempfile
import shutil

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from src.models.training_pipeline import run_training_pipeline
from src.features.feature_engineering_pipeline import run_feature_engineering_pipeline
from src.preprocessing.preprocess_pipeline import run_preprocessing_pipeline
from src.ingestion.ingest_pipeline import run_ingestion_pipeline
from src.utils.logging_config import setup_logging


class TestModelTrainingIntegration:
    """Integration tests for the full model training pipeline."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Set up temporary directories and clean up after tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir) / "data"
        self.data_dir.mkdir(parents=True)
        (self.data_dir / "raw").mkdir()
        (self.data_dir / "processed").mkdir()
        (self.data_dir / "models").mkdir()
        
        # Create necessary directories for logging
        (Path(self.temp_dir) / "logs").mkdir()
        
        # Save original environment
        self.original_data_dir = os.environ.get("DATA_DIR")
        os.environ["DATA_DIR"] = str(self.data_dir)
        
        yield
        
        # Cleanup
        if self.original_data_dir:
            os.environ["DATA_DIR"] = self.original_data_dir
        else:
            os.environ.pop("DATA_DIR", None)
        shutil.rmtree(self.temp_dir)

    def _create_test_data(self):
        """Create minimal test data for the pipeline."""
        # Create a minimal manual_curated.csv
        manual_csv = self.data_dir / "raw" / "manual_curated.csv"
        manual_csv.write_text(
            "composition,coercivity_oe,saturation_magnetization_emu_g,source_type,synthesis_method\n"
            "Co2MnGa,50,80,Manual,Arc Melting\n"
            "Ni2MnSn,100,90,Manual,Sputtering\n"
            "Co2FeAl,30,70,Manual,Evaporation\n"
            "FeMnAl,200,95,Manual,Arc Melting\n"
            "Co2MnSi,40,85,Manual,Sputtering\n"
        )
        
        # Create elemental_properties.csv
        elem_csv = self.data_dir / "raw" / "elemental_properties.csv"
        elem_csv.write_text(
            "element,electronegativity,atomic_radii,valence_electrons,source_reference\n"
            "Co,1.88,125,9,Pyykko 1988\n"
            "Mn,1.55,127,7,Pyykko 1988\n"
            "Ga,1.81,135,3,Pyykko 1988\n"
            "Ni,1.91,124,10,Pyykko 1988\n"
            "Sn,1.96,145,4,Pyykko 1988\n"
            "Fe,1.83,126,8,Pyykko 1988\n"
            "Al,1.61,143,3,Pyykko 1988\n"
            "Si,1.90,111,4,Pyykko 1988\n"
            "Mg,1.31,160,2,Pyykko 1988\n"
            "Cu,1.90,128,11,Pyykko 1988\n"
        )

    def test_full_training_pipeline_execution(self):
        """
        Test that the full training pipeline executes successfully:
        1. Ingests data (using manual fallback)
        2. Preprocesses data
        3. Engineers features
        4. Trains models with k-fold cross-validation
        5. Generates model_metrics.json with valid R² and MAE values
        """
        # Setup test data
        self._create_test_data()
        
        # Setup logging
        setup_logging(level="INFO")
        
        # Step 1: Run ingestion pipeline
        # Note: This will use manual_curated.csv as fallback
        try:
            run_ingestion_pipeline()
        except Exception as e:
            # If ingestion fails due to missing external sources, 
            # ensure manual data is used
            pytest.skip(f"Ingestion skipped due to external source issues: {e}")
        
        # Step 2: Run preprocessing pipeline
        # This should produce data/processed/alloys_raw.csv
        try:
            run_preprocessing_pipeline()
        except Exception as e:
            pytest.fail(f"Preprocessing pipeline failed: {e}")
        
        # Verify alloys_raw.csv was created
        raw_csv = self.data_dir / "processed" / "alloys_raw.csv"
        assert raw_csv.exists(), "alloys_raw.csv was not created by preprocessing pipeline"
        
        # Step 3: Run feature engineering pipeline
        # This should produce data/processed/alloys_features.csv
        try:
            run_feature_engineering_pipeline()
        except Exception as e:
            pytest.fail(f"Feature engineering pipeline failed: {e}")
        
        # Verify alloys_features.csv was created
        features_csv = self.data_dir / "processed" / "alloys_features.csv"
        assert features_csv.exists(), "alloys_features.csv was not created by feature engineering pipeline"
        
        # Step 4: Run training pipeline
        # This should train models and save them to code/models/
        # and generate data/processed/model_metrics.json
        try:
            run_training_pipeline()
        except Exception as e:
            pytest.fail(f"Training pipeline failed: {e}")
        
        # Step 5: Verify model_metrics.json exists and contains valid data
        metrics_file = self.data_dir / "processed" / "model_metrics.json"
        assert metrics_file.exists(), "model_metrics.json was not created by training pipeline"
        
        # Load and validate metrics
        with open(metrics_file, 'r') as f:
            metrics = json.load(f)
        
        # Check that both Linear and RF models have metrics
        assert "LinearRegression" in metrics, "LinearRegression metrics not found"
        assert "RandomForest" in metrics, "RandomForest metrics not found"
        
        # Validate LinearRegression metrics
        linear_metrics = metrics["LinearRegression"]
        assert "r2" in linear_metrics, "R² metric missing for LinearRegression"
        assert "mae" in linear_metrics, "MAE metric missing for LinearRegression"
        assert isinstance(linear_metrics["r2"], (int, float)), "R² must be numeric"
        assert isinstance(linear_metrics["mae"], (int, float)), "MAE must be numeric"
        
        # Validate RandomForest metrics
        rf_metrics = metrics["RandomForest"]
        assert "r2" in rf_metrics, "R² metric missing for RandomForest"
        assert "mae" in rf_metrics, "MAE metric missing for RandomForest"
        assert isinstance(rf_metrics["r2"], (int, float)), "R² must be numeric"
        assert isinstance(rf_metrics["mae"], (int, float)), "MAE must be numeric"
        
        # Check that k-fold cross-validation was performed (metrics should reflect this)
        # The presence of 'cv_score' or similar indicates CV was run
        assert "cv_score" in linear_metrics or "cv_scores" in linear_metrics, \
            "Cross-validation score not found - CV may not have been performed"
        assert "cv_score" in rf_metrics or "cv_scores" in rf_metrics, \
            "Cross-validation score not found - CV may not have been performed"

    def test_models_are_saved(self):
        """
        Test that trained models are saved to code/models/ directory.
        """
        self._create_test_data()
        setup_logging(level="INFO")
        
        # Run the full pipeline
        try:
            run_ingestion_pipeline()
            run_preprocessing_pipeline()
            run_feature_engineering_pipeline()
            run_training_pipeline()
        except Exception as e:
            pytest.fail(f"Pipeline execution failed: {e}")
        
        # Check that model files exist
        models_dir = Path(self.temp_dir) / "models"
        if not models_dir.exists():
            models_dir = project_root / "code" / "models"
        
        # Look for saved model files (pickle or joblib)
        model_files = list(models_dir.glob("*.pkl")) + list(models_dir.glob("*.joblib"))
        assert len(model_files) > 0, "No model files were saved to code/models/"
        
        # Verify at least one Linear and one RF model
        model_names = [f.name for f in model_files]
        linear_models = [n for n in model_names if "linear" in n.lower()]
        rf_models = [n for n in model_names if "random_forest" in n.lower() or "rf" in n.lower()]
        
        assert len(linear_models) > 0, "Linear model was not saved"
        assert len(rf_models) > 0, "RandomForest model was not saved"

    def test_kfold_cross_validation_is_performed(self):
        """
        Test that k-fold cross-validation is actually performed during training.
        This is verified by checking the training logs or metrics structure.
        """
        self._create_test_data()
        setup_logging(level="DEBUG")  # Ensure logs are verbose enough
        
        # Run pipeline
        try:
            run_ingestion_pipeline()
            run_preprocessing_pipeline()
            run_feature_engineering_pipeline()
            run_training_pipeline()
        except Exception as e:
            pytest.fail(f"Pipeline execution failed: {e}")
        
        # The training pipeline should have performed CV
        # This is implicitly verified by the presence of cv_score in metrics
        metrics_file = self.data_dir / "processed" / "model_metrics.json"
        with open(metrics_file, 'r') as f:
            metrics = json.load(f)
        
        # Check for CV indicators in both models
        for model_name in ["LinearRegression", "RandomForest"]:
            model_metrics = metrics[model_name]
            # Either a single cv_score or a list of cv_scores should exist
            has_cv = "cv_score" in model_metrics or "cv_scores" in model_metrics
            assert has_cv, f"Cross-validation not performed for {model_name}"