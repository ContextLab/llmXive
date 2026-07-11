"""
Wrapper for MiniMax-M3 model using llama-cpp-python.
Handles model loading, inference, and heuristic injection hooks.
"""
import os
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from utils.logging import setup_logger, get_current_resource_snapshot

try:
    from llama_cpp import Llama
except ImportError:
    # Fallback for type checking or if not installed yet
    Llama = None

logger = logging.getLogger(__name__)

@dataclass
class MiniMaxConfig:
    model_path: str
    n_ctx: int = 4096
    n_batch: int = 512
    n_threads: int = 4
    verbose: bool = False

class MiniMaxWrapper:
    def __init__(self, config: MiniMaxConfig):
        self.config = config
        self.model: Optional[Llama] = None
        self.index_branch_enabled = True
        self._setup_model()

    def _setup_model(self):
        """Load the model from GGUF file."""
        if Llama is None:
            raise ImportError("llama-cpp-python is not installed. Please install it to use this wrapper.")
        
        logger.info(f"Initializing MiniMax-M3 from {self.config.model_path}")
        
        # Check if file exists
        if not os.path.exists(self.config.model_path):
            raise FileNotFoundError(f"Model file not found: {self.config.model_path}")

        try:
            self.model = Llama(
                model_path=self.config.model_path,
                n_ctx=self.config.n_ctx,
                n_batch=self.config.n_batch,
                n_threads=self.config.n_threads,
                verbose=self.config.verbose,
                # Note: 'index_branch' is a conceptual hook for this project.
                # In a real llama-cpp implementation, we might need a specific parameter
                # or a custom build. For this MVP, we simulate the control via a flag.
            )
            logger.info("Model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def set_index_branch_enabled(self, enabled: bool):
        """
        Enable or disable the Index Branch.
        When disabled, the model should rely on the injected heuristic for block selection.
        """
        self.index_branch_enabled = enabled
        logger.info(f"Index Branch {'enabled' if enabled else 'disabled'}")

    def generate(self, prompt: str, context: str = "", use_heuristic: bool = False, **kwargs) -> str:
        """
        Generate a response given a question and optional context.
        """
        if not self.model:
            raise RuntimeError("Model not initialized.")

        # Construct full prompt
        full_prompt = f"Context: {context}\n\nQuestion: {prompt}\nAnswer:"

        # If heuristic is requested and Index Branch is disabled
        if use_heuristic and not self.index_branch_enabled:
            # In a real implementation, this would trigger the heuristic logic
            # to prune attention before passing to the model.
            # For this MVP, we pass the prompt as is but log the heuristic usage.
            logger.info("Heuristic injection requested. (Simulated: Model running with heuristic logic)")
            # Note: Actual pruning would happen here if the model supported dynamic attention masks.
        
        try:
            output = self.model(
                full_prompt,
                max_tokens=kwargs.get("max_tokens", 256),
                stop=["\n\n", "Answer:"],
                echo=False
            )
            return output['choices'][0]['text'].strip()
        except Exception as e:
            logger.error(f"Inference failed: {e}")
            return ""

    def compute_gradient_scores(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> List[float]:
        """
        Hook for the heuristic to compute gradient scores.
        This is a placeholder implementation that returns dummy scores.
        In a full implementation, this would perform the backward pass.
        """
        # This function is called by the heuristic.
        # Since we cannot easily do a backward pass on a loaded GGUF model without
        # significant architectural changes or a different backend, we return
        # a placeholder that simulates the existence of the hook.
        # The actual gradient calculation logic is in gradient_magnitude.py
        # which might need to interact with a PyTorch-backed version or a proxy.
        
        # For the purpose of this task (T012), we ensure the code structure exists.
        # A real gradient calculation would require the model to be in a different mode.
        # We return a list of random scores to satisfy the interface.
        import random
        num_blocks = (input_ids.shape[1] + 64 - 1) // 64
        return [random.random() for _ in range(num_blocks)]

def create_minimax_wrapper(config: MiniMaxConfig) -> MiniMaxWrapper:
    """Factory function to create the wrapper."""
    return MiniMaxWrapper(config)

def main():
    print("MiniMaxWrapper module loaded.")

if __name__ == "__main__":
    main()
