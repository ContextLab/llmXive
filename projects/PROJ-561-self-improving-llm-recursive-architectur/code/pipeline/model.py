import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Dict, Any, List, Tuple
import math
import json
import os
import time
from datetime import datetime
from utils.state_store import update_mod_history, get_modification_history
from schemas.modification_proposal import ModificationProposal, validate_modification_json

def load_gpt_124m() -> nn.Module:
    """
    Loads the GPT-124M model (CPU compatible).
    """
    # Placeholder for actual loading logic
    # In a real implementation, this would load from HF or a local checkpoint
    class MockGPT(nn.Module):
        def __init__(self):
            super().__init__()
            self.lm_head = nn.Linear(768, 50257)
            self.transformer = nn.ModuleDict({
                'wte': nn.Embedding(50257, 768),
                'wpe': nn.Embedding(1024, 768),
                'h': nn.ModuleList([
                    nn.ModuleDict({
                        'ln_1': nn.LayerNorm(768),
                        'attn': nn.MultiheadAttention(768, 12, batch_first=True),
                        'ln_2': nn.LayerNorm(768),
                        'mlp': nn.Sequential(
                            nn.Linear(768, 3072),
                            nn.GELU(),
                            nn.Linear(3072, 768)
                        )
                    }) for _ in range(12)
                ]),
                'ln_f': nn.LayerNorm(768)
            })

        def forward(self, input_ids):
            x = self.transformer.wte(input_ids) + self.transformer.wpe(torch.arange(input_ids.size(1), device=input_ids.device).unsqueeze(0))
            for block in self.transformer.h:
                x = block.attn(x, x, x, need_weights=False)[0] + x
                x = block.mlp(F.relu(block.ln_2(x))) + x
            return self.lm_head(self.transformer.ln_f(x))

    return MockGPT()

def get_model_param_count(model: nn.Module) -> int:
    """Returns the total number of parameters in the model."""
    return sum(p.numel() for p in model.parameters())

def inspect_model_structure(model: nn.Module) -> Dict[str, Any]:
    """Returns a summary of the model architecture."""
    return {
        "num_params": get_model_param_count(model),
        "layers": len(list(model.children()))
    }

def apply_weight_manipulation(model: nn.Module, operation: str, params: Dict) -> nn.Module:
    """Applies a weight manipulation operation."""
    # Placeholder
    return model

def save_model_state(model: nn.Module, path: str):
    """Saves model state to disk."""
    torch.save(model.state_dict(), path)

def load_model_state(model: nn.Module, path: str):
    """Loads model state from disk."""
    model.load_state_dict(torch.load(path, map_location='cpu'))

def get_modification_history() -> List[Dict]:
    """Retrieves modification history from state store."""
    return get_modification_history()

def reset_modification_history():
    """Resets modification history."""
    from utils.state_store import reset_state
    reset_state()

def validate_modification_distinctness(proposal: ModificationProposal, history: List[Dict]) -> bool:
    """
    Validates that a modification proposal is distinct from previous ones.
    """
    if not history:
        return True
    
    for h in history:
        if h.get('modification_type') == proposal.modification_type:
            # Check magnitude distinctness if same type
            if h.get('magnitude') == proposal.magnitude:
                return False
    return True

def apply_architectural_modification(model: nn.Module, proposal: ModificationProposal) -> nn.Module:
    """
    Applies an architectural modification to the model.
    """
    # This is a simplified implementation for the task
    # Real implementation would reconstruct the model graph
    if proposal.modification_type == "layer_add":
        # Logic to add layers would go here
        pass
    elif proposal.modification_type == "head_count_change":
        # Logic to change head count
        pass
    
    return model

def compute_and_record_flops(model: nn.Module) -> int:
    """Computes FLOPs for a forward pass."""
    # Placeholder
    return 0

def aggregate_flops_over_cycles(cycles: List[int]) -> int:
    """Aggregates FLOPs over multiple cycles."""
    return 0

def generate_modification_proposal(
    model: nn.Module,
    training_loss: float,
    cycle: int,
    **kwargs
) -> Optional[ModificationProposal]:
    """
    Generates a modification proposal based on internal model state.
    
    CRITICAL IMPLEMENTATION OF T037 (Separation of Generative/Verification Logic):
    
    This function constructs a prompt for the LLM (or heuristic logic) to propose
    an architectural change.
    
    CONSTRAINT: The prompt MUST NOT contain benchmark results (GSM8K, ARC, ECE).
    It MUST rely ONLY on:
    1. training_loss (internal training metric)
    2. model structure (internal weights/layers)
    3. cycle number
    
    Any attempt to pass benchmark metrics into this function or the prompt
    construction must be explicitly avoided to prevent logical feedback loops.
    """
    
    # 1. Construct the prompt content
    # We explicitly DO NOT include any 'benchmark_metrics' argument in the signature
    # or the prompt string below.
    
    prompt_content = f"""
    You are an autonomous AI researcher tasked with improving your own architecture.
    
    CURRENT STATE:
    - Cycle: {cycle}
    - Current Training Loss: {training_loss:.4f}
    - Model Parameters: {get_model_param_count(model)}
    
    INSTRUCTIONS:
    Propose a single architectural modification to improve training efficiency or convergence.
    You must base your decision SOLELY on the training loss and model structure provided above.
    
    RESTRICTIONS:
    - DO NOT consider benchmark performance (GSM8K, ARC, etc.) as they are not available here.
    - DO NOT consider external evaluation metrics.
    - Focus on internal dynamics (loss landscape, parameter efficiency).
    
    Output your proposal in valid JSON format matching the schema:
    {{
      "modification_type": "layer_add" | "head_count_change",
      "magnitude": <integer>,
      "rationale": "<string explaining why based on loss>",
      "estimated_param_count": <integer>
    }}
    """
    
    # 2. Simulate LLM response (In a real system, this would call an LLM)
    # For this implementation, we generate a deterministic proposal based on loss
    # to ensure the code runs without external LLM dependencies for the task demo.
    # However, the prompt structure above enforces the T037 constraint.
    
    if training_loss > 2.0:
        mod_type = "layer_add"
        mag = 1
        rationale = "High loss suggests capacity deficit."
    else:
        mod_type = "head_count_change"
        mag = 2
        rationale = "Low loss allows for attention head refinement."
    
    estimated_params = get_model_param_count(model) + (10000 if mod_type == "layer_add" else 5000)
    
    proposal_dict = {
        "modification_type": mod_type,
        "magnitude": mag,
        "rationale": rationale,
        "estimated_param_count": estimated_params
    }
    
    # Validate against schema
    try:
        proposal = ModificationProposal(**proposal_dict)
    except Exception as e:
        # Log error but return None if invalid
        print(f"Generated invalid proposal: {e}")
        return None
    
    # Update history
    update_mod_history(proposal)
    
    return proposal

def enforce_distinct_modification_constraint(proposal: ModificationProposal) -> bool:
    """
    Enforces that the proposal is distinct from history.
    """
    history = get_modification_history()
    return validate_modification_distinctness(proposal, history)
