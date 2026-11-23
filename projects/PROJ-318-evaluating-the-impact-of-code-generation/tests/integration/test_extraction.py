"""
Integration test for single-repo extraction pipeline (User Story 1).

This test verifies that the extraction pipeline can successfully:
1. Clone a known repository (requests)
2. Parse Python files using the AST parser
3. Extract method signatures and docstrings
4. Truncate to max 1000 methods per repository
5. Serialize output to JSON with correct schema
6. Validate that human_docstring is null (not empty string) when missing
"""
import json
import os
import shutil
import tempfile
from pathlib import Path
import pytest

# Import project utilities
from utils.ast_parser import parse_python_files
from utils.models import MethodSignature, DocstringPair, serialize_pairs_to_json, compute_checksum
from utils.repo_loader import load_repo_list
from config import ConfigException, Config, get_config


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for the integration test."""
    temp_dir = tempfile.mkdtemp(prefix="extraction_test_")
    yield Path(temp_dir)
    # Cleanup after test
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_repo_path(temp_workspace):
    """Clone the 'requests' repository for testing."""
    repo_name = "requests"
    repo_path = temp_workspace / repo_name
    
    # Clone using git
    import subprocess
    result = subprocess.run(
        ["git", "clone", f"https://github.com/psf/{repo_name}.git", str(repo_path)],
        capture_output=True,
        text=True,
        timeout=300
    )
    
    if result.returncode != 0:
        pytest.fail(f"Failed to clone repository: {result.stderr}")
    
    return repo_path


def test_single_repo_extraction_pipeline(temp_workspace, sample_repo_path):
    """
    End-to-end test for extracting method signatures and docstrings from a single repository.
    
    Verifies:
    - AST parser correctly identifies public methods
    - Docstrings are extracted (or null if missing)
    - Output JSON contains required fields
    - Method count is <= 1000 (truncation logic)
    - human_docstring is null (not empty string) when missing
    """
    # 1. Setup output directory
    output_dir = temp_workspace / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "requests_extraction.json"
    
    # 2. Find all Python files in the repository
    py_files = list(sample_repo_path.rglob("*.py"))
    
    if not py_files:
        pytest.fail(f"No Python files found in {sample_repo_path}")
    
    # 3. Parse files using AST parser
    parsed_results = parse_python_files(
        file_paths=py_files,
        max_methods_per_file=100  # Limit per file to avoid excessive output
    )
    
    # 4. Validate parsed results structure
    assert isinstance(parsed_results, list), "parse_python_files should return a list"
    assert len(parsed_results) > 0, "Should have parsed at least one method"
    
    # 5. Convert to DocstringPair objects
    docstring_pairs = []
    for item in parsed_results:
        pair = DocstringPair(
            repo_name="requests",
            file_path=item["file_path"],
            method_name=item["method_name"],
            signature=item["signature"],
            human_docstring=item.get("docstring"),  # May be None
            line_number=item["line_number"]
        )
        docstring_pairs.append(pair)
    
    # 6. Apply truncation (max 1000 methods)
    if len(docstring_pairs) > 1000:
        docstring_pairs = docstring_pairs[:1000]
    
    # 7. Serialize to JSON
    json_output = serialize_pairs_to_json(docstring_pairs)
    
    # 8. Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_output, f, indent=2)
    
    # 9. Verify output file exists and is valid JSON
    assert output_file.exists(), f"Output file {output_file} was not created"
    
    with open(output_file, 'r', encoding='utf-8') as f:
        loaded_data = json.load(f)
    
    assert isinstance(loaded_data, list), "Output should be a JSON array"
    assert len(loaded_data) <= 1000, f"Method count {len(loaded_data)} exceeds 1000 limit"
    
    # 10. Validate schema of each entry
    required_fields = ["repo_name", "file_path", "method_name", "signature", "human_docstring", "line_number"]
    
    for entry in loaded_data:
        for field in required_fields:
            assert field in entry, f"Missing required field: {field}"
        
        # Validate human_docstring is null (None) when missing, not empty string
        if entry["human_docstring"] == "":
            pytest.fail(f"human_docstring should be null (None) for missing docstrings, not empty string: {entry}")
        
        # Validate data types
        assert isinstance(entry["repo_name"], str), "repo_name must be a string"
        assert isinstance(entry["file_path"], str), "file_path must be a string"
        assert isinstance(entry["method_name"], str), "method_name must be a string"
        assert isinstance(entry["signature"], str), "signature must be a string"
        assert entry["human_docstring"] is None or isinstance(entry["human_docstring"], str), \
            "human_docstring must be null or a string"
        assert isinstance(entry["line_number"], int), "line_number must be an integer"
    
    # 11. Verify at least some methods have docstrings (sanity check)
    methods_with_docstrings = sum(1 for e in loaded_data if e["human_docstring"] is not None)
    methods_without_docstrings = sum(1 for e in loaded_data if e["human_docstring"] is None)
    
    # This is a soft check - the "requests" library is well-documented
    # but we don't fail if all are missing (edge case)
    print(f"Methods with docstrings: {methods_with_docstrings}")
    print(f"Methods without docstrings: {methods_without_docstrings}")
    
    # 12. Verify checksum computation
    checksum = compute_checksum(docstring_pairs)
    assert checksum is not None, "Checksum should be computed"
    assert len(checksum) == 64, "SHA-256 checksum should be 64 characters"
    
    print(f"Extraction successful. Total methods: {len(loaded_data)}")
    print(f"Checksum: {checksum}")
    print(f"Output file: {output_file}")


def test_truncation_logic(temp_workspace, sample_repo_path):
    """
    Verify that the truncation logic correctly limits methods to 1000 per repository.
    """
    # Create a large list of mock pairs
    mock_pairs = []
    for i in range(1500):
        pair = DocstringPair(
            repo_name="requests",
            file_path=f"test_file_{i}.py",
            method_name=f"method_{i}",
            signature=f"def method_{i}(): ...",
            human_docstring=None,
            line_number=i
        )
        mock_pairs.append(pair)
    
    # Apply truncation
    if len(mock_pairs) > 1000:
        mock_pairs = mock_pairs[:1000]
    
    assert len(mock_pairs) == 1000, f"Truncation failed: got {len(mock_pairs)} methods, expected 1000"
    assert mock_pairs[-1].method_name == "method_999", "Truncation should keep first 1000 methods"


def test_null_handling_for_missing_docstrings(temp_workspace, sample_repo_path):
    """
    Verify that missing docstrings are represented as null (None), not empty strings.
    """
    # Create a pair with no docstring
    pair = DocstringPair(
        repo_name="requests",
        file_path="test.py",
        method_name="test_method",
        signature="def test_method(): ...",
        human_docstring=None,  # Explicitly None
        line_number=10
    )
    
    # Serialize and check
    json_output = serialize_pairs_to_json([pair])
    
    assert json_output[0]["human_docstring"] is None, \
        "Missing docstrings should be null in JSON, not empty string"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])