import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.evaluation.run_node_tests import run_single_test, scan_translations, main
from src.utils.timeout_utils import TimeoutError as ProjectTimeoutError

@pytest.fixture
def temp_test_dirs():
    """Create temporary directories for testing."""
    base = Path(tempfile.mkdtemp())
    translations_dir = base / "data" / "evaluation" / "raw_translations"
    tests_dir = base / "data" / "evaluation" / "translated_tests"
    output_csv = base / "data" / "evaluation" / "test_execution_results.csv"
    
    # Create directory structure
    (translations_dir / "zero_shot_basic").mkdir(parents=True)
    (translations_dir / "zero_shot_style").mkdir(parents=True)
    (tests_dir).mkdir(parents=True)
    
    # Create mock translation files
    translation_content_1 = {
        "translated_code": "function add(a, b) { return a + b; }"
    }
    translation_file_1 = translations_dir / "zero_shot_basic" / "entry_001.js"
    translation_file_1.parent.mkdir(parents=True, exist_ok=True)
    with open(translation_file_1, 'w') as f:
        json.dump(translation_content_1, f)
    
    translation_content_2 = {
        "translated_code": "function multiply(a, b) { return a * b; }"
    }
    translation_file_2 = translations_dir / "zero_shot_style" / "entry_002.js"
    translation_file_2.parent.mkdir(parents=True, exist_ok=True)
    with open(translation_file_2, 'w') as f:
        json.dump(translation_content_2, f)
    
    # Create mock test files
    # Test 1: Should pass
    test_content_1 = """
    const assert = require('assert');
    // Simulate the translation being loaded
    function add(a, b) { return a + b; }
    
    try {
        assert.strictEqual(add(2, 3), 5);
        console.log(JSON.stringify({ passed: true }));
    } catch (e) {
        console.log(JSON.stringify({ passed: false, error: e.message }));
    }
    """
    test_file_1 = tests_dir / "entry_001_test.js"
    with open(test_file_1, 'w') as f:
        f.write(test_content_1)
    
    # Test 2: Should fail
    test_content_2 = """
    const assert = require('assert');
    // Simulate the translation being loaded
    function multiply(a, b) { return a * b; }
    
    try {
        assert.strictEqual(multiply(2, 3), 7); // This should fail
        console.log(JSON.stringify({ passed: true }));
    } catch (e) {
        console.log(JSON.stringify({ passed: false, error: e.message }));
    }
    """
    test_file_2 = tests_dir / "entry_002_test.js"
    with open(test_file_2, 'w') as f:
        f.write(test_content_2)
    
    # Mock the global paths
    with patch('src.evaluation.run_node_tests.TRANSLATIONS_DIR', translations_dir), \
         patch('src.evaluation.run_node_tests.TESTS_DIR', tests_dir), \
         patch('src.evaluation.run_node_tests.OUTPUT_CSV', output_csv):
        yield {
            'base': base,
            'translations_dir': translations_dir,
            'tests_dir': tests_dir,
            'output_csv': output_csv,
            'translation_file_1': translation_file_1,
            'translation_file_2': translation_file_2,
            'test_file_1': test_file_1,
            'test_file_2': test_file_2
        }
    
    # Cleanup
    shutil.rmtree(base, ignore_errors=True)

def test_run_single_test_passing(temp_test_dirs):
    """Test that a passing test is correctly identified."""
    test_file = temp_test_dirs['test_file_1']
    translation_file = temp_test_dirs['translation_file_1']
    
    result = run_single_test(test_file, translation_file)
    
    assert result["passed"] is True
    assert result["error"] is None
    assert result["timeout"] is False
    assert result["execution_time"] >= 0

def test_run_single_test_failing(temp_test_dirs):
    """Test that a failing test is correctly identified."""
    test_file = temp_test_dirs['test_file_2']
    translation_file = temp_test_dirs['translation_file_2']
    
    result = run_single_test(test_file, translation_file)
    
    assert result["passed"] is False
    assert result["error"] is not None
    assert "assert" in result["error"].lower() or "expected" in result["error"].lower()
    assert result["timeout"] is False

def test_scan_translations(temp_test_dirs):
    """Test that scan_translations finds all translation files."""
    test_pairs = scan_translations()
    
    assert len(test_pairs) == 2
    
    # Check that we found both test-translation pairs
    translation_paths = [str(p[1]) for p in test_pairs]
    assert str(temp_test_dirs['translation_file_1']) in translation_paths
    assert str(temp_test_dirs['translation_file_2']) in translation_paths

def test_main_creates_csv(temp_test_dirs):
    """Test that main() creates the output CSV file."""
    # Remove the CSV if it exists
    if temp_test_dirs['output_csv'].exists():
        temp_test_dirs['output_csv'].unlink()
    
    main()
    
    assert temp_test_dirs['output_csv'].exists()
    
    # Check CSV content
    import csv
    with open(temp_test_dirs['output_csv'], 'r') as f:
        reader = csv.reader(f)
        headers = next(reader)
        
        assert headers == ["test_file", "translation_file", "condition", "passed", "error", "timeout", "execution_time"]
        
        rows = list(reader)
        assert len(rows) == 2
        
        # Check that we have one passing and one failing test
        passed_count = sum(1 for row in rows if row[3] == 'True')
        failed_count = sum(1 for row in rows if row[3] == 'False')
        
        assert passed_count == 1
        assert failed_count == 1
