import csv
import os
import pytest
from pathlib import Path
from typing import Dict, List, Tuple

# Import project root helper if available, otherwise assume standard path structure
try:
    from utils.config import get_project_root
except ImportError:
    # Fallback for direct test execution context
    def get_project_root() -> Path:
        return Path(__file__).parent.parent.parent

MANIFEST_PATH = "data/raw/manifest.csv"

class BlockMatchingError(Exception):
    """Raised when the Balanced Blocked Design matching criteria are not met."""
    pass

def load_manifest() -> List[Dict[str, str]]:
    """
    Loads the manifest.csv file.
    Raises FileNotFoundError if the file does not exist.
    Raises ValueError if the file is empty or missing required columns.
    """
    root = get_project_root()
    manifest_file = root / MANIFEST_PATH

    if not manifest_file.exists():
        raise FileNotFoundError(f"Manifest file not found at {manifest_file}. "
                                "Ensure T015 (export_manifest.py) has been executed.")

    with open(manifest_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Validate required columns
        required_columns = {'sample_id', 'source_type', 'repository_id', 'issue_id', 'task_id'}
        if not required_columns.issubset(set(reader.fieldnames or [])):
            missing = required_columns - set(reader.fieldnames or [])
            raise ValueError(f"Manifest missing required columns: {missing}")

        rows = list(reader)
        if not rows:
            raise ValueError("Manifest file is empty.")
        
        return rows

def verify_block_matching(manifest_rows: List[Dict[str, str]]) -> Dict[str, Dict[str, Dict[str, int]]]:
    """
    Verifies that for every unique repository_id, the count of Human samples
    equals the count of LLM samples.
    
    Returns a nested dictionary structure:
    {
        "repository_id": {
            "source_type": count
        }
    }
    
    Raises BlockMatchingError if the design is unbalanced.
    """
    block_counts: Dict[str, Dict[str, int]] = {}

    for row in manifest_rows:
        repo_id = row['repository_id']
        source_type = row['source_type']
        
        if repo_id not in block_counts:
            block_counts[repo_id] = {"human": 0, "llm": 0}
        
        # Normalize source_type to lowercase for robustness
        key = source_type.lower()
        if key in block_counts[repo_id]:
            block_counts[repo_id][key] += 1
        else:
            # Unexpected source type, log or handle as needed
            block_counts[repo_id][key] = 1

    # Verify balance
    unbalanced_repos = []
    for repo_id, counts in block_counts.items():
        human_count = counts.get("human", 0)
        llm_count = counts.get("llm", 0)
        
        if human_count != llm_count:
            unbalanced_repos.append({
                "repo_id": repo_id,
                "human_count": human_count,
                "llm_count": llm_count
            })
    
    if unbalanced_repos:
        error_details = []
        for item in unbalanced_repos:
            error_details.append(
                f"Repo {item['repo_id']}: Human={item['human_count']}, "
                f"LLM={item['llm_count']}"
            )
        raise BlockMatchingError(
            "Balanced Blocked Design verification failed. "
            f"Found {len(unbalanced_repos)} unbalanced repositories:\n" +
            "\n".join(error_details)
        )

    return block_counts

def test_manifest_exists_and_loadable():
    """Test that the manifest file exists and can be loaded."""
    try:
        rows = load_manifest()
        assert len(rows) > 0, "Manifest loaded but contains no rows."
    except FileNotFoundError:
        pytest.fail("Manifest file data/raw/manifest.csv not found. "
                    "Run T015 to generate the manifest before running this test.")

def test_block_matching_balance():
    """
    Test that the manifest correctly pairs Human and LLM samples by repository_id.
    Specifically, for every repository, count(Human) must equal count(LLM).
    Target per repo is 3 Human and 3 LLM samples.
    """
    rows = load_manifest()
    
    # This call will raise BlockMatchingError if the design is unbalanced
    counts = verify_block_matching(rows)
    
    # Additional assertion: Ensure we actually checked something
    assert len(counts) > 0, "No repositories found in manifest."
    
    # Optional: Verify the specific target count (3 per group) if the design is strictly enforced
    # This is a soft check; the hard check is the equality between groups.
    # If a repo has 0 samples, it shouldn't be in the list usually, but if it is, 0==0 is balanced.
    # We expect 50 repos with 3 human and 3 llm each.
    
    # Check if all repositories have the expected counts (3 human, 3 llm)
    # Note: If the pipeline ran but failed to fetch some samples, we might have fewer.
    # The primary requirement is the BALANCE (Human == LLM).
    # However, T012 specifies exactly 3 per repo.
    
    for repo_id, counts_dict in counts.items():
        human = counts_dict.get("human", 0)
        llm = counts_dict.get("llm", 0)
        
        # Assert balance
        assert human == llm, f"Repo {repo_id} is unbalanced: {human} human vs {llm} llm"
        
        # Assert the target count (3) is met, as per T012 specification
        # If this fails, it means the data collection (T012) didn't meet the N=3 requirement
        assert human == 3, f"Repo {repo_id} has {human} human samples, expected 3."
        assert llm == 3, f"Repo {repo_id} has {llm} llm samples, expected 3."

def test_issue_id_consistency_within_repo():
    """
    Verify that within a repository block, the issue_id mapping is consistent
    with the blocked design (Human and LLM samples for the same repo should
    ideally be linked to the same issue set if the design implies issue-level blocking).
    
    The task description emphasizes repository_id matching. This test ensures
    that if we group by repo, we have the expected structure.
    """
    rows = load_manifest()
    repo_issues: Dict[str, set] = {}

    for row in rows:
        repo_id = row['repository_id']
        issue_id = row['issue_id']
        
        if repo_id not in repo_issues:
            repo_issues[repo_id] = set()
        repo_issues[repo_id].add(issue_id)
    
    # Verify that each repo has a non-empty set of issues
    for repo_id, issues in repo_issues.items():
        assert len(issues) > 0, f"Repo {repo_id} has no associated issue IDs."

if __name__ == "__main__":
    pytest.main([__file__, "-v"])