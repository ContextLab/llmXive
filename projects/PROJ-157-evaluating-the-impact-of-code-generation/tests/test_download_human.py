import json
from pathlib import Path
from llmxive_toolkit import paths

def test_codeforces_dataset_integrity():
    """
    Verify that the downloaded dataset exists, contains enough problems,
    and has the correct schema.
    """
    data_path = paths.data("raw", "codeforces_cpp.jsonl")
    assert data_path.exists(), f"Dataset file missing at {data_path}"
    
    problems = []
    with data_path.open("r", encoding="utf-8") as f:
        for line in f:
            entry = json.loads(line)
            assert "problem_id" in entry, "Entry missing problem_id"
            assert "human_code" in entry, "Entry missing human_code"
            assert isinstance(entry["human_code"], str), "human_code must be a string"
            assert len(entry["human_code"]) > 0, "human_code cannot be empty"
            problems.append(entry["problem_id"])
    
    # Verify minimum count of distinct problem IDs
    distinct_problems = set(problems)
    assert len(distinct_problems) >= 50, f"Expected >= 50 distinct problems, found {len(distinct_problems)}"