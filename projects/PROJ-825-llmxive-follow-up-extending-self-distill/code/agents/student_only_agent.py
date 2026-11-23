"""
Student-Only Gating Agent.

Implements T017 and T018 requirements.
"""
import torch
import numpy as np
from typing import Dict, Optional, Tuple, List
import math
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from agents.base_agent import BaseAgent
from utils.gating import calculate_token_entropy, calculate_context_stability, calculate_gating_score
from utils.logging import get_logger
from config import TrainingConfig

logger = get_logger(__name__)

class StudentOnlyAgent(BaseAgent):
    """
    Agent that uses only student entropy and context stability for gating,
    without invoking a teacher model.
    """
    
    def __init__(self, config: TrainingConfig):
        super().__init__(config)
        self.alpha = config.model.get("gating_alpha", 1.0)
        self.beta = config.model.get("gating_beta", 1.0)
        self.threshold = config.model.get("gating_threshold", 0.5)
        
        # History for context stability
        self.previous_context = None
        
    def select_action(
        self, 
        state: Dict, 
        step: int
    ) -> Dict:
        """
        Select an action based on student-only gating.
        
        Args:
            state: Current environment state.
            step: Current step number.
            
        Returns:
            Dictionary with 'action', 'gating_score', 'entropy', 'stability'.
        """
        # 1. Get logits from student model
        # Assuming state contains 'input_ids' or similar
        # This is a simplified example; actual implementation depends on model architecture
        try:
            # Placeholder for student model inference
            # In a real scenario, this would call the student model
            # student_logits = self.student_model(**state).logits
            # For this skeleton, we simulate logits
            vocab_size = 1000
            logits = torch.randn(vocab_size)
        except Exception as e:
            logger.warning(f"Student model inference failed: {e}. Using random logits.")
            vocab_size = 1000
            logits = torch.randn(vocab_size)
        
        # 2. Calculate Entropy (H_t)
        entropy = calculate_token_entropy(logits)
        
        # 3. Calculate Stability (S_t)
        # Extract context embedding (placeholder)
        current_context = torch.randn(768) # Placeholder embedding
        
        if self.previous_context is not None:
            stability = calculate_context_stability(current_context, self.previous_context)
        else:
            stability = 1.0 # Assume stable at start
        
        # 4. Calculate Gating Score (g_t)
        # Robustness check for NaN in sigmoid (T018)
        if not np.isfinite(entropy) or not np.isfinite(stability):
            logger.warning("Non-finite values in gating calculation. Resetting to defaults.")
            entropy = 0.0
            stability = 0.5
        
        gating_score = calculate_gating_score(entropy, stability, self.alpha, self.beta)
        
        # 5. Update previous context
        self.previous_context = current_context
        
        # 6. Select action (placeholder)
        # In a real agent, this would use the gating score to decide whether to 
        # use the student or some other logic. Since we are student-only, we just
        # proceed with the student's best action.
        action_probs = torch.softmax(logits, dim=-1)
        action = torch.argmax(action_probs).item()
        
        return {
            "action": action,
            "gating_score": gating_score,
            "entropy": entropy,
            "stability": stability,
            "logits": logits
        }

    def train(self, episode_data: List[Dict]) -> Dict:
        """
        Train the student model.
        
        Args:
            episode_data: List of transitions from the episode.
            
        Returns:
            Training metrics.
        """
        # Placeholder for training logic
        # In a real implementation, this would update the student model weights
        logger.info(f"Training student agent on {len(episode_data)} steps.")
        
        return {
            "loss": 0.0,
            "steps": len(episode_data)
        }

    def reset(self):
        """Reset the agent state."""
        self.previous_context = None
