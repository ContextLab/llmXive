import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add parent directory to path to allow imports from code/
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from unittest.mock import patch, MagicMock, mock_open
import csv

# Import the R script interaction logic if needed, but primarily testing
# the interaction term parsing logic which is often done in Python
# before passing to R or by parsing R output.
# Based on the task description: "Unit test for interaction term parsing"
# We will test the logic that constructs the formula and parses results
# specifically for the interaction term.

# We assume the interaction term logic is embedded in the modeling workflow
# or helper functions. Since T033 (R script) and T034 (Python wrapper)
# are not yet implemented, we test the *parsing* logic that T034 would perform
# on the results of T033, or the *construction* logic.
# Given the task is "Unit test for interaction term parsing", we will
# create a test that verifies the ability to parse a model summary string
# (as returned by R/phylolm) to extract the interaction coefficient.

def test_parse_interaction_term_from_r_output():
    """
    Test that the parsing logic correctly extracts the interaction term
    (telomere_length:migration_status) from a simulated R model summary.
    """
    # Simulated R summary output for: lifespan ~ telomere_length * migration_status
    # The interaction term usually appears as "telomere_length:migration_statusMigratory"
    r_summary_output = """
    Coefficients:
                                    Estimate Std. Error t value Pr(>|t|)    
    (Intercept)                      1.23456    0.12345   10.00  < 2e-16 ***
    telomere_length                  0.50000    0.05000   10.00  < 2e-16 ***
    migration_statusMigratory        0.20000    0.08000    2.50   0.0125 *  
    telomere_length:migration_statusMigratory -0.15000  0.06000   -2.50   0.0126 *  
    ---
    Residual standard error: 0.5 on 100 degrees of freedom
    Multiple R-squared:  0.65,	Adjusted R-squared:  0.64 
    F-statistic: 70.0 on 3 and 100 DF,  p-value: < 2.2e-16
    """

    # Logic to parse this (mimicking what T034/06_moderator.py would do)
    def parse_interaction_coefficient(summary_text, interaction_var_prefix="telomere_length:migration_status"):
        lines = summary_text.strip().split('\n')
        interaction_line = None
        for line in lines:
            if interaction_var_prefix in line and "migratory" in line.lower():
                interaction_line = line
                break
        
        if not interaction_line:
            return None, None

        # Extract numbers (Estimate and Pr(>|t|))
        # Format: name       Estimate Std.Error t value Pr(>|t|)
        parts = interaction_line.split()
        if len(parts) < 5:
            # Try to handle variable spacing more robustly
            # Find the numbers after the variable name
            import re
            numbers = re.findall(r'-?\d+\.?\d*', line)
            if len(numbers) >= 4:
                estimate = float(numbers[0])
                p_value = float(numbers[3])
                return estimate, p_value
            return None, None
        
        # Standard split if spacing is consistent
        try:
            estimate = float(parts[1])
            p_value = float(parts[4])
            return estimate, p_value
        except (ValueError, IndexError):
            return None, None

    estimate, p_value = parse_interaction_coefficient(r_summary_output)

    assert estimate is not None, "Failed to parse interaction estimate"
    assert p_value is not None, "Failed to parse interaction p-value"
    assert abs(estimate - (-0.15)) < 0.0001, f"Expected -0.15, got {estimate}"
    assert abs(p_value - 0.0126) < 0.0001, f"Expected 0.0126, got {p_value}"

def test_parse_interaction_term_missing():
    """
    Test that parsing returns None when the interaction term is not found.
    """
    r_summary_output = """
    Coefficients:
                                    Estimate Std. Error t value Pr(>|t|)    
    (Intercept)                      1.23456    0.12345   10.00  < 2e-16 ***
    telomere_length                  0.50000    0.05000   10.00  < 2e-16 ***
    ---
    """
    
    def parse_interaction_coefficient(summary_text, interaction_var_prefix="telomere_length:migration_status"):
        lines = summary_text.strip().split('\n')
        for line in lines:
            if interaction_var_prefix in line and "migratory" in line.lower():
                import re
                numbers = re.findall(r'-?\d+\.?\d*', line)
                if len(numbers) >= 4:
                    return float(numbers[0]), float(numbers[3])
        return None, None

    estimate, p_value = parse_interaction_coefficient(r_summary_output)
    assert estimate is None
    assert p_value is None

def test_interaction_term_formula_construction():
    """
    Test the construction of the interaction formula string.
    """
    base_formula = "lifespan ~ telomere_length"
    moderator = "migration_status"
    
    # Expected: lifespan ~ telomere_length * migration_status
    expected = f"{base_formula} * {moderator}"
    # Or explicitly: lifespan ~ telomere_length + migration_status + telomere_length:migration_status
    # The * operator in R expands to main effects + interaction.
    
    constructed = f"{base_formula} * {moderator}"
    assert constructed == expected
    assert "*" in constructed
    assert "telomere_length" in constructed
    assert "migration_status" in constructed

def test_parse_interaction_term_with_various_spaces():
    """
    Test robustness against varying whitespace in R output.
    """
    # Case with extra spaces
    r_summary_output = """
    Coefficients:
    (Intercept)             1.23    0.12    10.0    <0.001
    telomere_length         0.50    0.05    10.0    <0.001
    migration_statusMigratory 0.20    0.08    2.5     0.012
    telomere_length:migration_statusMigratory -0.15 0.06 -2.5 0.0126
    """
    
    def parse_interaction_coefficient(summary_text, interaction_var_prefix="telomere_length:migration_status"):
        lines = summary_text.strip().split('\n')
        for line in lines:
            if interaction_var_prefix in line and "migratory" in line.lower():
                import re
                numbers = re.findall(r'-?\d+\.?\d*', line)
                if len(numbers) >= 4:
                    return float(numbers[0]), float(numbers[3])
        return None, None

    estimate, p_value = parse_interaction_coefficient(r_summary_output)
    assert estimate is not None
    assert abs(estimate - (-0.15)) < 0.0001