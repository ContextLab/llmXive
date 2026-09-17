"""
Integration tests for User Story 2: Coverage Measurement and Comparison.

Specifically tests the end-to-end flow of running generated tests with JaCoCo
and verifying coverage data is returned correctly.
"""
import os
import sys
import json
import tempfile
import shutil
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from test_executor import (
    run_with_jacoco, 
    ExecutionResult, 
    parse_jacoco_xml,
    calculate_coverage_ratio,
    generate_coverage_csv
)
from config import get_data_dir, get_output_dir, get_timeout_exec


@pytest.fixture
def temp_workspace():
    """Create a temporary directory structure for integration testing."""
    base = tempfile.mkdtemp(prefix="jacoco_test_")
    data_dir = Path(base) / "data"
    data_dir.mkdir()
    
    # Create mock source files
    src_dir = data_dir / "src"
    src_dir.mkdir()
    (src_dir / "BugClass.java").write_text(
        "public class BugClass {\n"
        "    public int calculate(int x) {\n"
        "        return x + 1; // Bug: should be x + 2\n"
        "    }\n"
        "}\n"
    )
    
    # Create mock test file
    test_dir = data_dir / "tests"
    test_dir.mkdir()
    (test_dir / "BugClassTest.java").write_text(
        "import org.junit.Test;\n"
        "import static org.junit.Assert.*;\n"
        "\n"
        "public class BugClassTest {\n"
        "    @Test\n"
        "    public void testCalculate() {\n"
        "        BugClass b = new BugClass();\n"
        "        assertEquals(3, b.calculate(2)); // Intentional failure for coverage\n"
        "    }\n"
        "}\n"
    )
    
    # Create mock changed_lines.json
    changed_lines = {
        "project_001": {
            "bug_001": [3, 4] # Lines containing the bug
        }
    }
    (data_dir / "changed_lines.json").write_text(json.dumps(changed_lines))
    
    # Create mock coverage_metrics.csv header
    csv_path = data_dir / "coverage_metrics.csv"
    csv_path.write_text("project_id,test_type,coverage_percentage,status,error_msg,assertion_density\n")
    
    yield {
        "base": base,
        "data_dir": data_dir,
        "src_dir": src_dir,
        "test_dir": test_dir
    }
    
    # Cleanup
    shutil.rmtree(base, ignore_errors=True)


