"""Unit tests for TaskExecutor"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from src.task_executor import TaskExecutor


class TestTaskExecutor:
    """Test suite for TaskExecutor"""
    
    def test_initialization(self, task_executor):
        """Test TaskExecutor initialization"""
        assert task_executor.conv_mgr is not None
        assert task_executor.github is not None
        assert task_executor.parser is not None
        assert len(task_executor.task_handlers) > 40  # Should have all task types
    
    def test_execute_task_unknown_type(self, task_executor):
        """Test executing unknown task type"""
        result = task_executor.execute_task("UNKNOWN_TASK_TYPE", {})
        
        assert result['success'] is False
        assert "Unknown task type" in result['error']
    
    def test_execute_task_exception_handling(self, task_executor):
        """Test exception handling in task execution"""
        # Make a handler raise an exception
        task_executor.task_handlers["BRAINSTORM_IDEA"] = Mock(
            side_effect=Exception("Test error")
        )
        
        result = task_executor.execute_task("BRAINSTORM_IDEA", {})
        
        assert result['success'] is False
        assert "Test error" in result['error']
        assert result['task_type'] == "BRAINSTORM_IDEA"
    
    def test_brainstorm_idea_success(self, task_executor, sample_brainstorm_response):
        """Test successful idea brainstorming"""
        # Mock dependencies
        task_executor.github.get_backlog_ideas.return_value = []
        task_executor.conv_mgr.query_model.return_value = sample_brainstorm_response
        
        mock_issue = MagicMock()
        mock_issue.number = 123
        mock_issue.html_url = "https://github.com/test/issue/123"
        task_executor.github.create_issue.return_value = mock_issue
        
        result = task_executor.execute_brainstorm({})
        
        assert result['success'] is True
        assert result['issue_number'] == 123
        assert 'idea' in result
        
        # Check issue was created with correct labels
        create_call = task_executor.github.create_issue.call_args
        assert "backlog" in create_call[1]['labels']
        assert "idea" in create_call[1]['labels']
        assert "Score: 0" in create_call[1]['labels']
    
    def test_brainstorm_idea_parse_failure(self, task_executor):
        """Test brainstorming with parse failure"""
        task_executor.github.get_backlog_ideas.return_value = []
        task_executor.conv_mgr.query_model.return_value = "Invalid response format"
        
        result = task_executor.execute_brainstorm({})
        
        assert result['success'] is False
        assert "Failed to parse response" in result['error']
        assert 'raw_response' in result
    
    def test_write_technical_design(self, task_executor, sample_issue):
        """Test writing technical design document"""
        # Setup mocks
        task_executor.github.get_issue.return_value = sample_issue
        task_executor.conv_mgr.query_model.return_value = "# Technical Design\n\nDetailed design..."
        task_executor.github.create_file.return_value = True
        
        result = task_executor.execute_technical_design({'issue_number': 123})
        
        assert result['success'] is True
        assert 'design_path' in result
        assert result['project_id'] == 'ml-test-001'
        
        # Check file creation
        create_call = task_executor.github.create_file.call_args
        assert "technical_design_documents/ml-test-001/design.md" in create_call[0]
    
    def test_review_technical_design(self, task_executor, sample_design_document, sample_review_response):
        """Test reviewing technical design"""
        # Setup mocks
        task_executor.github.get_file_content.return_value = sample_design_document
        task_executor.conv_mgr.query_model.return_value = sample_review_response
        task_executor.github.create_file.return_value = True
        task_executor.github.get_issue_score.return_value = 5.0
        task_executor.github.update_issue_score.return_value = True
        
        context = {
            'design_path': 'technical_design_documents/test/design.md',
            'issue_number': 123,
            'project_id': 'test-001'
        }
        
        result = task_executor.execute_design_review(context)
        
        assert result['success'] is True
        assert result['score'] == 0.7
        assert result['recommendation'] == "Accept"
        
        # Check score update
        task_executor.github.update_issue_score.assert_called_with(123, 5.35)  # 5.0 + 0.7*0.5
    
    def test_write_code(self, task_executor):
        """Test code writing task"""
        # Setup mocks
        plan_content = "Implementation plan with module specifications..."
        task_executor.github.get_file_content.return_value = plan_content
        
        code_response = '''```python
def analyze_data(data):
    """Analyze research data."""
    return {"mean": sum(data)/len(data)}
```'''
        task_executor.conv_mgr.query_model.return_value = code_response
        task_executor.github.create_file.return_value = True
        
        context = {
            'plan_path': 'implementation_plans/test/plan.md',
            'project_id': 'test-001',
            'module_name': 'analyzer'
        }
        
        result = task_executor.execute_code_writing(context)
        
        assert result['success'] is True
        assert result['module_name'] == 'analyzer'
        assert 'lines_of_code' in result
        
        # Check code extraction worked
        create_call = task_executor.github.create_file.call_args
        assert "def analyze_data" in create_call[0][1]
    
    def test_write_tests(self, task_executor):
        """Test writing unit tests"""
        # Mock code to test
        code_content = '''def add(a, b):
    return a + b'''
        
        task_executor.github.get_file_content.return_value = code_content
        
        test_response = '''```python
import pytest
from module import add

def test_add_positive():
    assert add(2, 3) == 5

def test_add_negative():
    assert add(-1, 1) == 0
```'''
        
        task_executor.conv_mgr.query_model.return_value = test_response
        task_executor.github.create_file.return_value = True
        
        context = {'code_path': 'code/project/src/module.py'}
        result = task_executor.execute_test_writing(context)
        
        assert result['success'] is True
        assert result['num_tests'] == 2
        assert 'test_path' in result
    
    def test_literature_search(self, task_executor):
        """Test literature search in llmXive archive"""
        # Mock papers README
        papers_readme = """## Completed work

