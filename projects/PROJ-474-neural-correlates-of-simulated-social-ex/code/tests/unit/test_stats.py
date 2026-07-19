import pytest
import numpy as np
from src.stats import run_statistical_analysis, generate_sensitivity_curve
from src.exceptions import InsufficientDataError

class TestPermutationLogic:
    def test_shift_detection(self):
        # Synthetic data with known shift
        np.random.seed(42)
        inclusion = np.random.normal(0, 1, 50)
        exclusion = np.random.normal(0.5, 1, 50) # Shift of 0.5
        
        result = run_statistical_analysis(inclusion.tolist(), exclusion.tolist(), n_permutations=1000, seed=42)
        
        assert "p_value" in result
        assert "effect_size_cohen_d" in result
        # With a shift of 0.5 and n=50, p-value should be significant
        assert result["p_value"] < 0.05, "Should detect the shift"

class TestSensitivityCurve:
    def test_curve_generation(self, tmp_path):
        # Mock config
        config = {
            "base_path": str(tmp_path),
            "atlas": {"path": "dummy"}
        }
        
        # Create a fake subject_qc_list.json
        qc_data = [
            {"subject_id": "sub-01", "retained": True},
            {"subject_id": "sub-02", "retained": True}
        ]
        qc_path = tmp_path / "data" / "processed" / "subject_qc_list.json"
        qc_path.parent.mkdir(parents=True)
        with open(qc_path, "w") as f:
            import json
            json.dump(qc_data, f)
        
        # Create a fake connectivity_metrics.json
        metrics_data = [
            {"subject_id": "sub-01", "inclusion_mac": 0.5, "exclusion_mac": 0.6},
            {"subject_id": "sub-02", "inclusion_mac": 0.5, "exclusion_mac": 0.6}
        ]
        metrics_path = tmp_path / "data" / "processed" / "connectivity_metrics.json"
        with open(metrics_path, "w") as f:
            import json
            json.dump(metrics_data, f)
        
        # Run function
        df = generate_sensitivity_curve(
            subject_ids=["sub-01", "sub-02"],
            motion_thresholds=[2.0, 2.2],
            config=config,
            base_path=tmp_path
        )
        
        assert len(df) == 2
        assert "p_value" in df.columns
        assert "effect_size" in df.columns

class TestEdgeWiseFDR:
    # Placeholder for T034 tests if needed in this file
    pass

class TestStabilityMetric:
    # Placeholder for T035 tests if needed in this file
    pass