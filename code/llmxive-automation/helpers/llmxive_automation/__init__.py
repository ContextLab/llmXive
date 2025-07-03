"""llmXive Automation System - Autonomous Scientific Discovery Pipeline"""

__version__ = "0.1.0"

from .model_selector import ModelSelector
from .github_manager import GitHubManager
from .task_orchestrator import TaskOrchestrator
from .prompt_builder import PromptBuilder
from .main import LLMXiveAutomation

__all__ = [
    "ModelSelector",
    "GitHubManager", 
    "TaskOrchestrator",
    "PromptBuilder",
    "LLMXiveAutomation"
]