#!/usr/bin/env python3
"""Demo showing full llmXive automation running locally with mock GitHub"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, List, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.model_manager import ModelManager
from src.conversation_manager import ConversationManager
from src.response_parser import ResponseParser

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class MockGitHubHandler:
    """Mock GitHub handler for demo purposes"""
    
    def __init__(self):
        self.mock_issues = [
            {
                "number": 101,
                "title": "EEG-based emotion recognition using transformers",
                "labels": ["backlog"],
                "score": 3.5,
                "human_interest": 8,
                "days_old": 5
            },
            {
                "number": 102,
                "title": "Real-time cognitive load detection for adaptive learning",
                "labels": ["ready"],
                "score": 12,
                "human_interest": 15,
                "days_old": 10
            }
        ]
    
    def get_open_issues(self):
        return self.mock_issues
    
    def get_issue_score(self, issue_number):
        for issue in self.mock_issues:
            if issue["number"] == issue_number:
                return issue["score"]
        return 0
    
    def get_issue_reactions(self, issue_number):
        return {"thumbsup": 5, "thumbsdown": 0}
    
    def file_exists(self, path):
        return False
    
    def create_file(self, path, content, message):
        logging.info(f"[MOCK] Would create file: {path}")
        logging.info(f"[MOCK] Content preview: {content[:200]}...")
        return True

class DemoOrchestrator:
    """Simplified orchestrator for demo"""
    
    def __init__(self, model_size_gb=20):
        logging.info("Initializing demo orchestrator...")
        
        # Load model
        self.model_mgr = ModelManager(max_size_gb=model_size_gb)
        self.model, self.tokenizer = self.model_mgr.get_suitable_model()
        
        # Initialize components
        self.conv_mgr = ConversationManager(self.model, self.tokenizer)
        self.parser = ResponseParser()
        self.github = MockGitHubHandler()
        
        logging.info(f"Loaded model: {self.model.name_or_path}")
    
    def analyze_project_state(self):
        """Analyze mock project state"""
        issues = self.github.get_open_issues()
        
        state = {
            "backlog_items": [i for i in issues if "backlog" in i["labels"]],
            "ready_items": [i for i in issues if "ready" in i["labels"]],
            "in_progress_items": [],
            "pipeline_gaps": []
        }
        
        if len(state["backlog_items"]) < 5:
            state["pipeline_gaps"].append("low_backlog")
            
        return state
    
    def execute_task(self, task_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single task"""
        logging.info(f"Executing task: {task_type}")
        
        # Get system prompt for task
        system_prompt = ConversationManager.SYSTEM_PROMPTS.get(
            task_type, 
            "You are a helpful AI assistant."
        )
        
        # Create task-specific prompt
        if task_type == "BRAINSTORM_IDEA":
            prompt = """Generate a novel research idea for the llmXive platform.

Requirements:
1. Combine neuroscience/brain data with AI/ML
2. Be technically feasible
3. Have clear applications

Format your response as:
**Title**: [Your title here]
**Description**: [2-3 sentences]
**Key Innovation**: [What's novel]
**Technical Approach**: [Brief overview]
**Impact**: [Potential applications]"""

        elif task_type == "WRITE_TECHNICAL_DESIGN":
            prompt = f"""Write a technical design for issue #{context.get('issue_number', 'N/A')}.

Include:
1. System Architecture
2. Key Components
3. Data Flow
4. Technical Requirements

Be specific and implementation-focused."""

        else:
            prompt = "Complete the requested task with technical detail."
        
        # Query model
        response = self.conv_mgr.query_model(prompt, task_type=task_type)
        
        if response:
            # Parse response
            parsed = self.parser.parse_idea(response) if task_type == "BRAINSTORM_IDEA" else {"content": response}
            
            # Mock file creation
            if task_type == "BRAINSTORM_IDEA" and parsed.get("title"):
                self.github.create_file(
                    f"ideas/{parsed['title'].replace(' ', '_').lower()}.md",
                    response,
                    f"Add new idea: {parsed['title']}"
                )
            
            return {
                "success": True,
                "task_type": task_type,
                "response": response,
                "parsed": parsed
            }
        else:
            return {
                "success": False,
                "task_type": task_type,
                "error": "No response generated"
            }
    
    def run_automation_cycle(self, max_tasks=3):
        """Run a full automation cycle"""
        logging.info("\n" + "="*80)
        logging.info("Starting llmXive automation cycle")
        logging.info("="*80 + "\n")
        
        # Analyze state
        state = self.analyze_project_state()
        logging.info(f"Project state: {len(state['backlog_items'])} backlog, {len(state['ready_items'])} ready")
        
        # Generate tasks
        tasks = []
        
        # Add brainstorming if backlog is low
        if "low_backlog" in state["pipeline_gaps"]:
            tasks.append({
                "type": "BRAINSTORM_IDEA",
                "context": {},
                "priority": 0.9
            })
        
        # Add technical design for high-interest backlog items
        for item in state["backlog_items"]:
            if item["human_interest"] > 5:
                tasks.append({
                    "type": "WRITE_TECHNICAL_DESIGN",
                    "context": {"issue_number": item["number"]},
                    "priority": 0.8
                })
        
        # Execute tasks
        completed = 0
        for i, task in enumerate(tasks[:max_tasks]):
            logging.info(f"\nTask {i+1}/{min(len(tasks), max_tasks)}: {task['type']}")
            
            result = self.execute_task(task["type"], task["context"])
            
            if result["success"]:
                completed += 1
                logging.info("✓ Task completed successfully")
                if task["type"] == "BRAINSTORM_IDEA" and result.get("parsed", {}).get("title"):
                    logging.info(f"  Generated idea: {result['parsed']['title']}")
            else:
                logging.info("✗ Task failed")
        
        logging.info(f"\n{'='*80}")
        logging.info(f"Automation cycle complete: {completed}/{min(len(tasks), max_tasks)} tasks successful")
        logging.info(f"{'='*80}\n")
        
        return {
            "tasks_completed": completed,
            "total_tasks": min(len(tasks), max_tasks),
            "model_used": self.model.name_or_path
        }

def main():
    """Run the demo"""
    print("\n🚀 llmXive Automation - Local Execution Demo\n")
    
    # Initialize orchestrator with 20GB limit for local execution
    orchestrator = DemoOrchestrator(model_size_gb=20)
    
    # Run automation cycle
    result = orchestrator.run_automation_cycle(max_tasks=2)
    
    print("\n📊 Summary:")
    print(f"  - Model: {result['model_used']}")
    print(f"  - Tasks completed: {result['tasks_completed']}/{result['total_tasks']}")
    print(f"  - Running locally allows models up to 20GB (vs 3.5GB in CI)")
    
    print("\n💡 To run the full system with GitHub integration:")
    print("  export GITHUB_TOKEN=your_valid_token")
    print("  python cli.py --model-size-gb 20 --max-tasks 5")

if __name__ == "__main__":
    main()