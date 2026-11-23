"""
Light‑weight Graph Neural Network for composition‑only material graphs.

The architecture follows the specification:
* ≤ 3 GCNConv layers
* hidden dimension ≤ 128
* ReLU activations
* global mean pooling
* two linear heads – one for band‑gap, one for hardness
"""
import torch
from torch import nn
from torch_geometric.nn import GCNConv, global_mean_pool

class CompositionGNN(nn.Module):
    """
    Composition‑only GNN.

    Parameters
    ----------
    in_channels : int
        Number of node features (default 5 – element fraction + 4 periodic
        properties).
    hidden_dim : int, optional
        Hidden dimension for the GCN layers (default 128, respects the
        ≤ 128 constraint).
    """
    def __init__(self, in_channels: int = 5, hidden_dim: int = 128):
        super().__init__()
        # three GCN layers – the third can be omitted by setting hidden_dim to 0
        self.conv1 = GCNConv(in_channels, hidden_dim, add_self_loops=False)
        self.conv2 = GCNConv(hidden_dim, hidden_dim, add_self_loops=False)
        self.conv3 = GCNConv(hidden_dim, hidden_dim, add_self_loops=False)

        self.relu = nn.ReLU()
        self.pool = global_mean_pool

        # two heads – each predicts a single scalar
        self.head_bandgap = nn.Linear(hidden_dim, 1)
        self.head_hardness = nn.Linear(hidden_dim, 1)

    def forward(self, data):
        """
        Forward pass.

        Expects a :class:`torch_geometric.data.Data` object with the
        attributes ``x`` (node features), ``edge_index`` and optionally
        ``edge_weight``.  ``batch`` is created automatically by the
        :class:`torch_geometric.loader.DataLoader`.
        """
        x, edge_index, edge_weight, batch = (
            data.x,
            data.edge_index,
            getattr(data, "edge_weight", None),
            getattr(data, "batch", None),
        )

        # first conv
        x = self.conv1(x, edge_index, edge_weight)
        x = self.relu(x)

        # second conv
        x = self.conv2(x, edge_index, edge_weight)
        x = self.relu(x)

        # third conv
        x = self.conv3(x, edge_index, edge_weight)
        x = self.relu(x)

        # global mean pooling over each graph in the batch
        if batch is None:
            # single‑graph case – create a dummy batch vector
            batch = torch.zeros(x.size(0), dtype=torch.long, device=x.device)
        x = self.pool(x, batch)  # shape: [batch_size, hidden_dim]

        # heads
        band_gap = self.head_bandgap(x).squeeze(-1)      # [batch_size]
        hardness = self.head_hardness(x).squeeze(-1)    # [batch_size]

        return band_gap, hardness
