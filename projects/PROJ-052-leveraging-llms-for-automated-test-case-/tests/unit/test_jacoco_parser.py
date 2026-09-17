"""
Unit tests for JaCoCo XML parsing functionality.
This module verifies that the XML parsing logic correctly extracts
coverage percentages from JaCoCo report files.
"""
import os
import tempfile
import pytest
import xml.etree.ElementTree as ET
from pathlib import Path

# Import the function to test.
# The function `parse_jacoco_xml` is expected to be implemented in code/test_executor.py
# or a dedicated parser module. Based on the API surface, `test_executor` contains
# coverage logic. We will implement the helper function here for the test to call,
# or import it if it exists.
# Given the task description "verifying XML parsing returns correct coverage percentages",
# we assume a function `parse_jacoco_xml` exists or needs to be tested.
# Since the API surface for test_executor lists `run_with_jacoco`, `calculate_coverage_ratio`, etc.,
# but not explicitly `parse_jacoco_xml`, we will implement the parsing logic inline
# or import a helper if the project structure implies one.
# However, to strictly follow "Extend, don't re-author", we assume the parsing logic
# is part of `test_executor` or a new helper.
# Let's assume the function `parse_jacoco_xml` is to be added to `code/test_executor.py`
# or is an internal helper. For this test task, we will implement the parsing logic
# in the test file itself to verify the *logic* of parsing, or import it if we define it.
# Actually, the task is to write the TEST. The implementation of the parser might be
# in `test_executor.py` (e.g., inside `run_with_jacoco` or a helper).
# Let's create a helper function in the test file to simulate the parser if it's not exported,
# OR better, assume the task implies implementing the parser in `test_executor.py` as well?
# No, T020 is a TEST task. The implementation of the parser should ideally be in `code/test_executor.py`.
# But if it's missing, the test will fail.
# Let's check the API surface: `test_executor` has `run_with_jacoco`, `calculate_coverage_ratio`.
# It does not list `parse_jacoco_xml`.
# To satisfy the task "verifying XML parsing returns correct coverage percentages",
# I will implement a small helper `parse_jacoco_xml` in `code/test_executor.py`
# and then test it here.
# Wait, T020 is just the test. If the function doesn't exist, the test fails.
# The prompt says "Implement the task... write real, runnable research code".
# If the function is missing, I should probably add it to `test_executor.py` in this task
# to make the test runnable?
# The constraint says "Extend, don't re-author".
# Let's assume the function `parse_jacoco_xml` is needed and add it to `code/test_executor.py`
# as part of this task's artifacts to ensure the test passes.

from code.test_executor import parse_jacoco_xml

class TestJacocoParser:
    """Tests for JaCoCo XML parsing logic."""

    def test_parse_jacoco_xml_returns_coverage(self):
        """
        Verifying XML parsing returns correct coverage percentages.
        
        This test creates a mock JaCoCo XML report and verifies that the
        parser correctly extracts the coverage percentage.
        """
        # Create a temporary XML file with a known structure
        mock_xml_content = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <report name="TestProject">
            <sessioninfo id="test" start="123456789" dump="123456790"/>
            <package name="com.example">
                <class name="com.example/MyClass" sourcefilename="MyClass.java">
                    <method name="&lt;init&gt;" desc="()V">
                        <counter type="INSTRUCTION" missed="0" covered="3"/>
                        <counter type="BRANCH" missed="0" covered="0"/>
                    </method>
                    <counter type="INSTRUCTION" missed="2" covered="8"/>
                    <counter type="BRANCH" missed="1" covered="3"/>
                    <counter type="LINE" missed="1" covered="4"/>
                    <counter type="COMPLEXITY" missed="1" covered="2"/>
                    <counter type="METHOD" missed="0" covered="1"/>
                    <counter type="CLASS" missed="0" covered="1"/>
                </class>
                <sourcefile name="MyClass.java">
                    <line nr="10" mi="0" ci="2" mb="0" cb="0"/>
                    <line nr="11" mi="0" ci="2" mb="0" cb="0"/>
                    <line nr="12" mi="0" ci="2" mb="0" cb="0"/>
                    <line nr="13" mi="0" ci="2" mb="0" cb="0"/>
                    <line nr="14" mi="2" ci="0" mb="1" cb="1"/>
                    <counter type="INSTRUCTION" missed="2" covered="8"/>
                    <counter type="BRANCH" missed="1" covered="3"/>
                    <counter type="LINE" missed="1" covered="4"/>
                    <counter type="COMPLEXITY" missed="1" covered="2"/>
                    <counter type="METHOD" missed="0" covered="1"/>
                    <counter type="CLASS" missed="0" covered="1"/>
                </sourcefile>
                <counter type="INSTRUCTION" missed="2" covered="8"/>
                <counter type="BRANCH" missed="1" covered="3"/>
                <counter type="LINE" missed="1" covered="4"/>
                <counter type="COMPLEXITY" missed="1" covered="2"/>
                <counter type="METHOD" missed="0" covered="1"/>
                <counter type="CLASS" missed="0" covered="1"/>
            </package>
            <counter type="INSTRUCTION" missed="2" covered="8"/>
            <counter type="BRANCH" missed="1" covered="3"/>
            <counter type="LINE" missed="1" covered="4"/>
            <counter type="COMPLEXITY" missed="1" covered="2"/>
            <counter type="METHOD" missed="0" covered="1"/>
            <counter type="CLASS" missed="0" covered="1"/>
        </report>
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(mock_xml_content)
            temp_path = f.name

        try:
            # Parse the XML
            result = parse_jacoco_xml(temp_path)
            
            # Verify the result is a dictionary
            assert isinstance(result, dict), "Result should be a dictionary"
            
            # Verify expected keys exist
            assert 'total_instructions' in result, "Missing total_instructions"
            assert 'covered_instructions' in result, "Missing covered_instructions"
            assert 'missed_instructions' in result, "Missing missed_instructions"
            assert 'coverage_percentage' in result, "Missing coverage_percentage"
            
            # Verify the calculated values
            # Total instructions = missed (2) + covered (8) = 10
            assert result['total_instructions'] == 10, f"Expected 10, got {result['total_instructions']}"
            assert result['covered_instructions'] == 8, f"Expected 8, got {result['covered_instructions']}"
            assert result['missed_instructions'] == 2, f"Expected 2, got {result['missed_instructions']}"
            
            # Coverage percentage = (covered / total) * 100 = 80.0
            expected_percentage = 80.0
            assert abs(result['coverage_percentage'] - expected_percentage) < 0.01, \
                f"Expected {expected_percentage}, got {result['coverage_percentage']}"
            
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_parse_jacoco_xml_empty_file(self):
        """Test parsing an empty or minimal XML file."""
        mock_xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <report name="EmptyProject">
            <counter type="INSTRUCTION" missed="0" covered="0"/>
            <counter type="LINE" missed="0" covered="0"/>
        </report>
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(mock_xml_content)
            temp_path = f.name

        try:
            result = parse_jacoco_xml(temp_path)
            
            assert result['total_instructions'] == 0
            assert result['covered_instructions'] == 0
            assert result['missed_instructions'] == 0
            # Avoid division by zero; usually 0% or handled specifically
            assert result['coverage_percentage'] == 0.0
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_parse_jacoco_xml_no_counter(self):
        """Test parsing XML with no counter tags."""
        mock_xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <report name="NoCounters">
            <package name="com.example"/>
        </report>
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(mock_xml_content)
            temp_path = f.name

        try:
            result = parse_jacoco_xml(temp_path)
            
            assert result['total_instructions'] == 0
            assert result['coverage_percentage'] == 0.0
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
