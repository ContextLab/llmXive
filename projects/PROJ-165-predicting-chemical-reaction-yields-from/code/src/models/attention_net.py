import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple, Dict, Any, List

class MultiHeadSelfAttention(nn.Module):
    """
    Multi-head self-attention mechanism for processing concatenated spectral,
    fingerprint, and condition features.
    """
    def __init__(
        self,
        embed_dim: int,
        num_heads: int = 8,
        dropout: float = 0.1
    ):
        super().__init__()
        assert embed_dim % num_heads == 0, "embed_dim must be divisible by num_heads"
        
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        
        self.qkv_proj = nn.Linear(embed_dim, embed_dim * 3)
        self.out_proj = nn.Linear(embed_dim, embed_dim)
        
        self.dropout = nn.Dropout(dropout)
        self.layer_norm = nn.LayerNorm(embed_dim)

    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Args:
            x: Input tensor of shape (batch_size, seq_len, embed_dim)
            mask: Optional attention mask of shape (batch_size, 1, 1, seq_len)
        Returns:
            Output tensor of shape (batch_size, seq_len, embed_dim)
        """
        residual = x
        x = self.layer_norm(x)
        
        batch_size, seq_len, embed_dim = x.shape
        
        # Linear projection for Q, K, V
        qkv = self.qkv_proj(x)
        qkv = qkv.view(batch_size, seq_len, 3, self.num_heads, self.head_dim)
        qkv = qkv.permute(2, 0, 3, 1, 4)  # (3, batch, heads, seq, head_dim)
        q, k, v = qkv[0], qkv[1], qkv[2]
        
        # Scaled dot-product attention
        scores = torch.matmul(q, k.transpose(-2, -1)) / (self.head_dim ** 0.5)
        
        if mask is not None:
            scores = scores.masked_fill(mask == 0, float('-inf'))
        
        attn_weights = F.softmax(scores, dim=-1)
        attn_weights = self.dropout(attn_weights)
        
        attn_output = torch.matmul(attn_weights, v)
        attn_output = attn_output.permute(0, 2, 1, 3).contiguous()
        attn_output = attn_output.view(batch_size, seq_len, embed_dim)
        
        output = self.out_proj(attn_output)
        output = residual + output
        
        return output


class SpectralFusionBlock(nn.Module):
    """
    Block to process and fuse spectral data with self-attention.
    """
    def __init__(
        self,
        input_dim: int,
        embed_dim: int,
        num_heads: int = 8,
        dropout: float = 0.1
    ):
        super().__init__()
        
        self.input_proj = nn.Linear(input_dim, embed_dim)
        self.attention = MultiHeadSelfAttention(embed_dim, num_heads, dropout)
        self.ffn = nn.Sequential(
            nn.Linear(embed_dim, embed_dim * 4),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(embed_dim * 4, embed_dim),
            nn.Dropout(dropout)
        )
        self.layer_norm = nn.LayerNorm(embed_dim)

    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        residual = x
        x = self.input_proj(x)
        x = self.attention(x, mask)
        x = self.ffn(x)
        x = residual + x
        x = self.layer_norm(x)
        return x


class AttentionNet(nn.Module):
    """
    Multi-head self-attention network for predicting normalized DFT total molecular energy.
    
    Architecture:
    1. Spectral Fusion Block: Processes concatenated spectral tensors (IR, Raman, NMR)
    2. Fingerprint Projection: Embeds ECFP4 vectors
    3. Condition Embedding: Encodes reaction conditions
    4. Cross-Attention/Fusion: Fuses all modalities
    5. Regression Head: Predicts energy
    """
    def __init__(
        self,
        spectral_dim: int,
        fingerprint_dim: int,
        condition_dim: int,
        embed_dim: int = 256,
        num_heads: int = 8,
        num_layers: int = 2,
        dropout: float = 0.1,
        hidden_dim: int = 512
    ):
        super().__init__()
        
        self.embed_dim = embed_dim
        
        # Spectral processing
        self.spectral_fusion = SpectralFusionBlock(
            input_dim=spectral_dim,
            embed_dim=embed_dim,
            num_heads=num_heads,
            dropout=dropout
        )
        
        # Fingerprint projection
        self.fingerprint_proj = nn.Linear(fingerprint_dim, embed_dim)
        
        # Condition embedding
        self.condition_proj = nn.Linear(condition_dim, embed_dim)
        
        # Cross-modal fusion layers
        self.fusion_layers = nn.ModuleList([
            MultiHeadSelfAttention(embed_dim, num_heads, dropout)
            for _ in range(num_layers)
        ])
        
        # Regression head
        self.regression_head = nn.Sequential(
            nn.Linear(embed_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, embed_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(embed_dim, 1)  # Single output for energy
        )
        
        self.dropout = nn.Dropout(dropout)

    def forward(
        self,
        spectra: torch.Tensor,
        fingerprints: torch.Tensor,
        conditions: torch.Tensor,
        spectral_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Forward pass for energy prediction.
        
        Args:
            spectra: Spectral tensor of shape (batch_size, seq_len, spectral_dim)
            fingerprints: Fingerprint tensor of shape (batch_size, fingerprint_dim)
            conditions: Condition tensor of shape (batch_size, condition_dim)
            spectral_mask: Optional mask for spectral data (batch_size, 1, 1, seq_len)
        
        Returns:
            Predicted energy tensor of shape (batch_size, 1)
        """
        # Process spectra through fusion block
        spectral_features = self.spectral_fusion(spectra, spectral_mask)
        
        # Project fingerprints and conditions to embedding space
        fingerprint_features = self.fingerprint_proj(fingerprints)
        condition_features = self.condition_proj(conditions)
        
        # Add condition features to fingerprint features (broadcasting)
        fingerprint_features = fingerprint_features + condition_features
        
        # Expand fingerprint features to sequence length for fusion
        batch_size, seq_len = spectral_features.shape[0], spectral_features.shape[1]
        fingerprint_features = fingerprint_features.unsqueeze(1).expand(-1, seq_len, -1)
        
        # Concatenate spectral and fingerprint features
        combined = torch.cat([spectral_features, fingerprint_features], dim=-1)
        
        # Apply fusion layers
        for layer in self.fusion_layers:
            combined = layer(combined, spectral_mask)
        
        # Aggregate sequence (mean pooling over spectral positions)
        if spectral_mask is not None:
            # Mask-aware pooling
            mask_expanded = spectral_mask.squeeze(1).squeeze(1).unsqueeze(-1)  # (batch, seq, 1)
            masked_sum = (combined * mask_expanded).sum(dim=1)
            masked_count = mask_expanded.sum(dim=1).clamp(min=1e-9)
            aggregated = masked_sum / masked_count
        else:
            aggregated = combined.mean(dim=1)
        
        # Final regression
        energy = self.regression_head(aggregated)
        
        return energy

    def get_attention_weights(
        self,
        spectra: torch.Tensor,
        fingerprints: torch.Tensor,
        conditions: torch.Tensor,
        spectral_mask: Optional[torch.Tensor] = None
    ) -> List[torch.Tensor]:
        """
        Extract attention weights from all fusion layers for interpretability.
        
        Returns:
            List of attention weight tensors from each fusion layer.
        """
        spectral_features = self.spectral_fusion(spectra, spectral_mask)
        fingerprint_features = self.fingerprint_proj(fingerprints)
        condition_features = self.condition_proj(conditions)
        fingerprint_features = fingerprint_features + condition_features
        
        batch_size, seq_len = spectral_features.shape[0], spectral_features.shape[1]
        fingerprint_features = fingerprint_features.unsqueeze(1).expand(-1, seq_len, -1)
        
        combined = torch.cat([spectral_features, fingerprint_features], dim=-1)
        
        attention_weights = []
        for layer in self.fusion_layers:
            # Forward pass to get attention (we need to modify layer to return weights)
            # For now, we'll just return the layer's attention mechanism weights
            # This requires a slight modification to MultiHeadSelfAttention to expose weights
            residual = combined
            combined = layer.layer_norm(combined)
            
            batch_size, seq_len, embed_dim = combined.shape
            qkv = layer.qkv_proj(combined)
            qkv = qkv.view(batch_size, seq_len, 3, layer.num_heads, layer.head_dim)
            qkv = qkv.permute(2, 0, 3, 1, 4)
            q, k, v = qkv[0], qkv[1], qkv[2]
            
            scores = torch.matmul(q, k.transpose(-2, -1)) / (layer.head_dim ** 0.5)
            if spectral_mask is not None:
                scores = scores.masked_fill(spectral_mask == 0, float('-inf'))
            attn_weights = F.softmax(scores, dim=-1)
            attention_weights.append(attn_weights)
            
            attn_output = torch.matmul(attn_weights, v)
            attn_output = attn_output.permute(0, 2, 1, 3).contiguous()
            attn_output = attn_output.view(batch_size, seq_len, embed_dim)
            combined = residual + layer.out_proj(attn_output)
        
        return attention_weights


def create_attention_model(
    spectral_dim: int,
    fingerprint_dim: int,
    condition_dim: int,
    embed_dim: int = 256,
    num_heads: int = 8,
    num_layers: int = 2,
    dropout: float = 0.1,
    hidden_dim: int = 512
) -> AttentionNet:
    """
    Factory function to create an AttentionNet model with specified dimensions.
    
    Args:
        spectral_dim: Dimension of spectral input features
        fingerprint_dim: Dimension of ECFP4 fingerprint vector
        condition_dim: Dimension of encoded reaction conditions
        embed_dim: Embedding dimension for attention mechanism
        num_heads: Number of attention heads
        num_layers: Number of fusion layers
        dropout: Dropout probability
        hidden_dim: Hidden dimension in regression head
    
    Returns:
        Configured AttentionNet model instance
    """
    model = AttentionNet(
        spectral_dim=spectral_dim,
        fingerprint_dim=fingerprint_dim,
        condition_dim=condition_dim,
        embed_dim=embed_dim,
        num_heads=num_heads,
        num_layers=num_layers,
        dropout=dropout,
        hidden_dim=hidden_dim
    )
    return model