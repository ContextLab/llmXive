"""
Activation‑variance capture utilities for a Stable Diffusion pipeline.
The DiTActivationCapture class registers forward hooks on the UNet sub‑modules,
runs a dummy forward pass for a given prompt, and returns a dictionary mapping
layer names to the variance of their output activations.
"""
import torch
from llmxive_toolkit import get_logger
from typing import Dict

log = get_logger(__name__)

class DiTActivationCapture:
    """
    Captures activations from the UNet component of a Stable Diffusion pipeline
    and computes per‑layer variance for a given text prompt.
    """
    def __init__(self, pipeline):
        """
        Parameters
        ----------
        pipeline : StableDiffusionPipeline
            The diffusion pipeline whose ``unet`` will be instrumented.
        """
        self.pipeline = pipeline
        self._hooks = []
        self._activations = {}

    def _hook_factory(self, name):
        def hook(module, input, output):
            # Store a detached copy to avoid memory leaks
            self._activations[name] = output.detach()
        return hook

    def _register_hooks(self):
        """
        Registers forward hooks on every sub‑module of the UNet.
        """
        for name, module in self.pipeline.unet.named_modules():
            # Register on all modules – the overhead is negligible for the size of
            # the UNet and keeps the implementation simple.
            handle = module.register_forward_hook(self._hook_factory(name))
            self._hooks.append(handle)

    def _remove_hooks(self):
        for handle in self._hooks:
            handle.remove()
        self._hooks.clear()

    def measure_variance(self, prompt: str) -> Dict[str, float]:
        """
        Runs a forward pass through the UNet for ``prompt`` and returns a mapping
        from layer name to activation variance (as a Python float).

        Parameters
        ----------
        prompt : str
            Text prompt to condition the generation.

        Returns
        -------
        dict
            ``{layer_name: variance}`` for each hooked layer.
        """
        device = self.pipeline.device

        # Encode the prompt using the pipeline's tokenizer & text encoder
        tokenizer = self.pipeline.tokenizer
        text_inputs = tokenizer(
            prompt,
            padding="max_length",
            truncation=True,
            max_length=tokenizer.model_max_length,
            return_tensors="pt",
        ).to(device)

        with torch.no_grad():
            # Obtain text embeddings
            encoder_hidden_states = self.pipeline.text_encoder(**text_inputs).last_hidden_state

            # Dummy latent tensor (shape matches UNet expectations)
            latent_shape = (1, self.pipeline.unet.in_channels, 64, 64)
            latents = torch.randn(latent_shape, device=device)

            # Use a mid‑range timestep (half of training timesteps)
            timesteps = torch.tensor(
                [self.pipeline.scheduler.config.num_train_timesteps // 2],
                device=device,
                dtype=torch.long,
            )

            # Register hooks before the forward pass
            self._register_hooks()

            # Forward through UNet – this triggers the hooks
            _ = self.pipeline.unet(latents, timesteps, encoder_hidden_states)

            # Remove hooks immediately after the pass to avoid side effects
            self._remove_hooks()

        # Compute variance per layer
        variance_dict = {}
        for name, activation in self._activations.items():
            # ``activation`` is a tensor of shape (B, C, H, W) or similar
            var = torch.var(activation).item()
            variance_dict[name] = var
        # Clean stored activations
        self._activations.clear()

        log.info(f"Captured variance for prompt '{prompt}' on {len(variance_dict)} layers")
        return variance_dict