| ID | Title | Status | Issue | Paper | Contributors |
|----|-------|--------|-------|-------|--------------|
| ml-001 | Machine Learning Study | Done | #1 | [Paper](link) | @user1 |
| neuro-001 | Neuroscience Research | Done | #2 | [Paper](link) | @user2 |
"""
        
        task_executor.github.get_file_content.side_effect = [
            papers_readme,  # First call for README
            "Abstract: Machine learning paper content...",  # Paper 1
            "Abstract: Neuroscience paper content..."  # Paper 2
        ]
        
        task_executor.github.create_file.return_value = True
        
        context = {
            'topic': 'machine learning',
            'keywords': ['ML', 'neural'],
            'project_id': 'test-001'
        }
        
        result = task_executor.execute_literature_search(context)
        
        assert result['success'] is True
        assert result['papers_found'] >= 0
        assert 'bibliography_path' in result
    
    def test_check_project_status(self, task_executor):
        """Test project status checking"""
        # Mock issue
        mock_issue = MagicMock()
        mock_issue.number = 123
        mock_issue.labels = [MagicMock(name="backlog")]
        
        task_executor.github.get_issue.return_value = mock_issue
        task_executor.github.get_issue_score.return_value = 12.0
        task_executor.github.update_issue_stage.return_value = True
        
        context = {
            'issue_number': 123,
            'auto_advance': True
        }
        
        result = task_executor.execute_status_check(context)
        
        assert result['success'] is True
        assert result['current_stage'] == 'backlog'
        assert result['next_stage'] == 'ready'
        assert result['can_advance'] is True
        
        # Should auto-advance
        task_executor.github.update_issue_stage.assert_called_with(123, 'ready')
    
    def test_create_issue_comment(self, task_executor):
        """Test creating issue comment"""
        task_executor.github.create_issue_comment.return_value = True
        
        context = {
            'issue_number': 123,
            'comment': 'Test comment text'
        }
        
        result = task_executor.execute_issue_comment(context)
        
        assert result['success'] is True
        
        # Check comment was posted with footer
        comment_call = task_executor.github.create_issue_comment.call_args
        assert "Test comment text" in comment_call[0][1]
        assert "llmXive automation system" in comment_call[0][1]
    
    def test_update_readme_table(self, task_executor):
        """Test updating README table"""
        # Mock file content
        readme_content = """# Project README

