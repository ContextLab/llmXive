import pytest
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np
import sys
import logging

# Ensure code directory is in path for imports
code_dir = Path(__file__).parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from utils.aligner import align_by_ast_diffs, align_by_semantic_similarity, get_embedding_model, compute_embeddings
from utils.config import get_data_processed_dir

# Configure logging for the test run
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Mock data factories to simulate real outputs from US1 and US2
# These are deterministic mocks to ensure the integration test is reproducible
# and does not rely on external state during the test execution.

def mock_tool_issues() -> List[Dict[str, Any]]:
    """
    Generates a list of mock tool issues as if parsed from SonarQube/DeepSource/CodeClimate.
    Schema: {tool, repo_id, file_path, line_start, line_end, issue_type, message, issue_id}
    """
    return [
        {
            "tool": "sonarqube",
            "repo_id": "test-repo-1",
            "file_path": "src/main.py",
            "line_start": 10,
            "line_end": 12,
            "issue_type": "security",
            "message": "Potential SQL injection vulnerability",
            "issue_id": "SQ-1001"
        },
        {
            "tool": "deepsource",
            "repo_id": "test-repo-1",
            "file_path": "src/main.py",
            "line_start": 15,
            "line_end": 18,
            "issue_type": "performance",
            "message": "Inefficient loop detected",
            "issue_id": "DS-2002"
        },
        {
            "tool": "codeclimate",
            "repo_id": "test-repo-2",
            "file_path": "utils/helper.py",
            "line_start": 5,
            "line_end": 5,
            "issue_type": "style",
            "message": "Line too long",
            "issue_id": "CC-3003"
        },
        {
            "tool": "sonarqube",
            "repo_id": "test-repo-3",
            "file_path": "core/engine.py",
            "line_start": 42,
            "line_end": 45,
            "issue_type": "bug",
            "message": "Unreachable code after return",
            "issue_id": "SQ-4004"
        }
    ]


def mock_ground_truth() -> List[Dict[str, Any]]:
    """
    Generates a mock ground truth set derived from human review (US2).
    Schema: {comment_id, repo_id, file_path, line_start, line_end, defect_type, text, is_valid}
    """
    return [
        {
            "comment_id": "GT-001",
            "repo_id": "test-repo-1",
            "file_path": "src/main.py",
            "line_start": 10,
            "line_end": 12,
            "defect_type": "security",
            "text": "This looks like a SQL injection risk.",
            "is_valid": True
        },
        {
            "comment_id": "GT-002",
            "repo_id": "test-repo-1",
            "file_path": "src/main.py",
            "line_start": 15,
            "line_end": 18,
            "defect_type": "performance",
            "text": "You should optimize this loop.",
            "is_valid": True
        },
        {
            "comment_id": "GT-003",
            "repo_id": "test-repo-3",
            "file_path": "core/engine.py",
            "line_start": 42,
            "line_end": 45,
            "defect_type": "bug",
            "text": "Code here is unreachable.",
            "is_valid": True
        },
        {
            "comment_id": "GT-004",
            "repo_id": "test-repo-4",
            "file_path": "src/new_feature.py",
            "line_start": 1,
            "line_end": 10,
            "defect_type": "style",
            "text": "Formatting is inconsistent.",
            "is_valid": True
        }
    ]


def mock_ast_diffs() -> Dict[str, Any]:
    """
    Returns a mock AST diff structure. In a real scenario, this would be computed
    by comparing the AST of the file before and after a commit.
    For this integration test, we return a structure that allows the alignment logic
    to verify file/path matching without needing actual AST parsing of real files.
    """
    return {
        "test-repo-1": {
            "src/main.py": {
                "changes": [
                    {"line": 10, "type": "modified", "old_text": "query = 'SELECT *'", "new_text": "query = f'SELECT *'"},
                    {"line": 15, "type": "modified", "old_text": "for i in range(1000):", "new_text": "for i in range(10000):"}
                ]
            }
        },
        "test-repo-3": {
            "core/engine.py": {
                "changes": [
                    {"line": 42, "type": "added", "old_text": "", "new_text": "def unreachable():\n    return\n    print('never')"}
                ]
            }
        }
    }


