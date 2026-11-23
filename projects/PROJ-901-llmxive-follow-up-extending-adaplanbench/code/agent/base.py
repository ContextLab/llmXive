"""
Base classes and types for agent implementations.
Defines the core interfaces and data structures used across the agent system.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

class ViolationType:
    """Represents a constraint violation."""
    
    def __init__(self, type: str, constraint: str, reason: str):
        self.type = type
        self.constraint = constraint
        self.reason = reason
    
    def __repr__(self):
        return f"ViolationType(type={self.type}, constraint={self.constraint}, reason={self.reason})"

@dataclass
class ExecutionResult:
    """Result of an agent execution."""
    generated_plan: str
    final_score: float
    violations: List[ViolationType] = field(default_factory=list)

@dataclass
class TaskContext:
    """Context for a task execution."""
    task_id: str
    raw_prompt: str
    constraints: List[str]
    constraint_count: int

class BaseAgent(ABC):
    """Abstract base class for all agents."""
    
    @abstractmethod
    def execute(self, context: TaskContext) -> ExecutionResult:
        """
        Execute the agent on the given task context.
        
        Args:
            context: Task context containing prompt and constraints.
            
        Returns:
            ExecutionResult with generated plan and violation information.
        """
        pass