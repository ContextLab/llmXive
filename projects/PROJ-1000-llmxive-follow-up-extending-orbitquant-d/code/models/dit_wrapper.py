"""
DiT Wrapper for activation capture during text-to-image generation.

This module injects hooks into DiT intermediate layers to capture float32 activation
tensors during the generative trajectory. It wraps the model forward pass to record
activations at specified layers without modifying the model weights.
"""

import torch
import torch.nn as nn
from typing import Dict, List, Any, Optional, Callable, Tuple
from collections import OrderedDict
import logging

from config import Config

logger = logging.getLogger(__name__)


class ActivationCapture:
    """
    A context manager and storage class for capturing activations.

    Stores activations as float32 tensors. Supports multiple layers and multiple
    forward passes (e.g., different time steps in a diffusion trajectory).
    """

    def __init__(self):
        self.activations: Dict[str, List[torch.Tensor]] = {}
        self.layer_names: List[str] = []

    def register_layer(self, name: str):
        """Register a layer name to capture."""
        if name not in self.layer_names:
            self.layer_names.append(name)
            self.activations[name] = []

    def capture(self, name: str, tensor: torch.Tensor):
        """
        Capture a tensor for a specific layer.

        Ensures the tensor is float32 and detached from the graph to save memory.
        """
        if name not in self.activations:
            logger.warning(f"Attempted to capture activation for unregistered layer: {name}")
            return

        # Ensure float32 and detach
        if tensor.dtype != torch.float32:
            tensor = tensor.to(torch.float32)
        
        # Detach to free computation graph memory
        captured = tensor.detach()

        self.activations[name].append(captured)

    def clear(self):
        """Clear all captured activations."""
        for key in self.activations:
            self.activations[key] = []

    def get_statistics(self) -> Dict[str, Dict[str, float]]:
        """
        Compute basic statistics (mean, std, min, max) for all captured layers.

        Returns:
            Dict mapping layer_name to stats dict.
        """
        stats = {}
        for name, tensors in self.activations.items():
            if not tensors:
                stats[name] = {"count": 0}
                continue

            # Concatenate all timesteps for this layer
            # Note: We concatenate along the batch dimension or keep as list depending on usage
            # Here we compute stats per timestep and aggregate, or just global stats if needed.
            # For variance analysis, we often need per-timestep variance.
            # Let's return a list of per-timestep stats to preserve trajectory info.
            
            timestep_stats = []
            for t, t_tensor in enumerate(tensors):
                # t_tensor shape: [B, C, H, W] or [B, N, D]
                stats_t = {
                    "mean": float(t_tensor.mean().item()),
                    "std": float(t_tensor.std().item()),
                    "min": float(t_tensor.min().item()),
                    "max": float(t_tensor.max().item()),
                    "var": float(t_tensor.var().item()),
                    "shape": list(t_tensor.shape)
                }
                timestep_stats.append(stats_t)
            
            stats[name] = {
                "timesteps": timestep_stats,
                "count": len(tensors)
            }
        return stats


class DiTWrapper(nn.Module):
    """
    Wrapper for DiT models to inject hooks and capture activations.

    This wrapper does not own the model but manages the hooking lifecycle
    for a given model instance.
    """

    def __init__(self, model: nn.Module, target_layers: List[str], config: Optional[Config] = None):
        """
        Initialize the wrapper.

        Args:
            model: The underlying DiT model (e.g., Flux, SD3, Wan).
            target_layers: List of layer names (keys in model.named_modules()) to hook.
            config: Optional Config instance for logging/debug settings.
        """
        super().__init__()
        self.model = model
        self.target_layers = target_layers
        self.config = config or Config()
        self.activation_capture = ActivationCapture()
        self._hooks: List[Any] = []
        self._hook_registered = False

        # Validate target layers exist
        module_names = [name for name, _ in model.named_modules()]
        missing = [l for l in target_layers if l not in module_names]
        if missing:
            logger.warning(f"Target layers not found in model: {missing}. "
                         f"Available: {module_names}")

    def _make_hook(self, name: str) -> Callable:
        """Create a hook function for a specific layer."""
        def hook_fn(module: nn.Module, input: Tuple, output: torch.Tensor):
            # Capture the output (activation)
            # output is typically the activation tensor
            self.activation_capture.capture(name, output)
        return hook_fn

    def register_hooks(self):
        """Register forward hooks on target layers."""
        if self._hook_registered:
            logger.info("Hooks already registered.")
            return

        for name in self.target_layers:
            try:
                module = dict(self.model.named_modules())[name]
                hook = self._make_hook(name)
                handle = module.register_forward_hook(hook)
                self._hooks.append(handle)
                logger.debug(f"Registered hook for layer: {name}")
            except KeyError:
                logger.warning(f"Could not find module: {name}")
        
        self._hook_registered = True
        # Initialize capture storage for registered layers
        for name in self.target_layers:
            self.activation_capture.register_layer(name)

    def remove_hooks(self):
        """Remove all registered hooks."""
        for handle in self._hooks:
            handle.remove()
        self._hooks.clear()
        self._hook_registered = False

    def clear_activations(self):
        """Clear stored activations from previous runs."""
        self.activation_capture.clear()

    def forward(self, *args, **kwargs):
        """
        Forward pass through the wrapped model.

        Activations are captured automatically if hooks are registered.
        """
        if not self._hook_registered:
            self.register_hooks()
        
        return self.model(*args, **kwargs)

    def get_activations(self) -> Dict[str, List[torch.Tensor]]:
        """Return the current captured activations."""
        return self.activation_capture.activations

    def get_activation_stats(self) -> Dict[str, Dict[str, Any]]:
        """Return statistics of captured activations."""
        return self.activation_capture.get_statistics()

    def __getattr__(self, name: str):
        """Delegate attribute access to the underlying model if not found in wrapper."""
        try:
            return super().__getattr__(name)
        except AttributeError:
            return getattr(self.model, name)

def get_default_dit_layers(model_type: str) -> List[str]:
    """
    Return default target layers for common DiT architectures.
    
    These are heuristic defaults based on common transformer structures.
    Users should verify against the specific model's architecture.
    """
    defaults = {
        "flux": [
            "double_blocks.0", "double_blocks.5", "double_blocks.10",
            "single_blocks.0", "single_blocks.10", "single_blocks.20"
        ],
        "sd3": [
            "transformer_blocks.0", "transformer_blocks.5", "transformer_blocks.10",
            "final_layer"
        ],
        "wan": [
            "blocks.0", "blocks.5", "blocks.10",
            "norm_out"
        ],
        "default": [
            "layers.0", "layers.5", "layers.10"
        ]
    }
    return defaults.get(model_type.lower(), defaults["default"])

def create_dit_wrapper(model: nn.Module, 
                       model_type: str = "default", 
                       custom_layers: Optional[List[str]] = None,
                       config: Optional[Config] = None) -> DiTWrapper:
    """
    Factory function to create a DiTWrapper with appropriate layers.
    
    Args:
        model: The model instance.
        model_type: String identifier for the model architecture.
        custom_layers: Optional list of specific layer names to hook.
        config: Optional config.
    
    Returns:
        Configured DiTWrapper instance.
    """
    layers = custom_layers if custom_layers else get_default_dit_layers(model_type)
    return DiTWrapper(model, layers, config)

# Example usage pattern (not executed on import):
# wrapper = create_dit_wrapper(model, model_type="flux")
# wrapper.register_hooks()
# output = wrapper(prompt_embeds, timesteps, ...)
# stats = wrapper.get_activation_stats()
# wrapper.remove_hooks()