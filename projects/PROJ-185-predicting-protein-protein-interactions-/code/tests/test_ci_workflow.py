import re
from pathlib import Path

def test_ci_workflow_contains_validate_job():
    """
    Verify that the CI workflow file exists and defines a job named `validate`.
    """
    workflow_path = Path(".github/workflows/ci.yml")
    assert workflow_path.is_file(), "CI workflow file .github/workflows/ci.yml does not exist"

    content = workflow_path.read_text()
    # Look for a top‑level job entry named `validate:` (allow indentation)
    pattern = r"^\\s*validate\\s*:"
    assert re.search(pattern, content, re.MULTILINE), "CI workflow does not contain a `validate` job"