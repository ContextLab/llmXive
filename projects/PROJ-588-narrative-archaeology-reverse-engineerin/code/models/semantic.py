"""
Semantic feature extraction using BERT.
"""
import torch
from transformers import BertTokenizer, BertModel
import numpy as np
import logging
import code.config as config

logger = logging.getLogger(__name__)

def get_semantic_features(texts):
    """
    Extract semantic features from a list of text strings.
    
    Args:
        texts (list): List of strings.
    
    Returns:
        np.array: Feature matrix (n_texts, hidden_size).
    """
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
    model = BertModel.from_pretrained('bert-base-uncased')
    model.eval()
    
    # Move to CPU
    model.to(config.DEVICE)
    
    features = []
    with torch.no_grad():
        for text in texts:
            inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
            inputs = {k: v.to(config.DEVICE) for k, v in inputs.items()}
            outputs = model(**inputs)
            # Use last hidden state mean pool
            last_hidden_state = outputs.last_hidden_state
            feature = last_hidden_state.mean(dim=1).squeeze().cpu().numpy()
            features.append(feature)
    
    return np.array(features)
