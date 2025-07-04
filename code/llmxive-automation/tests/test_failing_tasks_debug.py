#!/usr/bin/env python3
"""Debug script for the 3 failing tasks"""

import os
import sys
from unittest.mock import Mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.task_executor import TaskExecutor
from src.conversation_manager import ConversationManager
from src.github_handler import GitHubHandler


def test_review_technical_design():
    """Debug REVIEW_TECHNICAL_DESIGN task"""
    print("\n=== Testing REVIEW_TECHNICAL_DESIGN ===")
    
    # Setup
    conv_mgr = Mock(spec=ConversationManager)
    conv_mgr.model_name = "test-model"
    github = Mock(spec=GitHubHandler)
    
    # Mock responses
    github.get_file_content.return_value = "# Technical Design\n\nThis is a test design document."
    conv_mgr.query_model.return_value = """Score: 8.5

Strengths:
- Clear methodology
- Novel approach
- Good feasibility

Concerns:
- Needs more evaluation metrics
- Timeline seems aggressive

Recommendation: Accept
Summary: Strong proposal with minor revisions needed."""
    
    github.create_file.return_value = True
    github.get_issue_score.return_value = 5.0
    github.update_issue_score.return_value = True
    
    executor = TaskExecutor(conv_mgr, github)
    
    # Test with proper context
    context = {
        "design_path": "technical_design_documents/test-proj/design.md",
        "project_id": "test-proj",  # This was missing in the test!
        "issue_number": 123
    }
    
    result = executor.execute_task("REVIEW_TECHNICAL_DESIGN", context)
    print(f"Result: {result}")
    print(f"Success: {result.get('success', False)}")
    if not result.get('success'):
        print(f"Error: {result.get('error')}")
        if 'raw_response' in result:
            print(f"Raw response: {result['raw_response']}")


def test_update_readme_table():
    """Debug UPDATE_README_TABLE task"""
    print("\n=== Testing UPDATE_README_TABLE ===")
    
    # Setup
    conv_mgr = Mock(spec=ConversationManager)
    conv_mgr.model_name = "test-model"
    github = Mock(spec=GitHubHandler)
    
    # Mock responses
    github.get_file_content.return_value = """# README

## Projects Table

| ID | Name | Status |
|----|------|--------|
| p1 | Project 1 | Active |
"""
    
    conv_mgr.query_model.return_value = "| test-proj | Test Project | In Progress |"
    github.insert_table_row.return_value = True
    
    executor = TaskExecutor(conv_mgr, github)
    
    # Test with CORRECT parameter names
    context = {
        "file_path": "README.md",  # Not readme_path
        "table_identifier": "Projects Table",  # Not table_name
        "new_entry": {"id": "test-proj", "name": "Test Project", "status": "In Progress"}  # Not new_row
    }
    
    result = executor.execute_task("UPDATE_README_TABLE", context)
    print(f"Result: {result}")
    print(f"Success: {result.get('success', False)}")
    if not result.get('success'):
        print(f"Error: {result.get('error')}")


def test_fork_idea():
    """Debug FORK_IDEA task"""
    print("\n=== Testing FORK_IDEA ===")
    
    # Setup
    conv_mgr = Mock(spec=ConversationManager)
    conv_mgr.model_name = "test-model"
    github = Mock(spec=GitHubHandler)
    
    # Mock original issue
    original_issue = Mock()
    original_issue.number = 123
    original_issue.title = "Original Research Idea"
    original_issue.body = """**Field**: Computer Science
**Abstract**: This is the original idea
**Approach**: Novel approach"""
    
    github.get_issue.return_value = original_issue
    
    # Mock model response with proper format
    conv_mgr.query_model.return_value = """Title: Variation 1 - Applied to Biology
Field: Biology
Idea: Apply the same technique to biological systems
Abstract: Testing in biological context
Approach: Adapted approach for bio

Title: Variation 2 - Different Method
Field: Computer Science  
Idea: Use alternative algorithm for same problem
Abstract: Different algorithmic approach
Approach: New method

Title: Variation 3 - Extended Complexity
Field: Computer Science
Idea: Extend original with multi-modal inputs
Abstract: Enhanced version with more features
Approach: Extended framework"""
    
    # Mock issue creation
    created_issue = Mock()
    created_issue.number = 124
    github.create_issue.return_value = created_issue
    
    executor = TaskExecutor(conv_mgr, github)
    
    # Test with correct parameter name
    context = {
        "issue_number": 123  # This is correct but was being called as parent_issue in test
    }
    
    result = executor.execute_task("FORK_IDEA", context)
    print(f"Result: {result}")
    print(f"Success: {result.get('success', False)}")
    if not result.get('success'):
        print(f"Error: {result.get('error')}")
    else:
        print(f"Created issues: {result.get('forked_issues', [])}")


def test_parse_issue_for_idea():
    """Test the _parse_issue_for_idea helper"""
    print("\n=== Testing _parse_issue_for_idea helper ===")
    
    # Setup
    conv_mgr = Mock(spec=ConversationManager)
    github = Mock(spec=GitHubHandler)
    executor = TaskExecutor(conv_mgr, github)
    
    # Test issue
    issue = Mock()
    issue.title = "[Idea] Test Research Idea"
    issue.body = """**Field**: Computer Science

**Abstract**: This is a test abstract

**Approach**: Novel approach using AI

**Keywords**: AI, machine learning, research"""
    
    result = executor._parse_issue_for_idea(issue)
    print(f"Parsed result: {result}")


if __name__ == "__main__":
    test_review_technical_design()
    test_update_readme_table()
    test_fork_idea()
    test_parse_issue_for_idea()