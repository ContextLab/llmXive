"""Main orchestration logic for llmXive automation"""

import os
import json
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from .model_manager import ModelManager
from .conversation_manager import ConversationManager
from .github_handler import GitHubHandler
from .task_executor import TaskExecutor

logger = logging.getLogger(__name__)


class LLMXiveOrchestrator:
    """Main orchestration for the automation system"""
    
    def __init__(self, github_token: str, hf_token: Optional[str] = None,
                 model_cache_dir: Optional[str] = None):
        """
        Initialize orchestrator
        
        Args:
            github_token: GitHub access token
            hf_token: HuggingFace token (optional)
            model_cache_dir: Directory for model cache
        """
        self.github_token = github_token
        self.hf_token = hf_token
        
        # Initialize components
        self.model_mgr = ModelManager(cache_dir=model_cache_dir)
        self.github = GitHubHandler(github_token)
        
        # Task queue and logs
        self.task_queue: List[Dict[str, Any]] = []
        self.execution_log: List[Dict[str, Any]] = []
        
        # Load model and set up executor
        self.model = None
        self.tokenizer = None
        self.conv_mgr = None
        self.executor = None
        
    def initialize_model(self):
        """Load model and initialize conversation manager"""
        logger.info("Loading model...")
        self.model, self.tokenizer = self.model_mgr.get_suitable_model()
        
        # Initialize conversation manager
        self.conv_mgr = ConversationManager(self.model, self.tokenizer)
        
        # Initialize task executor
        self.executor = TaskExecutor(self.conv_mgr, self.github)
        
        logger.info(f"Model loaded: {self.model.name_or_path}")
        
    def run_automation_cycle(self, max_tasks: int = 5, 
                           specific_task: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute one full automation cycle
        
        Args:
            max_tasks: Maximum number of tasks to execute
            specific_task: Specific task type to run (optional)
            
        Returns:
            Execution summary
        """
        start_time = datetime.now()
        
        # Initialize model if not already loaded
        if not self.model:
            self.initialize_model()
            
        # Step 1: Analyze project state
        logger.info("Analyzing project state...")
        project_state = self.analyze_project_state()
        
        # Step 2: Generate or use specific task
        if specific_task:
            self.task_queue = [{
                "type": specific_task,
                "context": {},
                "priority_score": 1.0
            }]
        else:
            # Generate prioritized task queue
            self.task_queue = self.prioritize_tasks(project_state)
            
        # Step 3: Execute tasks
        tasks_completed = 0
        tasks_failed = 0
        
        for i, task in enumerate(self.task_queue[:max_tasks]):
            logger.info(f"Task {i+1}/{min(len(self.task_queue), max_tasks)}: "
                       f"{task['type']} (priority: {task.get('priority_score', 0):.2f})")
            
            try:
                result = self.executor.execute_task(
                    task_type=task['type'],
                    context=task.get('context', {})
                )
                
                self.execution_log.append({
                    "task": task,
                    "result": result,
                    "timestamp": datetime.now().isoformat(),
                    "model": self.model.name_or_path
                })
                
                if result.get("success"):
                    tasks_completed += 1
                    logger.info(f"Task completed successfully")
                else:
                    tasks_failed += 1
                    logger.error(f"Task failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                logger.error(f"Task execution error: {e}", exc_info=True)
                tasks_failed += 1
                
        # Step 4: Save execution log
        self.save_execution_log()
        
        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "tasks_completed": tasks_completed,
            "tasks_failed": tasks_failed,
            "total_tasks": len(self.task_queue[:max_tasks]),
            "model_used": self.model.name_or_path if self.model else "None",
            "execution_time_seconds": execution_time,
            "timestamp": datetime.now().isoformat()
        }
        
    def analyze_project_state(self) -> Dict[str, Any]:
        """Analyze current state of the llmXive project"""
        state = {
            "backlog_items": [],
            "ready_items": [],
            "in_progress_items": [],
            "pipeline_gaps": [],
            "stale_items": [],
            "repo_stats": {}
        }
        
        # Get all open issues
        open_issues = self.github.get_open_issues()
        
        for issue in open_issues:
            labels = [l.name for l in issue.labels]
            
            # Get human interest signals
            reactions = self.github.get_issue_reactions(issue.number)
            human_score = reactions['thumbsup'] - reactions['thumbsdown']
            
            # Check staleness
            days_old = (datetime.now() - issue.created_at.replace(tzinfo=None)).days
            last_updated = (datetime.now() - issue.updated_at.replace(tzinfo=None)).days
            
            item_data = {
                "number": issue.number,
                "title": issue.title,
                "labels": labels,
                "score": self.github.get_issue_score(issue.number),
                "human_interest": human_score,
                "reactions": reactions,
                "days_old": days_old,
                "days_since_update": last_updated,
                "comment_count": issue.comments
            }
            
            # Categorize by stage
            if "backlog" in labels:
                state["backlog_items"].append(item_data)
                if last_updated > 30:
                    state["stale_items"].append(item_data)
                    
            elif "ready" in labels:
                state["ready_items"].append(item_data)
                if last_updated > 14:
                    state["stale_items"].append(item_data)
                    
            elif "in-progress" in labels:
                state["in_progress_items"].append(item_data)
                if last_updated > 7:
                    state["stale_items"].append(item_data)
                    
        # Identify pipeline gaps
        if len(state["backlog_items"]) < 5:
            state["pipeline_gaps"].append("low_backlog")
        if len(state["ready_items"]) < 2:
            state["pipeline_gaps"].append("low_ready")
        if len(state["in_progress_items"]) == 0:
            state["pipeline_gaps"].append("no_active_work")
            
        # Get repository stats
        state["repo_stats"] = self.github.get_repository_stats()
        
        logger.info(f"Project state: {len(state['backlog_items'])} backlog, "
                   f"{len(state['ready_items'])} ready, "
                   f"{len(state['in_progress_items'])} in progress")
        
        return state
        
    def prioritize_tasks(self, project_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate prioritized task queue"""
        candidates = []
        
        # Brainstorming tasks (if backlog is low)
        if len(project_state['backlog_items']) < 10:
            for _ in range(3):
                candidates.append({
                    "type": "BRAINSTORM_IDEA",
                    "context": {},
                    "category": "pipeline_fill",
                    "urgency": 0.8 if len(project_state['backlog_items']) < 5 else 0.5
                })
                
        # Review tasks for high-interest items
        for item in sorted(project_state['backlog_items'],
                          key=lambda x: x['human_interest'], reverse=True)[:5]:
            if item['score'] < 10:  # Not yet ready
                # Try to find design document
                project_id = self._extract_project_id_from_issue(item['number'])
                design_path = f"technical_design_documents/{project_id}/design.md"
                
                if self.github.file_exists(design_path):
                    # Design exists, review it
                    candidates.append({
                        "type": "REVIEW_TECHNICAL_DESIGN",
                        "context": {
                            "design_path": design_path,
                            "issue_number": item['number'],
                            "project_id": project_id
                        },
                        "category": "advance_item",
                        "human_interest": item['human_interest'],
                        "urgency": 0.7
                    })
                else:
                    # No design yet, create one
                    candidates.append({
                        "type": "WRITE_TECHNICAL_DESIGN",
                        "context": {
                            "issue_number": item['number']
                        },
                        "category": "advance_item",
                        "human_interest": item['human_interest'],
                        "urgency": 0.8
                    })
                    
        # Implementation tasks for ready items
        for item in project_state['ready_items']:
            project_id = self._extract_project_id_from_issue(item['number'])
            
            # Check if implementation plan exists
            plan_path = f"implementation_plans/{project_id}/implementation_plan.md"
            
            if self.github.file_exists(plan_path):
                # Plan exists, start implementation
                candidates.append({
                    "type": "WRITE_CODE",
                    "context": {
                        "plan_path": plan_path,
                        "project_id": project_id,
                        "module_name": "main"
                    },
                    "category": "implement",
                    "human_interest": item['human_interest'],
                    "urgency": 0.9
                })
            else:
                # No plan yet
                candidates.append({
                    "type": "WRITE_IMPLEMENTATION_PLAN",
                    "context": {
                        "issue_number": item['number'],
                        "project_id": project_id
                    },
                    "category": "advance_item",
                    "urgency": 0.85
                })
                
        # Complete in-progress work
        for item in project_state['in_progress_items']:
            project_id = self._extract_project_id_from_issue(item['number'])
            
            # Check what's needed
            paper_sections = self._check_paper_sections(project_id)
            
            if not paper_sections.get('methods'):
                candidates.append({
                    "type": "WRITE_METHODS",
                    "context": {
                        "project_id": project_id,
                        "implementation_path": f"implementation_plans/{project_id}/implementation_plan.md"
                    },
                    "category": "complete_work",
                    "urgency": 1.0
                })
                
            if not paper_sections.get('introduction'):
                candidates.append({
                    "type": "WRITE_INTRODUCTION",
                    "context": {
                        "project_id": project_id,
                        "design_path": f"technical_design_documents/{project_id}/design.md"
                    },
                    "category": "complete_work",
                    "urgency": 0.95
                })
                
        # Status checks for items that might be ready to advance
        for stage_items in [project_state['backlog_items'], project_state['ready_items']]:
            for item in stage_items:
                if item['score'] >= 5:  # Might be ready to advance
                    candidates.append({
                        "type": "CHECK_PROJECT_STATUS",
                        "context": {
                            "issue_number": item['number'],
                            "auto_advance": True
                        },
                        "category": "maintenance",
                        "urgency": 0.6
                    })
                    
        # Calculate priority scores
        for task in candidates:
            task['priority_score'] = self._calculate_priority_score(task, project_state)
            
        # Sort by priority
        candidates.sort(key=lambda x: x['priority_score'], reverse=True)
        
        return candidates
        
    def _calculate_priority_score(self, task: Dict[str, Any], 
                                 project_state: Dict[str, Any]) -> float:
        """Calculate priority score for a task"""
        score = 0.0
        
        # Base score from category
        category_scores = {
            "complete_work": 0.9,
            "implement": 0.8,
            "advance_item": 0.7,
            "pipeline_fill": 0.6,
            "maintenance": 0.3
        }
        score += category_scores.get(task.get('category', 'maintenance'), 0.3)
        
        # Urgency factor
        score += task.get('urgency', 0.5) * 0.3
        
        # Human interest factor
        if 'human_interest' in task:
            # Normalize to 0-1 range
            normalized_interest = min(max((task['human_interest'] + 5) / 10, 0), 1)
            score += normalized_interest * 0.2
            
        # Pipeline gap bonus
        if project_state['pipeline_gaps']:
            if "no_active_work" in project_state['pipeline_gaps'] and \
               task.get('category') in ['implement', 'advance_item']:
                score += 0.2
            elif "low_backlog" in project_state['pipeline_gaps'] and \
                 task['type'] == "BRAINSTORM_IDEA":
                score += 0.2
                
        # Add small random factor
        score += random.uniform(0, 0.05)
        
        return min(score, 1.0)
        
    def save_execution_log(self):
        """Save execution log to file"""
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        # Detailed log
        log_path = os.path.join(log_dir, f"execution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        with open(log_path, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "model": self.model.name_or_path if self.model else "None",
                "tasks_executed": len(self.execution_log),
                "execution_details": self.execution_log
            }, f, indent=2, default=str)
            
        # Update summary
        summary_path = os.path.join(log_dir, "execution_summary.md")
        
        with open(summary_path, 'a') as f:
            f.write(f"\n## Execution on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            if self.model:
                f.write(f"- Model: {self.model.name_or_path}\n")
            else:
                f.write("- Model: Not loaded\n")
                
            success_count = sum(1 for log in self.execution_log 
                              if log['result'].get('success'))
            f.write(f"- Tasks completed: {success_count}/{len(self.execution_log)}\n")
            
            for log in self.execution_log:
                status = "✅" if log['result'].get('success') else "❌"
                error = log['result'].get('error', 'Success')
                f.write(f"  - {status} {log['task']['type']}: {error}\n")
                
        logger.info(f"Execution log saved to {log_path}")
        
    def _extract_project_id_from_issue(self, issue_number: int) -> str:
        """Extract or generate project ID from issue"""
        issue = self.github.get_issue(issue_number)
        if not issue:
            return f"project-{issue_number}"
            
        # Try to extract from body
        import re
        body = issue.body or ""
        id_match = re.search(r'\*\*Suggested ID\*\*:\s*(.+)', body)
        
        if id_match:
            return id_match.group(1).strip()
            
        return f"project-{issue_number}"
        
    def _check_paper_sections(self, project_id: str) -> Dict[str, bool]:
        """Check which paper sections exist"""
        sections = {}
        section_names = ['abstract', 'introduction', 'methods', 'results', 'discussion']
        
        for section in section_names:
            path = f"papers/{project_id}/sections/{section}.md"
            sections[section] = self.github.file_exists(path)
            
        return sections