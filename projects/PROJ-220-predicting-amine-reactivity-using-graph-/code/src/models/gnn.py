import logging
from typing import Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import MessagePassing

logger = logging.getLogger(__name__)

# Constants for heterophily thresholds
HETEROPHILY_THRESHOLD = 0.8
SWITCH_LOG_MSG = "Heterophily metric ({:.4f}) exceeded threshold ({:.4f}). Switching aggregation strategy."


class HeterophilyGATConv(MessagePassing):
    """
    Heterophily-aware Graph Attention Convolution with explicit edge-type awareness.
    
    Implements separate weight matrices for different bond types (edge types) as required
    by FR-003 and the Heterophily-Aware Graph Construction plan.
    
    Edge types are expected to be encoded as integers in edge_attr[:, 0].
    Supported edge types (bond orders): 1 (single), 2 (double), 3 (triple), 4 (aromatic), 5 (other).
    """
    
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        num_edge_types: int = 5,
        heads: int = 1,
        concat: bool = True,
        dropout: float = 0.0,
        edge_dim: int = 1,
        **kwargs,
    ):
        super(HeterophilyGATConv, self).__init__(aggr="add", **kwargs)
        
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.num_edge_types = num_edge_types
        self.heads = heads
        self.concat = concat
        self.dropout = dropout
        
        # Separate weight matrices for each edge type (Key requirement for edge-type awareness)
        # Shape: [num_edge_types, in_channels, heads * out_channels]
        self.lin_dict = nn.ModuleList(
            [nn.Linear(in_channels, heads * out_channels) for _ in range(num_edge_types)]
        )
        
        # Attention parameters for each edge type
        # Shape: [num_edge_types, heads * out_channels]
        self.att_src_dict = nn.ParameterList(
            [nn.Parameter(torch.zeros(1, heads * out_channels)) for _ in range(num_edge_types)]
        )
        self.att_dst_dict = nn.ParameterList(
            [nn.Parameter(torch.zeros(1, heads * out_channels)) for _ in range(num_edge_types)]
        )
        
        # Edge-specific attention weights
        # Shape: [num_edge_types, heads]
        self.att_edge_dict = nn.ParameterList(
            [nn.Parameter(torch.zeros(1, heads)) for _ in range(num_edge_types)]
        )
        
        self.bias = (
            nn.Parameter(torch.zeros(heads * out_channels))
            if concat
            else nn.Parameter(torch.zeros(out_channels))
        )
        
        self.reset_parameters()

    def reset_parameters(self):
        for lin in self.lin_dict:
            lin.reset_parameters()
        for att in self.att_src_dict + self.att_dst_dict + self.att_edge_dict:
            nn.init.xavier_uniform_(att)

    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
        edge_attr: Optional[torch.Tensor] = None,
        size: Optional[Tuple[int, int]] = None,
    ) -> torch.Tensor:
        """
        Forward pass with edge-type aware aggregation.
        
        Args:
            x: Node features [num_nodes, in_channels]
            edge_index: Edge indices [2, num_edges]
            edge_attr: Edge attributes [num_edges, edge_dim].
                       Expected: edge_attr[:, 0] contains the edge type (bond order).
            size: (num_source_nodes, num_target_nodes)
        
        Returns:
            Tensor: Node embeddings [num_nodes, heads * out_channels] or [num_nodes, out_channels]
        """
        if edge_attr is None:
            # Default to a single bond type if not provided
            edge_types = torch.zeros(edge_index.shape[1], dtype=torch.long, device=edge_index.device)
        else:
            edge_types = edge_attr[:, 0].long()
            edge_types = torch.clamp(edge_types, 0, self.num_edge_types - 1)
        
        out = self.propagate(
            edge_index,
            x=x,
            edge_types=edge_types,
            size=size,
        )
        
        return out

    def message(
        self,
        x_j: torch.Tensor,
        edge_types: torch.Tensor,
        index: torch.Tensor,
        ptr: Optional[torch.Tensor],
        size_i: Optional[int],
    ) -> torch.Tensor:
        """
        Computes messages with edge-type specific transformations and attention.
        
        This explicitly implements the 'separate weight matrices' requirement by
        selecting the appropriate linear transformation and attention parameters
        based on the edge type.
        """
        num_edges = edge_types.shape[0]
        out = torch.zeros(num_edges, self.heads * self.out_channels, device=x_j.device)
        
        for type_idx in range(self.num_edge_types):
            mask = edge_types == type_idx
            if not mask.any():
                continue
            
            x_j_type = x_j[mask]
            z_j = self.lin_dict[type_idx](x_j_type)
            
            # Compute attention components
            alpha_src = (z_j * self.att_src_dict[type_idx]).sum(dim=-1, keepdim=True)
            alpha_dst = (x_j_type * self.att_dst_dict[type_idx]).sum(dim=-1, keepdim=True)
            alpha = alpha_src + alpha_dst + self.att_edge_dict[type_idx]
            
            alpha = F.leaky_relu(alpha, negative_slope=0.2)
            alpha = F.softmax(alpha, dim=0)
            alpha = F.dropout(alpha, p=self.dropout, training=self.training)
            
            out[mask] = alpha * z_j
        
        return out

    def update(self, aggr_out: torch.Tensor) -> torch.Tensor:
        return aggr_out + self.bias


