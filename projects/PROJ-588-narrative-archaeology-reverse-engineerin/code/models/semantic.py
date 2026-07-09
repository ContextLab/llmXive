"""
Semantic feature extraction using BERT (CPU-only).
Features are used for RSA or as covariates, NOT as primary decoder inputs.
"""
import torch
from transformers import BertTokenizer, BertModel
import numpy as np
import logging
import code.config as config

logger = logging.getLogger(__name__)

def get_semantic_features(texts):
    """
    Extract BERT embeddings for a list of text strings.
    Runs in CPU-only mode.
    """
    if not texts:
        return np.array([])

    logger.info("Loading BERT model (CPU)...")
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
    model = BertModel.from_pretrained('bert-base-uncased')
    model.eval()

    if config.CPU_ONLY:
        model = model.cpu()

    features = []
    with torch.no_grad():
        for text in texts:
            inputs = tokenizer(text, return_tensors='pt', truncation=True, padding=True)
            if config.CPU_ONLY:
                inputs = {k: v.cpu() for k, v in inputs.items()}
            
            outputs = model(**inputs)
            # Use last hidden state mean pooling
            last_hidden = outputs.last_hidden_state
            mask = inputs['attention_mask']
            pooled = (last_hidden * mask.unsqueeze(-1)).sum(1) / mask.sum(-1, keepdim=True)
            features.append(pooled.numpy())

    return np.vstack(features)
