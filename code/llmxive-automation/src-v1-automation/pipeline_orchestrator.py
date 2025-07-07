"""Production pipeline orchestrator for llmXive automation

This orchestrator uses the same pipeline pattern as the test orchestrator
but integrates with real LLM models and the existing automation infrastructure.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from .model_manager import ModelManager
from .conversation_manager import ConversationManager
from .github_handler import GitHubHandler
from .task_executor import TaskExecutor
from .scoring.score_tracker import ScoreTracker
from .scoring.stage_manager import StageManager, ProjectStage

logger = logging.getLogger(__name__)


class ProductionPipelineOrchestrator:
    """Production pipeline orchestrator using real models"""
    
    def __init__(self, github_token: Optional[str] = None, hf_token: Optional[str] = None,
                 model_cache_dir: Optional[str] = None, model_size_gb: float = 3.5,
                 specific_model: Optional[str] = None):
        """
        Initialize production pipeline orchestrator
        
        Args:
            github_token: GitHub access token
            hf_token: HuggingFace token
            model_cache_dir: Directory for model cache
            model_size_gb: Maximum model size in GB
            specific_model: Specific model to use
        """
        self.github_token = github_token
        self.hf_token = hf_token
        self.specific_model = specific_model
        
        # Initialize components
        self.model_mgr = ModelManager(max_size_gb=model_size_gb, cache_dir=model_cache_dir)
        self.github = GitHubHandler(github_token)
        self.score_tracker = ScoreTracker()
        self.stage_manager = StageManager(self.github, self.score_tracker)
        
        # Model and conversation management
        self.model = None
        self.tokenizer = None
        self.conv_mgr = None
        self.executor = None
        
        # Pipeline state
        self.current_project = None
        self.execution_history = []
        
    def initialize_model(self):
        """Load model and initialize conversation manager"""
        logger.info("Loading model...")
        
        if self.specific_model:
            logger.info(f"Loading specific model: {self.specific_model}")
            self.model, self.tokenizer = self.model_mgr._load_model(self.specific_model)
        else:
            self.model, self.tokenizer = self.model_mgr.get_suitable_model()
        
        # Initialize conversation manager and executor
        self.conv_mgr = ConversationManager(self.model, self.tokenizer)
        self.executor = TaskExecutor(self.conv_mgr, self.github)
        
        logger.info(f"Model loaded: {self.model.name_or_path}")
        
    def run_automation_cycle(self, max_tasks: int = 5, 
                           specific_task: Optional[str] = None,
                           project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute automation cycle using pipeline pattern
        
        Args:
            max_tasks: Maximum number of tasks to execute
            specific_task: Specific task type to run
            project_id: Specific project to work on
            
        Returns:
            Execution summary
        """
        start_time = datetime.now()
        
        # Initialize model if needed
        if not self.model:
            self.initialize_model()
            
        # Get project state
        if project_id:
            self.current_project = self._get_project_by_id(project_id)
        else:
            self.current_project = self._select_project()
            
        if not self.current_project:
            logger.warning("No suitable project found")
            return {
                "tasks_completed": 0,
                "tasks_failed": 0,
                "total_tasks": 0,
                "execution_time_seconds": 0,
                "message": "No suitable project found"
            }
            
        # Execute tasks
        tasks_completed = 0
        tasks_failed = 0
        
        if specific_task:
            # Execute specific task
            tasks = [{"type": specific_task, "context": {"project_id": self.current_project["id"]}}]
        else:
            # Generate task queue based on project state
            tasks = self._generate_task_queue(self.current_project, max_tasks)
            
        for i, task in enumerate(tasks):
            logger.info(f"Task {i+1}/{len(tasks)}: {task['type']}")
            
            try:
                result = self._execute_task(task)
                
                if result.get("success"):
                    tasks_completed += 1
                    logger.info("Task completed successfully")
                else:
                    tasks_failed += 1
                    logger.error(f"Task failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                logger.error(f"Task execution error: {e}", exc_info=True)
                tasks_failed += 1
                
        # Save execution history
        self._save_execution_log()
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "tasks_completed": tasks_completed,
            "tasks_failed": tasks_failed,
            "total_tasks": len(tasks),
            "model_used": self.model.name_or_path if self.model else "None",
            "execution_time_seconds": execution_time,
            "project_id": self.current_project["id"] if self.current_project else None,
            "timestamp": datetime.now().isoformat()
        }
        
    def _get_project_by_id(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project details by ID"""
        # Search through issues to find the project
        issues = self.github.get_open_issues()
        
        for issue in issues:
            # Extract project ID from issue
            if self._extract_project_id(issue) == project_id:
                return self._issue_to_project(issue)
                
        return None
        
    def _select_project(self) -> Optional[Dict[str, Any]]:
        """Select the most suitable project to work on"""
        issues = self.github.get_open_issues()
        
        # Score and rank projects
        scored_projects = []
        
        for issue in issues:
            project = self._issue_to_project(issue)
            priority = self._calculate_project_priority(project)
            
            scored_projects.append({
                **project,
                "priority": priority
            })
            
        # Sort by priority
        scored_projects.sort(key=lambda x: x["priority"], reverse=True)
        
        if scored_projects:
            selected = scored_projects[0]
            logger.info(f"Selected project: {selected['id']} (priority: {selected['priority']:.2f})")
            return selected
            
        return None
        
    def _issue_to_project(self, issue) -> Dict[str, Any]:
        """Convert GitHub issue to project dict"""
        labels = [l.name for l in issue.labels]
        stage = self._extract_stage_from_labels(labels)
        
        return {
            "id": self._extract_project_id(issue),
            "issue_number": issue.number,
            "title": issue.title,
            "stage": stage,
            "score": self.github.get_issue_score(issue.number),
            "labels": labels,
            "created_at": issue.created_at,
            "updated_at": issue.updated_at,
            "comments": issue.comments
        }
        
    def _extract_project_id(self, issue) -> str:
        """Extract project ID from issue"""
        import re
        body = getattr(issue, 'body', None) or ""
        id_match = re.search(r'\*\*Suggested ID\*\*:\s*(.+)', body)
        
        if id_match:
            return id_match.group(1).strip()
            
        return f"project-{issue.number}"
        
    def _extract_stage_from_labels(self, labels: List[str]) -> str:
        """Extract stage from labels"""
        stage_map = {
            "stage: backlog": "backlog",
            "stage: ready": "ready", 
            "stage: in-progress": "in_progress",
            "stage: in-review": "in_review",
            "stage: done": "done"
        }
        
        for label in labels:
            if label in stage_map:
                return stage_map[label]
                
        return "backlog"
        
    def _calculate_project_priority(self, project: Dict[str, Any]) -> float:
        """Calculate priority score for a project"""
        priority = 0.0
        
        # Stage-based priority
        stage_priorities = {
            "in_progress": 1.0,  # Highest - finish what's started
            "ready": 0.8,        # High - ready to implement
            "backlog": 0.5,      # Medium - needs advancement
            "in_review": 0.9,    # Very high - almost done
            "done": 0.0          # No priority
        }
        priority += stage_priorities.get(project["stage"], 0.3)
        
        # Score proximity (how close to advancing)
        score = project["score"]
        if project["stage"] == "backlog" and score >= 4:
            priority += 0.2
        elif project["stage"] == "ready" and score >= 4:
            priority += 0.2
        elif project["stage"] == "in_progress" and score >= 0.5:
            priority += 0.1
            
        # Staleness factor
        days_since_update = (datetime.now() - project["updated_at"].replace(tzinfo=None)).days
        if days_since_update > 7:
            priority += 0.1
        elif days_since_update > 14:
            priority += 0.2
            
        return min(priority, 1.5)
        
    def _generate_task_queue(self, project: Dict[str, Any], max_tasks: int) -> List[Dict[str, Any]]:
        """Generate prioritized task queue for project"""
        tasks = []
        project_id = project["id"]
        stage = project["stage"]
        
        if stage == "backlog":
            # Check for technical design
            design_path = f"technical_design_documents/{project_id}/design.md"
            if not self.github.file_exists(design_path):
                tasks.append({
                    "type": "WRITE_TECHNICAL_DESIGN",
                    "context": {"issue_number": project["issue_number"]}
                })
            else:
                # Design exists, get reviews
                tasks.append({
                    "type": "REVIEW_TECHNICAL_DESIGN",
                    "context": {
                        "design_path": design_path,
                        "issue_number": project["issue_number"],
                        "project_id": project_id
                    }
                })
                
        elif stage == "ready":
            # Check for implementation plan
            plan_path = f"implementation_plans/{project_id}/implementation_plan.md"
            if not self.github.file_exists(plan_path):
                tasks.append({
                    "type": "WRITE_IMPLEMENTATION_PLAN",
                    "context": {
                        "issue_number": project["issue_number"],
                        "project_id": project_id
                    }
                })
            else:
                # Check if we can advance
                if project["score"] >= 5:
                    tasks.append({
                        "type": "CHECK_PROJECT_STATUS",
                        "context": {
                            "issue_number": project["issue_number"],
                            "auto_advance": True
                        }
                    })
                else:
                    # Get more reviews
                    tasks.append({
                        "type": "REVIEW_IMPLEMENTATION_PLAN",
                        "context": {
                            "plan_path": plan_path,
                            "issue_number": project["issue_number"]
                        }
                    })
                    
        elif stage == "in_progress":
            # Check what needs to be done
            code_path = f"code/{project_id}"
            paper_path = f"papers/{project_id}"
            
            if not self.github.file_exists(f"{code_path}/helpers"):
                tasks.append({
                    "type": "WRITE_CODE",
                    "context": {
                        "project_id": project_id,
                        "module_name": "main"
                    }
                })
            elif not self.github.file_exists(f"{paper_path}/sections/methods.md"):
                tasks.append({
                    "type": "WRITE_METHODS",
                    "context": {"project_id": project_id}
                })
            elif not self.github.file_exists(f"{paper_path}/sections/introduction.md"):
                tasks.append({
                    "type": "WRITE_INTRODUCTION", 
                    "context": {"project_id": project_id}
                })
            else:
                # Check if ready to advance
                if project["score"] >= 1:
                    tasks.append({
                        "type": "CHECK_PROJECT_STATUS",
                        "context": {
                            "issue_number": project["issue_number"],
                            "auto_advance": True
                        }
                    })
                    
        elif stage == "in_review":
            # Final reviews and preparation
            if project["score"] >= 5:
                tasks.append({
                    "type": "CHECK_PROJECT_STATUS",
                    "context": {
                        "issue_number": project["issue_number"],
                        "auto_advance": True
                    }
                })
            else:
                tasks.append({
                    "type": "REVIEW_PAPER",
                    "context": {
                        "project_id": project_id,
                        "issue_number": project["issue_number"]
                    }
                })
                
        # Always check status at the end
        if tasks and tasks[-1]["type"] != "CHECK_PROJECT_STATUS":
            tasks.append({
                "type": "CHECK_PROJECT_STATUS",
                "context": {"issue_number": project["issue_number"]}
            })
            
        return tasks[:max_tasks]
        
    def _execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single task"""
        task_type = task["type"]
        context = task.get("context", {})
        
        # Record start
        self.execution_history.append({
            "timestamp": datetime.now().isoformat(),
            "task": task,
            "project_id": self.current_project["id"] if self.current_project else None
        })
        
        try:
            # Use the existing task executor
            result = self.executor.execute_task(task_type, context)
            
            # Update execution history
            self.execution_history[-1]["result"] = result
            
            # Handle stage advancement if needed
            if result.get("success") and task_type == "CHECK_PROJECT_STATUS":
                if result.get("advanced"):
                    logger.info(f"Project advanced to {result.get('new_stage')}")
                    
            return result
            
        except Exception as e:
            error_result = {
                "success": False,
                "error": str(e),
                "task_type": task_type
            }
            self.execution_history[-1]["result"] = error_result
            return error_result
            
    def _save_execution_log(self):
        """Save execution history"""
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_path = os.path.join(log_dir, f"pipeline_execution_{timestamp}.json")
        
        with open(log_path, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "model": self.model.name_or_path if self.model else "None",
                "project": self.current_project,
                "execution_history": self.execution_history
            }, f, indent=2, default=str)
            
        logger.info(f"Execution log saved to {log_path}")