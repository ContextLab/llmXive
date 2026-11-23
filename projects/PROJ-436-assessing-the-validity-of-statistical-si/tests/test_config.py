"""
Tests for the config module.
"""
import pytest
import json
import os
import tempfile
from code.config import (
    SimulationConfig,
    MissingMechanism,
    OutcomeType,
    AnalysisMethod,
    load_config,
    create_default_config
)


class TestSimulationConfigCreation:
    """Tests for creating SimulationConfig instances."""
    
    def test_create_valid_config(self):
        """Test creating a valid configuration."""
        config = SimulationConfig(
            dataset_id=123,
            mechanism=MissingMechanism.MCAR,
            missing_rate=0.2,
            outcome_type=OutcomeType.CONTINUOUS
        )
        
        assert config.dataset_id == 123
        assert config.mechanism == MissingMechanism.MCAR
        assert config.missing_rate == 0.2
        assert config.outcome_type == OutcomeType.CONTINUOUS
        assert config.n_iterations == 1000
        assert config.seed == 42
        assert config.alpha == 0.05
        assert len(config.analysis_methods) == 3  # Default all methods
    
    def test_create_config_with_custom_parameters(self):
        """Test creating a config with custom parameters."""
        config = SimulationConfig(
            dataset_id=456,
            mechanism=MissingMechanism.MNAR,
            missing_rate=0.5,
            outcome_type=OutcomeType.BINARY,
            n_iterations=500,
            seed=12345,
            alpha=0.01
        )
        
        assert config.dataset_id == 456
        assert config.mechanism == MissingMechanism.MNAR
        assert config.missing_rate == 0.5
        assert config.outcome_type == OutcomeType.BINARY
        assert config.n_iterations == 500
        assert config.seed == 12345
        assert config.alpha == 0.01
    
    def test_invalid_missing_rate_too_low(self):
        """Test that missing_rate < 0 raises ValueError."""
        with pytest.raises(ValueError, match="missing_rate must be between 0.0 and 1.0"):
            SimulationConfig(
                dataset_id=123,
                mechanism=MissingMechanism.MCAR,
                missing_rate=-0.1,
                outcome_type=OutcomeType.CONTINUOUS
            )
    
    def test_invalid_missing_rate_too_high(self):
        """Test that missing_rate > 1 raises ValueError."""
        with pytest.raises(ValueError, match="missing_rate must be between 0.0 and 1.0"):
            SimulationConfig(
                dataset_id=123,
                mechanism=MissingMechanism.MCAR,
                missing_rate=1.1,
                outcome_type=OutcomeType.CONTINUOUS
            )
    
    def test_invalid_n_iterations(self):
        """Test that n_iterations < 1 raises ValueError."""
        with pytest.raises(ValueError, match="n_iterations must be at least 1"):
            SimulationConfig(
                dataset_id=123,
                mechanism=MissingMechanism.MCAR,
                missing_rate=0.2,
                outcome_type=OutcomeType.CONTINUOUS,
                n_iterations=0
            )
    
    def test_invalid_alpha(self):
        """Test that invalid alpha raises ValueError."""
        with pytest.raises(ValueError, match="alpha must be between 0.0 and 1.0"):
            SimulationConfig(
                dataset_id=123,
                mechanism=MissingMechanism.MCAR,
                missing_rate=0.2,
                outcome_type=OutcomeType.CONTINUOUS,
                alpha=0.0
            )
        
        with pytest.raises(ValueError, match="alpha must be between 0.0 and 1.0"):
            SimulationConfig(
                dataset_id=123,
                mechanism=MissingMechanism.MCAR,
                missing_rate=0.2,
                outcome_type=OutcomeType.CONTINUOUS,
                alpha=1.0
            )
    
    def test_invalid_dataset_id(self):
        """Test that invalid dataset_id raises ValueError."""
        with pytest.raises(ValueError, match="dataset_id must be a positive integer"):
            SimulationConfig(
                dataset_id=0,
                mechanism=MissingMechanism.MCAR,
                missing_rate=0.2,
                outcome_type=OutcomeType.CONTINUOUS
            )
        
        with pytest.raises(ValueError, match="dataset_id must be a positive integer"):
            SimulationConfig(
                dataset_id=-1,
                mechanism=MissingMechanism.MCAR,
                missing_rate=0.2,
                outcome_type=OutcomeType.CONTINUOUS
            )
    
    def test_default_analysis_methods(self):
        """Test that default analysis methods include all methods."""
        config = SimulationConfig(
            dataset_id=123,
            mechanism=MissingMechanism.MCAR,
            missing_rate=0.2,
            outcome_type=OutcomeType.CONTINUOUS
        )
        
        expected_methods = list(AnalysisMethod)
        assert config.analysis_methods == expected_methods
    
    def test_custom_analysis_methods(self):
        """Test creating config with specific analysis methods."""
        config = SimulationConfig(
            dataset_id=123,
            mechanism=MissingMechanism.MCAR,
            missing_rate=0.2,
            outcome_type=OutcomeType.CONTINUOUS,
            analysis_methods=[AnalysisMethod.COMPLETE_CASE, AnalysisMethod.IPW]
        )
        
        assert len(config.analysis_methods) == 2
        assert AnalysisMethod.COMPLETE_CASE in config.analysis_methods
        assert AnalysisMethod.IPW in config.analysis_methods


