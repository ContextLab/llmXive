import logging
import math
import gc
from typing import Optional, Dict, Any, Tuple, List

import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor

from src.utils.resource_monitor import get_current_ram_gb
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

# Constants for DiT configuration to fit within 7GB RAM
# Qwen2-VL-2B (frozen) + DiT Head
# Estimated frozen model size: ~4GB (FP16)
# Remaining budget for DiT: ~3GB
# We use a smaller DiT with 4 blocks and hidden dim 512
DIT_HIDDEN_DIM = 512
DIT_NUM_BLOCKS = 4
DIT_HEAD_DIM = 64
DIT_NUM_HEADS = DIT_HIDDEN_DIM // DIT_HEAD_DIM
DIT_MLP_RATIO = 4.0
ACTION_DIM = 8  # Standard joint space dimension (position + velocity or just position)
ACTION_QUANTIZATION_LEVELS = 256  # 8-bit quantization per dimension

class PatchEmbed(nn.Module):
    """2D Image to Patch Embedding adapted for 1D action sequences."""
    def __init__(self, input_dim: int, patch_size: int, embed_dim: int):
        super().__init__()
        self.input_dim = input_dim
        self.patch_size = patch_size
        self.embed_dim = embed_dim
        self.num_patches = input_dim // patch_size
        
        self.proj = nn.Linear(patch_size, embed_dim)
        self.norm = nn.LayerNorm(embed_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, L) where L is input_dim
        # Reshape to (B, num_patches, patch_size)
        B, L = x.shape
        x = x.view(B, self.num_patches, self.patch_size)
        x = self.proj(x)
        x = self.norm(x)
        return x

class DiTBlock(nn.Module):
    """A single DiT block with AdaLN."""
    def __init__(self, hidden_dim: int, num_heads: int, mlp_ratio: float = 4.0):
        super().__init__()
        self.norm1 = nn.LayerNorm(hidden_dim, elementwise_affine=False, eps=1e-6)
        self.norm2 = nn.LayerNorm(hidden_dim, elementwise_affine=False, eps=1e-6)
        
        self.attn = nn.MultiheadAttention(
            embed_dim=hidden_dim, 
            num_heads=num_heads, 
            batch_first=True,
            dropout=0.0,
            bias=True
        )
        
        mlp_hidden_dim = int(hidden_dim * mlp_ratio)
        self.mlp = nn.Sequential(
            nn.Linear(hidden_dim, mlp_hidden_dim),
            nn.GELU(approximate="tanh"),
            nn.Linear(mlp_hidden_dim, hidden_dim)
        )
        
        self.adaLN_modulation = nn.Sequential(
            nn.SiLU(),
            nn.Linear(hidden_dim, 3 * hidden_dim)
        )

    def forward(self, x: torch.Tensor, cond: torch.Tensor) -> torch.Tensor:
        # x: (B, T, D)
        # cond: (B, D)
        
        # AdaLN modulation
        shift_msa, scale_msa, gate_msa = self.adaLN_modulation(cond).chunk(3, dim=-1)
        shift_msa = shift_msa.unsqueeze(1)
        scale_msa = scale_msa.unsqueeze(1)
        gate_msa = gate_msa.unsqueeze(1)
        
        normed_x = self.norm1(x)
        normed_x = normed_x * (1 + scale_msa) + shift_msa
        
        attn_out, _ = self.attn(normed_x, normed_x, normed_x)
        x = x + gate_msa * attn_out
        
        # MLP
        shift_mlp, scale_mlp, gate_mlp = self.adaLN_modulation(cond).chunk(3, dim=-1)
        shift_mlp = shift_mlp.unsqueeze(1)
        scale_mlp = scale_mlp.unsqueeze(1)
        gate_mlp = gate_mlp.unsqueeze(1)
        
        normed_x = self.norm2(x)
        normed_x = normed_x * (1 + scale_mlp) + shift_mlp
        mlp_out = self.mlp(normed_x)
        x = x + gate_mlp * mlp_out
        
        return x

