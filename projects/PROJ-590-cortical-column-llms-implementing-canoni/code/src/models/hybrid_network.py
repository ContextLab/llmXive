import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple, Dict, List
import math
import logging
import sys
import os

# Add project root to path to ensure imports work in execution context
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.models.microcircuit import MicrocircuitColumn, create_microcircuit_column
from src.models.baseline_transformer import BaselineTransformer, count_parameters as baseline_count_parameters
from src.training.homeostasis import HomeostasisConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HybridAttentionBlock(nn.Module):
    """
    A transformer block where the standard FeedForward (MLP) layer is replaced
    by a MicrocircuitColumn. The attention mechanism remains standard.
    """
    def __init__(
        self,
        d_model: int,
        nhead: int,
        num_columns: int = 1,
        dim_feedforward: int = 2048,
        dropout: float = 0.1,
        layer_norm_eps: float = 1e-5
    ):
        super().__init__()
        self.d_model = d_model
        self.nhead = nhead

        # Standard Multi-Head Attention
        self.self_attn = nn.MultiheadAttention(d_model, nhead, dropout=dropout, batch_first=True)
        self.norm1 = nn.LayerNorm(d_model, eps=layer_norm_eps)
        self.dropout = nn.Dropout(dropout)

        # REPLACE Standard MLP with Microcircuit Column
        # The microcircuit column must accept input of size d_model and output d_model
        self.microcircuit = create_microcircuit_column(
            input_size=d_model,
            output_size=d_model,
            num_columns=num_columns,
            config=HomeostasisConfig() # Default config for now
        )

        # Residual connection and normalization for the microcircuit path
        self.norm2 = nn.LayerNorm(d_model, eps=layer_norm_eps)

    def forward(
        self,
        src: torch.Tensor,
        src_mask: Optional[torch.Tensor] = None,
        src_key_padding_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        # Self-Attention Path
        attn_output, _ = self.self_attn(
            src, src, src,
            attn_mask=src_mask,
            key_padding_mask=src_key_padding_mask
        )
        src = src + self.dropout(attn_output)
        src = self.norm1(src)

        # Microcircuit Path (replaces MLP)
        # Ensure input is 3D: (Batch, Seq, Dim)
        if src.dim() == 2:
            src = src.unsqueeze(1)
        
        microcircuit_out = self.microcircuit(src)
        
        # The microcircuit might output a different shape if not perfectly tuned,
        # but create_microcircuit_column should ensure output_size matches input_size.
        # We apply residual and norm.
        src = src + self.dropout(microcircuit_out)
        src = self.norm2(src)

        return src


class HybridNetwork(nn.Module):
    """
    A Transformer-like network where the FeedForward layers are replaced
    by MicrocircuitColumns.
    """
    def __init__(
        self,
        d_model: int = 512,
        nhead: int = 8,
        num_layers: int = 6,
        num_columns: int = 1,
        dim_feedforward: int = 2048, # Kept for reference, but microcircuit defines actual capacity
        dropout: float = 0.1,
        input_size: int = 784,
        num_classes: int = 10
    ):
        super().__init__()
        self.d_model = d_model
        self.num_layers = num_layers

        # Input projection
        self.input_proj = nn.Linear(input_size, d_model)
        
        # Positional Encoding
        self.pos_encoder = nn.Parameter(torch.zeros(1, 1024, d_model)) # Fixed max seq len for simplicity
        nn.init.normal_(self.pos_encoder, std=0.02)

        # Transformer Blocks with Microcircuits
        self.layers = nn.ModuleList([
            HybridAttentionBlock(
                d_model=d_model,
                nhead=nhead,
                num_columns=num_columns,
                dim_feedforward=dim_feedforward,
                dropout=dropout
            )
            for _ in range(num_layers)
        ])

        self.norm = nn.LayerNorm(d_model)
        
        # Output head
        self.classifier = nn.Linear(d_model, num_classes)

        self._init_weights()

    def _init_weights(self):
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)

    def forward(self, src: torch.Tensor, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        # src shape: (Batch, Seq, InputDim) or (Batch, InputDim)
        if src.dim() == 2:
            src = src.unsqueeze(1)
        
        x = self.input_proj(src)
        x = x + self.pos_encoder[:, :x.size(1), :]
        
        for layer in self.layers:
            x = layer(x, src_mask=mask)
        
        x = self.norm(x)
        # Global average pooling over sequence dimension
        x = x.mean(dim=1)
        return self.classifier(x)


def create_hybrid_network(
    input_size: int = 784,
    num_classes: int = 10,
    d_model: int = 512,
    nhead: int = 8,
    num_layers: int = 6,
    num_columns: int = 1,
    dropout: float = 0.1
) -> HybridNetwork:
    """
    Factory function to create a HybridNetwork.
    """
    return HybridNetwork(
        input_size=input_size,
        num_classes=num_classes,
        d_model=d_model,
        nhead=nhead,
        num_layers=num_layers,
        num_columns=num_columns,
        dropout=dropout
    )


def count_parameters(model: nn.Module) -> int:
    """
    Counts the total number of parameters in the model.
    """
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def verify_parameter_count_match(
    hybrid_model: HybridNetwork,
    baseline_model: BaselineTransformer,
    tolerance: float = 0.01
) -> Tuple[bool, Dict[str, float]]:
    """
    Verifies that the parameter count of the hybrid model is within ±1% 
    of the baseline model.
    
    Returns:
        Tuple[bool, Dict]: (is_match, details_dict)
    """
    hybrid_params = count_parameters(hybrid_model)
    baseline_params = count_parameters(baseline_model)
    
    diff = abs(hybrid_params - baseline_params)
    ratio = diff / baseline_params if baseline_params > 0 else 0.0
    
    logger.info(f"Baseline Parameters: {baseline_params:,}")
    logger.info(f"Hybrid Parameters: {hybrid_params:,}")
    logger.info(f"Difference: {diff:,} ({ratio*100:.2f}%)")
    
    if ratio <= tolerance:
        logger.info("Parameter count verification PASSED.")
        return True, {
            "hybrid_params": hybrid_params,
            "baseline_params": baseline_params,
            "difference": diff,
            "ratio": ratio,
            "status": "PASS"
        }
    else:
        logger.error(f"Parameter count verification FAILED. Exceeded {tolerance*100}% tolerance.")
        return False, {
            "hybrid_params": hybrid_params,
            "baseline_params": baseline_params,
            "difference": diff,
            "ratio": ratio,
            "status": "FAIL"
        }


def main():
    """
    Main entry point to demonstrate Hybrid Network creation and parameter verification.
    This script creates a baseline and a hybrid model, verifies parameter counts,
    and logs the result.
    """
    logger.info("Starting Hybrid Network Verification...")
    
    # Configuration
    INPUT_SIZE = 784
    NUM_CLASSES = 10
    D_MODEL = 256  # Smaller for faster testing
    NHEAD = 4
    NUM_LAYERS = 4
    NUM_COLUMNS = 1
    DROPOUT = 0.1

    # 1. Create Baseline Model
    baseline = BaselineTransformer(
        input_size=INPUT_SIZE,
        num_classes=NUM_CLASSES,
        d_model=D_MODEL,
        nhead=NHEAD,
        num_layers=NUM_LAYERS,
        dropout=DROPOUT
    )
    
    # 2. Create Hybrid Model
    hybrid = create_hybrid_network(
        input_size=INPUT_SIZE,
        num_classes=NUM_CLASSES,
        d_model=D_MODEL,
        nhead=NHEAD,
        num_layers=NUM_LAYERS,
        num_columns=NUM_COLUMNS,
        dropout=DROPOUT
    )

    # 3. Verify Parameter Count
    is_match, details = verify_parameter_count_match(hybrid, baseline, tolerance=0.01)
    
    if not is_match:
        # If not matching within 1%, we might need to adjust the microcircuit config
        # or accept that the biological plausibility comes at a parameter cost.
        # However, the task requires verification. We log the failure.
        logger.warning("Parameter counts do not match within 1%. This is a critical check for T048.")
    
    # 4. Simple forward pass to ensure no runtime errors
    dummy_input = torch.randn(2, INPUT_SIZE)
    try:
        _ = hybrid(dummy_input)
        logger.info("Forward pass successful.")
    except Exception as e:
        logger.error(f"Forward pass failed: {e}")
        raise

    return is_match, details


if __name__ == "__main__":
    main()
