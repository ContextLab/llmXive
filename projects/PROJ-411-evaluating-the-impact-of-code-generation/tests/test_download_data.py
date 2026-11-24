import json
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def test_raw_json_files_exist():
    """Ensure that at least one JSON file was created in data/raw/."""
    raw_dir = paths.data("raw")
    json_files = list(raw_dir.glob("*.json"))
    assert json_files, "No JSON files found in data/raw/ after download_data execution"

    # Verify that each JSON file contains a list of records and that required fields exist
    required = {
        "pr_id",
        "repo_name",
        "created_at",
        "merged_at",
        "additions",
        "deletions",
        "comment_count",
        "commit_message",
        "first_comment_timestamp",
    }
    for jf in json_files:
        with open(jf, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, list), f"{jf} does not contain a JSON list"
        if data:  # non‑empty
            first = data[0]
            missing = required - set(first.keys())
            assert not missing, f"{jf} is missing required fields: {missing}"