## Projects Table

| ID | Name | Status |
|----|------|--------|
| p1 | Proj1 | Active |
"""
        
        task_executor.github.get_file_content.return_value = readme_content
        task_executor.conv_mgr.query_model.return_value = "| p2 | Proj2 | New |"
        task_executor.github.insert_table_row.return_value = True
        
        context = {
            'file_path': 'README.md',
            'table_identifier': 'Projects Table',
            'new_entry': {'id': 'p2', 'name': 'Proj2', 'status': 'New'}
        }
        
        result = task_executor.execute_readme_update(context)
        
        assert result['success'] is True
        assert 'row_added' in result
    
    def test_paper_writing_tasks(self, task_executor):
        """Test various paper writing tasks"""
        # Mock common dependencies
        task_executor.github.get_file_content.return_value = "Mock content"
        task_executor.conv_mgr.query_model.return_value = "Generated paper section content..."
        task_executor.github.create_file.return_value = True
        
        # Test abstract writing
        result = task_executor.execute_abstract_writing({'project_id': 'test-001'})
        assert result['success'] is True
        assert 'word_count' in result
        
        # Test introduction writing
        result = task_executor.execute_intro_writing({
            'design_path': 'path/to/design.md',
            'project_id': 'test-001'
        })
        assert result['success'] is True
        
        # Test methods writing
        result = task_executor.execute_methods_writing({
            'implementation_path': 'path/to/impl.md',
            'project_id': 'test-001'
        })
        assert result['success'] is True
        
        # Test results writing
        result = task_executor.execute_results_writing({
            'analysis_results': 'Statistical results...',
            'project_id': 'test-001'
        })
        assert result['success'] is True
        
        # Test discussion writing
        result = task_executor.execute_discussion_writing({
            'project_id': 'test-001'
        })
        assert result['success'] is True
    
    def test_review_tasks(self, task_executor):
        """Test review tasks"""
        task_executor.github.get_file_content.return_value = "Content to review"
        task_executor.conv_mgr.query_model.return_value = "Review feedback..."
        task_executor.github.create_file.return_value = True
        task_executor.github.create_issue_comment.return_value = True
        
        # Test paper review
        result = task_executor.execute_paper_review({
            'paper_path': 'papers/test/paper.md',
            'project_id': 'test-001'
        })
        assert result['success'] is True
        
        # Test code review
        result = task_executor.execute_code_review({
            'code_path': 'code/test.py',
            'issue_number': 123
        })
        assert result['success'] is True
    
    def test_helper_methods(self, task_executor):
        """Test helper methods"""
        # Test _parse_issue_for_idea
        mock_issue = MagicMock()
        mock_issue.title = "Test Issue"
        mock_issue.body = """**Field**: Computer Science
**Description**: Test description
**Suggested ID**: cs-test-001
**Keywords**: test, keywords"""
        
        result = task_executor._parse_issue_for_idea(mock_issue)
        
        assert result['field'] == 'Computer Science'
        assert result['description'] == 'Test description'
        assert result['id'] == 'cs-test-001'
        assert 'test, keywords' in result['keywords']
    
    def test_error_handling_missing_context(self, task_executor):
        """Test error handling for missing context parameters"""
        # Test missing issue_number
        result = task_executor.execute_technical_design({})
        assert result['success'] is False
        assert "No issue_number provided" in result['error']
        
        # Test missing code_path
        result = task_executor.execute_test_writing({})
        assert result['success'] is False
        assert "No code_path provided" in result['error']
        
        # Test missing file paths
        result = task_executor.execute_design_review({})
        assert result['success'] is False
        assert "No design_path provided" in result['error']