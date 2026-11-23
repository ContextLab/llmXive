import re
import yaml
from pathlib import Path


def _extract_frontmatter(content: str) -> dict:
    """
    Extract YAML front‑matter from a markdown file.

    The front‑matter is expected to be delimited by lines containing only ``---``.
    """
    match = re.search(r'^---\\s*(.*?)\\s*---', content, re.DOTALL)
    if not match:
        raise AssertionError("Missing YAML front‑matter delimited by '---'")
    yaml_block = match.group(1)
    return yaml.safe_load(yaml_block)


def test_semantic_alignment_minigrid_contract():
    """
    Verify that the MiniGrid semantic‑alignment contract exists and contains the required fields.
    """
    contract_path = Path(
        "specs/001-entropy-validity-prediction/contracts/semantic_alignment_minigrid.md"
    )
    assert contract_path.is_file(), f"Contract file not found at {contract_path}"

    content = contract_path.read_text(encoding="utf-8")
    data = _extract_frontmatter(content)

    # Required top‑level keys according to the semantic‑alignment schema
    required_keys = {"task_type", "description", "validity_criteria", "ground_truth_source"}
    missing = required_keys - data.keys()
    assert not missing, f"Contract is missing required keys: {missing}"

    # Basic sanity checks on values
    assert data["task_type"].lower() == "minigrid", "task_type must be 'MiniGrid'"
    assert isinstance(data["description"], str) and data["description"], "description must be a non‑empty string"
    assert isinstance(data["validity_criteria"], str) and data["validity_criteria"], "validity_criteria must be a non‑empty string"
    assert isinstance(data["ground_truth_source"], str) and data["ground_truth_source"], "ground_truth_source must be a non‑empty string"

    # Ensure the referenced ground‑truth file exists
    gt_path = Path(data["ground_truth_source"])
    assert gt_path.is_file(), f"Referenced ground‑truth file does not exist: {gt_path}"

# The test can be run with ``pytest tests/contract/test_semantic_alignment_minigrid.py``.