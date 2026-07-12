"""
Unit tests for the Gatekeeper Pipeline.
"""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.gatekeeper.pipeline import run_query, GatekeeperPipeline
from code.models import Query
from code.gatekeeper.classifier import ClassificationResult, FrozenDistilBERTClassifier
from code.gatekeeper.rules import check_access_policy, DeletionLog, RoleDefinition

class TestGatekeeperPipeline:
    """Tests for the Gatekeeper Pipeline logic."""

    def test_run_query_allows_valid_request(self):
        """Test that a valid request with authorized role passes."""
        # Mock the classifier to return a safe intent
        mock_result = ClassificationResult(intent="general_query", confidence=0.95)
        
        with patch('code.gatekeeper.pipeline.run_intent_classification', return_value=mock_result):
            with patch('code.gatekeeper.pipeline.check_access_policy') as mock_policy:
                # Mock policy to allow
                mock_policy.return_value.is_allowed = True
                mock_policy.return_value.reason = "Authorized"

                query = Query(
                    query_id="q1",
                    query_text="Hello",
                    role="admin",
                    target_entity="system_status"
                )

                result = run_query(query)

                assert result.is_allowed is True
                assert result.intent == "general_query"
                assert "Intent: general_query" in result.reasons

    def test_run_query_blocks_unauthorized_role(self):
        """Test that an unauthorized role is blocked before classification."""
        query = Query(
            query_id="q2",
            query_text="Delete all data",
            role="guest",
            target_entity="database"
        )

        with patch('code.gatekeeper.pipeline.check_access_policy') as mock_policy:
            # Mock policy to deny
            mock_policy.return_value.is_allowed = False
            mock_policy.return_value.reason = "Role not authorized"
            
            # Classifier should NOT be called
            with patch('code.gatekeeper.pipeline.run_intent_classification') as mock_classify:
                result = run_query(query)

                assert result.is_allowed is False
                assert "Access Denied by Rules" in result.reasons
                mock_classify.assert_not_called()

    def test_run_query_blocks_deleted_target(self):
        """Test that a deleted target is blocked regardless of role."""
        query = Query(
            query_id="q3",
            query_text="Show me the deleted user",
            role="admin",
            target_entity="user_123"
        )

        with patch('code.gatekeeper.pipeline.check_access_policy') as mock_policy:
            mock_policy.return_value.is_allowed = False
            mock_policy.return_value.reason = "Target deleted"

            with patch('code.gatekeeper.pipeline.run_intent_classification') as mock_classify:
                result = run_query(query)

                assert result.is_allowed is False
                mock_classify.assert_not_called()

    def test_run_query_handles_timeout(self):
        """Test that a timeout during classification results in denial."""
        query = Query(
            query_id="q4",
            query_text="Complex analysis",
            role="analyst",
            target_entity="report_data"
        )

        with patch('code.gatekeeper.pipeline.check_access_policy') as mock_policy:
            mock_policy.return_value.is_allowed = True
            
            with patch('code.gatekeeper.pipeline.run_intent_classification') as mock_classify:
                mock_classify.side_effect = TimeoutError("Inference took too long")
                
                result = run_query(query)

                assert result.is_allowed is False
                assert "Timeout during classification" in result.reasons

    def test_pipeline_class_initialization(self):
        """Test direct instantiation of the Pipeline class."""
        pipeline = GatekeeperPipeline(
            deletion_log_path="nonexistent.json",
            role_definition_path="nonexistent.json",
            timeout_seconds=10.0
        )
        
        assert pipeline.timeout_seconds == 10.0
        assert len(pipeline.deletion_logs) == 0
        assert len(pipeline.role_definitions) == 0
        assert pipeline.classifier is not None

    def test_pipeline_run_query_method(self):
        """Test the run_query method on the Pipeline instance."""
        mock_result = ClassificationResult(intent="data_extraction", confidence=0.80)
        
        pipeline = GatekeeperPipeline()
        
        with patch.object(pipeline, 'classifier') as mock_classifier:
            # Mock the classifier's internal logic if needed, but run_intent_classification is the main entry
            with patch('code.gatekeeper.pipeline.run_intent_classification', return_value=mock_result):
                with patch('code.gatekeeper.pipeline.check_access_policy') as mock_policy:
                    mock_policy.return_value.is_allowed = True
                    
                    query = Query(
                        query_id="q5",
                        query_text="Extract data",
                        role="user",
                        target_entity="records"
                    )
                    
                    result = pipeline.run_query(query)
                    
                    assert result.is_allowed is True # Default allow if rules pass
                    assert result.intent == "data_extraction"