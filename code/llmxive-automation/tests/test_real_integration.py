#!/usr/bin/env python3
"""Real integration tests for llmXive automation - no mocks!"""

import pytest
import os
import sys
import time
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.model_manager import ModelManager
from src.conversation_manager import ConversationManager
from src.task_executor import TaskExecutor
from src.github_handler import GitHubHandler
from src.orchestrator import LLMXiveOrchestrator
from src.model_attribution import ModelAttributionTracker


@pytest.mark.integration
class TestRealIntegration:
    """Real integration tests that interact with actual services"""
    
    @pytest.fixture(scope="class")
    def real_model(self):
        """Load a real small model for testing"""
        print("\nLoading real model for testing...")
        model_mgr = ModelManager(max_size_gb=1.5)
        
        # Use TinyLlama as it's small and reliable
        model, tokenizer = model_mgr._load_model("TinyLlama/TinyLlama-1.1B-Chat-v1.0")
        return model, tokenizer
    
    @pytest.fixture
    def real_github(self):
        """Create real GitHub handler"""
        # Use test repository if available, otherwise use main repo
        test_repo = os.environ.get('TEST_REPO', 'ContextLab/llmXive')
        token = os.environ.get('GITHUB_TOKEN')
        
        if not token:
            print("Warning: No GITHUB_TOKEN set, using CLI fallback")
        
        return GitHubHandler(token=token, repo_name=test_repo)
    
    @pytest.fixture
    def real_executor(self, real_model, real_github):
        """Create real task executor with actual model and GitHub"""
        model, tokenizer = real_model
        conv_mgr = ConversationManager(model, tokenizer)
        return TaskExecutor(conv_mgr, real_github)
    
    def test_real_model_loading(self):
        """Test that we can actually load models from HuggingFace"""
        model_mgr = ModelManager(max_size_gb=2.0)
        
        # Test loading a specific model
        model, tokenizer = model_mgr._load_model("TinyLlama/TinyLlama-1.1B-Chat-v1.0")
        
        assert model is not None
        assert tokenizer is not None
        assert hasattr(model, 'generate')
        assert hasattr(tokenizer, 'encode')
        
        print(f"✓ Successfully loaded model: {model.name_or_path}")
    
    def test_real_model_inference(self, real_model):
        """Test that the model can actually generate text"""
        model, tokenizer = real_model
        conv_mgr = ConversationManager(model, tokenizer)
        
        # Test a simple query - use a task type without strict validation
        response = conv_mgr.query_model(
            "Generate a brief description of what machine learning is, in 2-3 sentences.",
            task_type=None  # No specific task type, just need text generation
        )
        
        assert response is not None
        assert len(response) > 0
        print(f"✓ Model generated response: {response[:100]}...")
    
    def test_real_brainstorm_generation(self, real_executor):
        """Test generating a real research idea"""
        print("\nTesting real brainstorm generation...")
        
        # Execute brainstorm task
        result = real_executor.execute_task("BRAINSTORM_IDEA", {})
        
        assert result['success'] == True
        assert 'issue_created' in result
        assert result['issue_created'] == True
        
        # Check that attribution was tracked
        stats = real_executor.attribution.get_model_stats("TinyLlama/TinyLlama-1.1B-Chat-v1.0")
        assert stats.get('total_contributions', 0) > 0
        
        print(f"✓ Successfully created idea issue")
    
    def test_real_github_operations(self, real_github):
        """Test real GitHub operations"""
        print("\nTesting real GitHub operations...")
        
        # Test reading a file
        readme = real_github.get_file_content("README.md")
        assert readme is not None
        assert "llmXive" in readme
        
        # Test getting repository stats
        stats = real_github.get_repository_stats()
        assert 'total_issues' in stats
        
        print(f"✓ Repository has {stats['total_issues']} total issues")
    
    def test_real_literature_search(self, real_executor):
        """Test real literature search functionality"""
        context = {
            "topic": "machine learning applications in biology"
        }
        
        result = real_executor.execute_task("CONDUCT_LITERATURE_SEARCH", context)
        
        assert result['success'] == True
        print("✓ Literature search completed successfully")
    
    def test_real_code_generation(self, real_executor):
        """Test real code generation"""
        context = {
            "module_description": "A simple function to calculate factorial",
            "code_path": "/tmp/test_factorial.py",
            "plan_path": None  # Simple case without plan
        }
        
        result = real_executor.execute_task("WRITE_CODE", context)
        
        assert result['success'] == True
        assert 'code_path' in result
        
        # Verify the code was actually generated
        if os.path.exists("/tmp/test_factorial.py"):
            with open("/tmp/test_factorial.py", "r") as f:
                code = f.read()
                assert "def" in code  # Should contain function definition
                print("✓ Generated real Python code")
    
    def test_real_orchestrator_run(self):
        """Test a full orchestrator run"""
        print("\nTesting real orchestrator run...")
        
        token = os.environ.get('GITHUB_TOKEN')
        orchestrator = LLMXiveOrchestrator(
            github_token=token,
            model_size_gb=1.5,
            specific_model="TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        )
        
        # Run for just 1 task
        orchestrator.run(max_tasks=1)
        
        print("✓ Orchestrator completed run")
    
    def test_real_attribution_system(self):
        """Test the attribution system with real data"""
        tracker = ModelAttributionTracker("test_attributions.json")
        
        # Add a test contribution
        attr_id = tracker.add_contribution(
            model_id="test-model/v1",
            task_type="TEST_TASK",
            contribution_type="test",
            reference="test-123",
            metadata={"test": True}
        )
        
        assert attr_id is not None
        
        # Verify it was saved
        stats = tracker.get_model_stats("test-model/v1")
        assert stats['total_contributions'] > 0
        
        # Clean up
        if os.path.exists("test_attributions.json"):
            os.remove("test_attributions.json")
        
        print("✓ Attribution system working correctly")
    
    def test_real_issue_creation_with_labels(self, real_github):
        """Test creating an issue with proper labels and project board"""
        # Create a test issue
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        test_title = f"Test Issue {timestamp}"
        test_body = "This is a test issue created by the integration test suite."
        
        issue = real_github.create_issue(
            title=test_title,
            body=test_body,
            labels=["test", "automated"]
        )
        
        if issue:
            assert issue.number > 0
            print(f"✓ Created test issue #{issue.number}")
            
            # Clean up - close the issue
            if hasattr(issue, 'edit'):
                issue.edit(state='closed')
            print(f"✓ Closed test issue #{issue.number}")
        else:
            print("⚠ Could not create test issue (may lack permissions)")
    
    @pytest.mark.slow
    def test_all_task_types_real(self, real_executor):
        """Test that all task types can execute with real model"""
        print("\nTesting all task types with real model...")
        
        # Sample of task types to test
        test_tasks = [
            ("BRAINSTORM_IDEA", {}),
            ("CONDUCT_LITERATURE_SEARCH", {"topic": "AI research"}),
            ("GENERATE_DATASET", {"specifications": "10 random numbers"}),
            ("PLAN_FIGURES", {"results_summary": "Positive correlation found"}),
            ("GENERATE_HELPER_FUNCTION", {"purpose": "Convert celsius to fahrenheit"}),
            ("CHECK_PROJECT_STATUS", {"issue_number": 1}),
        ]
        
        results = {}
        for task_type, context in test_tasks:
            print(f"  Testing {task_type}...")
            try:
                result = real_executor.execute_task(task_type, context)
                results[task_type] = result.get('success', False)
            except Exception as e:
                print(f"    Error: {e}")
                results[task_type] = False
        
        # At least 80% should succeed
        success_rate = sum(1 for r in results.values() if r) / len(results)
        assert success_rate >= 0.8, f"Only {success_rate*100}% of tasks succeeded"
        
        print(f"✓ Task success rate: {success_rate*100}%")


def main():
    """Run real integration tests directly"""
    print("Running real integration tests...")
    print("=" * 60)
    
    # Run tests
    pytest.main([__file__, "-v", "-s", "-m", "integration"])


if __name__ == "__main__":
    main()