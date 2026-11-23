import os
import json
import pytest
import tempfile
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from benchmarks.config import ConfigManager, BenchmarkConfig

class TestConfigManager:
    def test_default_flags(self):
        """Test that default flags are loaded when no file provided."""
        manager = ConfigManager()
        expected_defaults = [
            "-O0", "-O1", "-O2", "-O3", "-Os",
            "-march=native", "-ffast-math", "-funroll-loops"
        ]
        assert manager._flags == expected_defaults

    def test_custom_flags_from_yaml(self):
        """Test loading flags from a YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("- -O2\n- -march=native\n- -ffast-math\n")
            yaml_path = f.name

        try:
            manager = ConfigManager(flags_file=yaml_path)
            assert manager._flags == ["-O2", "-march=native", "-ffast-math"]
        finally:
            os.unlink(yaml_path)

    def test_custom_flags_from_json(self):
        """Test loading flags from a JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"flags": ["-O3", "-funroll-loops"]}, f)
            json_path = f.name

        try:
            manager = ConfigManager(flags_file=json_path)
            assert manager._flags == ["-O3", "-funroll-loops"]
        finally:
            os.unlink(json_path)

    def test_validate_flags_rejects_invalid(self):
        """Test that flags not starting with '-' are rejected."""
        manager = ConfigManager()
        with pytest.raises(ValueError) as excinfo:
            manager.validate_flags(["-O2", "invalid_flag"])
        assert "invalid_flag" in str(excinfo.value)

    def test_generate_combinations(self):
        """Test combination generation logic."""
        # Test with a small set
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("- -O2\n- -O3\n")
            yaml_path = f.name

        try:
            manager = ConfigManager(flags_file=yaml_path)
            combos = manager.generate_combinations()
            
            # Should have 3 combinations: [-O2], [-O3], [-O2, -O3]
            assert len(combos) == 3
            assert ["-O2"] in combos
            assert ["-O3"] in combos
            assert ["-O2", "-O3"] in combos
        finally:
            os.unlink(yaml_path)

    def test_generate_configurations(self):
        """Test full configuration generation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("- -O2\n")
            yaml_path = f.name

        try:
            manager = ConfigManager(flags_file=yaml_path)
            configs = list(manager.generate_configurations(kernel="matmul", compiler="g++"))
            
            assert len(configs) == 1
            config = configs[0]
            assert config.kernel == "matmul"
            assert config.compiler == "g++"
            assert config.flags == ["-O2"]
            assert config.config_id.startswith("matmul_g++_O2")
        finally:
            os.unlink(yaml_path)

    def test_cli_generate_combinations(self):
        """Test the CLI entry point for generating combinations."""
        import subprocess
        import sys

        # Create a temporary output file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name

        try:
            # Run the CLI
            result = subprocess.run(
                [sys.executable, "code/benchmarks/config.py", 
                 "--generate-combinations", 
                 "--input", "data/flags.yaml",
                 "--output", output_path],
                capture_output=True,
                text=True,
                cwd=str(Path(__file__).parent.parent.parent)
            )

            assert result.returncode == 0
            assert os.path.exists(output_path)

            # Verify the output
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert isinstance(data, list)
            assert len(data) > 0
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)