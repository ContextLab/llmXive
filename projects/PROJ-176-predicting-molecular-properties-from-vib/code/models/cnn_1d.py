import torch
import torch.nn as nn

class ConvBlock(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size):
        super().__init__()
        self.conv = nn.Conv1d(in_channels, out_channels, kernel_size, padding='same')
        self.relu = nn.ReLU()
        self.pool = nn.MaxPool1d(2)

    def forward(self, x):
        x = self.conv(x)
        x = self.relu(x)
        x = self.pool(x)
        return x

class MolecularPropertyCNN(nn.Module):
    def __init__(self, input_dim=3601, num_filters=64):
        super().__init__()
        # 3 convolutional blocks as per spec
        self.block1 = ConvBlock(1, num_filters, kernel_size=9)
        self.block2 = ConvBlock(num_filters, num_filters, kernel_size=9)
        self.block3 = ConvBlock(num_filters, num_filters, kernel_size=9)
        
        # Adaptive pooling to handle variable input sizes after pooling
        self.pool = nn.AdaptiveAvgPool1d(1)
        
        # Regression heads
        self.head_mu = nn.Sequential(nn.Linear(num_filters, 1))
        self.head_alpha = nn.Sequential(nn.Linear(num_filters, 1))
        self.head_gap = nn.Sequential(nn.Linear(num_filters, 1))

    def forward(self, x):
        # x shape: (batch, 1, seq_len)
        x = self.block1(x)
        x = self.block2(x)
        x = self.block3(x)
        x = self.pool(x)
        x = x.squeeze(-1)
        
        return {
            "mu": self.head_mu(x),
            "alpha": self.head_alpha(x),
            "gap": self.head_gap(x)
        }

if __name__ == "__main__":
    model = MolecularPropertyCNN()
    dummy = torch.randn(2, 1, 3601)
    out = model(dummy)
    print("Model forward pass successful")
