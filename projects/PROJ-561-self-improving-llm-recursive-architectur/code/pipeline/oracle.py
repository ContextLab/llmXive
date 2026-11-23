import torch
import torch.nn as nn
from typing import Dict, Any, Tuple, Optional, Callable
from pipeline.evaluator import run_all_benchmarks
from pipeline.model import get_model_param_count
from utils.memory import check_and_terminate_if_exceeds
from schemas.modification_proposal import ModificationProposal
from config import get_config

class FixedPointOracle:
    """
    External Oracle for validating modification proposals.
    Enforces structural validity and parameter increase constraints (<= 30%).
    """
    def __init__(self):
        self.config = get_config()
        self.max_param_increase_percent = self.config.safety.max_param_increase_percent

    def validate_structure(self, proposal: ModificationProposal) -> bool:
        """
        Checks if the proposed modification is structurally valid for a GPT-2 model.
        Validates that hidden sizes are multiples of 64, heads are valid, etc.
        """
        # Basic structural sanity checks
        if proposal.hidden_size_change is not None:
            if proposal.hidden_size_change <= 0:
                return False
            if proposal.hidden_size_change % 64 != 0:
                return False
        
        if proposal.head_count_change is not None:
            if proposal.head_count_change <= 0:
                return False
            # GPT-2 124M has 12 heads. 124M config: n_embd=768, n_head=12, n_layer=12
            # 768 / 12 = 64. If we change heads, we must ensure hidden_size % head_count == 0
            # But since we might change both, we check consistency in apply_modification.
            # Here we just check positive integers.
            pass

        if proposal.activation_change is not None:
            valid_activations = ['relu', 'gelu', 'gelu_new', 'gelu_fast', 'gelu_approx']
            if proposal.activation_change not in valid_activations:
                return False

        if proposal.layer_add is not None:
            if proposal.layer_add <= 0:
                return False

        return True

    def validate_external_oracle(self, proposal: ModificationProposal, current_model: nn.Module) -> Tuple[bool, str]:
        """
        Main entry point for the External Oracle.
        Returns (is_valid, reason).
        
        Constraints:
        1. Structural validity (via validate_structure)
        2. Parameter increase <= 30% (SC-004)
        """
        # 1. Structural Validity
        if not self.validate_structure(proposal):
            return False, "Proposal failed structural validity checks."

        # 2. Parameter Count Constraint
        current_params = get_model_param_count(current_model)
        
        # Estimate new parameter count based on proposal
        # We need to simulate the new model structure to count params accurately
        # without actually instantiating it if it's too large, but for GPT-2 124M
        # modifications, we can estimate or instantiate a dummy.
        
        # A simple heuristic based on GPT-2 architecture:
        # Params ~ (hidden_size^2 * 12) + (vocab_size * hidden_size * 2) + (hidden_size * 4 * hidden_size)
        # More accurately, we should apply the modification to a dummy model or calculate analytically.
        # Given the constraint is 30%, we can calculate the expected delta.
        
        # Let's use a rough analytical estimator based on the specific change types.
        # GPT-2 124M baseline:
        # n_embd = 768, n_head = 12, n_layer = 12, vocab = 50257
        # Attn + MLP + Embed + LN
        
        current_n_embd = current_model.config.n_embd
        current_n_head = current_model.config.n_head
        current_n_layer = current_model.config.n_layer
        current_vocab = current_model.config.vocab_size

        # Estimate new dimensions
        new_n_embd = current_n_embd
        if proposal.hidden_size_change is not None:
            new_n_embd = proposal.hidden_size_change
        
        new_n_head = current_n_head
        if proposal.head_count_change is not None:
            new_n_head = proposal.head_count_change
        
        new_n_layer = current_n_layer
        if proposal.layer_add is not None:
            new_n_layer = current_n_layer + proposal.layer_add

        # Parameter estimation function for GPT-2-like models
        def estimate_params(n_embd, n_head, n_layer, vocab):
            # Attention: 4 * n_embd * n_embd per layer (Q, K, V, C_proj)
            attn_params = 4 * n_embd * n_embd * n_layer
            # MLP: 4 * n_embd * n_embd per layer (usually 4x expansion)
            mlp_params = 4 * n_embd * n_embd * n_layer
            # Embedding: vocab * n_embd
            embed_params = vocab * n_embd
            # Output projection (often tied with embed, but counting separately for safety or if untied)
            # GPT-2 ties, so no extra params for output.
            # LN params: 2 * n_embd per layer * 2 (attn and mlp) = 4 * n_embd * n_layer
            ln_params = 4 * n_embd * n_layer
            
            # Bias terms are negligible for this order of magnitude
            return attn_params + mlp_params + embed_params + ln_params

        estimated_new_params = estimate_params(new_n_embd, new_n_head, new_n_layer, current_vocab)
        
        increase_ratio = (estimated_new_params - current_params) / current_params
        increase_percent = increase_ratio * 100

        if increase_percent > self.max_param_increase_percent:
            return False, f"Parameter increase {increase_percent:.2f}% exceeds limit of {self.max_param_increase_percent}%."

        return True, "Oracle validation passed."

def create_immutable_oracle() -> Callable[[ModificationProposal, nn.Module], Tuple[bool, str]]:
    """
    Factory to create a stateless oracle function for use in contexts where
    the oracle object shouldn't be mutated or passed directly.
    """
    oracle = FixedPointOracle()
    def oracle_func(proposal: ModificationProposal, model: nn.Module) -> Tuple[bool, str]:
        return oracle.validate_external_oracle(proposal, model)
    return oracle_func
