import os
import sys
import tempfile
import shutil
import random
import numpy as np
import pytest
from pathlib import Path
from typing import Generator, Dict, Any, Optional

# Ensure the project root is in the path for imports
@pytest.fixture(autouse=True)
def setup_path():
    """Automatically add the project root to sys.path for all tests."""
    project_root = Path(__file__).parent.parent
    if str(project_root / "code") not in sys.path:
        sys.path.insert(0, str(project_root / "code"))
    yield
    # Cleanup path if necessary, though usually not required for test isolation
    if str(project_root / "code") in sys.path:
        sys.path.remove(str(project_root / "code"))

@pytest.fixture
def project_root() -> Path:
    """Fixture returning the project root directory."""
    return Path(__file__).parent.parent.parent

@pytest.fixture
def temp_project_dir(project_root: Path) -> Generator[Path, None, None]:
    """
    Creates a temporary directory to simulate the project root for isolated tests.
    Ensures that tests do not interfere with the actual project data or results.
    """
    temp_dir = tempfile.mkdtemp(prefix="llmXive_test_")
    temp_path = Path(temp_dir)

    # Create the standard directory structure expected by the project
    dirs = [
        "src/data", "src/models", "src/analysis", "src/cli", "src/lib",
        "data/raw", "data/processed", "results",
        "tests/unit", "tests/integration", "tests/contract"
    ]
    for d in dirs:
        (temp_path / d).mkdir(parents=True, exist_ok=True)

    yield temp_path

    # Cleanup: remove the temporary directory and all contents
    shutil.rmtree(temp_path, ignore_errors=True)

@pytest.fixture
def mocked_data_paths(temp_project_dir: Path) -> Dict[str, Path]:
    """
    Creates mocked file paths for data inputs and outputs within the temp directory.
    Useful for testing data loading and saving without relying on real external data.
    """
    raw_data_dir = temp_project_dir / "data" / "raw"
    processed_data_dir = temp_project_dir / "data" / "processed"
    results_dir = temp_project_dir / "results"

    # Create mock files to simulate existing data
    mock_raw_file = raw_data_dir / "mock_code_searchnet.jsonl"
    mock_processed_file = processed_data_dir / "processed_snippets.jsonl"
    mock_results_file = results_dir / "mock_results.csv"

    # Write minimal valid JSON lines for testing
    with open(mock_raw_file, "w", encoding="utf-8") as f:
        f.write('{"id": "mock-1", "language": "python", "code": "def hello(): pass", "docstring": "A hello function"}\n')
        f.write('{"id": "mock-2", "language": "java", "code": "public class Test {}", "docstring": "A test class"}\n')

    with open(mock_processed_file, "w", encoding="utf-8") as f:
        f.write('{"id": "mock-1", "tokens": ["def", "hello", ":", "pass"], "code": "def hello(): pass"}\n')
        f.write('{"id": "mock-2", "tokens": ["public", "class", "Test", "{}"], "code": "public class Test {}"}\n')

    with open(mock_results_file, "w", encoding="utf-8") as f:
        f.write("method,query_id,ndcg@10\n")
        f.write("bm25,mock-1,0.5\n")

    return {
        "raw": mock_raw_file,
        "processed": mock_processed_file,
        "results": mock_results_file,
        "data_dir": temp_project_dir / "data",
        "results_dir": results_dir
    }

@pytest.fixture(autouse=True)
def reset_seeds():
    """
    Automatically resets random seeds before each test to ensure reproducibility.
    This prevents tests from influencing each's random state.
    """
    random.seed(42)
    np.random.seed(42)
    yield
    # Seeds are reset again implicitly by the fixture runner, but explicit return is safe

@pytest.fixture
def sample_code_snippet() -> Dict[str, Any]:
    """Returns a sample code snippet dictionary matching the expected schema."""
    return {
        "id": "snippet-001",
        "language": "python",
        "code": "def add(a, b):\n    return a + b",
        "docstring": "Adds two numbers.",
        "tokens": ["def", "add", "(", "a", ",", "b", ")", ":", "return", "a", "+", "b"]
    }

@pytest.fixture
def sample_query() -> Dict[str, Any]:
    """Returns a sample query dictionary matching the expected schema."""
    return {
        "id": "query-001",
        "text": "function to add two numbers",
        "ground_truth_ids": ["snippet-001", "snippet-002"]
    }

@pytest.fixture
def sample_embeddings(sample_code_snippet: Dict[str, Any]) -> Dict[str, Any]:
    """
    Returns a sample embedding dictionary for the provided snippet.
    Simulates the output of a neural retriever.
    """
    import numpy as np
    # Create a dummy embedding vector of size 384 (common for MiniLM)
    dummy_embedding = np.random.randn(384).astype(np.float32)
    return {
        "id": sample_code_snippet["id"],
        "embedding": dummy_embedding.tolist()
    }