@pytest.fixture
def mock_jacoco_xml():
    """Return a minimal valid JaCoCo XML content string."""
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <report name="TestReport">
      <sessioninfo id="localhost" start="12345" dump="12346"/>
      <package name="com.example">
        <class name="BugClass" sourcefilename="BugClass.java">
          <method name="calculate" desc="(I)I">
            <counter type="INSTRUCTION" missed="0" covered="3"/>
            <counter type="LINE" missed="0" covered="1"/>
          </method>
          <counter type="INSTRUCTION" missed="0" covered="3"/>
          <counter type="LINE" missed="0" covered="1"/>
        </class>
        <sourcefile name="BugClass.java">
          <line nr="3" mi="0" ci="1" mb="0" cb="0"/>
          <line nr="4" mi="0" ci="2" mb="0" cb="0"/>
          <counter type="INSTRUCTION" missed="0" covered="3"/>
          <counter type="LINE" missed="0" covered="2"/>
        </sourcefile>
      </package>
    </report>
    """


def test_run_with_jacoco_returns_coverage(temp_workspace, mock_jacoco_xml):
    """
    Integration test: Verify that run_with_jacoco executes successfully 
    (with mocked subprocess) and returns a valid ExecutionResult with coverage data.
    
    This test simulates the flow where:
    1. The test executor compiles the test (mocked).
    2. The test executor runs the test with JaCoCo (mocked).
    3. The JaCoCo XML is parsed.
    4. Coverage ratio is calculated against changed lines.
    """
    data_dir = temp_workspace["data_dir"]
    src_dir = temp_workspace["src_dir"]
    test_dir = temp_workspace["test_dir"]
    
    project_id = "project_001"
    bug_id = "bug_001"
    test_file_path = str(test_dir / "BugClassTest.java")
    source_file_path = str(src_dir / "BugClass.java")
    
    # Mock subprocess.run to simulate successful compilation and execution
    # and to inject the mock JaCoCo XML into the output directory
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "Execution completed successfully"
    mock_result.stderr = ""
    
    # We need to ensure the mock creates the jacoco.exec file or xml report
    # Since run_with_jacoco expects the XML to be generated, we mock the 
    # file system state after the subprocess call.
    
    with patch('test_executor.subprocess.run', return_value=mock_result) as mock_run:
        with patch('test_executor.Path.exists', return_value=True):
            # Mock the XML reading part by patching the file read
            # The actual function calls parse_jacoco_xml which reads the file.
            # We will mock the file content read inside parse_jacoco_xml or 
            # ensure the file exists in the temp dir if we were doing a real run.
            # For this integration test, we mock the file reading to return our XML.
            
            with patch('builtins.open', mock_open(read_data=mock_jacoco_xml)):
                # Mock the specific file path that parse_jacoco_xml would look for
                # In a real scenario, this is the jacoco.xml report
                xml_path = data_dir / "jacoco.xml"
                
                # We need to patch the path where the XML is expected to be read
                # The function `run_with_jacoco` usually constructs the path to the report.
                # Let's assume the report is written to `data_dir / "jacoco.xml"`
                
                # Patch the internal call to parse_jacoco_xml to return a known good value
                # or mock the file existence and content.
                
                # Strategy: Mock the file read in parse_jacoco_xml directly
                with patch('test_executor.parse_jacoco_xml') as mock_parse:
                    mock_parse.return_value = {
                        "BugClass": {
                            "lines": {3: True, 4: True} # Lines covered
                        }
                    }
                    
                    result = run_with_jacoco(
                        project_id=project_id,
                        bug_id=bug_id,
                        test_file=test_file_path,
                        source_file=source_file_path,
                        data_dir=str(data_dir),
                        timeout=get_timeout_exec()
                    )
                    
                    # Assertions
                    assert isinstance(result, ExecutionResult), "Result must be ExecutionResult"
                    assert result.success is True, "Execution should be marked successful in mock"
                    assert result.coverage_data is not None, "Coverage data must be populated"
                    
                    # Verify subprocess was called (mock verification)
                    assert mock_run.called, "subprocess.run should be called to execute tests"


def test_parse_jacoco_xml_returns_coverage(mock_jacoco_xml, temp_workspace):
    """
    Verify that the XML parser correctly extracts line-level coverage.
    """
    # Create a temporary file to hold the XML
    xml_path = temp_workspace["data_dir"] / "test_report.xml"
    xml_path.write_text(mock_jacoco_xml)
    
    coverage_data = parse_jacoco_xml(str(xml_path))
    
    assert isinstance(coverage_data, dict), "Coverage data must be a dictionary"
    assert "BugClass" in coverage_data, "BugClass must be in coverage data"
    assert "lines" in coverage_data["BugClass"], "Lines must be present"
    
    # Check specific lines
    lines = coverage_data["BugClass"]["lines"]
    assert 3 in lines, "Line 3 should be covered"
    assert 4 in lines, "Line 4 should be covered"


def test_calculate_coverage_ratio_correct(temp_workspace, mock_jacoco_xml):
    """
    Verify coverage ratio calculation against changed lines.
    """
    # Mock changed lines: only line 3 is in the changed set
    changed_lines = {3}
    covered_lines = {3, 4}
    
    ratio = calculate_coverage_ratio(changed_lines, covered_lines)
    
    # 1 out of 1 changed line is covered -> 100%
    assert ratio == 1.0, f"Expected 1.0, got {ratio}"


def test_generate_coverage_csv_writes_file(temp_workspace):
    """
    Verify that generate_coverage_csv writes the correct CSV format.
    """
    data_dir = temp_workspace["data_dir"]
    csv_path = data_dir / "coverage_metrics.csv"
    
    # Prepare sample data
    metrics = [
        {
            "project_id": "p1",
            "test_type": "llm",
            "coverage_percentage": 85.5,
            "status": "passed",
            "error_msg": "",
            "assertion_density": 0.5
        }
    ]
    
    generate_coverage_csv(metrics, str(data_dir))
    
    assert csv_path.exists(), "CSV file must be created"
    
    content = csv_path.read_text()
    lines = content.strip().split("\n")
    
    assert len(lines) == 2, "Should have header + 1 data row"
    assert "p1" in lines[1], "Project ID must be in CSV"
    assert "85.5" in lines[1], "Coverage percentage must be in CSV"