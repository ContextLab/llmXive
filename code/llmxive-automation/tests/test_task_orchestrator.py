"""Unit tests for task orchestration system"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock
from llmxive_automation.task_orchestrator import TaskOrchestrator, TaskType, Task
from llmxive_automation.model_selector import ModelConfig


class TestTaskOrchestrator:
    """Test cases for TaskOrchestrator class"""
    
    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance for testing"""
        model_config = ModelConfig(
            model_id="test/model",
            model_size=2e9,
            likes=100,
            downloads=1000,
            pipeline_tag="text-generation"
        )
        github_manager = Mock()
        prompt_builder = Mock()
        
        return TaskOrchestrator(model_config, github_manager, prompt_builder)
    
    def test_select_next_task_empty_backlog(self, orchestrator):
        """Test task selection with empty backlog"""
        project_state = {
            "Backlog": [],
            "Ready": [],
            "In progress": [],
            "In review": [],
            "Done": []
        }
        
        task = orchestrator.select_next_task(project_state)
        
        assert task.task_type == TaskType.BRAINSTORM_IDEAS
        assert task.priority == 80  # High priority for empty backlog
    
    def test_select_next_task_needs_review(self, orchestrator):
        """Test task selection for items needing review"""
        project_state = {
            "Backlog": [
                {
                    "number": 1,
                    "title": "Test Idea",
                    "labels": ["backlog"],
                    "comments": 0,
                    "updated_at": datetime.now()
                }
            ],
            "Ready": [],
            "In progress": [],
            "In review": [],
            "Done": []
        }
        
        task = orchestrator.select_next_task(project_state)
        
        # Should develop technical design for backlog item
        assert task.task_type == TaskType.DEVELOP_TECHNICAL_DESIGN
        assert task.target["number"] == 1
    
    def test_select_next_task_high_score_review(self, orchestrator):
        """Test task selection for high-score items"""
        project_state = {
            "Backlog": [
                {
                    "number": 1,
                    "title": "High Score Idea",
                    "labels": ["backlog", "score:9.5"],
                    "updated_at": datetime.now()
                }
            ],
            "Ready": [],
            "In progress": [],
            "In review": [],
            "Done": []
        }
        
        task = orchestrator.select_next_task(project_state)
        
        # Should write review to push over threshold
        assert task.task_type == TaskType.WRITE_REVIEW
        assert task.priority == 90
    
    def test_select_next_task_ready_implementation(self, orchestrator):
        """Test task selection for ready items needing implementation"""
        project_state = {
            "Backlog": [],
            "Ready": [
                {
                    "number": 2,
                    "title": "Ready Project",
                    "body": "Technical design complete",
                    "labels": ["ready"],
                    "updated_at": datetime.now()
                }
            ],
            "In progress": [],
            "In review": [],
            "Done": []
        }
        
        task = orchestrator.select_next_task(project_state)
        
        # Should implement research
        assert task.task_type == TaskType.IMPLEMENT_RESEARCH
        assert task.target["number"] == 2
    
    def test_calculate_issue_score(self, orchestrator):
        """Test issue score calculation"""
        issue = {
            "labels": ["score:5.5", "backlog"]
        }
        
        score = orchestrator._calculate_issue_score(issue)
        assert score == 5.5
        
        # Test with no score label
        issue_no_score = {"labels": ["backlog"]}
        score = orchestrator._calculate_issue_score(issue_no_score)
        assert score == 0.0
    
    def test_get_issue_status(self, orchestrator):
        """Test issue status determination"""
        test_cases = [
            (["backlog"], "Backlog"),
            (["ready"], "Ready"),
            (["in-progress"], "In progress"),
            (["in-review"], "In review"),
            (["done"], "Done"),
            ([], "Backlog"),  # Default
        ]
        
        for labels, expected_status in test_cases:
            issue = {"labels": labels}
            status = orchestrator._get_issue_status(issue)
            assert status == expected_status
    
    def test_get_next_status(self, orchestrator):
        """Test workflow progression"""
        test_cases = [
            ("Backlog", "Ready"),
            ("Ready", "In progress"),
            ("In progress", "In review"),
            ("In review", "Done"),
            ("Done", None),
            ("Unknown", None),
        ]
        
        for current, expected_next in test_cases:
            next_status = orchestrator._get_next_status(current)
            assert next_status == expected_next
    
    def test_analyze_project_state(self, orchestrator):
        """Test project state analysis"""
        cutoff_date = datetime.now() - timedelta(days=10)
        
        project_state = {
            "Backlog": [
                {
                    "number": 1,
                    "updated_at": cutoff_date,  # Stale
                    "labels": ["score:9.0"],
                    "comments": 0
                }
            ],
            "Ready": [
                {
                    "number": 2,
                    "body": "needs implementation",
                    "updated_at": datetime.now(),
                    "labels": []
                }
            ],
            "In progress": [],
            "In review": [],
            "Done": []
        }
        
        analysis = orchestrator._analyze_project_state(project_state)
        
        assert analysis["total_issues"] == 2
        assert analysis["backlog_size"] == 1
        assert analysis["ready_size"] == 1
        assert len(analysis["stale_issues"]) == 1
        assert len(analysis["high_score_issues"]) == 1
        assert len(analysis["needs_review"]) == 1
    
    def test_record_task_completion(self, orchestrator):
        """Test task completion recording"""
        task = Task(TaskType.BRAINSTORM_IDEAS, priority=50)
        
        orchestrator.record_task_completion(task, success=True, details={"ideas": 3})
        
        assert len(orchestrator.task_history) == 1
        assert orchestrator.task_history[0]["success"] is True
        assert orchestrator.task_history[0]["details"]["ideas"] == 3
        
        # Test history limit
        for i in range(110):
            orchestrator.record_task_completion(task, success=True)
        
        assert len(orchestrator.task_history) == 100  # Limited to 100