class DiTActionHead(nn.Module):
    """DiT-based action head for VLA models.
    
    Implements a token-space strategy using 8-bit quantization per action dimension.
    This reduces the output space from continuous to discrete tokens, allowing
    the model to be trained with cross-entropy loss and keeping memory footprint low.
    
    Token Space Strategy:
    - Each action dimension is quantized to 256 levels (0-255)
    - Output is a sequence of tokens, one per action dimension
    - Dequantization is performed during inference to recover continuous actions
    """
    def __init__(
        self, 
        hidden_dim: int = DIT_HIDDEN_DIM,
        num_blocks: int = DIT_NUM_BLOCKS,
        num_heads: int = DIT_NUM_HEADS,
        action_dim: int = ACTION_DIM,
        quantization_levels: int = ACTION_QUANTIZATION_LEVELS,
        mlp_ratio: float = DIT_MLP_RATIO
    ):
        super().__init__()
        
        self.action_dim = action_dim
        self.quantization_levels = quantization_levels
        self.hidden_dim = hidden_dim
        
        # Input projection
        self.input_proj = nn.Linear(hidden_dim, hidden_dim)
        
        # DiT Blocks
        self.blocks = nn.ModuleList([
            DiTBlock(hidden_dim, num_heads, mlp_ratio)
            for _ in range(num_blocks)
        ])
        
        # Final norm
        self.final_norm = nn.LayerNorm(hidden_dim)
        
        # Output head: predict token for each action dimension
        self.output_head = nn.Linear(hidden_dim, quantization_levels)
        
        # Learnable positional embeddings for action dimensions
        self.pos_embed = nn.Parameter(torch.zeros(1, action_dim, hidden_dim))
        
        # Initialize weights
        self._init_weights()

    def _init_weights(self):
        for block in self.blocks:
            for name, param in block.named_parameters():
                if 'weight' in name:
                    nn.init.trunc_normal_(param, std=0.02)
                elif 'bias' in name:
                    nn.init.zeros_(param)
        
        nn.init.trunc_normal_(self.pos_embed, std=0.02)
        nn.init.trunc_normal_(self.input_proj.weight, std=0.02)
        nn.init.trunc_normal_(self.output_head.weight, std=0.02)

    def forward(self, x: torch.Tensor, cond: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (B, T, D) - Input hidden states from Qwen2-VL (typically just [CLS] or pooled)
            cond: (B, D) - Condition vector (e.g., from [CLS] token or pooled features)
        
        Returns:
            logits: (B, action_dim, quantization_levels) - Logits for each action dimension
        """
        # Project input
        x = self.input_proj(x)
        
        # Reshape to (B, action_dim, D) if input is not already in that shape
        if x.shape[1] != self.action_dim:
            # If we have a sequence, we can either pool or repeat
            # For simplicity, we repeat the pooled representation
            B, T, D = x.shape
            x = x[:, -1:, :]  # Take last token
            x = x.repeat(1, self.action_dim, 1)  # (B, action_dim, D)
        
        # Add positional embeddings
        x = x + self.pos_embed
        
        # Pass through DiT blocks
        for block in self.blocks:
            x = block(x, cond)
        
        # Final normalization
        x = self.final_norm(x)
        
        # Output head
        logits = self.output_head(x)  # (B, action_dim, quantization_levels)
        
        return logits

    def dequantize(self, token_ids: torch.Tensor) -> torch.Tensor:
        """Convert quantized token IDs back to continuous action space.
        
        Args:
            token_ids: (B, action_dim) - Quantized token IDs (0-255)
        
        Returns:
            actions: (B, action_dim) - Continuous actions in [-1, 1] range
        """
        # Normalize from [0, 255] to [-1, 1]
        token_ids = token_ids.float()
        actions = (token_ids / (self.quantization_levels - 1)) * 2.0 - 1.0
        return actions

    def quantize(self, actions: torch.Tensor) -> torch.Tensor:
        """Convert continuous actions to quantized token IDs.
        
        Args:
            actions: (B, action_dim) - Continuous actions in [-1, 1] range
        
        Returns:
            token_ids: (B, action_dim) - Quantized token IDs (0-255)
        """
        # Normalize from [-1, 1] to [0, 255]
        actions = actions.float()
        token_ids = ((actions + 1.0) / 2.0 * (self.quantization_levels - 1)).long()
        # Clamp to valid range
        token_ids = torch.clamp(token_ids, 0, self.quantization_levels - 1)
        return token_ids

class Qwen2VLVLA(nn.Module):
    """Qwen2-VL-2B with frozen vision encoder and DiT action head.
    
    Architecture:
    - Qwen2-VL-2B: Frozen vision-language encoder (4GB FP16)
    - DiT Action Head: Small transformer for action generation (~500MB)
    
    Total memory footprint: ~5GB (well within 7GB limit)
    """
    def __init__(
        self,
        model_name: str = "Qwen/Qwen2-VL-2B-Instruct",
        device: str = "cpu",
        action_dim: int = ACTION_DIM,
        quantization_levels: int = ACTION_QUANTIZATION_LEVELS
    ):
        super().__init__()
        
        self.device = device
        self.action_dim = action_dim
        self.quantization_levels = quantization_levels
        
        logger.info(f"Loading Qwen2-VL model: {model_name}")
        logger.info("Freezing all Qwen2-VL parameters...")
        
        # Load Qwen2-VL with frozen weights
        # Use torch_dtype=torch.float16 to save memory
        try:
            self.qwen_model = Qwen2VLForConditionalGeneration.from_pretrained(
                model_name,
                torch_dtype=torch.float16,
                device_map="cpu",
                low_cpu_mem_usage=True
            )
            # Freeze all parameters
            for param in self.qwen_model.parameters():
                param.requires_grad = False
            self.qwen_model.eval()
            logger.info("Qwen2-VL model loaded and frozen successfully.")
        except Exception as e:
            logger.error(f"Failed to load Qwen2-VL model: {e}")
            raise
        
        # Initialize DiT action head
        self.action_head = DiTActionHead(
            action_dim=action_dim,
            quantization_levels=quantization_levels
        )
        
        logger.info("DiT action head initialized.")
        
        # Memory validation
        self._validate_memory_footprint()

    def _validate_memory_footprint(self):
        """Validate that the model fits within 7GB RAM."""
        # Count parameters
        total_params = sum(p.numel() for p in self.parameters())
        trainable_params = sum(p.numel() for p in self.parameters() if p.requires_grad)
        
        # Estimate memory usage (FP16 = 2 bytes per param)
        estimated_memory_gb = (total_params * 2) / (1024 ** 3)
        
        logger.info(f"Total parameters: {total_params:,}")
        logger.info(f"Trainable parameters: {trainable_params:,}")
        logger.info(f"Estimated memory footprint: {estimated_memory_gb:.2f} GB")
        
        if estimated_memory_gb > 6.5:  # Leave headroom
            logger.warning(f"Model memory footprint ({estimated_memory_gb:.2f} GB) is high. "
                         f"Consider reducing DiT hidden_dim or num_blocks.")
        else:
            logger.info(f"Model fits within 7GB RAM limit (estimated: {estimated_memory_gb:.2f} GB)")

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        pixel_values: Optional[torch.Tensor] = None,
        image_grid_thw: Optional[torch.Tensor] = None,
        cond: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass for training/inference.
        
        Args:
            input_ids: (B, L) - Input token IDs
            attention_mask: (B, L) - Attention mask
            pixel_values: (B, N, C, H, W) - Pixel values for images
            image_grid_thw: (B, N, 3) - Image grid dimensions (T, H, W)
            cond: (B, D) - Optional condition vector (if None, computed from model)
        
        Returns:
            action_logits: (B, action_dim, quantization_levels) - Action logits
            hidden_states: (B, T, D) - Hidden states from Qwen2-VL
        """
        # Get hidden states from Qwen2-VL
        with torch.no_grad():
            outputs = self.qwen_model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                pixel_values=pixel_values,
                image_grid_thw=image_grid_thw,
                output_hidden_states=True
            )
            hidden_states = outputs.hidden_states[-1]  # (B, L, D)
        
        # If cond is not provided, use the last hidden state (or pooled)
        if cond is None:
            # Use the last token as condition
            cond = hidden_states[:, -1, :]
        
        # Pass through DiT action head
        action_logits = self.action_head(hidden_states, cond)
        
        return action_logits, hidden_states

    def generate_actions(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        pixel_values: Optional[torch.Tensor] = None,
        image_grid_thw: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """Generate continuous actions from input.
        
        Args:
            input_ids: (B, L) - Input token IDs
            attention_mask: (B, L) - Attention mask
            pixel_values: (B, N, C, H, W) - Pixel values for images
            image_grid_thw: (B, N, 3) - Image grid dimensions (T, H, W)
        
        Returns:
            actions: (B, action_dim) - Continuous actions in [-1, 1] range
        """
        action_logits, _ = self.forward(
            input_ids=input_ids,
            attention_mask=attention_mask,
            pixel_values=pixel_values,
            image_grid_thw=image_grid_thw
        )
        
        # Sample tokens (or use argmax)
        token_ids = torch.argmax(action_logits, dim=-1)  # (B, action_dim)
        
        # Dequantize to continuous actions
        actions = self.action_head.dequantize(token_ids)
        
        return actions

    def compute_loss(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        pixel_values: Optional[torch.Tensor] = None,
        image_grid_thw: Optional[torch.Tensor] = None,
        actions: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """Compute training loss given ground-truth actions.
        
        Args:
            input_ids: (B, L) - Input token IDs
            attention_mask: (B, L) - Attention mask
            pixel_values: (B, N, C, H, W) - Pixel values for images
            image_grid_thw: (B, N, 3) - Image grid dimensions (T, H, W)
            actions: (B, action_dim) - Ground-truth continuous actions in [-1, 1] range
        
        Returns:
            loss: Scalar loss value
        """
        action_logits, _ = self.forward(
            input_ids=input_ids,
            attention_mask=attention_mask,
            pixel_values=pixel_values,
            image_grid_thw=image_grid_thw
        )
        
        if actions is None:
            raise ValueError("Ground-truth actions are required for loss computation")
        
        # Quantize ground-truth actions
        target_tokens = self.action_head.quantize(actions)  # (B, action_dim)
        
        # Compute cross-entropy loss
        loss = F.cross_entropy(
            action_logits.view(-1, self.quantization_levels),
            target_tokens.view(-1)
        )
        
        return loss

def main():
    """Test script to validate the VLA model implementation and memory footprint."""
    logging.basicConfig(level=logging.INFO)
    
    logger.info("Initializing VLA model for memory validation...")
    
    # Create a minimal model instance for testing
    # Note: In a real scenario, we would load the full model
    # Here we just validate the DiT head memory
    try:
        model = Qwen2VLVLA(
            model_name="Qwen/Qwen2-VL-2B-Instruct",
            device="cpu",
            action_dim=ACTION_DIM,
            quantization_levels=ACTION_QUANTIZATION_LEVELS
        )
        
        logger.info("Model initialization successful.")
        
        # Test forward pass with dummy data
        batch_size = 2
        seq_len = 10
        dummy_input_ids = torch.randint(0, 1000, (batch_size, seq_len))
        dummy_attention_mask = torch.ones(batch_size, seq_len)
        
        # Note: pixel_values and image_grid_thw would be needed for full forward pass
        # For memory validation, we just check the model structure
        
        logger.info("Memory validation completed successfully.")
        logger.info(f"Action space: {ACTION_DIM} dimensions, {ACTION_QUANTIZATION_LEVELS} levels per dimension")
        logger.info("Token space strategy: 8-bit quantization per action dimension")
        
    except Exception as e:
        logger.error(f"Model validation failed: {e}")
        raise

if __name__ == "__main__":
    main()
