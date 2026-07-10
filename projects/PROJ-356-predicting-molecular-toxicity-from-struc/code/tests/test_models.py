"""
Tests for the models package.

These tests verify the functionality of the rule-based and logistic
regression models.
"""
import pytest
import numpy as np
from pathlib import Path
import sys

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent
sys.path.insert(0, str(code_dir))

try:
    from rdkit import Chem
    RDKit_AVAILABLE = True
except ImportError:
    RDKit_AVAILABLE = False

try:
    from sklearn.datasets import make_classification
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


@pytest.mark.skipif(not RDKit_AVAILABLE, reason="RDKit not available")
class TestRuleBasedModel:
    """Tests for the rule-based model."""

    def test_model_initialization(self, tmp_path):
        """Test that the model can be initialized with a valid config."""
        from models.rule_based import RuleBasedModel

        # Create a minimal config file
        config_data = {
            "alerts": [
                {
                    "name": "TestAlert",
                    "smarts": "[#6]",  # Any carbon
                    "weight": 1.0,
                    "description": "Test alert"
                }
            ]
        }

        config_file = tmp_path / "test_config.json"
        import json
        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        model = RuleBasedModel(config_path=str(config_file))
        assert len(model.alerts) == 1
        assert len(model.patterns) == 1
        assert model.weights[0] == 1.0

    def test_scoring_with_alert(self, tmp_path):
        """Test that the model scores molecules with alerts correctly."""
        from models.rule_based import RuleBasedModel

        # Create config with a simple alert
        config_data = {
            "alerts": [
                {
                    "name": "CarbonAlert",
                    "smarts": "[#6]",
                    "weight": 2.0,
                    "description": "Any carbon"
                }
            ]
        }

        config_file = tmp_path / "test_config.json"
        import json
        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        model = RuleBasedModel(config_path=str(config_file))

        # Test with a molecule containing carbon (benzene)
        score = model.predict_score("c1ccccc1")
        assert score == 2.0  # Should match the alert once

    def test_scoring_without_alert(self, tmp_path):
        """Test that the model scores molecules without alerts as 0."""
        from models.rule_based import RuleBasedModel

        # Create config with an alert that won't match
        config_data = {
            "alerts": [
                {
                    "name": "NitroAlert",
                    "smarts": "[N+](=O)[O-]",
                    "weight": 1.5,
                    "description": "Nitro group"
                }
            ]
        }

        config_file = tmp_path / "test_config.json"
        import json
        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        model = RuleBasedModel(config_path=str(config_file))

        # Test with a molecule without nitro group
        score = model.predict_score("CCO")  # Ethanol
        assert score == 0.0

    def test_binary_prediction(self, tmp_path):
        """Test binary prediction with threshold."""
        from models.rule_based import RuleBasedModel

        config_data = {
            "alerts": [
                {
                    "name": "TestAlert",
                    "smarts": "[#6]",
                    "weight": 1.0,
                    "description": "Test"
                }
            ]
        }

        config_file = tmp_path / "test_config.json"
        import json
        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        model = RuleBasedModel(config_path=str(config_file))

        # Test binary prediction
        smiles_list = ["c1ccccc1", "CCO", "CC"]
        predictions = model.predict_binary(smiles_list, threshold=0.5)

        assert len(predictions) == 3
        assert all(p in [0, 1] for p in predictions)


@pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="scikit-learn not available")
class TestLogisticModel:
    """Tests for the logistic regression model."""

    def test_model_initialization(self):
        """Test that the model can be initialized with default parameters."""
        from models.logistic import LogisticModel

        model = LogisticModel(n_splits=3, n_repeats=2)
        assert model.n_splits == 3
        assert model.n_repeats == 2
        assert model.C == 1.0

    def test_fit_and_predict(self):
        """Test fitting and predicting with the model."""
        from models.logistic import LogisticModel

        # Generate synthetic data
        X, y = make_classification(
            n_samples=100,
            n_features=10,
            n_informative=5,
            n_redundant=0,
            random_state=42
        )

        model = LogisticModel(n_splits=3, n_repeats=1, random_state=42)
        results = model.fit(X, y, return_oof=True)

        assert "results" in results
        assert len(results["results"]) == 3  # 3 folds
        assert "oof_predictions" in results
        assert len(results["oof_predictions"]) == 100

        # Test prediction on new data
        X_new = X[:10]
        predictions = model.predict(X_new)
        probabilities = model.predict_proba(X_new)

        assert len(predictions) == 10
        assert len(probabilities) == 10
        assert all(0 <= p <= 1 for p in probabilities)

    def test_cv_results(self):
        """Test that CV results contain expected metrics."""
        from models.logistic import LogisticModel

        X, y = make_classification(
            n_samples=100,
            n_features=10,
            n_informative=5,
            random_state=42
        )

        model = LogisticModel(n_splits=3, n_repeats=2, random_state=42)
        results = model.fit(X, y)

        assert len(results["results"]) == 6  # 3 folds * 2 repeats
        for result in results["results"]:
            assert "auc" in result
            assert "f1" in result
            assert "repeat" in result
            assert "fold" in result

    def test_best_params(self):
        """Test getting best parameters from CV."""
        from models.logistic import LogisticModel

        X, y = make_classification(
            n_samples=100,
            n_features=10,
            n_informative=5,
            random_state=42
        )

        model = LogisticModel(n_splits=3, n_repeats=1, random_state=42)
        model.fit(X, y)

        best_params = model.get_best_params()
        assert "best_auc" in best_params
        assert "best_f1" in best_params
        assert "best_repeat" in best_params
        assert "best_fold" in best_params


def test_models_package_importable():
    """Test that the models package is importable."""
    import models
    assert hasattr(models, '__path__')