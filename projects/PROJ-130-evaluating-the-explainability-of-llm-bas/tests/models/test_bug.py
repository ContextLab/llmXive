"""
Unit tests for the Bug entity in code/models/bug.py.
"""
import pytest
from code.models.bug import Bug


def test_bug_creation():
    """Test that a Bug can be created with valid data."""
    bug = Bug(
        id="Lang-1",
        file_path="src/main/java/org/example/Calculator.java",
        test_suite=["org.example.CalculatorTest.testAdd"],
        reference_text="public int add(int a, int b) { return a - b; }"
    )
    assert bug.id == "Lang-1"
    assert bug.file_path == "src/main/java/org/example/Calculator.java"
    assert len(bug.test_suite) == 1
    assert bug.reference_text == "public int add(int a, int b) { return a - b; }"


def test_bug_to_dict():
    """Test conversion of Bug to dictionary."""
    bug = Bug(
        id="Math-42",
        file_path="src/NumberUtils.java",
        test_suite=["TestA", "TestB"],
        reference_text="code..."
    )
    data = bug.to_dict()
    assert data["id"] == "Math-42"
    assert data["file_path"] == "src/NumberUtils.java"
    assert data["test_suite"] == ["TestA", "TestB"]
    assert data["reference_text"] == "code..."


def test_bug_from_dict():
    """Test creation of Bug from dictionary."""
    data = {
        "id": "Lang-5",
        "file_path": "path/to/file.java",
        "test_suite": ["TestX"],
        "reference_text": "source code"
    }
    bug = Bug.from_dict(data)
    assert bug.id == "Lang-5"
    assert bug.file_path == "path/to/file.java"
    assert bug.test_suite == ["TestX"]
    assert bug.reference_text == "source code"


def test_bug_empty_id_raises_error():
    """Test that creating a Bug with an empty ID raises ValueError."""
    with pytest.raises(ValueError):
        Bug(
            id="",
            file_path="file.java",
            test_suite=[],
            reference_text="code"
        )


def test_bug_empty_file_path_raises_error():
    """Test that creating a Bug with an empty file_path raises ValueError."""
    with pytest.raises(ValueError):
        Bug(
            id="Lang-1",
            file_path="",
            test_suite=[],
            reference_text="code"
        )


def test_bug_invalid_test_suite_type_raises_error():
    """Test that creating a Bug with non-list test_suite raises TypeError."""
    with pytest.raises(TypeError):
        Bug(
            id="Lang-1",
            file_path="file.java",
            test_suite="not_a_list",
            reference_text="code"
        )


def test_bug_empty_reference_text_raises_error():
    """Test that creating a Bug with empty reference_text raises ValueError."""
    with pytest.raises(ValueError):
        Bug(
            id="Lang-1",
            file_path="file.java",
            test_suite=[],
            reference_text=""
        )