"""Task orchestration system for managing the research pipeline"""

import logging
import random
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from .model_selector import ModelConfig
from .github_manager import GitHubManager
from .prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Types of tasks the system can perform"""
    BRAINSTORM_IDEAS = "brainstorm_ideas"
    DEVELOP_TECHNICAL_DESIGN = "develop_technical_design"
    WRITE_REVIEW = "write_review"
    IMPLEMENT_RESEARCH = "implement_research"
    GENERATE_PAPER = "generate_paper"
    VALIDATE_REFERENCES = "validate_references"
    UPDATE_PROJECT_STATUS = "update_project_status"


@dataclass
class Task:
    """Represents a task to be executed"""
    task_type: TaskType
    priority: int
    target: Optional[Dict] = None
    context: Dict = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}


class TaskOrchestrator:
    """Orchestrates research tasks based on project state"""
    
    def __init__(self, model_config: ModelConfig, github_manager: GitHubManager, 
                 prompt_builder: PromptBuilder):
        """
        Initialize task orchestrator
        
        Args:
            model_config: Configuration for the selected model
            github_manager: GitHub API manager
            prompt_builder: Prompt construction system
        """
        self.model_config = model_config
        self.github = github_manager
        self.prompt_builder = prompt_builder
        self.task_history = []
        
    def select_next_task(self, project_state: Dict[str, List[Dict]]) -> Task:
        """
        Select the most appropriate task based on project state
        
        Args:
            project_state: Current state of the project board
            
        Returns:
            Selected Task object
        """
        # Analyze project state
        analysis = self._analyze_project_state(project_state)
        
        # Generate candidate tasks
        candidates = self._generate_candidate_tasks(analysis)
        
        # Score and select best task
        if candidates:
            candidates.sort(key=lambda t: t.priority, reverse=True)
            selected = candidates[0]
            logger.info(f"Selected task: {selected.task_type.value} with priority {selected.priority}")
            return selected
        
        # Default to brainstorming if no other tasks
        logger.info("No specific tasks identified, defaulting to brainstorming")
        return Task(TaskType.BRAINSTORM_IDEAS, priority=50)
    
    def _analyze_project_state(self, project_state: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Analyze the current project state"""
        analysis = {
            "total_issues": sum(len(issues) for issues in project_state.values()),
            "backlog_size": len(project_state.get("Backlog", [])),
            "ready_size": len(project_state.get("Ready", [])),
            "in_progress_size": len(project_state.get("In progress", [])),
            "in_review_size": len(project_state.get("In review", [])),
            "done_size": len(project_state.get("Done", [])),
            "stale_issues": [],
            "high_score_issues": [],
            "needs_implementation": [],
            "needs_review": []
        }
        
        # Find stale issues (no update in 7 days)
        cutoff_date = datetime.now() - timedelta(days=7)
        
        for status, issues in project_state.items():
            for issue in issues:
                # Check if stale
                updated = issue.get("updated_at")
                if updated and isinstance(updated, datetime):
                    if updated < cutoff_date:
                        analysis["stale_issues"].append(issue)
                
                # Check review scores
                score = self._calculate_issue_score(issue)
                if score >= 8:  # Close to threshold
                    analysis["high_score_issues"].append((issue, score))
                
                # Check if needs implementation
                if status == "Ready" and "implementation" not in str(issue.get("body", "")).lower():
                    analysis["needs_implementation"].append(issue)
                
                # Check if needs review
                if status in ["In progress", "Backlog"] and issue.get("comments", 0) == 0:
                    analysis["needs_review"].append(issue)
        
        return analysis
    
    def _generate_candidate_tasks(self, analysis: Dict[str, Any]) -> List[Task]:
        """Generate candidate tasks based on analysis"""
        candidates = []
        
        # 1. Check if we need more ideas in backlog
        if analysis["backlog_size"] < 10:
            candidates.append(Task(
                TaskType.BRAINSTORM_IDEAS,
                priority=80,
                context={"reason": "Low backlog size"}
            ))
        
        # 2. Develop technical designs for high-potential backlog items
        for issue in analysis["needs_review"][:3]:  # Top 3
            if "Backlog" in self._get_issue_status(issue):
                candidates.append(Task(
                    TaskType.DEVELOP_TECHNICAL_DESIGN,
                    priority=70,
                    target=issue,
                    context={"issue": issue}
                ))
        
        # 3. Write reviews for items close to threshold
        for issue, score in analysis["high_score_issues"]:
            if score < 10:  # Not yet at threshold
                candidates.append(Task(
                    TaskType.WRITE_REVIEW,
                    priority=90,  # High priority to push over threshold
                    target=issue,
                    context={"issue": issue, "current_score": score}
                ))
        
        # 4. Implement research for ready items
        for issue in analysis["needs_implementation"][:2]:  # Top 2
            candidates.append(Task(
                TaskType.IMPLEMENT_RESEARCH,
                priority=85,
                target=issue,
                context={"issue": issue}
            ))
        
        # 5. Generate papers for implemented work
        in_progress = analysis.get("in_progress_size", 0)
        if in_progress > 0:
            # Check if any in-progress items have implementations
            for issue in analysis.get("project_state", {}).get("In progress", []):
                if self._has_implementation(issue):
                    candidates.append(Task(
                        TaskType.GENERATE_PAPER,
                        priority=75,
                        target=issue,
                        context={"issue": issue}
                    ))
        
        # 6. Validate references for papers in review
        for issue in analysis.get("project_state", {}).get("In review", []):
            if self._needs_reference_validation(issue):
                candidates.append(Task(
                    TaskType.VALIDATE_REFERENCES,
                    priority=95,  # Very high priority
                    target=issue,
                    context={"issue": issue}
                ))
        
        # 7. Update project status for completed reviews
        for issue, score in analysis["high_score_issues"]:
            if score >= 10:
                current_status = self._get_issue_status(issue)
                next_status = self._get_next_status(current_status)
                if next_status:
                    candidates.append(Task(
                        TaskType.UPDATE_PROJECT_STATUS,
                        priority=100,  # Highest priority
                        target=issue,
                        context={
                            "issue": issue,
                            "current_status": current_status,
                            "next_status": next_status
                        }
                    ))
        
        return candidates
    
    def _calculate_issue_score(self, issue: Dict) -> float:
        """Calculate total review score for an issue"""
        score = 0.0
        
        # Parse score from labels
        for label in issue.get("labels", []):
            if label.startswith("score:"):
                try:
                    score = float(label.split(":")[1])
                except:
                    pass
        
        return score
    
    def _get_issue_status(self, issue: Dict) -> str:
        """Determine issue status from labels"""
        labels = [l.lower() for l in issue.get("labels", [])]
        
        status_map = {
            "done": "Done",
            "in-review": "In review",
            "in-progress": "In progress",
            "ready": "Ready",
            "backlog": "Backlog"
        }
        
        for label in labels:
            for key, status in status_map.items():
                if key in label:
                    return status
        
        return "Backlog"  # Default
    
    def _get_next_status(self, current_status: str) -> Optional[str]:
        """Get the next status in the workflow"""
        workflow = ["Backlog", "Ready", "In progress", "In review", "Done"]
        
        try:
            current_index = workflow.index(current_status)
            if current_index < len(workflow) - 1:
                return workflow[current_index + 1]
        except ValueError:
            pass
        
        return None
    
    def _has_implementation(self, issue: Dict) -> bool:
        """Check if an issue has associated implementation"""
        # Simple heuristic - check if implementation mentioned in comments
        # In production, would check for linked code files
        body = issue.get("body", "").lower()
        return "implementation" in body or "code" in body
    
    def _needs_reference_validation(self, issue: Dict) -> bool:
        """Check if an issue needs reference validation"""
        # Check if it's a paper that hasn't been validated
        body = issue.get("body", "").lower()
        labels = [l.lower() for l in issue.get("labels", [])]
        
        has_paper = "paper" in body or "manuscript" in body
        validated = "references-validated" in labels
        
        return has_paper and not validated
    
    def record_task_completion(self, task: Task, success: bool, details: Dict = None):
        """Record task completion for learning"""
        self.task_history.append({
            "task": task,
            "success": success,
            "timestamp": datetime.now(),
            "details": details or {}
        })
        
        # Keep only recent history
        if len(self.task_history) > 100:
            self.task_history = self.task_history[-100:]