"""
EvoMem-All Agent implementation.

This agent retrieves the last N patches without any conflict filtering,
serving as a baseline for comparison with the conflict-filtering variant.
"""
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import random
import numpy as np
import torch
from src.agents.base_agent import BaseAgent
from src.utils.seeding import set_deterministic_seed


class EvoMemAll(BaseAgent):
    """
    EvoMem-All agent that retrieves the last N patches without filtering.
    
    This serves as the baseline agent that retrieves all recent patches
    without any conflict detection or filtering logic.
    """
    
    def __init__(self, n_patches: int = 10, seed: int = 42):
        """
        Initialize the EvoMem-All agent.
        
        Args:
            n_patches (int): Number of most recent patches to retrieve.
            seed (int): Random seed for reproducibility.
        """
        super().__init__(name="EvoMem-All", seed=seed)
        self.n_patches = n_patches
        set_deterministic_seed(seed)
    
    def retrieve_patches(self, task_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Retrieve the last N patches from the available patches.
        
        Args:
            task_context (Dict[str, Any]): Task context containing available patches.
        
        Returns:
            List[Dict[str, Any]]: List of the last N patches.
        """
        available_patches = task_context.get('patches', [])
        
        if not available_patches:
            return []
        
        # Retrieve the last N patches
        start_index = max(0, len(available_patches) - self.n_patches)
        selected_patches = available_patches[start_index:]
        
        # Update metrics
        context_text = self.build_context(selected_patches)
        self.metrics['context_tokens'] = self.count_tokens(context_text)
        
        return selected_patches
    
    def execute_task(self, task: Dict[str, Any], patches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute a task using the retrieved patches.
        
        Args:
            task (Dict[str, Any]): The task to execute.
            patches (List[Dict[str, Any]]): Retrieved patches to use.
        
        Returns:
            Dict[str, Any]: Execution results.
        """
        # Build context from patches
        context = self.build_context(patches)
        
        # Update metrics
        self.metrics['context_tokens'] = self.count_tokens(context)
        
        # Simulate task execution (in a real implementation, this would call an LLM)
        # For now, we return a placeholder result
        result = {
            'task_id': task.get('task_id', 'unknown'),
            'agent_variant': self.name,
            'context_tokens': self.metrics['context_tokens'],
            'success_status': True,  # Placeholder
            'output': f"Executed task {task.get('task_id')} with {len(patches)} patches"
        }
        
        self.metrics['success_status'] = result['success_status']
        return result
