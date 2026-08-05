"""
Integration test for alignment logic (AST + semantic) in code/tests/test_alignment.py.

This test validates the end-to-end alignment pipeline:
1. Loads mock tool issues (simulating US1 output)
2. Loads mock ground truth annotations (simulating US2 output)
3. Executes AST-based alignment
4. Executes semantic alignment fallback
5. Validates the structure and accuracy of aligned pairs

This test is independent of real US1/US2 execution by using mocked data fixtures.
"""
import pytest
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np

# Import the alignment logic from the project
from utils.aligner import (
    get_embedding_model,
    compute_embeddings,
    cosine_similarity_matrix,
    find_best_matches,
    align_by_semantic_similarity,
    align_by_ast_diffs
)
from utils.config import get_data_processed_dir, get_code_dir

# ============================================================================
# FIXTURES: Mock Data Generation
# ============================================================================

@pytest.fixture
def mock_tool_issues() -> List[Dict[str, Any]]:
    """
    Generate a realistic set of tool issues (simulating output from SonarQube/DeepSource).
    These represent issues detected by automated tools.
    """
    return [
        {
            "tool": "sonarqube",
            "issue_id": "SQ-1001",
            "type": "bug",
            "severity": "major",
            "line_start": 45,
            "line_end": 48,
            "file_path": "src/main.py",
            "message": "Potential null pointer dereference in function 'process_data'",
            "code_snippet": "if (data is not None):\n    return data.value\nelse:\n    return None"
        },
        {
            "tool": "deepsource",
            "issue_id": "DS-2045",
            "type": "security",
            "severity": "critical",
            "line_start": 12,
            "line_end": 15,
            "file_path": "src/auth.py",
            "message": "Hardcoded secret key detected",
            "code_snippet": "SECRET_KEY = 'super_secret_123'\napp.config['SECRET_KEY'] = SECRET_KEY"
        },
        {
            "tool": "codeclimate",
            "issue_id": "CC-3321",
            "type": "style",
            "severity": "minor",
            "line_start": 78,
            "line_end": 82,
            "file_path": "src/utils.py",
            "message": "Function has too many arguments (6 > 5)",
            "code_snippet": "def complex_function(a, b, c, d, e, f):\n    # Implementation details\n    pass"
        },
        {
            "tool": "sonarqube",
            "issue_id": "SQ-1002",
            "type": "bug",
            "severity": "critical",
            "line_start": 200,
            "line_end": 205,
            "file_path": "src/api.py",
            "message": "SQL Injection vulnerability in query construction",
            "code_snippet": "query = f\"SELECT * FROM users WHERE id = {user_id}\"\nresult = db.execute(query)"
        }
    ]

@pytest.fixture
def mock_ground_truth() -> List[Dict[str, Any]]:
    """
    Generate a set of human-validated ground truth annotations (simulating US2 output).
    These represent confirmed defects found by human reviewers.
    """
    return [
        {
            "annotation_id": "GT-001",
            "type": "bug",
            "line_start": 45,
            "line_end": 48,
            "file_path": "src/main.py",
            "description": "Null pointer issue in data processing",
            "reviewer": "expert_1",
            "confidence": 0.95,
            "code_snippet": "if (data is not None):\n    return data.value\nelse:\n    return None"
        },
        {
            "annotation_id": "GT-002",
            "type": "security",
            "line_start": 12,
            "line_end": 15,
            "file_path": "src/auth.py",
            "description": "Hardcoded credentials security risk",
            "reviewer": "expert_2",
            "confidence": 0.99,
            "code_snippet": "SECRET_KEY = 'super_secret_123'\napp.config['SECRET_KEY'] = SECRET_KEY"
        },
        {
            "annotation_id": "GT-003",
            "type": "bug",
            "line_start": 200,
            "line_end": 205,
            "file_path": "src/api.py",
            "description": "SQL injection vulnerability",
            "reviewer": "expert_1",
            "confidence": 0.98,
            "code_snippet": "query = f\"SELECT * FROM users WHERE id = {user_id}\"\nresult = db.execute(query)"
        },
        {
            "annotation_id": "GT-004",
            "type": "style",
            "line_start": 78,
            "line_end": 82,
            "file_path": "src/utils.py",
            "description": "Too many arguments in function",
            "reviewer": "expert_3",
            "confidence": 0.85,
            "code_snippet": "def complex_function(a, b, c, d, e, f):\n    # Implementation details\n    pass"
        }
    ]

