import json
from pathlib import Path

def test_permutation_results_file_exists():
    """Simple sanity test – the permutation script should create the JSON file."""
    result_path = Path("data/processed/permutation_results.json")
    assert result_path.is_file(), f"{result_path} does not exist"

    # The file should contain valid JSON with the expected keys
    with result_path.open() as f:
        data = json.load(f)
    assert "permutations" in data and data["permutations"] == 500
    assert "auc_scores" in data and isinstance(data["auc_scores"], list)