class TestFromDict:
    """Tests for from_dict class method."""
    
    def test_from_dict_with_strings(self):
        """Test creating config from dict with string enums."""
        data = {
            "dataset_id": 789,
            "mechanism": "mar",
            "missing_rate": 0.3,
            "outcome_type": "binary",
            "n_iterations": 200,
            "seed": 99,
            "alpha": 0.1
        }
        
        config = SimulationConfig.from_dict(data)
        
        assert config.dataset_id == 789
        assert config.mechanism == MissingMechanism.MAR
        assert config.missing_rate == 0.3
        assert config.outcome_type == OutcomeType.BINARY
        assert config.n_iterations == 200
        assert config.seed == 99
        assert config.alpha == 0.1
    
    def test_from_dict_with_enum_instances(self):
        """Test creating config from dict with enum instances."""
        data = {
            "dataset_id": 789,
            "mechanism": MissingMechanism.MNAR,
            "missing_rate": 0.3,
            "outcome_type": OutcomeType.CONTINUOUS,
            "n_iterations": 200,
            "seed": 99
        }
        
        config = SimulationConfig.from_dict(data)
        
        assert config.mechanism == MissingMechanism.MNAR
        assert config.outcome_type == OutcomeType.CONTINUOUS
    
    def test_from_dict_invalid_mechanism(self):
        """Test that invalid mechanism string raises ValueError."""
        data = {
            "dataset_id": 123,
            "mechanism": "invalid",
            "missing_rate": 0.2,
            "outcome_type": "continuous"
        }
        
        with pytest.raises(ValueError, match="Invalid mechanism"):
            SimulationConfig.from_dict(data)
    
    def test_from_dict_invalid_outcome_type(self):
        """Test that invalid outcome_type string raises ValueError."""
        data = {
            "dataset_id": 123,
            "mechanism": "mcar",
            "missing_rate": 0.2,
            "outcome_type": "invalid"
        }
        
        with pytest.raises(ValueError, match="Invalid outcome_type"):
            SimulationConfig.from_dict(data)
    
    def test_from_dict_with_analysis_methods(self):
        """Test creating config with specific analysis methods from dict."""
        data = {
            "dataset_id": 123,
            "mechanism": "mcar",
            "missing_rate": 0.2,
            "outcome_type": "continuous",
            "analysis_methods": ["complete_case", "multiple_imputation"]
        }
        
        config = SimulationConfig.from_dict(data)
        
        assert len(config.analysis_methods) == 2
        assert config.analysis_methods[0] == AnalysisMethod.COMPLETE_CASE
        assert config.analysis_methods[1] == AnalysisMethod.MULTIPLE_IMPUTATION
    
    def test_from_dict_invalid_analysis_method(self):
        """Test that invalid analysis method string raises ValueError."""
        data = {
            "dataset_id": 123,
            "mechanism": "mcar",
            "missing_rate": 0.2,
            "outcome_type": "continuous",
            "analysis_methods": ["invalid_method"]
        }
        
        with pytest.raises(ValueError, match="Invalid analysis_method"):
            SimulationConfig.from_dict(data)


class TestSerialization:
    """Tests for serialization and deserialization."""
    
    def test_to_dict_and_back(self):
        """Test round-trip serialization."""
        original = SimulationConfig(
            dataset_id=123,
            mechanism=MissingMechanism.MAR,
            missing_rate=0.4,
            outcome_type=OutcomeType.BINARY,
            n_iterations=300,
            seed=555,
            alpha=0.025
        )
        
        data = original.to_dict()
        restored = SimulationConfig.from_dict(data)
        
        assert original.dataset_id == restored.dataset_id
        assert original.mechanism == restored.mechanism
        assert original.missing_rate == restored.missing_rate
        assert original.outcome_type == restored.outcome_type
        assert original.n_iterations == restored.n_iterations
        assert original.seed == restored.seed
        assert original.alpha == restored.alpha
        assert original.analysis_methods == restored.analysis_methods
    
    def test_to_json_file_and_load(self):
        """Test saving to and loading from JSON file."""
        config = SimulationConfig(
            dataset_id=456,
            mechanism=MissingMechanism.MNAR,
            missing_rate=0.6,
            outcome_type=OutcomeType.CONTINUOUS
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            config.to_json_file(temp_path)
            loaded = load_config(temp_path)
            
            assert config.dataset_id == loaded.dataset_id
            assert config.mechanism == loaded.mechanism
            assert config.missing_rate == loaded.missing_rate
            assert config.outcome_type == loaded.outcome_type
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def test_load_config_file_not_found(self):
        """Test that loading non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/path/config.json")


class TestCreateDefaultConfig:
    """Tests for create_default_config helper."""
    
    def test_create_default_config(self):
        """Test creating a default config."""
        config = create_default_config(
            dataset_id=789,
            mechanism="mar",
            missing_rate=0.25,
            outcome_type="continuous"
        )
        
        assert config.dataset_id == 789
        assert config.mechanism == MissingMechanism.MAR
        assert config.missing_rate == 0.25
        assert config.outcome_type == OutcomeType.CONTINUOUS
        assert config.n_iterations == 1000
        assert config.seed == 42
    
    def test_create_default_config_custom_values(self):
        """Test creating default config with custom values."""
        config = create_default_config(
            dataset_id=111,
            mechanism="mnar",
            missing_rate=0.5,
            outcome_type="binary",
            n_iterations=2000,
            seed=123,
            alpha=0.01
        )
        
        assert config.dataset_id == 111
        assert config.mechanism == MissingMechanism.MNAR
        assert config.missing_rate == 0.5
        assert config.outcome_type == OutcomeType.BINARY
        assert config.n_iterations == 2000
        assert config.seed == 123
        assert config.alpha == 0.01