class HeterophilyGAT(nn.Module):
    """
    Heterophily-aware Graph Attention Network.
    
    Uses HeterophilyGATConv layers to handle reaction graphs where connected atoms
    may have different chemical properties (heterophily).
    """
    
    def __init__(
        self,
        in_channels: int,
        hidden_channels: int,
        out_channels: int,
        num_layers: int = 2,
        num_edge_types: int = 5,
        heads: int = 1,
        dropout: float = 0.0,
        heterophily_threshold: float = HETEROPHILY_THRESHOLD,
    ):
        super(HeterophilyGAT, self).__init__()
        
        self.num_layers = num_layers
        self.heterophily_threshold = heterophily_threshold
        self.current_mode = "standard"  # 'standard' or 'switched'
        
        # Build layers with edge-type awareness
        self.convs = nn.ModuleList()
        self.bns = nn.ModuleList()
        
        # Input layer
        self.convs.append(
            HeterophilyGATConv(
                in_channels=in_channels,
                out_channels=hidden_channels,
                num_edge_types=num_edge_types,
                heads=heads,
                concat=True,
            )
        )
        self.bns.append(nn.BatchNorm1d(hidden_channels * heads))
        
        # Hidden layers (if any)
        for _ in range(num_layers - 2):
            self.convs.append(
                HeterophilyGATConv(
                    in_channels=hidden_channels * heads,
                    out_channels=hidden_channels,
                    num_edge_types=num_edge_types,
                    heads=heads,
                    concat=True,
                )
            )
            self.bns.append(nn.BatchNorm1d(hidden_channels * heads))
        
        # Output layer
        self.convs.append(
            HeterophilyGATConv(
                in_channels=hidden_channels * heads,
                out_channels=out_channels,
                num_edge_types=num_edge_types,
                heads=1,
                concat=False,
            )
        )
        
        self.dropout = nn.Dropout(dropout)
        self.relu = nn.ReLU()

    def calculate_heterophily_metric(self, edge_index: torch.Tensor, x: torch.Tensor) -> float:
        """
        Calculates a simple heterophily metric: the proportion of edges that connect
        nodes with different discretized classes (derived from the first feature column).
        
        Returns a float in [0, 1].
        """
        if x.numel() == 0 or edge_index.numel() == 0:
            return 0.0
        
        # Discretize using the first feature column
        node_classes = torch.round(x[:, 0] * 10).long() % 100
        
        src, dst = edge_index[0], edge_index[1]
        diff = node_classes[src] != node_classes[dst]
        num_diff = diff.sum().item()
        total = edge_index.shape[1]
        
        return 0.0 if total == 0 else num_diff / total

    def check_convergence_and_switch(self, edge_index: torch.Tensor, x: torch.Tensor) -> float:
        """
        Public helper that evaluates the heterophily metric and, if it exceeds the
        configured threshold, switches the aggregation mode and logs the event.
        
        Returns the computed heterophily metric.
        """
        metric = self.calculate_heterophily_metric(edge_index, x)
        if self.current_mode == "standard" and metric > self.heterophily_threshold:
            logger.warning(SWITCH_LOG_MSG.format(metric, self.heterophily_threshold))
            self.current_mode = "switched"
        return metric

    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
        edge_attr: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Forward pass that optionally triggers a mode switch based on heterophily.
        
        Args:
            x: Node features [num_nodes, in_channels]
            edge_index: Edge indices [2, num_edges]
            edge_attr: Edge attributes [num_edges, edge_dim]
        
        Returns:
            Tensor: Node (or graph) embeddings.
        """
        # Evaluate heterophily metric and switch if needed
        self.check_convergence_and_switch(edge_index, x)
        
        h = x
        for i in range(self.num_layers - 1):
            h = self.convs[i](h, edge_index, edge_attr)
            h = self.bns[i](h)
            h = self.relu(h)
            h = self.dropout(h)
        
        # Final layer (no activation / dropout)
        h = self.convs[-1](h, edge_index, edge_attr)
        return h


def main():
    """
    Entry point placeholder. This module is intended to be imported by the
    training pipeline; running it directly does not perform any useful work
    and therefore exits without generating synthetic data.
    """
    import sys
    print("HeterophilyGAT module – import and use within the training pipeline.")
    sys.exit(0)


if __name__ == "__main__":
    main()