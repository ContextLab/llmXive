import torch
import torch.nn as nn
from typing import Optional, Dict, Any, Tuple
import numpy as np
from models.base import ProjectionModel
from utils.logging import get_logger, log_info, log_error

logger = get_logger(__name__)

class MLPProjection(nn.Module, ProjectionModel):
    def __init__(self, input_dim: int, tabular_dim: int, hidden_dim: int = 128, output_dim: int = 1):
        super().__init__()
        self.input_dim = input_dim
        self.tabular_dim = tabular_dim
        
        # Project embedding
        self.embedding_proj = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1)
        )
        
        # Project tabular features
        self.tabular_proj = nn.Sequential(
            nn.Linear(tabular_dim, hidden_dim),
            nn.ReLU()
        )
        
        # Fusion
        self.fusion = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim)
        )

    def forward(self, x_emb: torch.Tensor, x_tabular: torch.Tensor) -> torch.Tensor:
        # x_emb: (N, input_dim)
        # x_tabular: (N, tabular_dim)
        
        emb_out = self.embedding_proj(x_emb)
        tab_out = self.tabular_proj(x_tabular)
        
        # Concatenate
        combined = torch.cat([emb_out, tab_out], dim=1)
        
        output = self.fusion(combined)
        return output

class AttentionProjection(nn.Module, ProjectionModel):
    def __init__(self, input_dim: int, tabular_dim: int, hidden_dim: int = 128, output_dim: int = 1):
        super().__init__()
        self.input_dim = input_dim
        self.tabular_dim = tabular_dim
        
        # Query from tabular, Key/Value from embedding
        self.query_proj = nn.Linear(tabular_dim, hidden_dim)
        self.key_proj = nn.Linear(input_dim, hidden_dim)
        self.value_proj = nn.Linear(input_dim, hidden_dim)
        
        self.attention = nn.MultiheadAttention(embed_dim=hidden_dim, num_heads=4, batch_first=True)
        
        self.output_proj = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim)
        )

    def forward(self, x_emb: torch.Tensor, x_tabular: torch.Tensor) -> torch.Tensor:
        # x_emb: (N, input_dim) -> (N, 1, input_dim)
        # x_tabular: (N, tabular_dim) -> (N, 1, tabular_dim)
        
        # Add sequence dimension
        x_emb_seq = x_emb.unsqueeze(1) # (N, 1, input_dim)
        x_tab_seq = x_tabular.unsqueeze(1) # (N, 1, tabular_dim)
        
        query = self.query_proj(x_tab_seq) # (N, 1, hidden)
        key = self.key_proj(x_emb_seq) # (N, 1, hidden)
        value = self.value_proj(x_emb_seq) # (N, 1, hidden)
        
        attn_out, _ = self.attention(query, key, value)
        
        output = self.output_proj(attn_out.squeeze(1))
        return output

class GatedProjection(nn.Module, ProjectionModel):
    def __init__(self, input_dim: int, tabular_dim: int, hidden_dim: int = 128, output_dim: int = 1):
        super().__init__()
        self.input_dim = input_dim
        self.tabular_dim = tabular_dim
        
        self.embedding_proj = nn.Linear(input_dim, hidden_dim)
        self.tabular_proj = nn.Linear(tabular_dim, hidden_dim)
        
        # Gating mechanism
        self.gate = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.Sigmoid()
        )
        
        self.output_proj = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim)
        )

    def forward(self, x_emb: torch.Tensor, x_tabular: torch.Tensor) -> torch.Tensor:
        emb_out = self.embedding_proj(x_emb)
        tab_out = self.tabular_proj(x_tabular)
        
        combined = torch.cat([emb_out, tab_out], dim=1)
        gate_val = self.gate(combined)
        
        # Apply gate
        gated_out = emb_out * gate_val[:, :self.input_dim] # Simplified gating
        
        output = self.output_proj(gated_out)
        return output

def create_projection_model(model_type: str = "mlp", input_dim: int = 512, output_dim: int = 1, tabular_dim: int = 10) -> nn.Module:
    if model_type == "mlp":
        return MLPProjection(input_dim=input_dim, tabular_dim=tabular_dim, output_dim=output_dim)
    elif model_type == "attention":
        return AttentionProjection(input_dim=input_dim, tabular_dim=tabular_dim, output_dim=output_dim)
    elif model_type == "gated":
        return GatedProjection(input_dim=input_dim, tabular_dim=tabular_dim, output_dim=output_dim)
    else:
        raise ValueError(f"Unknown model type: {model_type}")
