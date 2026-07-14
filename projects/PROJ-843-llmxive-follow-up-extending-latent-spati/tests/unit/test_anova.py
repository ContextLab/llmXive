"""
Unit tests for code/eval/anova.py
Tests cover:
- Data loading for ANOVA
- Two-way ANOVA execution
- Interaction effect detection
- P-value validation
"""
import os
import sys
import json
import numpy as np
import pandas as pd
import pytest
from pathlib import Path
from scipy import stats

# Add code to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from eval.anova import (
    load_metrics_for_anova,
    run_anova,
    main
)
from utils.seeds import set_global_seed
from config import get_results_dir

@pytest.fixture(autouse=True)
def setup_seed():
    set_global_seed(42)

class TestLoadMetricsForAnova:
    def test_load_metrics_from_json(self, tmp_path):
        """Test loading metrics from a JSON file."""
        metrics_file = tmp_path / "metrics.json"
        
        # Create test metrics
        metrics_data = {
            "sequences": [
                {
                    "id": "seq1",
                    "dynamics": "static",
                    "texture": "high",
                    "world_score": 0.85,
                    "sparse_consistency": 0.92
                },
                {
                    "id": "seq2",
                    "dynamics": "fast",
                    "texture": "low",
                    "world_score": 0.72,
                    "sparse_consistency": 0.78
                }
            ]
        }
        
        with open(metrics_file, 'w') as f:
            json.dump(metrics_data, f)
        
        df = load_metrics_for_anova(str(metrics_file))
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "dynamics" in df.columns
        assert "texture" in df.columns
        assert "world_score" in df.columns
        assert "sparse_consistency" in df.columns

    def test_load_metrics_missing_fields(self, tmp_path):
        """Test loading metrics with missing fields."""
        metrics_file = tmp_path / "metrics_partial.json"
        
        metrics_data = {
            "sequences": [
                {
                    "id": "seq1",
                    "dynamics": "static",
                    "texture": "high"
                    # Missing world_score and sparse_consistency
                }
            ]
        }
        
        with open(metrics_file, 'w') as f:
            json.dump(metrics_data, f)
        
        # Should handle missing fields gracefully
        df = load_metrics_for_anova(str(metrics_file))
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1

class TestRunAnova:
    def test_run_anova_two_way(self, tmp_path):
        """Test two-way ANOVA with valid data."""
        # Create synthetic data
        np.random.seed(42)
        
        data = {
            "dynamics": ["static"] * 20 + ["fast"] * 20,
            "texture": ["high"] * 10 + ["low"] * 10 + ["high"] * 10 + ["low"] * 10,
            "world_score": np.concatenate([
                np.random.normal(0.85, 0.05, 20),
                np.random.normal(0.70, 0.08, 20)
            ]),
            "sparse_consistency": np.concatenate([
                np.random.normal(0.90, 0.04, 20),
                np.random.normal(0.75, 0.07, 20)
            ])
        }
        
        df = pd.DataFrame(data)
        
        # Run ANOVA
        result = run_anova(df, metric="world_score")
        
        assert result is not None
        assert "f_statistic" in result
        assert "p_value" in result
        assert "interaction_p_value" in result
        assert result["p_value"] > 0  # Should be a valid probability

    def test_run_anova_with_interaction(self, tmp_path):
        """Test ANOVA that detects interaction effects."""
        np.random.seed(42)
        
        # Create data with clear interaction
        data = []
        for dynamics in ["static", "fast"]:
            for texture in ["high", "low"]:
                # Create interaction: effect depends on both factors
                if dynamics == "static" and texture == "high":
                    mean = 0.95
                elif dynamics == "static" and texture == "low":
                    mean = 0.85
                elif dynamics == "fast" and texture == "high":
                    mean = 0.80
                else:  # fast, low
                    mean = 0.60
                
                values = np.random.normal(mean, 0.05, 15)
                for v in values:
                    data.append({
                        "dynamics": dynamics,
                        "texture": texture,
                        "world_score": v
                    })
        
        df = pd.DataFrame(data)
        
        result = run_anova(df, metric="world_score")
        
        assert result is not None
        assert "interaction_p_value" in result
        # With this strong interaction, p-value should be small
        assert result["interaction_p_value"] < 0.05

    def test_run_anova_small_sample(self, tmp_path):
        """Test ANOVA with small sample size."""
        np.random.seed(42)
        
        data = {
            "dynamics": ["static"] * 3 + ["fast"] * 3,
            "texture": ["high"] * 2 + ["low"] * 1 + ["high"] * 2 + ["low"] * 1,
            "world_score": [0.8, 0.85, 0.75, 0.7, 0.65, 0.6]
        }
        
        df = pd.DataFrame(data)
        
        # Should handle small samples without crashing
        result = run_anova(df, metric="world_score")
        
        assert result is not None
        assert "f_statistic" in result
        assert "p_value" in result

class TestAnovaIntegration:
    def test_anova_workflow(self, tmp_path):
        """Test the complete ANOVA workflow."""
        set_global_seed(42)
        
        # Create metrics file
        metrics_file = tmp_path / "metrics.json"
        
        sequences = []
        for dynamics in ["static", "fast"]:
            for texture in ["high", "low"]:
                for i in range(10):
                    sequences.append({
                        "id": f"{dynamics}_{texture}_{i}",
                        "dynamics": dynamics,
                        "texture": texture,
                        "world_score": np.random.normal(
                            0.8 if dynamics == "static" else 0.65,
                            0.05
                        ),
                        "sparse_consistency": np.random.normal(
                            0.85 if texture == "high" else 0.7,
                            0.06
                        )
                    })
        
        metrics_data = {"sequences": sequences}
        
        with open(metrics_file, 'w') as f:
            json.dump(metrics_data, f)
        
        # Load and run ANOVA
        df = load_metrics_for_anova(str(metrics_file))
        world_result = run_anova(df, metric="world_score")
        sc_result = run_anova(df, metric="sparse_consistency")
        
        assert world_result is not None
        assert sc_result is not None
        assert "f_statistic" in world_result
        assert "f_statistic" in sc_result
        assert "p_value" in world_result
        assert "p_value" in sc_result

    def test_anova_significance_threshold(self, tmp_path):
        """Test ANOVA results against significance threshold."""
        np.random.seed(42)
        
        # Create data with significant effect
        data = {
            "dynamics": ["static"] * 30 + ["fast"] * 30,
            "texture": ["high"] * 15 + ["low"] * 15 + ["high"] * 15 + ["low"] * 15,
            "world_score": np.concatenate([
                np.random.normal(0.9, 0.03, 30),
                np.random.normal(0.6, 0.05, 30)
            ])
        }
        
        df = pd.DataFrame(data)
        
        result = run_anova(df, metric="world_score")
        
        # Main effect should be significant
        assert result["p_value"] < 0.05
        # Interaction might or might not be significant depending on data
        assert result["interaction_p_value"] >= 0  # Valid probability
