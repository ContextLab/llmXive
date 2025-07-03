"""Main llmXive automation system"""

import os
import sys
import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime
import traceback

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

from .model_selector import ModelSelector
from .github_manager import GitHubManager
from .task_orchestrator import TaskOrchestrator, TaskType
from .prompt_builder import PromptBuilder

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LLMXiveAutomation:
    """Main automation system for llmXive scientific discovery"""
    
    def __init__(self, mode: str = "auto", task_override: Optional[str] = None,
                 model_override: Optional[str] = None, dry_run: bool = False):
        """
        Initialize automation system
        
        Args:
            mode: Execution mode (auto, interactive, single-task)
            task_override: Specific task to execute
            model_override: Override model selection
            dry_run: Preview mode without making changes
        """
        self.mode = mode
        self.task_override = task_override
        self.model_override = model_override
        self.dry_run = dry_run
        
        # Initialize components
        self.model_selector = ModelSelector()
        self.github_manager = GitHubManager()
        self.prompt_builder = PromptBuilder()
        
        # Will be initialized after model selection
        self.model = None
        self.tokenizer = None
        self.orchestrator = None
        
    def run(self):
        """Run the automation system"""
        try:
            logger.info(f"Starting llmXive automation in {self.mode} mode")
            
            # Select and load model
            self._initialize_model()
            
            # Initialize orchestrator
            self.orchestrator = TaskOrchestrator(
                self.model_config,
                self.github_manager,
                self.prompt_builder
            )
            
            # Execute based on mode
            if self.mode == "auto":
                self._run_auto_mode()
            elif self.mode == "interactive":
                self._run_interactive_mode()
            elif self.mode == "single-task":
                self._run_single_task()
            else:
                raise ValueError(f"Unknown mode: {self.mode}")
                
        except Exception as e:
            logger.error(f"Automation failed: {e}")
            logger.error(traceback.format_exc())
            sys.exit(1)
    
    def _initialize_model(self):
        """Select and initialize the language model"""
        if self.model_override:
            logger.info(f"Using override model: {self.model_override}")
            self.model_config = self.model_selector._get_fallback_model()
            self.model_config.model_id = self.model_override
        else:
            logger.info("Selecting model from HuggingFace...")
            self.model_config = self.model_selector.get_trending_model()
        
        logger.info(f"Loading model: {self.model_config.model_id}")
        
        # Load model and tokenizer
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_config.model_id)
            
            # Configure for smaller memory footprint
            model_kwargs = {
                "torch_dtype": torch.float16,
                "device_map": "auto",
                "low_cpu_mem_usage": True
            }
            
            # Add quantization if available
            if self.model_config.quantization:
                model_kwargs["load_in_8bit"] = True
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_config.model_id,
                **model_kwargs
            )
            
            logger.info("Model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            logger.info("Falling back to API mode")
            # In production, would fall back to API-based inference
            raise
    
    def _run_auto_mode(self):
        """Run automatic task selection and execution"""
        logger.info("Running in automatic mode")
        
        # Get current project state
        project_state = self.github_manager.get_project_state()
        logger.info(f"Project state: {self._summarize_project_state(project_state)}")
        
        # Select next task
        task = self.orchestrator.select_next_task(project_state)
        logger.info(f"Selected task: {task.task_type.value}")
        
        # Execute task
        self._execute_task(task, project_state)
    
    def _run_interactive_mode(self):
        """Run in interactive mode with user input"""
        logger.info("Running in interactive mode")
        
        # Get project state
        project_state = self.github_manager.get_project_state()
        
        # Show options
        print("\nAvailable tasks:")
        for i, task_type in enumerate(TaskType):
            print(f"{i+1}. {task_type.value}")
        
        # Get user choice
        choice = input("\nSelect task (number): ").strip()
        
        try:
            task_index = int(choice) - 1
            task_type = list(TaskType)[task_index]
            
            # Create task
            task = self.orchestrator.Task(task_type, priority=100)
            
            # Execute
            self._execute_task(task, project_state)
            
        except (ValueError, IndexError):
            logger.error("Invalid task selection")
    
    def _run_single_task(self):
        """Run a single specified task"""
        if not self.task_override:
            logger.error("No task specified for single-task mode")
            return
        
        logger.info(f"Running single task: {self.task_override}")
        
        # Get project state
        project_state = self.github_manager.get_project_state()
        
        # Create task
        try:
            task_type = TaskType(self.task_override)
            task = self.orchestrator.Task(task_type, priority=100)
            
            # Execute
            self._execute_task(task, project_state)
            
        except ValueError:
            logger.error(f"Unknown task type: {self.task_override}")
    
    def _execute_task(self, task: Any, project_state: Dict):
        """Execute a specific task"""
        logger.info(f"Executing task: {task.task_type.value}")
        
        if self.dry_run:
            logger.info("DRY RUN: Would execute task but not making changes")
            return
        
        try:
            if task.task_type == TaskType.BRAINSTORM_IDEAS:
                self._brainstorm_ideas(project_state)
            elif task.task_type == TaskType.DEVELOP_TECHNICAL_DESIGN:
                self._develop_technical_design(task, project_state)
            elif task.task_type == TaskType.WRITE_REVIEW:
                self._write_review(task, project_state)
            elif task.task_type == TaskType.IMPLEMENT_RESEARCH:
                self._implement_research(task, project_state)
            elif task.task_type == TaskType.GENERATE_PAPER:
                self._generate_paper(task, project_state)
            elif task.task_type == TaskType.VALIDATE_REFERENCES:
                self._validate_references(task, project_state)
            elif task.task_type == TaskType.UPDATE_PROJECT_STATUS:
                self._update_project_status(task)
            else:
                logger.error(f"Unknown task type: {task.task_type}")
                
            # Record success
            self.orchestrator.record_task_completion(task, success=True)
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            logger.error(traceback.format_exc())
            self.orchestrator.record_task_completion(task, success=False, details={"error": str(e)})
    
    def _brainstorm_ideas(self, project_state: Dict):
        """Generate new research ideas"""
        logger.info("Brainstorming new research ideas...")
        
        # Build prompt
        prompt = self.prompt_builder.build_task_prompt(
            "brainstorm_ideas",
            {"project_state": project_state}
        )
        
        # Generate response
        response = self._generate_response(prompt)
        
        # Parse ideas from response
        ideas = self._parse_brainstorm_response(response)
        
        # Create issues for each idea
        for idea in ideas:
            if self.dry_run:
                logger.info(f"DRY RUN: Would create issue - {idea['title']}")
            else:
                issue = self.github_manager.create_issue(
                    title=idea['title'],
                    body=idea['body']
                )
                if issue:
                    logger.info(f"Created issue #{issue.number}: {idea['title']}")
    
    def _develop_technical_design(self, task: Any, project_state: Dict):
        """Develop technical design document for an idea"""
        issue = task.target
        if not issue:
            logger.error("No target issue for technical design")
            return
        
        logger.info(f"Developing technical design for issue #{issue['number']}")
        
        # Build prompt
        prompt = self.prompt_builder.build_task_prompt(
            "develop_technical_design",
            {"target_issue": issue}
        )
        
        # Generate design
        design = self._generate_response(prompt)
        
        # Save design document
        file_path = f"technical_design_documents/project_{issue['number']}/design.md"
        
        if self.dry_run:
            logger.info(f"DRY RUN: Would save design to {file_path}")
        else:
            self.github_manager.commit_files(
                {file_path: design},
                f"Add technical design for issue #{issue['number']}"
            )
            
            # Update issue
            self.github_manager.add_review_score(issue['number'], "llmxive-auto", 0.5)
    
    def _write_review(self, task: Any, project_state: Dict):
        """Write a review for a document"""
        issue = task.target
        if not issue:
            logger.error("No target issue for review")
            return
        
        logger.info(f"Writing review for issue #{issue['number']}")
        
        # Get document content (simplified - would fetch actual document)
        document_content = issue.get('body', '')
        
        # Build prompt
        prompt = self.prompt_builder.build_task_prompt(
            "write_review",
            {
                "document_content": document_content,
                "document_type": "design"
            }
        )
        
        # Generate review
        review = self._generate_response(prompt)
        
        # Save review
        file_path = f"reviews/project_{issue['number']}/llmxive-auto__{datetime.now().strftime('%m-%d-%Y')}__A.md"
        
        if self.dry_run:
            logger.info(f"DRY RUN: Would save review to {file_path}")
        else:
            self.github_manager.commit_files(
                {file_path: review},
                f"Add automated review for issue #{issue['number']}"
            )
            
            # Add review score
            self.github_manager.add_review_score(issue['number'], "llmxive-auto", 0.5)
    
    def _generate_response(self, prompt: str) -> str:
        """Generate response from the model"""
        # Tokenize input
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
        
        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=1024,
                temperature=0.7,
                do_sample=True,
                top_p=0.9,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        # Decode response
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract only the generated part
        response = response[len(prompt):].strip()
        
        return response
    
    def _parse_brainstorm_response(self, response: str) -> List[Dict[str, str]]:
        """Parse brainstormed ideas from model response"""
        ideas = []
        
        # Simple parsing - look for Title: and Body: patterns
        lines = response.split('\n')
        current_idea = {}
        
        for line in lines:
            if line.startswith("Title:") or line.startswith("- Title:"):
                if current_idea:
                    ideas.append(current_idea)
                current_idea = {"title": line.split(":", 1)[1].strip()}
            elif line.startswith("Body:") or line.startswith("- Body:"):
                if current_idea:
                    current_idea["body"] = line.split(":", 1)[1].strip()
        
        if current_idea and "title" in current_idea:
            ideas.append(current_idea)
        
        return ideas[:5]  # Limit to 5 ideas
    
    def _summarize_project_state(self, project_state: Dict) -> str:
        """Create a summary of project state"""
        summary_parts = []
        for status, issues in project_state.items():
            summary_parts.append(f"{status}: {len(issues)}")
        return ", ".join(summary_parts)
    
    # Placeholder methods for remaining task types
    def _implement_research(self, task: Any, project_state: Dict):
        """Implement research code"""
        logger.info("Research implementation not yet implemented")
    
    def _generate_paper(self, task: Any, project_state: Dict):
        """Generate research paper"""
        logger.info("Paper generation not yet implemented")
    
    def _validate_references(self, task: Any, project_state: Dict):
        """Validate paper references"""
        logger.info("Reference validation not yet implemented")
    
    def _update_project_status(self, task: Any):
        """Update project status"""
        issue = task.target
        next_status = task.context.get("next_status")
        
        if not issue or not next_status:
            logger.error("Missing information for status update")
            return
        
        if self.dry_run:
            logger.info(f"DRY RUN: Would update issue #{issue['number']} to {next_status}")
        else:
            success = self.github_manager.update_issue_status(issue['number'], next_status)
            if success:
                logger.info(f"Updated issue #{issue['number']} to {next_status}")