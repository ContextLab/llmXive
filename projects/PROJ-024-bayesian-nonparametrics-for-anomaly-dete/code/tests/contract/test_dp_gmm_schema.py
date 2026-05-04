"""
Contract test for DPGMM model output schema.

Validates that DPGMM outputs conform to specs/contracts/anomaly_score.schema.yaml
"""
import pytest
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
from datetime import datetime

# Project root for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
import sys
sys.path.insert(0, str(PROJECT_ROOT / "code"))

# Import from models module - matches API surface
from models.anomaly_score import AnomalyScore
from models.dp_gmm import DPGMMModel, DPGMMConfig, ELBOHistory

class TestDPGMMOutputSchema:
    """Validate DPGMM model outputs match schema."""

    def test_anomaly_score_schema(self):
        """AnomalyScore must have required fields with correct types."""
        score = AnomalyScore(
            timestamp=datetime.now(),
            value=100.0,
            anomaly_score=-5.0,
            is_anomaly=False,
            uncertainty=0.1,
            component_id=0,
            posterior_weights={0: 0.8, 1: 0.2},
            elbo=-100.0
        )
        
        # Validate required fields exist
        assert hasattr(score, 'timestamp')
        assert hasattr(score, 'value')
        assert hasattr(score, 'anomaly_score')
        assert hasattr(score, 'is_anomaly')
        assert hasattr(score, 'uncertainty')
        assert hasattr(score, 'component_id')
        assert hasattr(score, 'posterior_weights')
        assert hasattr(score, 'elbo')
        
        # Validate field types
        assert isinstance(score.timestamp, datetime)
        assert isinstance(score.value, (int, float, np.number))
        assert isinstance(score.anomaly_score, (int, float, np.number))
        assert isinstance(score.is_anomaly, bool)
        assert isinstance(score.uncertainty, (int, float, np.number))
        assert isinstance(score.component_id, int)
        assert isinstance(score.posterior_weights, dict)
        assert isinstance(score.elbo, (int, float, np.number))

    def test_dp_gmm_config_schema(self):
        """DPGMMConfig must have required hyperparameters."""
        config = DPGMMConfig(
            alpha=1.0,
            beta=0.1,
            kappa=1.0,
            nu=2,
            max_components=50,
            min_components=1,
            convergence_threshold=0.001,
            max_iterations=500,
            random_seed=42
        )
        
        # Validate required fields exist
        assert hasattr(config, 'alpha')
        assert hasattr(config, 'beta')
        assert hasattr(config, 'kappa')
        assert hasattr(config, 'nu')
        assert hasattr(config, 'max_components')
        assert hasattr(config, 'min_components')
        assert hasattr(config, 'convergence_threshold')
        assert hasattr(config, 'max_iterations')
        assert hasattr(config, 'random_seed')
        
        # Validate reasonable defaults
        assert config.max_components >= 10
        assert config.min_components >= 1
        assert config.convergence_threshold > 0
        assert config.max_iterations >= 100

    def test_elbo_history_schema(self):
        """ELBOHistory must track convergence metrics."""
        history = ELBOHistory(
            iterations=[0, 1, 2, 3],
            elbo_values=[-500.0, -450.0, -420.0, -410.0],
            component_counts=[1, 2, 3, 3],
            convergence_achieved=True,
            final_elbo=-410.0
        )
        
        # Validate required fields exist
        assert hasattr(history, 'iterations')
        assert hasattr(history, 'elbo_values')
        assert hasattr(history, 'component_counts')
        assert hasattr(history, 'convergence_achieved')
        assert hasattr(history, 'final_elbo')
        
        # Validate list lengths match
        assert len(history.iterations) == len(history.elbo_values)
        assert len(history.iterations) == len(history.component_counts)
        
        # Validate ELBO is monotonically increasing (for variational inference)
        elbo_array = np.array(history.elbo_values)
        assert np.all(np.diff(elbo_array) >= -1e-6)  # Allow small numerical errors

    def test_model_output_consistency(self):
        """Model output must be consistent across multiple calls."""
        config = DPGMMConfig(random_seed=42)
        model = DPGMMModel(config=config)
        
        # Process same data twice
        data1 = np.random.randn(100, 1)
        scores1 = model.compute_scores(data1)
        
        # Reset and reprocess
        model.reset()
        scores2 = model.compute_scores(data1)
        
        # Scores should be identical with same seed
        assert len(scores1) == len(scores2)
        for s1, s2 in zip(scores1, scores2):
            assert s1.anomaly_score == s2.anomaly_score
            assert s1.component_id == s2.component_id
