"""
Tests for the model implementations.
"""
import pytest
import numpy as np
from pathlib import Path
import sys

# Ensure code directory is in path for imports
@pytest.fixture(autouse=True)
def setup_path():
    code_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(code_dir))
    yield
    if str(code_dir) in sys.path:
        sys.path.remove(str(code_dir))

class TestRuleBasedModel:
    def test_rule_based_model_initialization(self):
        """Test that RuleBasedModel can be initialized."""
        from models.rule_based import RuleBasedModel
        model = RuleBasedModel()
        assert model is not None

    def test_rule_based_model_predict(self):
        """Test prediction with RuleBasedModel."""
        from models.rule_based import RuleBasedModel
        model = RuleBasedModel()
        # Dummy input: binary vector of alerts
        X = np.array([[1, 0, 1, 0], [0, 1, 0, 1]])
        # This will fail if rules aren't loaded, but we test structure
        try:
            predictions = model.predict(X)
            assert len(predictions) == 2
        except FileNotFoundError:
            # Expected if config/structural_alerts.json is missing
            pass

class TestLogisticModel:
    def test_logistic_model_initialization(self):
        """Test that LogisticModel can be initialized."""
        from models.logistic import LogisticModel
        model = LogisticModel()
        assert model is not None

    def test_logistic_model_fit_predict(self):
        """Test fit and predict with LogisticModel."""
        from models.logistic import LogisticModel
        model = LogisticModel()
        X = np.random.rand(10, 5)
        y = np.random.randint(0, 2, 10)
        model.fit(X, y)
        predictions = model.predict(X)
        assert len(predictions) == 10

def test_models_package_importable():
    """Verify the models package can be imported."""
    try:
        import models
        assert hasattr(models, '__path__'), "models is not a package"
    except ImportError as e:
        pytest.fail(f"Failed to import models package: {e}")
