# Placeholder for CNN model
import torch
import torch.nn as nn

class StiffnessPredictorCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv = nn.Conv2d(1, 8, 3)
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Linear(8, 1)

    def forward(self, x):
        x = torch.relu(self.conv(x))
        x = self.pool(x)
        x = x.view(x.size(0), -1)
        return self.fc(x)

def create_model():
    return StiffnessPredictorCNN()
