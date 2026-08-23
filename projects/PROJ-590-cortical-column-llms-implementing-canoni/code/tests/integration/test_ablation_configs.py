import pytest
import json
import os
import tempfile
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.experiments.ablation import generate_ablation_configs, save_ablation_configs, load_ablation_configs, AblationConfig

class TestAblationConfigs:
    """Tests for ablation configuration generation."""

    def test_generate_ablation_configs_returns_list(self):
        """Test that generate_ablation_configs returns a non-empty list."""
        configs = generate_ablation_configs()
        assert isinstance(configs, list)
        assert len(configs) > 0

    def test_generate_ablation_configs_contains_baseline(self):
        """Test that the baseline configuration is included."""
        configs = generate_ablation_configs()
        baseline_names = [c.name for c in configs]
        assert "baseline_full_microcircuit" in baseline_names

    def test_generate_ablation_configs_contains_ablations(self):
        """Test that ablation configurations are included."""
        configs = generate_ablation_configs()
        config_names = [c.name for c in configs]
        
        expected_ablations = [
            "ablation_no_recurrence",
            "ablation_no_inhibition",
            "ablation_no_laminar_topology",
            "ablation_no_homeostasis"
        ]
        
        for expected in expected_ablations:
            assert expected in config_names, f"Missing ablation config: {expected}"

    def test_save_and_load_ablation_configs(self, tmp_path):
        """Test that configs can be saved to and loaded from a JSON file."""
        configs = generate_ablation_configs()
        output_path = tmp_path / "ablation_configs.json"
        
        save_ablation_configs(configs, str(output_path))
        assert output_path.exists()
        
        loaded_configs = load_ablation_configs(str(output_path))
        assert len(loaded_configs) == len(configs)
        
        # Verify content
        for orig, loaded in zip(configs, loaded_configs):
            assert orig.name == loaded.name
            assert orig.description == loaded.description
            assert orig.remove_recurrence == loaded.remove_recurrence
            assert orig.remove_inhibition == loaded.remove_inhibition

    def test_ablation_config_serialization(self):
        """Test that AblationConfig can be serialized and deserialized correctly."""
        config = AblationConfig(
            name="test_config",
            description="Test description",
            remove_recurrence=True,
            remove_inhibition=False,
            num_columns=2,
            hidden_dim=128
        )
        
        config_dict = config.to_dict()
        restored_config = AblationConfig.from_dict(config_dict)
        
        assert config.name == restored_config.name
        assert config.description == restored_config.description
        assert config.remove_recurrence == restored_config.remove_recurrence
        assert config.remove_inhibition == restored_config.remove_inhibition
        assert config.num_columns == restored_config.num_columns
        assert config.hidden_dim == restored_config.hidden_dim

    def test_ablation_configs_have_unique_names(self):
        """Test that all generated configs have unique names."""
        configs = generate_ablation_configs()
        names = [c.name for c in configs]
        assert len(names) == len(set(names)), "Duplicate config names found"