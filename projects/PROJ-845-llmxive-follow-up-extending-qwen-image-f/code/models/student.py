import torch
import torch.nn as nn
from torch.nn import CrossEntropyLoss, MSELoss
from transformers import DistilBertConfig, DistilBertModel
from transformers.modeling_outputs import SequenceClassifierOutput
from typing import Dict, Any, Optional
import random

# Add project root to path
import os
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logger import get_logger

logger = get_logger("student")

class DistilBERTStudent(nn.Module):
    """
    A lightweight DistilBERT-based student model for CPU inference.
    Designed to be <100M parameters.
    """
    
    def __init__(self, seed: int = 42, hidden_dim: int = 256, num_classes: int = 10):
        super().__init__()
        random.seed(seed)
        torch.manual_seed(seed)
        
        # Use a smaller config for CPU tractability
        config = DistilBertConfig(
            vocab_size=30522,
            max_position_embeddings=512,
            num_attention_heads=4,  # Reduced from 12
            hidden_size=256,         # Reduced from 768
            num_hidden_layers=4,     # Reduced from 6
            intermediate_size=512,   # Reduced from 3072
            dropout=0.1
        )
        
        self.bert = DistilBertModel(config)
        self.classifier = nn.Linear(config.hidden_size, num_classes)
        self.dropout = nn.Dropout(config.dropout)
        
        # Optimizer setup
        self.optimizer = torch.optim.Adam(self.parameters(), lr=1e-4)
        
        logger.info(f"Initialized DistilBERTStudent with {sum(p.numel() for p in self.parameters()):,} parameters")
    
    def forward(self, input_data: Dict[str, Any]) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            input_data: Dictionary containing 'input_text' and other fields
            
        Returns:
            Logits tensor
        """
        # For this simplified implementation, we'll use a placeholder encoding
        # In a real implementation, we'd tokenize input_text properly
        
        # Create a dummy input tensor based on text length
        text = input_data.get("input_text", "")
        seq_len = min(len(text.split()), 512)
        
        # Create dummy inputs for DistilBERT
        dummy_input_ids = torch.randint(0, 30522, (1, seq_len))
        dummy_attention_mask = torch.ones((1, seq_len), dtype=torch.long)
        
        # Forward through BERT
        outputs = self.bert(
            input_ids=dummy_input_ids,
            attention_mask=dummy_attention_mask
        )
        
        # Get pooled output
        pooled_output = outputs.last_hidden_state[:, 0, :]  # [1, hidden_size]
        
        # Apply classifier
        logits = self.classifier(self.dropout(pooled_output))
        
        return logits

def create_student_model(seed: int = 42) -> DistilBERTStudent:
    """Factory function to create a student model."""
    return DistilBERTStudent(seed=seed)

def main():
    """Test the student model."""
    model = create_student_model(seed=42)
    
    # Test forward pass
    test_input = {
        "input_text": "This is a test problem with some premises and operators.",
        "premises": ["P1", "P2"],
        "operators": ["AND", "IMPLIES"],
        "solution": "S1"
    }
    
    model.eval()
    with torch.no_grad():
        output = model(test_input)
        print(f"Output shape: {output.shape}")
        print(f"Output: {output}")

if __name__ == "__main__":
    main()