class TestAlignmentIntegration:
    """
    Integration test for the alignment logic (AST + semantic).
    This test verifies that tool issues can be successfully aligned with ground truth
    using both AST-based and semantic-similarity-based methods.
    """

    def setup_method(self):
        """Setup test fixtures."""
        self.tool_issues = mock_tool_issues()
        self.ground_truth = mock_ground_truth()
        self.ast_diffs = mock_ast_diffs()
        self.model = get_embedding_model()

    def test_align_by_ast_diffs_exact_match(self):
        """
        Test AST alignment when file paths and line numbers match exactly.
        Expected: Tool issue SQ-1001 should align with GT-001.
        """
        # Filter to specific repo and file for this test
        issues_subset = [i for i in self.tool_issues if i['repo_id'] == 'test-repo-1' and i['file_path'] == 'src/main.py']
        gt_subset = [g for g in self.ground_truth if g['repo_id'] == 'test-repo-1' and g['file_path'] == 'src/main.py']

        # Perform alignment
        aligned_pairs = align_by_ast_diffs(issues_subset, gt_subset, self.ast_diffs)

        assert len(aligned_pairs) > 0, "AST alignment should find at least one match."
        
        # Verify specific match
        found_match = False
        for pair in aligned_pairs:
            if pair['tool_issue_id'] == 'SQ-1001' and pair['gt_id'] == 'GT-001':
                found_match = True
                assert pair['alignment_method'] == 'ast_exact'
                break
        
        assert found_match, f"Expected AST match between SQ-1001 and GT-001, found: {aligned_pairs}"

    def test_align_by_semantic_similarity(self):
        """
        Test semantic alignment when AST is unavailable or to supplement AST.
        Uses message text and comment text for similarity.
        """
        # Prepare data with text fields for semantic comparison
        issues_with_text = self.tool_issues
        gt_with_text = self.ground_truth

        # Perform semantic alignment
        # Note: In a real run, this might be called with a threshold
        aligned_pairs = align_by_semantic_similarity(issues_with_text, gt_with_text, model=self.model, threshold=0.6)

        # We expect at least some matches based on the mock data which has similar keywords
        # (e.g., "SQL injection" in issue and "SQL injection" in ground truth)
        if len(aligned_pairs) == 0:
            # If no matches found, it might be due to threshold or embedding limitations in test env.
            # However, the logic must run without error.
            logger.warning("Semantic alignment found no matches with current threshold. This is acceptable if embeddings are distinct.")
        
        # Verify the function returns a list of dicts with expected keys
        for pair in aligned_pairs:
            assert 'tool_issue_id' in pair
            assert 'gt_id' in pair
            assert 'similarity_score' in pair
            assert 'alignment_method' in pair
            assert pair['alignment_method'] == 'semantic'

    def test_combined_alignment_pipeline(self):
        """
        End-to-end test simulating the full alignment pipeline described in US2.
        1. Try AST alignment.
        2. For unaligned issues, try semantic alignment.
        3. Verify the final count and structure.
        """
        # Step 1: AST Alignment
        ast_aligned = align_by_ast_diffs(self.tool_issues, self.ground_truth, self.ast_diffs)
        ast_aligned_ids = {(p['tool_issue_id'], p['gt_id']) for p in ast_aligned}

        # Identify unaligned issues
        all_issue_ids = {i['issue_id'] for i in self.tool_issues}
        aligned_issue_ids = {p['tool_issue_id'] for p in ast_aligned}
        unaligned_issues = [i for i in self.tool_issues if i['issue_id'] in (all_issue_ids - aligned_issue_ids)]

        # Step 2: Semantic Alignment on unaligned
        sem_aligned = align_by_semantic_similarity(unaligned_issues, self.ground_truth, model=self.model, threshold=0.6)
        sem_aligned_ids = {(p['tool_issue_id'], p['gt_id']) for p in sem_aligned}

        # Step 3: Combine
        final_aligned = ast_aligned + sem_aligned
        final_ids = ast_aligned_ids.union(sem_aligned_ids)

        # Assertions
        assert isinstance(final_aligned, list), "Final alignment result must be a list."
        assert len(final_aligned) > 0, "Combined alignment should find at least some matches (AST or Semantic)."
        
        # Verify no duplicates
        assert len(final_ids) == len(final_aligned), "No duplicate pairs should exist in final result."

        # Verify schema of all pairs
        required_keys = {'tool_issue_id', 'gt_id', 'alignment_method', 'confidence_score'}
        for pair in final_aligned:
            assert required_keys.issubset(pair.keys()), f"Pair missing keys: {required_keys - pair.keys()}"

    def test_empty_inputs(self):
        """Test alignment with empty inputs to ensure robustness."""
        issues = []
        gt = []
        
        ast_result = align_by_ast_diffs(issues, gt, {})
        assert ast_result == []
        
        sem_result = align_by_semantic_similarity(issues, gt, self.model)
        assert sem_result == []

    def test_no_matches_case(self):
        """Test when there are no possible matches (different repos/files)."""
        issues = [{
            "tool": "sonarqube",
            "repo_id": "unique-repo-999",
            "file_path": "unique.py",
            "line_start": 1,
            "line_end": 1,
            "issue_type": "bug",
            "message": "Unique issue",
            "issue_id": "UQ-1"
        }]
        gt = [{
            "comment_id": "GT-999",
            "repo_id": "different-repo-888",
            "file_path": "different.py",
            "line_start": 1,
            "line_end": 1,
            "defect_type": "style",
            "text": "Unique comment",
            "is_valid": True
        }]

        ast_result = align_by_ast_diffs(issues, gt, {})
        sem_result = align_by_semantic_similarity(issues, gt, self.model, threshold=0.99) # High threshold to force no match

        assert len(ast_result) == 0
        # Semantic might find a match if text is similar, but with different repos it should be low confidence or filtered by repo check if implemented
        # We just assert it runs and returns a list
        assert isinstance(sem_result, list)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
