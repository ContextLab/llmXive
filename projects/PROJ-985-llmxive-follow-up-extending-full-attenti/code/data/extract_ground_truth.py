import os
import gc
import logging
import h5py
import numpy as np
import torch

from typing import List, Dict, Any, NamedTuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock model loading for T012 implementation
# In a real scenario, this would load the frozen Llama model
class RTPurboResult(NamedTuple):
    doc_id: str
    indices: List[int]
    attention_map: np.ndarray

def load_frozen_model(model_name: str = "meta-llama/Llama-3-8B"):
    """
    Loads the frozen Llama-3-8B model.
    Uses torch.no_grad() and requires_grad=False as per spec.
    """
    logger.info(f"Loading frozen model: {model_name}")
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float32, # Full precision
            device_map="cpu" # Keep on CPU for memory safety in this demo
        )
        model.eval()
        for param in model.parameters():
            param.requires_grad = False
        logger.info("Model loaded successfully.")
        return model, tokenizer
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

def compute_rtpurbo_indices(
    attention_map: np.ndarray,
    threshold: float = 0.01
) -> List[int]:
    """
    Computes RTPurbo indices based on attention map.
    """
    # Flatten and sort
    flat = attention_map.flatten()
    # Sort indices by attention weight descending
    sorted_indices = np.argsort(flat)[::-1]
    # Select top K or those above threshold
    # For simplicity, select top 10%
    k = max(1, len(sorted_indices) // 10)
    return sorted_indices[:k].tolist()

def process_document(
    model,
    tokenizer,
    text: str,
    doc_id: str
) -> RTPurboResult:
    """
    Processes a single document to compute attention and RTPurbo indices.
    """
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=1024)
    
    with torch.no_grad():
        outputs = model(**inputs)
        # Extract attention weights (last layer)
        # Shape: (batch, heads, seq_len, seq_len)
        attention = outputs.attentions[-1].squeeze(0).cpu().numpy()
    
    # Aggregate attention (mean over heads)
    attn_mean = np.mean(attention, axis=0)
    
    indices = compute_rtpurbo_indices(attn_mean)
    
    return RTPurboResult(doc_id=doc_id, indices=indices, attention_map=attn_mean)

def save_to_hdf5(results: List[RTPurboResult], output_path: str):
    """
    Saves attention maps and RTPurbo indices to HDF5.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with h5py.File(output_path, 'w') as f:
        for res in results:
            grp = f.create_group(res.doc_id)
            grp.create_dataset("indices", data=np.array(res.indices))
            grp.create_dataset("attention", data=res.attention_map)
    logger.info(f"Saved {len(results)} documents to {output_path}")

def main():
    """
    Main entry point for ground truth extraction.
    """
    logger.info("Starting ground truth extraction...")
    
    # Load model
    model, tokenizer = load_frozen_model()
    
    # Stream dataset (using download.py logic)
    from data.download import stream_ruler_dataset
    
    results = []
    anomaly_log = []
    
    count = 0
    for item in stream_ruler_dataset(sample_size=5): # Sample for demo
        doc_id = item.get('id', f"doc_{count}")
        text = item.get('text', '')
        
        if not text:
            anomaly_log.append({"doc_id": doc_id, "reason": "empty_text"})
            continue
        
        try:
            res = process_document(model, tokenizer, text, doc_id)
            if len(res.indices) == 0:
                anomaly_log.append({"doc_id": doc_id, "reason": "zero_rtpurbo_tokens"})
            else:
                results.append(res)
        except Exception as e:
            logger.error(f"Error processing {doc_id}: {e}")
            anomaly_log.append({"doc_id": doc_id, "reason": str(e)})
        
        count += 1
        gc.collect()
    
    # Save results
    save_to_hdf5(results, "data/intermediate/attention_maps.h5")
    
    # Save anomalies
    import pandas as pd
    if anomaly_log:
        pd.DataFrame(anomaly_log).to_csv("data/logs/anomalies.csv", index=False)
        logger.info(f"Logged {len(anomaly_log)} anomalies.")
    else:
        # Create empty file if none
        pd.DataFrame(columns=["doc_id", "reason"]).to_csv("data/logs/anomalies.csv", index=False)

if __name__ == "__main__":
    main()