@pytest.fixture
def mock_ast_diffs() -> Dict[str, List[Dict[str, Any]]]:
    """
    Mock AST-based diff information for alignment verification.
    In a real scenario, this would be generated by comparing ASTs of original vs modified code.
    """
    return {
        "src/main.py": [
            {
                "type": "change",
                "start_line": 45,
                "end_line": 48,
                "node_type": "IfStatement",
                "confidence": 0.92
            }
        ],
        "src/auth.py": [
            {
                "type": "change",
                "start_line": 12,
                "end_line": 15,
                "node_type": "Assignment",
                "confidence": 0.98
            }
        ],
        "src/api.py": [
            {
                "type": "change",
                "start_line": 200,
                "end_line": 205,
                "node_type": "Call",
                "confidence": 0.95
            }
        ],
        "src/utils.py": [
            {
                "type": "change",
                "start_line": 78,
                "end_line": 82,
                "node_type": "FunctionDef",
                "confidence": 0.88
            }
        ]
    }

# ============================================================================
# TESTS
# ============================================================================

class TestAlignmentIntegration:
    """Integration tests for the alignment logic (AST + semantic)."""

    def test_ast_alignment_matches_ground_truth(self, mock_tool_issues, mock_ground_truth, mock_ast_diffs):
        """
        Test that AST-based alignment correctly matches tool issues to ground truth.
        
        Expected behavior:
        - Tool issues and ground truth with same file/line ranges should align
        - Alignment should produce valid pairs with confidence scores
        """
        # Run AST-based alignment
        aligned_pairs = align_by_ast_diffs(
            tool_issues=mock_tool_issues,
            ground_truth=mock_ground_truth,
            ast_diffs=mock_ast_diffs
        )
        
        # Verify alignment results
        assert isinstance(aligned_pairs, list), "Aligned pairs must be a list"
        assert len(aligned_pairs) > 0, "Expected at least one aligned pair"
        
        # Check structure of aligned pairs
        for pair in aligned_pairs:
            assert "tool_issue" in pair, "Missing tool_issue in pair"
            assert "ground_truth" in pair, "Missing ground_truth in pair"
            assert "alignment_method" in pair, "Missing alignment_method"
            assert "confidence" in pair, "Missing confidence score"
            assert pair["alignment_method"] == "ast", "Expected AST alignment method"
            assert 0 <= pair["confidence"] <= 1, "Confidence must be between 0 and 1"
        
        # Verify specific matches (expected matches based on mock data)
        matched_issue_ids = {p["tool_issue"]["issue_id"] for p in aligned_pairs}
        expected_matches = {"SQ-1001", "DS-2045", "SQ-1002", "CC-3321"}
        
        # At least 3 out of 4 should match (allowing for some tolerance)
        assert len(matched_issue_ids.intersection(expected_matches)) >= 3, \
            f"Expected at least 3 matches, got {len(matched_issue_ids.intersection(expected_matches))}"
    
    def test_semantic_alignment_fallback(self, mock_tool_issues, mock_ground_truth):
        """
        Test that semantic alignment works as a fallback when AST is unavailable.
        
        This test simulates a scenario where AST diffs are missing and semantic
        similarity is used for alignment.
        """
        # Run semantic alignment (simulating AST failure scenario)
        aligned_pairs = align_by_semantic_similarity(
            tool_issues=mock_tool_issues,
            ground_truth=mock_ground_truth,
            threshold=0.7
        )
        
        # Verify alignment results
        assert isinstance(aligned_pairs, list), "Aligned pairs must be a list"
        assert len(aligned_pairs) > 0, "Expected at least one aligned pair"
        
        # Check structure
        for pair in aligned_pairs:
            assert "tool_issue" in pair
            assert "ground_truth" in pair
            assert "alignment_method" in pair
            assert "confidence" in pair
            assert pair["alignment_method"] == "semantic", "Expected semantic alignment method"
            assert 0 <= pair["confidence"] <= 1
    
    def test_combined_alignment_pipeline(self, mock_tool_issues, mock_ground_truth, mock_ast_diffs):
        """
        Test the combined alignment pipeline: AST first, then semantic fallback.
        
        This test validates the full integration flow where:
        1. AST alignment is attempted first
        2. Unmatched items fall back to semantic alignment
        3. Final output contains all successfully aligned pairs
        """
        # Step 1: AST alignment
        ast_pairs = align_by_ast_diffs(
            tool_issues=mock_tool_issues,
            ground_truth=mock_ground_truth,
            ast_diffs=mock_ast_diffs
        )
        
        # Extract matched issue IDs
        matched_tool_ids = {p["tool_issue"]["issue_id"] for p in ast_pairs}
        matched_gt_ids = {p["ground_truth"]["annotation_id"] for p in ast_pairs}
        
        # Step 2: Identify unmatched items for semantic fallback
        unmatched_tool_issues = [
            issue for issue in mock_tool_issues
            if issue["issue_id"] not in matched_tool_ids
        ]
        unmatched_ground_truth = [
            gt for gt in mock_ground_truth
            if gt["annotation_id"] not in matched_gt_ids
        ]
        
        # Step 3: Semantic alignment for unmatched items
        semantic_pairs = []
        if unmatched_tool_issues and unmatched_ground_truth:
            semantic_pairs = align_by_semantic_similarity(
                tool_issues=unmatched_tool_issues,
                ground_truth=unmatched_ground_truth,
                threshold=0.6
            )
        
        # Combine results
        all_pairs = ast_pairs + semantic_pairs
        
        # Verify total coverage
        assert len(all_pairs) > 0, "Expected at least some aligned pairs"
        
        # Verify no duplicates
        all_tool_ids = [p["tool_issue"]["issue_id"] for p in all_pairs]
        assert len(all_tool_ids) == len(set(all_tool_ids)), "Duplicate tool issues found"
        
        # Verify structure integrity
        for pair in all_pairs:
            assert "tool_issue" in pair
            assert "ground_truth" in pair
            assert "alignment_method" in pair
            assert "confidence" in pair
            assert pair["alignment_method"] in ["ast", "semantic"]
    
    def test_alignment_accuracy_threshold(self, mock_tool_issues, mock_ground_truth, mock_ast_diffs):
        """
        Test that alignment accuracy meets the minimum threshold (≥0.90).
        
        This test calculates the accuracy of alignment against a known set of
        expected matches and verifies it meets the project requirement.
        """
        # Run AST alignment
        aligned_pairs = align_by_ast_diffs(
            tool_issues=mock_tool_issues,
            ground_truth=mock_ground_truth,
            ast_diffs=mock_ast_diffs
        )
        
        # Define expected matches (based on mock data design)
        expected_matches = [
            ("SQ-1001", "GT-001"),
            ("DS-2045", "GT-002"),
            ("SQ-1002", "GT-003"),
            ("CC-3321", "GT-004")
        ]
        
        # Calculate accuracy
        actual_matches = [
            (p["tool_issue"]["issue_id"], p["ground_truth"]["annotation_id"])
            for p in aligned_pairs
        ]
        
        true_positives = len([m for m in actual_matches if m in expected_matches])
        total_expected = len(expected_matches)
        
        accuracy = true_positives / total_expected if total_expected > 0 else 0.0
        
        # Verify accuracy meets threshold (≥0.90)
        assert accuracy >= 0.90, f"Alignment accuracy {accuracy:.2f} is below threshold 0.90"
    
    def test_embedding_model_initialization(self):
        """Test that the embedding model initializes correctly for semantic alignment."""
        # This test ensures the embedding model can be loaded without errors
        model = get_embedding_model()
        assert model is not None, "Embedding model should not be None"
        
        # Test that embeddings can be computed
        test_texts = ["test sentence 1", "test sentence 2"]
        embeddings = compute_embeddings(model, test_texts)
        
        assert embeddings is not None, "Embeddings should not be None"
        assert len(embeddings) == 2, f"Expected 2 embeddings, got {len(embeddings)}"
        assert embeddings.shape[0] == 2, "Embeddings shape mismatch"
        assert embeddings.shape[1] > 0, "Embeddings should have non-zero dimensions"
    
    def test_cosine_similarity_computation(self):
        """Test that cosine similarity matrix is computed correctly."""
        # Create simple test vectors
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([0.0, 1.0, 0.0])
        vec3 = np.array([1.0, 1.0, 0.0])
        
        vectors = np.array([vec1, vec2, vec3])
        
        # Compute similarity matrix
        similarity_matrix = cosine_similarity_matrix(vectors)
        
        # Verify dimensions
        assert similarity_matrix.shape == (3, 3), "Similarity matrix should be 3x3"
        
        # Verify diagonal is 1.0 (self-similarity)
        assert np.allclose(np.diag(similarity_matrix), 1.0), "Diagonal should be 1.0"
        
        # Verify symmetry
        assert np.allclose(similarity_matrix, similarity_matrix.T), "Matrix should be symmetric"
        
        # Verify specific values
        assert np.isclose(similarity_matrix[0, 1], 0.0), "Orthogonal vectors should have 0 similarity"
        assert np.isclose(similarity_matrix[0, 2], np.sqrt(0.5)), "Expected similarity for [1,0,0] and [1,1,0]"
    
    def test_find_best_matches(self):
        """Test the best match finding algorithm."""
        # Create test embeddings
        query_vecs = np.array([[1.0, 0.0], [0.0, 1.0]])
        target_vecs = np.array([[1.0, 0.1], [0.1, 1.0], [0.0, 0.0]])
        
        # Find best matches
        matches = find_best_matches(query_vecs, target_vecs, top_k=2)
        
        # Verify structure
        assert isinstance(matches, list), "Matches should be a list"
        assert len(matches) == 2, f"Expected 2 query matches, got {len(matches)}"
        
        # Verify each match has required fields
        for match in matches:
            assert "query_idx" in match
            assert "target_idx" in match
            assert "similarity" in match
            assert 0 <= match["similarity"] <= 1

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])