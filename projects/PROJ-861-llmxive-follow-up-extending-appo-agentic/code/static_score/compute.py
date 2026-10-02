import math
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import numpy as np
from transformers import AutoModelForCausalLM, AutoTokenizer
from utils.logger import get_logger
from utils.config import get_config

logger = get_logger(__name__)

def compute_kl_divergence(p: List[float], q: List[float], epsilon: float = 1e-9) -> float:
    """
    Computes the KL Divergence between two probability distributions p and q.
    Applies epsilon smoothing to prevent log(0).
    """
    # Clamp probabilities
    p = [max(x, epsilon) for x in p]
    q = [max(x, epsilon) for x in q]
    
    # Normalize to ensure they sum to 1 (though they should already be probs)
    p_sum = sum(p)
    q_sum = sum(q)
    p = [x / p_sum for x in p]
    q = [x / q_sum for x in q]
    
    # Compute KL(p || q)
    kl = 0.0
    for pi, qi in zip(p, q):
        if pi > 0:
            kl += pi * math.log(pi / qi)
    
    return kl

class StaticScorer:
    def __init__(self, model_name: str = "microsoft/phi-2", device: str = "cpu", epsilon: float = 1e-9):
        self.model_name = model_name
        self.device = device
        self.epsilon = epsilon
        self.tokenizer = None
        self.model = None
        self._load_model()

    def _load_model(self):
        """Loads the model and tokenizer."""
        logger.info(f"Loading model {self.model_name} on {self.device}...")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, trust_remote_code=True)
            # Force CPU only as per constraints
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                torch_dtype="auto",
                device_map={"": self.device}
            )
            self.model.eval()
            logger.info("Model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def score_task(self, prompt: str) -> List[float]:
        """
        Computes static branching scores for a given prompt.
        Returns a list of scores corresponding to decision points.
        """
        # Tokenize
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        
        # Get logits
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
        
        # Calculate scores based on KL divergence against uniform distribution
        # This is a simplified version. In reality, we'd compare against a baseline or uniform.
        # For this task, we simulate the score calculation.
        scores = []
        vocab_size = logits.shape[-1]
        uniform_dist = [1.0 / vocab_size] * vocab_size
        
        # Iterate over tokens (simplified)
        for i in range(logits.shape[1]):
            token_logits = logits[0, i].cpu().numpy()
            # Softmax
            probs = np.exp(token_logits - np.max(token_logits))
            probs = probs / probs.sum()
            
            # KL against uniform
            kl = compute_kl_divergence(probs.tolist(), uniform_dist, self.epsilon)
            scores.append(float(kl))
        
        return scores

def main():
    """
    Main entry point for the static score module.
    """
    config = get_config()
    scorer = StaticScorer(
        model_name=config.get("model_name"),
        device=config.get("device"),
        epsilon=config.get("epsilon")
    )
    
    test_prompt = "What is 2+2?"
    scores = scorer.score_task(test_prompt)
    print(f"Scores for test prompt: {scores}")

if __name__ == "__main__":
    import torch
    main()
