import os
import yaml
import pandas as pd
import pytest
import time
import shutil
from unittest.mock import patch, MagicMock

# Import the function under test
from code.utils import (
    check_halt_signal,
    write_halt_signal,
    calculate_processing_success_rate,
    enforce_success_rate_threshold,
    STATE_DIR
)

class TestCheckHaltSignal:
    """Tests for the flexible check_halt_signal function (T012 fix)."""

    def setup_method(self):
        """Create a temporary state directory for tests."""
        self.test_state_dir = "test_state_temp"
        if os.path.exists(self.test_state_dir):
            shutil.rmtree(self.test_state_dir)
        os.makedirs(self.test_state_dir, exist_ok=True)

    def teardown_method(self):
        """Clean up temporary state directory."""
        if os.path.exists(self.test_state_dir):
            shutil.rmtree(self.test_state_dir)

    def test_check_halt_signal_no_args(self):
        """Test check_halt_signal() with no arguments (uses default STATE_DIR)."""
        # Ensure no signal exists in default STATE_DIR
        signal_file = os.path.join(STATE_DIR, "HALT_SIGNAL.yaml")
        if os.path.exists(signal_file):
            os.remove(signal_file)
        
        result = check_halt_signal()
        assert result is False, "Should return False when no signal exists"

    def test_check_halt_signal_custom_path(self):
        """Test check_halt_signal(state_dir) with a custom path."""
        # Create a signal in the custom path
        signal_file = os.path.join(self.test_state_dir, "HALT_SIGNAL.yaml")
        with open(signal_file, 'w') as f:
            yaml.dump({"halt": True, "reason": "Test"}, f)
        
        result = check_halt_signal(self.test_state_dir)
        assert result is True, "Should return True when signal exists in custom path"

    def test_check_halt_signal_none_arg(self):
        """Test check_halt_signal(None) behaves like no arg."""
        # Ensure no signal in default
        signal_file = os.path.join(STATE_DIR, "HALT_SIGNAL.yaml")
        if os.path.exists(signal_file):
            os.remove(signal_file)
        
        result = check_halt_signal(None)
        assert result is False, "Should return False when signal missing and arg is None"

    def test_check_halt_signal_with_signal_in_default(self):
        """Test check_halt_signal() detects signal in default STATE_DIR."""
        signal_file = os.path.join(STATE_DIR, "HALT_SIGNAL.yaml")
        with open(signal_file, 'w') as f:
            yaml.dump({"halt": True, "reason": "Test Default"}, f)
        
        try:
            result = check_halt_signal()
            assert result is True, "Should return True when signal exists in default"
        finally:
            # Cleanup
            if os.path.exists(signal_file):
                os.remove(signal_file)

class TestProcessingSuccessRate:
    """Tests for T012: Processing Success Rate Calculation and Enforcement."""

    def test_calculate_success_rate_perfect(self):
        """Test calculation with 100% success rate."""
        df = pd.DataFrame({'col': [1, 2, 3, 4, 5]})
        rate = calculate_processing_success_rate(df, total_expected=5)
        assert rate == 100.0

    def test_calculate_success_rate_partial(self):
        """Test calculation with 80% success rate."""
        df = pd.DataFrame({'col': [1, 2, 3, 4]})
        rate = calculate_processing_success_rate(df, total_expected=5)
        assert rate == 80.0

    def test_calculate_success_rate_empty(self):
        """Test calculation with 0 processed rows."""
        df = pd.DataFrame({'col': []})
        rate = calculate_processing_success_rate(df, total_expected=10)
        assert rate == 0.0

    def test_enforce_success_rate_pass(self):
        """Test enforcement passes when rate >= 95%."""
        df = pd.DataFrame({'col': [1, 2, 3, 4, 5]}) # 5/5 = 100%
        result = enforce_success_rate_threshold(df, total_expected=5, threshold=95.0)
        assert result is True

    def test_enforce_success_rate_fail(self):
        """Test enforcement fails when rate < 95%."""
        df = pd.DataFrame({'col': [1, 2, 3, 4]}) # 4/5 = 80%
        result = enforce_success_rate_threshold(df, total_expected=5, threshold=95.0)
        assert result is False

    def test_enforce_success_rate_exact_threshold(self):
        """Test enforcement passes exactly at threshold."""
        # 95/100 = 95%
        df = pd.DataFrame({'col': list(range(95))})
        result = enforce_success_rate_threshold(df, total_expected=100, threshold=95.0)
        assert result is True