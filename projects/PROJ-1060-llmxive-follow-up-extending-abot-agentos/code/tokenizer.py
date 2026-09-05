import json
import os
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import MODEL_ID, GRANULARITY, RANDOM_SEED

# Mock VLM tokenizer for T012 to avoid GPU dependency in this specific script
# In a real scenario, this would load the model from config.MODEL_ID
# For the purpose of T016c execution without GPU, we simulate the discretization
# deterministically based on the input trace content.

class SymbolicTokenizer:
    def __init__(self, granularity: str = "coarse"):
        self.granularity = granularity
        self.taxonomy = {
            "coarse": ["object", "surface", "location", "action"],
            "fine": ["red_object", "blue_surface", "table_location", "pick_action", "place_action", "open_action"]
        }
        self.seed = random.seed(RANDOM_SEED)

    def discretize(self, observation: str) -> List[str]:
        """
        Map a raw observation string to a list of semantic tokens.
        This is a deterministic mock implementation for T012.
        """
        if self.granularity == "fine":
            # Simulate fine-grained detection based on keywords
            tokens = []
            if "red" in observation.lower(): tokens.append("red_object")
            if "blue" in observation.lower(): tokens.append("blue_surface")
            if "table" in observation.lower(): tokens.append("table_location")
            if "pick" in observation.lower(): tokens.append("pick_action")
            if "place" in observation.lower(): tokens.append("place_action")
            if "open" in observation.lower(): tokens.append("open_action")
            if not tokens: tokens.append("unknown_object")
            return tokens
        else:
            # Coarse
            if "object" in observation.lower() or "red" in observation.lower() or "blue" in observation.lower():
                return ["object"]
            if "table" in observation.lower() or "shelf" in observation.lower():
                return ["location"]
            if "pick" in observation.lower() or "place" in observation.lower():
                return ["action"]
            return ["unknown_object"]

def discretize_trace(trace: Dict[str, Any], granularity: Optional[str] = None) -> List[str]:
    """
    Process a single trace dict and return a list of semantic tokens.
    """
    if granularity is None:
        granularity = GRANULARITY
    
    tokenizer = SymbolicTokenizer(granularity=granularity)
    
    # Extract observations from trace (mocking the structure expected from ALFWorld)
    # ALFWorld traces typically have 'observation' or 'steps' with observations
    tokens = []
    
    # Try to find observation keys
    obs_keys = ["observation", "obs", "current_observation"]
    for key in obs_keys:
        if key in trace:
            obs = trace[key]
            if isinstance(obs, list):
                for item in obs:
                    tokens.extend(tokenizer.discretize(str(item)))
            else:
                tokens.extend(tokenizer.discretize(str(obs)))
            break
    
    # If no observation found, check steps
    if not tokens and "steps" in trace:
        for step in trace["steps"]:
            if "observation" in step:
                tokens.extend(tokenizer.discretize(str(step["observation"])))
    
    if not tokens:
        tokens.append("unknown_object")
        
    return tokens

def main():
    print("Tokenizer module loaded.")
    print(f"Default Granularity: {GRANULARITY}")
    print(f"Model ID: {MODEL_ID}")
