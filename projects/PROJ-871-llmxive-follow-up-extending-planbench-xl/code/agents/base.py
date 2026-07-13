from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class BaseAgent(ABC):
    """
    Abstract base class for all agents in the llmXive pipeline.
    """
    
    @abstractmethod
    def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent on a given task.
        
        Args:
            task: Dictionary containing task details.
            
        Returns:
            Dictionary containing the execution result.
        """
        pass
