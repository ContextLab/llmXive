"""
1D CNN model for predicting molecular properties from vibrational spectra.
Implements three convolutional blocks with kernel sizes 9, 7, and 5,
and three separate regression heads.
"""
import torch
import torch.nn as nn

class ConvBlock(nn.Module):
    """
    Convolutional block with Conv1d, ReLU, and MaxPool1d.
    """
    def __init__(self, in_channels: int, out_channels: int, kernel_size: int):
        """
        Initialize the convolutional block.

        Args:
            in_channels: Number of input channels.
            out_channels: Number of output channels.
            kernel_size: Size of the convolutional kernel.
        """
        super(ConvBlock, self).__init__()

        padding = kernel_size // 2

        self.conv = nn.Conv1d(
            in_channels=in_channels,
            out_channels=out_channels,
            kernel_size=kernel_size,
            padding=padding
        )
        self.relu = nn.ReLU()
        self.pool = nn.MaxPool1d(kernel_size=2, stride=2)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the convolutional block.

        Args:
            x: Input tensor of shape (batch_size, in_channels, sequence_length).

        Returns:
            Output tensor of shape (batch_size, out_channels, sequence_length // 2).
        """
        x = self.conv(x)
        x = self.relu(x)
        x = self.pool(x)
        return x

class MolecularPropertyCNN(nn.Module):
    """
    1D CNN model for predicting molecular properties.

    Architecture:
    - Three convolutional blocks with kernel sizes 9, 7, and 5
    - Three separate regression heads for dipole, polarizability, and HOMO-LUMO gap
    """
    def __init__(
        self,
        input_dim: int = 3601,
        num_targets: int = 3,
        hidden_channels: int = 64
    ):
        """
        Initialize the model.

        Args:
            input_dim: Input dimension (number of wavenumber points).
            num_targets: Number of target properties.
            hidden_channels: Number of filters in each convolutional block.
        """
        super(MolecularPropertyCNN, self).__init__()

        # First convolutional block (kernel size 9)
        self.block1 = ConvBlock(
            in_channels=1,
            out_channels=hidden_channels,
            kernel_size=9
        )

        # Second convolutional block (kernel size 7)
        self.block2 = ConvBlock(
            in_channels=hidden_channels,
            out_channels=hidden_channels,
            kernel_size=7
        )

        # Third convolutional block (kernel size 5)
        self.block3 = ConvBlock(
            in_channels=hidden_channels,
            out_channels=hidden_channels,
            kernel_size=5
        )

        # Calculate the flattened feature size after pooling
        # Input: (batch, 1, input_dim)
        # After block1: (batch, hidden_channels, input_dim // 2)
        # After block2: (batch, hidden_channels, input_dim // 4)
        # After block3: (batch, hidden_channels, input_dim // 8)
        self.flattened_size = hidden_channels * (input_dim // 8)

        # Three separate regression heads
        self.head_dipole = nn.Sequential(
            nn.Linear(self.flattened_size, hidden_channels),
            nn.ReLU(),
            nn.Linear(hidden_channels, 1)
        )

        self.head_polarizability = nn.Sequential(
            nn.Linear(self.flattened_size, hidden_channels),
            nn.ReLU(),
            nn.Linear(hidden_channels, 1)
        )

        self.head_homo_lumo = nn.Sequential(
            nn.Linear(self.flattened_size, hidden_channels),
            nn.ReLU(),
            nn.Linear(hidden_channels, 1)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the model.

        Args:
            x: Input tensor of shape (batch_size, 1, input_dim).

        Returns:
            Output tensor of shape (batch_size, 3) with predictions for
            [dipole, polarizability, homo_lumo_gap].
        """
        # Add channel dimension if not present
        if x.dim() == 2:
            x = x.unsqueeze(1)  # (batch, 1, input_dim)

        # Convolutional blocks
        x = self.block1(x)
        x = self.block2(x)
        x = self.block3(x)

        # Flatten
        x = x.view(x.size(0), -1)

        # Get predictions from each head
        dipole_pred = self.head_dipole(x)
        polarizability_pred = self.head_polarizability(x)
        homo_lumo_pred = self.head_homo_lumo(x)

        # Concatenate predictions
        output = torch.cat([dipole_pred, polarizability_pred, homo_lumo_pred], dim=1)

        return output

def main():
    """
    Main entry point for testing the model architecture.
    """
    print("Testing model architecture...")

    # Create a sample input
    batch_size = 4
    input_dim = 3601  # 4000 - 400 + 1
    x = torch.randn(batch_size, input_dim)

    # Create model
    model = MolecularPropertyCNN(input_dim=input_dim)

    # Forward pass
    output = model(x)

    print(f"Input shape: {x.shape}")
    print(f"Output shape: {output.shape}")
    print(f"Expected output shape: ({batch_size}, 3)")
    print("Model architecture test passed!")

if __name__ == "__main__":
    main()
