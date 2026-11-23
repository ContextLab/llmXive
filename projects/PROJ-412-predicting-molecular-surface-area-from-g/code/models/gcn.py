import torch
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, global_mean_pool
from torch_geometric.data import Data
from typing import Optional, Tuple, List
import logging

logger = logging.getLogger(__name__)

class GCNModel(torch.nn.Module):
    """
    Lightweight Graph Convolutional Network for predicting molecular surface area.
    Designed to be CPU-tractable as per project constraints.
    
    Attributes:
        conv1 (GCNConv): First graph convolutional layer.
        conv2 (GCNConv): Second graph convolutional layer.
        fc (torch.nn.Linear): Fully connected output layer.
    """

    def __init__(
        self,
        in_channels: int,
        hidden_channels: int = 64,
        out_channels: int = 1,
        dropout: float = 0.1
    ):
        """
        Initialize the GCN model.
        
        Args:
            in_channels (int): Number of input features per node (e.g., atom_type, hybridization, charge).
            hidden_channels (int): Number of hidden units in GCN layers.
            out_channels (int): Number of output features (1 for regression of SASA).
            dropout (float): Dropout probability for regularization.
        """
        super(GCNModel, self).__init__()
        self.conv1 = GCNConv(in_channels, hidden_channels)
        self.conv2 = GCNConv(hidden_channels, hidden_channels)
        self.fc = torch.nn.Linear(hidden_channels, out_channels)
        self.dropout = dropout
        self.hidden_channels = hidden_channels

    def forward(self, input_tensor: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the network.
        
        This method expects a PyTorch Geometric style input where the tensor
        represents node features. In a full training loop, this would be called
        with `model(data.x, data.edge_index, data.batch)`. For this implementation,
        we assume `input_tensor` is the node feature matrix `x`.
        
        To perform a full graph-level prediction, the caller should handle
        the edge_index and batch vector, or this method can be extended to accept
        them. However, adhering strictly to the task signature `forward(input_tensor)`,
        we implement the node-wise transformation and pooling logic here
        assuming the surrounding context provides the graph structure if needed,
        or we return the pooled representation if `input_tensor` is pre-aggregated.
        
        Correction for strict API compliance:
        The task asks for `forward(input_tensor)`. In standard PyG usage,
        the model is called as `model(x, edge_index, batch)`.
        To make this robust and runnable as a `forward(input_tensor)` method
        where `input_tensor` is the node feature matrix, we will assume
        the graph structure (edge_index) and batch vector are either
        stored as attributes or passed in a way compatible with PyG's Data object.
        
        However, to strictly satisfy the prompt's `forward(input_tensor)` signature
        while remaining a valid GCN, we will implement a version that expects
        `input_tensor` to be a dictionary or object containing `x`, `edge_index`,
        and `batch` if we are doing graph-level regression, OR we assume
        the caller passes the raw node features and we cannot compute edge convolutions
        without the edge index.
        
        Re-reading the task: "containing class GCNModel with forward(input_tensor) method".
        In the context of the training loop (T022), the data loader yields `Data` objects.
        The standard pattern is `y_pred = model(data.x, data.edge_index, data.batch)`.
        If we force `forward(input_tensor)` where `input_tensor` is just `x`,
        we cannot perform GCN convolutions without `edge_index`.
        
        Solution: We will implement `forward` to accept the node features `x`
        but we will also require `edge_index` and `batch` to be passed as keyword arguments
        or assume the input is a `Data` object.
        
        Wait, the prompt explicitly says `forward(input_tensor)`.
        If I strictly follow `forward(self, input_tensor: torch.Tensor)`, I cannot
        do GCN without `edge_index`.
        
        Let's look at the existing API surface provided in the prompt:
        `code/models/gcn.py` imports: `GCNConv, global_mean_pool`.
        The prompt says "extend it".
        
        Let's assume `input_tensor` in the prompt description refers to the
        `Data` object or the tuple of tensors. But the type hint says `torch.Tensor`.
        
        Let's interpret `input_tensor` as the node feature matrix `x`, and
        assume the `edge_index` and `batch` are available in the context
        or passed as additional arguments.
        
        Actually, the most robust interpretation for a "forward(input_tensor)"
        in a PyG context where we need graph structure is that `input_tensor`
        might be a `Data` object (which is a Tensor-like container) or the
        method signature in the prompt is a simplification.
        
        To be safe and functional:
        We will define `forward` to accept `x` (node features) and optionally
        `edge_index` and `batch`. If only `x` is provided, we cannot compute
        graph convolutions.
        
        However, looking at the training loop requirements (T022), it will likely
        call `model(data.x, data.edge_index, data.batch)`.
        
        Let's implement `forward` to handle the standard PyG call signature:
        `forward(x, edge_index, batch=None)`.
        If the prompt strictly demands `forward(self, input_tensor)`, I will
        implement it such that `input_tensor` is the `x` and I raise an error
        if `edge_index` is not provided, OR I assume `input_tensor` is a `Data` object.
        
        Let's assume the prompt's `input_tensor` is a placeholder for the
        graph data.
        
        Refined Plan:
        Implement `forward(self, x, edge_index, batch=None)`.
        This is the standard PyG signature.
        If the user calls `model(data.x, data.edge_index, data.batch)`, it works.
        If the user calls `model(data)`, it fails.
        
        Wait, the prompt says: "with `forward(input_tensor)` method".
        I will implement `forward(self, input_tensor)` where `input_tensor`
        is expected to be a `Data` object (which inherits from `dict` and has `x`, `edge_index`).
        This satisfies the signature `forward(input_tensor)` and allows the model
        to work with `Data` objects.
        
        Actually, `Data` is not a `torch.Tensor`. The type hint `torch.Tensor` in the
        prompt might be a simplification.
        
        Let's try to be as flexible as possible.
        If `input_tensor` is a `Data` object, use `input_tensor.x`, `input_tensor.edge_index`.
        If `input_tensor` is a tuple `(x, edge_index, batch)`, unpack it.
        If `input_tensor` is just `x`, we can't do much.
        
        Let's assume the standard PyG usage where the training loop passes:
        `out = model(data.x, data.edge_index, data.batch)`
        and the method signature is `forward(self, x, edge_index, batch=None)`.
        The prompt's `forward(input_tensor)` might be a slight inaccuracy in the
        task description regarding the exact argument name, but the intent is
        "a forward method that takes the input data".
        
        I will implement `forward(self, x, edge_index, batch=None)` as it is the
        only way to make a GCN work. I will add a check to see if `x` is a `Data` object
        to handle the `forward(input_tensor)` literal interpretation if `input_tensor`
        is a `Data` object.
        
        Let's stick to the standard PyG signature which is robust:
        `forward(self, x, edge_index, batch=None)`
        This allows `model(data.x, data.edge_index, data.batch)`.
        
        Wait, if the task explicitly says `forward(input_tensor)`, I should probably
        name the argument `input_tensor` but handle the unpacking if it's a `Data` object.
        
        Let's do this:
        def forward(self, input_tensor, edge_index=None, batch=None):
            if isinstance(input_tensor, Data):
                x = input_tensor.x
                if edge_index is None: edge_index = input_tensor.edge_index
                if batch is None: batch = input_tensor.batch
            else:
                x = input_tensor
            
            # Proceed with GCN logic
        
        This satisfies `forward(input_tensor)` and handles `Data` objects.
        
        Let's refine the GCN logic:
        1. conv1: x -> hidden
        2. ReLU + Dropout
        3. conv2: hidden -> hidden
        4. ReLU + Dropout
        5. global_mean_pool (if batch provided)
        6. Linear -> output
        
        """
        # Handle potential Data object input or raw tensor
        if isinstance(input_tensor, Data):
            x = input_tensor.x
            if edge_index is None:
                edge_index = input_tensor.edge_index
            if batch is None:
                batch = input_tensor.batch
        else:
            x = input_tensor

        if edge_index is None:
            raise ValueError("GCN requires edge_index for graph convolution. "
                           "Pass edge_index explicitly or provide a Data object.")

        # Layer 1
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)

        # Layer 2
        x = self.conv2(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)

        # Global pooling if batch vector is provided
        if batch is not None:
            x = global_mean_pool(x, batch)

        # Output layer
        x = self.fc(x)
        
        return x

def create_model_from_processed_data(
    in_channels: int,
    hidden_channels: int = 64,
    dropout: float = 0.1
) -> GCNModel:
    """
    Factory function to create a GCNModel instance with specified dimensions.
    
    Args:
        in_channels (int): Number of input node features.
        hidden_channels (int): Hidden layer size.
        dropout (float): Dropout rate.
        
    Returns:
        GCNModel: Initialized model instance.
    """
    logger.info(f"Creating GCN model with input channels: {in_channels}, hidden: {hidden_channels}")
    return GCNModel(
        in_channels=in_channels,
        hidden_channels=hidden_channels,
        out_channels=1,
        dropout=dropout
    )