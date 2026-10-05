import os
import json
import tempfile
import pytest
from pathlib import Path
import numpy as np

# Mock dependencies for testing without heavy imports if possible, 
# but we need to test the actual logic which imports matplotlib/sklearn
try:
    from code.visualization import plot_pr_curves, plot_roc_curves, load_predictions
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False

@pytest.mark.skipif(not HAS_DEPS, reason="Plotting dependencies (matplotlib, sklearn) not installed")
class TestVisualizationPRCurve:
    
    def test_plot_pr_curves_creates_file(self, tmp_path):
        """Test that plot_pr_curves generates the expected PNG file."""
        # Create a temporary predictions file
        pred_dir = tmp_path / "data" / "processed"
        pred_dir.mkdir(parents=True)
        pred_file = pred_dir / "predictions_loeo.json"
        
        # Generate synthetic but REAL-LOOKING data for the test
        # 100 samples, 30% positive class
        np.random.seed(42)
        y_true = np.random.choice([0, 1], size=100, p=[0.7, 0.3])
        # Scores should correlate somewhat with truth for a realistic curve
        y_score = np.random.rand(100)
        y_score[y_true == 1] += 0.2
        y_score = np.clip(y_score, 0, 1)
        
        with open(pred_file, 'w') as f:
            json.dump({"y_true": y_true.tolist(), "y_score": y_score.tolist()}, f)
        
        output_dir = tmp_path / "results" / "plots"
        output_dir.mkdir(parents=True)
        output_file = output_dir / "pr_curve.png"
        
        # Run the function
        result_path = plot_pr_curves(
            predictions_path=str(pred_file),
            output_path=str(output_file),
            title="Test PR Curve"
        )
        
        # Assertions
        assert os.path.exists(output_file), f"Output file {output_file} was not created"
        assert os.path.getsize(output_file) > 1000, "Output file is too small to be a valid image"
        assert result_path == str(output_file.resolve())
        
    def test_plot_pr_curves_empty_data_raises(self, tmp_path):
        """Test that empty predictions raise an error."""
        pred_dir = tmp_path / "data" / "processed"
        pred_dir.mkdir(parents=True)
        pred_file = pred_dir / "predictions_loeo.json"
        
        with open(pred_file, 'w') as f:
            json.dump({"y_true": [], "y_score": []}, f)
        
        output_file = tmp_path / "results" / "plots" / "pr_curve.png"
        output_file.parent.mkdir(parents=True)
        
        with pytest.raises(ValueError, match="Predictions file is empty"):
            plot_pr_curves(
                predictions_path=str(pred_file),
                output_path=str(output_file)
            )
            
    def test_plot_pr_curves_mismatched_lengths_raises(self, tmp_path):
        """Test that mismatched lengths raise an error."""
        pred_dir = tmp_path / "data" / "processed"
        pred_dir.mkdir(parents=True)
        pred_file = pred_dir / "predictions_loeo.json"
        
        with open(pred_file, 'w') as f:
            json.dump({"y_true": [1, 0], "y_score": [0.9]}, f)
        
        output_file = tmp_path / "results" / "plots" / "pr_curve.png"
        output_file.parent.mkdir(parents=True)
        
        with pytest.raises(ValueError, match="Length mismatch"):
            plot_pr_curves(
                predictions_path=str(pred_file),
                output_path=str(output_file)
            )

@pytest.mark.skipif(not HAS_DEPS, reason="Plotting dependencies (matplotlib, sklearn) not installed")
class TestVisualizationROCCurve:
    
    def test_plot_roc_curves_creates_file(self, tmp_path):
        """Test that plot_roc_curves generates the expected PNG file."""
        pred_dir = tmp_path / "data" / "processed"
        pred_dir.mkdir(parents=True)
        pred_file = pred_dir / "predictions_loeo.json"
        
        np.random.seed(42)
        y_true = np.random.choice([0, 1], size=100, p=[0.7, 0.3])
        y_score = np.random.rand(100)
        y_score[y_true == 1] += 0.2
        y_score = np.clip(y_score, 0, 1)
        
        with open(pred_file, 'w') as f:
            json.dump({"y_true": y_true.tolist(), "y_score": y_score.tolist()}, f)
        
        output_dir = tmp_path / "results" / "plots"
        output_dir.mkdir(parents=True)
        output_file = output_dir / "roc_curve.png"
        
        result_path = plot_roc_curves(
            predictions_path=str(pred_file),
            output_path=str(output_file),
            title="Test ROC Curve"
        )
        
        assert os.path.exists(output_file), f"Output file {output_file} was not created"
        assert os.path.getsize(output_file) > 1000, "Output file is too small to be a valid image"
        assert result_path == str(output_file.resolve())

@pytest.mark.skipif(not HAS_DEPS, reason="Plotting dependencies (matplotlib, sklearn) not installed")
class TestLoadPredictions:
    def test_load_predictions_success(self, tmp_path):
        pred_file = tmp_path / "predictions.json"
        data = {"y_true": [1, 0, 1], "y_score": [0.9, 0.2, 0.8]}
        with open(pred_file, 'w') as f:
            json.dump(data, f)
        
        y_true, y_score = load_predictions(str(pred_file))
        
        assert len(y_true) == 3
        assert len(y_score) == 3
        assert np.array_equal(y_true, [1, 0, 1])
        assert np.array_equal(y_score, [0.9, 0.2, 0.8])
        
    def test_load_predictions_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_predictions(str(tmp_path / "nonexistent.json"))