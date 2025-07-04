"""Pytest configuration and fixtures for llmXive automation tests - REAL tests only, no mocks!"""

import os
import sys
import pytest
import tempfile
import shutil
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from src.model_manager import ModelManager
from src.conversation_manager import ConversationManager
from src.github_handler import GitHubHandler
from src.response_parser import ResponseParser
from src.task_executor import TaskExecutor
from src.orchestrator import LLMXiveOrchestrator
from src.model_attribution import ModelAttributionTracker


@pytest.fixture(scope="session")
def real_small_model():
    """Load a real small model for testing - session scoped to avoid reloading"""
    print("\nLoading real model for test session...")
    model_mgr = ModelManager(max_size_gb=1.5)
    
    # Use TinyLlama as it's small and reliable
    model, tokenizer = model_mgr._load_model("TinyLlama/TinyLlama-1.1B-Chat-v1.0")
    return model, tokenizer


@pytest.fixture
def real_github():
    """Create real GitHub handler - uses CLI fallback if no token"""
    test_repo = os.environ.get('TEST_REPO', 'ContextLab/llmXive')
    token = os.environ.get('GITHUB_TOKEN')
    
    if not token:
        print("Note: No GITHUB_TOKEN set, using CLI fallback")
    
    return GitHubHandler(token=token, repo_name=test_repo)


@pytest.fixture
def real_conversation_manager(real_small_model):
    """Create real conversation manager with actual model"""
    model, tokenizer = real_small_model
    return ConversationManager(model, tokenizer)


@pytest.fixture
def real_task_executor(real_conversation_manager, real_github):
    """Create real task executor with actual components"""
    return TaskExecutor(real_conversation_manager, real_github)


@pytest.fixture
def response_parser():
    """Response parser instance - this is a pure logic component"""
    return ResponseParser()


@pytest.fixture
def real_orchestrator():
    """Create real orchestrator with actual components"""
    token = os.environ.get('GITHUB_TOKEN')
    return LLMXiveOrchestrator(
        github_token=token,
        model_size_gb=1.5,  # Use small model for tests
        specific_model="TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    )


@pytest.fixture
def test_workspace(tmp_path):
    """Create a temporary workspace for test files"""
    workspace = tmp_path / "test_workspace"
    workspace.mkdir()
    
    # Create some test structure
    (workspace / "papers").mkdir()
    (workspace / "code").mkdir()
    (workspace / "data").mkdir()
    (workspace / "technical_design_documents").mkdir()
    (workspace / "implementation_plans").mkdir()
    (workspace / "reviews").mkdir()
    
    # Create a sample README
    readme_content = """# Test Project

## Papers

| ID | Title | Status | Contributors | Date |
|----|-------|---------|--------------|------|
| test-001 | Test Paper | Done | @testuser | 2024-01-15 |
"""
    (workspace / "papers" / "README.md").write_text(readme_content)
    
    yield workspace
    
    # Cleanup
    shutil.rmtree(workspace)


@pytest.fixture
def real_attribution_tracker(tmp_path):
    """Create real attribution tracker with temporary file"""
    tracker_file = tmp_path / "test_attributions.json"
    tracker = ModelAttributionTracker(str(tracker_file))
    
    yield tracker
    
    # Cleanup
    if tracker_file.exists():
        tracker_file.unlink()


@pytest.fixture
def sample_github_issue_data():
    """Sample issue data that matches real GitHub issue structure"""
    return {
        'number': 999,
        'title': 'Test Research Idea: Quantum Computing Applications',
        'body': """**Field**: Quantum Computing
**Description**: Exploring novel quantum algorithms for optimization
**Suggested ID**: quantum-opt-001
**Keywords**: quantum computing, optimization, algorithms""",
        'state': 'open',
        'labels': ['backlog', 'Score: 0'],
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
        'html_url': 'https://github.com/ContextLab/llmXive/issues/999',
        'user': {'login': 'testuser'},
        'comments': 0
    }


@pytest.fixture
def sample_design_document():
    """Sample technical design document content"""
    return """# Technical Design Document: Quantum Optimization Framework

**Project ID**: quantum-opt-001
**Date**: 2024-01-15
**Author**: LLM (Automated)

## Abstract
This document outlines a novel quantum computing framework for solving optimization problems...

## Introduction
Background and motivation for quantum optimization research...

## Proposed Approach
Technical framework leveraging quantum annealing and gate-based algorithms...

## Implementation Strategy
Key components including quantum circuit design and classical preprocessing...

## Evaluation Plan
Benchmarking against classical algorithms on standard optimization problems...

## Timeline and Milestones
- Month 1-2: Algorithm development
- Month 3-4: Implementation
- Month 5-6: Testing and optimization
"""


@pytest.fixture
def test_data_files(tmp_path):
    """Create temporary test data files"""
    data_dir = tmp_path / "test_data"
    data_dir.mkdir()
    
    # Create various test files
    (data_dir / "sample.txt").write_text("Sample test data for processing")
    
    (data_dir / "test_code.py").write_text("""
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

def test_factorial():
    assert factorial(5) == 120
    assert factorial(0) == 1
""")
    
    (data_dir / "data.csv").write_text("""x,y
1,2
3,4
5,6
""")
    
    return data_dir


@pytest.fixture(autouse=True)
def capture_logs(caplog):
    """Capture log output for all tests"""
    import logging
    caplog.set_level(logging.DEBUG)
    return caplog


@pytest.fixture
def env_backup():
    """Backup and restore environment variables"""
    backup = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(backup)


# Markers for different test types
def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires external services)"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow (may take several seconds)"
    )
    config.addinivalue_line(
        "markers", "requires_github: mark test as requiring GitHub access"
    )
    config.addinivalue_line(
        "markers", "requires_model: mark test as requiring model loading"
    )