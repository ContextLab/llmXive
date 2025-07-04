"""Pytest configuration and fixtures for llmXive automation tests"""

import os
import sys
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from src.model_manager import ModelManager
from src.conversation_manager import ConversationManager
from src.github_handler import GitHubHandler
from src.response_parser import ResponseParser
from src.task_executor import TaskExecutor
from src.orchestrator import LLMXiveOrchestrator


@pytest.fixture
def mock_github_token():
    """Mock GitHub token"""
    return "ghp_test_token_12345"


@pytest.fixture
def mock_hf_token():
    """Mock HuggingFace token"""
    return "hf_test_token_12345"


@pytest.fixture
def mock_model():
    """Mock a small HuggingFace model"""
    model = MagicMock()
    model.name_or_path = "microsoft/phi-2"
    model.config = MagicMock()
    model.config.max_position_embeddings = 2048
    return model


@pytest.fixture
def mock_tokenizer():
    """Mock tokenizer"""
    tokenizer = MagicMock()
    tokenizer.model_max_length = 2048
    tokenizer.encode = Mock(return_value=[1, 2, 3, 4, 5])
    tokenizer.decode = Mock(return_value="Mock response")
    tokenizer.pad_token_id = 0
    tokenizer.eos_token_id = 1
    return tokenizer


@pytest.fixture
def mock_github_handler(mock_github_token):
    """Mock GitHub handler"""
    with patch('src.github_handler.Github'):
        handler = GitHubHandler(mock_github_token)
        
        # Mock common methods
        handler.get_file_content = Mock(return_value="Mock file content")
        handler.create_file = Mock(return_value=True)
        handler.update_file = Mock(return_value=True)
        handler.file_exists = Mock(return_value=False)
        handler.create_issue = Mock()
        handler.get_issue = Mock()
        handler.get_open_issues = Mock(return_value=[])
        handler.get_backlog_ideas = Mock(return_value=[])
        
        return handler


@pytest.fixture
def response_parser():
    """Response parser instance"""
    return ResponseParser()


@pytest.fixture
def conversation_manager(mock_model, mock_tokenizer):
    """Mock conversation manager"""
    manager = ConversationManager(mock_model, mock_tokenizer)
    manager.query_model = Mock(return_value="Mock LLM response")
    return manager


@pytest.fixture
def task_executor(conversation_manager, mock_github_handler):
    """Task executor with mocked dependencies"""
    return TaskExecutor(conversation_manager, mock_github_handler)


@pytest.fixture
def orchestrator(mock_github_token, mock_hf_token):
    """Orchestrator with mocked dependencies"""
    with patch('src.orchestrator.ModelManager'):
        orch = LLMXiveOrchestrator(
            github_token=mock_github_token,
            hf_token=mock_hf_token
        )
        return orch


@pytest.fixture
def sample_issue():
    """Sample GitHub issue"""
    issue = MagicMock()
    issue.number = 123
    issue.title = "[Idea] Test Research Idea"
    issue.body = """**Field**: Machine Learning
**Description**: A novel approach to test research
**Suggested ID**: ml-test-001
**Keywords**: machine learning, testing, automation"""
    issue.labels = [MagicMock(name="backlog"), MagicMock(name="Score: 0")]
    issue.created_at = datetime.now()
    issue.updated_at = datetime.now()
    issue.comments = 0
    issue.html_url = "https://github.com/ContextLab/llmXive/issues/123"
    return issue


@pytest.fixture
def sample_design_document():
    """Sample technical design document"""
    return """# Technical Design Document: ML Test Project

**Project ID**: ml-test-001
**Date**: 2024-01-15
**Author**: LLM (Automated)

## Abstract
This document outlines a novel approach to machine learning testing...

## Introduction
Background and motivation for the research...

## Proposed Approach
Technical framework and methodology...

## Implementation Strategy
Key components and requirements...

## Evaluation Plan
Success metrics and validation methods...

## Timeline and Milestones
Project schedule...
"""


@pytest.fixture
def sample_brainstorm_response():
    """Sample LLM response for brainstorming"""
    return """Field: Neuroscience
Idea: Develop a novel brain-computer interface using quantum computing principles to decode neural signals with unprecedented accuracy. This approach would combine quantum entanglement theory with neural network architectures to create a more efficient signal processing system. The expected impact includes enabling paralyzed patients to control external devices with near-natural precision.
ID: neuro-quantum-bci-001
Keywords: neuroscience, quantum computing, brain-computer interface, neural decoding, medical devices"""


@pytest.fixture
def sample_review_response():
    """Sample LLM response for review"""
    return """Strengths:
- Clear research objectives and well-defined methodology
- Novel approach combining two cutting-edge fields
- Strong potential for clinical impact
- Comprehensive evaluation plan

Concerns:
- Quantum computing requirements may be prohibitive
- Limited discussion of ethical considerations
- Timeline seems optimistic given complexity

Recommendation: Accept
Score: 0.7
Summary: This is a promising interdisciplinary proposal that merges quantum computing with neuroscience, though implementation challenges need addressing."""


# Test data fixtures
@pytest.fixture
def test_data_dir(tmp_path):
    """Create temporary test data directory"""
    data_dir = tmp_path / "test_data"
    data_dir.mkdir()
    
    # Create sample files
    (data_dir / "sample.txt").write_text("Sample test data")
    (data_dir / "code.py").write_text("def hello():\n    return 'world'")
    
    return data_dir


@pytest.fixture
def mock_llm_responses():
    """Dictionary of mock LLM responses for different task types"""
    return {
        "BRAINSTORM_IDEA": """Field: Computational Biology
Idea: Create an AI system that predicts protein folding patterns using graph neural networks.
ID: compbio-protein-gnn-001
Keywords: protein folding, graph neural networks, computational biology""",
        
        "WRITE_CODE": """```python
def analyze_protein_structure(sequence):
    \"\"\"Analyze protein structure from amino acid sequence.\"\"\"
    # Implementation here
    return {"structure": "alpha-helix", "confidence": 0.95}
```""",
        
        "WRITE_TESTS": """```python
import pytest
from protein_analyzer import analyze_protein_structure

def test_analyze_protein_structure():
    result = analyze_protein_structure("MKTAYIAKQRQISFVKSHFSRQ")
    assert result["confidence"] > 0.8
    assert "structure" in result
```""",
        
        "REVIEW_CODE": """Status: PASS
Issues Found:
- Missing error handling for invalid sequences

Suggestions:
- Add input validation
- Include more comprehensive tests

Code Quality Score: 8/10
Summary: Well-structured code with minor improvements needed."""
    }


@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset all mocks before each test"""
    yield
    # Cleanup after test if needed


@pytest.fixture
def capture_logs(caplog):
    """Capture log output for testing"""
    import logging
    caplog.set_level(logging.DEBUG)
    return caplog