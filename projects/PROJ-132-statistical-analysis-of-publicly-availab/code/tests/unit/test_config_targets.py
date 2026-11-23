"""
Tests for T001: Assumption Targets Configuration.

Verifies that:
1. src/config.py contains the correct numeric targets
2. plan.md references these targets correctly
3. All targets are valid positive numbers
"""
import pytest
import os
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.config import (
    POWER_TARGET,
    INSUFFICIENT_DATA_TARGET,
    CONVERGENCE_TARGET,
    CI_WIDTH_TARGET,
    verify_config_targets
)

class TestAssumptionTargets:
    """Test suite for T001 assumption targets."""
    
    def test_power_target_exists_and_valid(self):
        """Verify POWER_TARGET is set to 0.80."""
        assert POWER_TARGET == 0.80, f"POWER_TARGET should be 0.80, got {POWER_TARGET}"
        assert isinstance(POWER_TARGET, (int, float)), "POWER_TARGET must be numeric"
        assert POWER_TARGET > 0, "POWER_TARGET must be positive"
    
    def test_insufficient_data_target_exists_and_valid(self):
        """Verify INSUFFICIENT_DATA_TARGET is set to 0.20."""
        assert INSUFFICIENT_DATA_TARGET == 0.20, f"INSUFFICIENT_DATA_TARGET should be 0.20, got {INSUFFICIENT_DATA_TARGET}"
        assert isinstance(INSUFFICIENT_DATA_TARGET, (int, float)), "INSUFFICIENT_DATA_TARGET must be numeric"
        assert INSUFFICIENT_DATA_TARGET > 0, "INSUFFICIENT_DATA_TARGET must be positive"
    
    def test_convergence_target_exists_and_valid(self):
        """Verify CONVERGENCE_TARGET is set to 0.90."""
        assert CONVERGENCE_TARGET == 0.90, f"CONVERGENCE_TARGET should be 0.90, got {CONVERGENCE_TARGET}"
        assert isinstance(CONVERGENCE_TARGET, (int, float)), "CONVERGENCE_TARGET must be numeric"
        assert CONVERGENCE_TARGET > 0, "CONVERGENCE_TARGET must be positive"
    
    def test_ci_width_target_exists_and_valid(self):
        """Verify CI_WIDTH_TARGET is set to 5.0."""
        assert CI_WIDTH_TARGET == 5.0, f"CI_WIDTH_TARGET should be 5.0, got {CI_WIDTH_TARGET}"
        assert isinstance(CI_WIDTH_TARGET, (int, float)), "CI_WIDTH_TARGET must be numeric"
        assert CI_WIDTH_TARGET > 0, "CI_WIDTH_TARGET must be positive"
    
    def test_verify_config_targets_returns_true(self):
        """Verify that all targets are valid."""
        assert verify_config_targets() is True, "verify_config_targets should return True for valid targets"
    
    def test_plan_md_contains_targets(self):
        """Verify plan.md references the assumption targets."""
        plan_path = Path(__file__).resolve().parent.parent.parent / "plan.md"
        assert plan_path.exists(), "plan.md must exist"
        
        with open(plan_path, 'r') as f:
            plan_content = f.read()
        
        # Check for target mentions
        assert "POWER_TARGET" in plan_content, "plan.md must reference POWER_TARGET"
        assert "INSUFFICIENT_DATA_TARGET" in plan_content, "plan.md must reference INSUFFICIENT_DATA_TARGET"
        assert "CONVERGENCE_TARGET" in plan_content, "plan.md must reference CONVERGENCE_TARGET"
        assert "CI_WIDTH_TARGET" in plan_content, "plan.md must reference CI_WIDTH_TARGET"
        
        # Check for numeric values
        assert "0.80" in plan_content, "plan.md must contain POWER_TARGET value (0.80)"
        assert "0.20" in plan_content, "plan.md must contain INSUFFICIENT_DATA_TARGET value (0.20)"
        assert "0.90" in plan_content, "plan.md must contain CONVERGENCE_TARGET value (0.90)"
        assert "5.0" in plan_content, "plan.md must contain CI_WIDTH_TARGET value (5.0)"
    
    def test_config_exports_all_targets(self):
        """Verify all targets are exported from config module."""
        import src.config as config
        
        required_exports = [
            "POWER_TARGET",
            "INSUFFICIENT_DATA_TARGET",
            "CONVERGENCE_TARGET",
            "CI_WIDTH_TARGET"
        ]
        
        for export in required_exports:
            assert hasattr(config, export), f"config module must export {export}"
            value = getattr(config, export)
            assert value is not None, f"{export} must not be None"
            assert isinstance(value, (int, float)), f"{export} must be numeric"
