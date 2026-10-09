import re
import yaml
from pathlib import Path


def test_semantic_alignment_gsm8k_contract():
    """
    Verify that the GSM8K semantic alignment contract exists and conforms
    to the expected minimal schema (front-matter fields).
    """
    # Resolve the contract file relative to the repository root
    contract_path = (
        Path(__file__).resolve().parents[2]
        / "specs"
        / "001-entropy-validity-prediction"
        / "contracts"
        / "semantic_alignment_gsm8k.md"
    )

    assert contract_path.is_file(), f"Contract file not found at {contract_path}"

    content = contract_path.read_text()

    # Extract YAML front-matter delimited by triple dashes
    frontmatter_match = re.search(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    assert frontmatter_match, "Front-matter block not found in contract"

    frontmatter_yaml = frontmatter_match.group(1)
    data = yaml.safe_load(frontmatter_yaml)

    # Basic schema checks
    assert isinstance(data, dict), "Front-matter must be a mapping"
    assert data.get("task") == "gsm8k", "Front-matter 'task' must be 'gsm8k'"
    assert data.get("type") == "semantic_alignment", "Front-matter 'type' must be 'semantic_alignment'"
    # Ensure required alignment fields are present
    alignment = data.get("alignment", {})
    assert alignment.get("method") == "exact_match", "Alignment method should be 'exact_match'"
    assert alignment.get("source_field") == "answer", "Source field should be 'answer'"
    assert alignment.get("tokenization") == "whitespace", "Tokenization should be 'whitespace'"