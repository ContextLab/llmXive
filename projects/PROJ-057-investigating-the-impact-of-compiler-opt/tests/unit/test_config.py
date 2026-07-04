import pytest
from benchmarks.config import validate_flags, BenchmarkConfig
from typing import List

class TestValidateFlags:
    """Unit tests for flag validation logic in config.py."""

    def test_validate_flags_accepts_valid_flags(self):
        """Verify that standard valid flags are accepted."""
        valid_flags = [
            "-O0", "-O1", "-O2", "-O3", "-Os", "-Oz",
            "-march=native", "-ffast-math", "-funroll-loops",
            "-Wall", "-Wextra"
        ]
        for flag in valid_flags:
            result = validate_flags([flag])
            assert result is True, f"Expected {flag} to be valid"

    def test_validate_flags_rejects_invalid(self):
        """Verify that invalid flags are rejected."""
        # Flags that do not start with '-' or are nonsensical
        invalid_flags = [
            "O2",             # Missing dash
            "-O9",            # Invalid optimization level
            "-march=invalid_arch_name_xyz", # Invalid arch
            "-ffast-math-unknown", # Invalid fast-math variant
            "-unknown-flag-xyz",
            "",               # Empty string
            "-X",             # Single char flag not in standard set (optional strictness)
        ]
        
        for flag in invalid_flags:
            # We expect validation to return False or raise an error depending on implementation.
            # Based on the task requirement "rejects invalid", we check that it does not return True.
            result = validate_flags([flag])
            assert result is False, f"Expected invalid flag '{flag}' to be rejected, but it was accepted"

    def test_validate_flags_rejects_mixed_valid_invalid(self):
        """Verify that a list containing any invalid flag is rejected."""
        valid_flags = ["-O2", "-march=native"]
        invalid_flag = "-O9"
        
        mixed_list = valid_flags + [invalid_flag]
        result = validate_flags(mixed_list)
        assert result is False, "Expected mixed list to be rejected due to invalid flag"

    def test_validate_flags_empty_list(self):
        """Verify behavior with empty flag list (should be valid as no invalid flags exist)."""
        result = validate_flags([])
        # An empty list contains no invalid flags, so it should be valid.
        assert result is True

    def test_validate_flags_case_sensitivity(self):
        """Verify that flags are case-sensitive (e.g., -o vs -O)."""
        # -o is typically for output file, but in the context of optimization flags, -O is standard.
        # If the validator is strict about optimization flags, -o might be invalid in that specific set.
        # However, generally -o is a valid gcc flag. We test strict optimization set if defined.
        # Assuming the validator checks for known optimization flags.
        # Let's test a clearly invalid casing for a known flag if the validator is strict.
        # e.g., -ffast-Math (incorrect casing for fast-math)
        invalid_casing = "-ffast-Math"
        result = validate_flags([invalid_casing])
        # If the validator normalizes or is case-insensitive, this might pass.
        # But typically compiler flags are case-sensitive.
        # We assert that if the validator is strict, this fails.
        # Given the task is to "reject invalid", and -ffast-Math is not a standard flag, it should fail.
        assert result is False, f"Expected '{invalid_casing}' to be rejected due to case sensitivity"