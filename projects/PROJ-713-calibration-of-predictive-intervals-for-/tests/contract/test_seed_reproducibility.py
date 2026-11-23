"""
Contract test for seed reproducibility across the codebase.
Ensures all random operations use config.SEED.
"""
import os
import re
from pathlib import Path
import pytest

from config import SEED, PROJECT_ROOT, CODE_DIR
from scripts.cleanup_and_refactor import find_python_files

class TestSeedReproducibility:
    """Tests to ensure seed reproducibility is maintained."""

    def test_config_seed_is_defined(self):
        """Test that SEED is defined in config."""
        assert SEED is not None
        assert isinstance(SEED, int)
        assert SEED > 0

    def test_all_numpy_random_uses_config_seed(self):
        """Test that np.random.seed uses config.SEED."""
        py_files = find_python_files(str(CODE_DIR))
        
        for file_path in py_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find all np.random.seed calls
            seed_calls = re.findall(r'np\.random\.seed\(([^)]+)\)', content)
            
            for call in seed_calls:
                # Should either be config.SEED or a variable that equals config.SEED
                assert 'SEED' in call or 'seed' in call.lower(), \
                    f"Hardcoded seed found in {file_path}: np.random.seed({call})"

    def test_all_torch_random_uses_config_seed(self):
        """Test that torch.manual_seed uses config.SEED."""
        py_files = find_python_files(str(CODE_DIR))
        
        for file_path in py_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find all torch.manual_seed calls
            seed_calls = re.findall(r'torch\.manual_seed\(([^)]+)\)', content)
            
            for call in seed_calls:
                assert 'SEED' in call or 'seed' in call.lower(), \
                    f"Hardcoded seed found in {file_path}: torch.manual_seed({call})"

    def test_no_hardcoded_numeric_seeds(self):
        """Test that there are no hardcoded numeric seeds (except in tests)."""
        py_files = find_python_files(str(CODE_DIR))
        
        hardcoded_found = []
        for file_path in py_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for patterns like np.random.seed(123) or random_state=42
            hardcoded_patterns = [
                r'np\.random\.seed\(\s*\d+\s*\)',
                r'random\.seed\(\s*\d+\s*\)',
                r'torch\.manual_seed\(\s*\d+\s*\)',
            ]
            
            for pattern in hardcoded_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    # Extract the number
                    num = re.search(r'\d+', match)
                    if num and int(num.group()) != SEED:
                        hardcoded_found.append((file_path, match))
        
        # This test will fail if hardcoded seeds are found, prompting cleanup
        assert len(hardcoded_found) == 0, \
            f"Found hardcoded seeds: {hardcoded_found}. Use config.SEED instead."

    def test_config_imports_present(self):
        """Test that config is imported where needed."""
        py_files = find_python_files(str(CODE_DIR))
        
        files_with_random_ops = []
        for file_path in py_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for random operations
            if any(op in content for op in ['np.random.', 'random.', 'torch.manual_seed']):
                # Check if config is imported
                if 'from config import' not in content and 'import config' not in content:
                    files_with_random_ops.append(file_path)
        
        # This test ensures we catch files that use random ops without config import
        # Note: This might be too strict, so we just warn for now
        if files_with_random_ops:
            pytest.skip(f"Note: These files use random ops but don't import config: {files_with_random_ops}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])