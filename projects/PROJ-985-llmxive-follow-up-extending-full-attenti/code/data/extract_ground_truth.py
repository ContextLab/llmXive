import os
import gc
import logging
import h5py
import numpy as np
import torch
import pandas as pd
from typing import Dict, List, Optional, Any, NamedTuple, Set
from dataclasses import dataclass, field
from collections import defaultdict

# Import from local lib to ensure consistent logging and memory handling
from lib.logging_config import setup_logging, get_logger
from lib.data_loader import get_current_memory_mb, stream_ruler_dataset

# Configure logging for this module
logger = get_logger(__name__)

@dataclass
class RTPurboResult:
    """Container for RTPurbo extraction results for a single document."""
    doc_id: str
    total_tokens: int
    selected_indices: List[int]
    attention_scores: Optional[np.ndarray] = None
    is_anomaly: bool = False
    anomaly_reason: Optional[str] = None

def load_frozen_model(model_name: str = "meta-llama/Meta-Llama-3-8B", device: str = "cpu") -> torch.nn.Module:
    """
    Load a frozen Llama-3-8B model for inference.
    Ensures no gradients are computed and model is in eval mode.
    """
    logger.info(f"Loading model {model_name} on {device}...")
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError:
        raise ImportError("transformers library is required. Install with: pip install transformers")

    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float32 if device == "cpu" else torch.float16,
        device_map=device if device != "cpu" else None,
        low_cpu_mem_usage=True,
        trust_remote_code=True
    )

    # Freeze all parameters
    for param in model.parameters():
        param.requires_grad = False

    model.eval()
    
    # Verify freezing
    assert all(not p.requires_grad for p in model.parameters()), "Model parameters are not frozen!"
    
    logger.info(f"Model loaded and frozen. Requires Grad: {any(p.requires_grad for p in model.parameters())}")
    return model, tokenizer

def compute_rtpurbo_indices(
    attention_map: np.ndarray,
    top_k_ratio: float = 0.1
) -> List[int]:
    """
    Compute RTPurbo indices from an attention map.
    Selects the top-k% tokens with the highest attention scores.
    
    Args:
        attention_map: 1D or 2D array of attention scores.
        top_k_ratio: Fraction of tokens to select (0.0 to 1.0).
        
    Returns:
        List of indices corresponding to selected tokens.
    """
    if attention_map.ndim == 2:
        # If 2D (e.g., [heads, seq_len] or [seq_len, heads]), aggregate
        # Usually we care about the sum over heads or mean
        attention_scores = np.mean(attention_map, axis=0)
    else:
        attention_scores = attention_map

    # Normalize to ensure positive scores if necessary, though attention is usually softmaxed
    # Select top-k
    num_tokens = len(attention_scores)
    k = max(1, int(num_tokens * top_k_ratio))
    
    # Get indices of top-k values
    top_indices = np.argsort(attention_scores)[-k:]
    
    return sorted(top_indices.tolist())

def process_document(
    doc_id: str,
    tokens: List[str],
    model: torch.nn.Module,
    tokenizer,
    device: str = "cpu"
) -> RTPurboResult:
    """
    Process a single document to extract RTPurbo indices.
    
    Args:
        doc_id: Unique identifier for the document.
        tokens: List of token strings.
        model: Frozen LLM model.
        tokenizer: Tokenizer for the model.
        device: Device to run inference on.
        
    Returns:
        RTPurboResult object.
    """
    try:
        # Tokenize
        input_ids = tokenizer.encode(" ".join(tokens), return_tensors="pt").to(device)
        
        # Check for empty input
        if input_ids.shape[1] == 0:
            return RTPurboResult(
                doc_id=doc_id,
                total_tokens=0,
                selected_indices=[],
                is_anomaly=True,
                anomaly_reason="Empty token sequence"
            )

        with torch.no_grad():
            # Forward pass with output_attentions=True
            outputs = model(input_ids, output_attentions=True)
            
            # Extract attention maps from the last layer
            # outputs.attentions is a tuple of tensors, one per layer
            # Shape: (num_layers, batch_size, num_heads, seq_len, seq_len)
            last_layer_attentions = outputs.attentions[-1]
            
            # We typically look at the attention from the last token or aggregate
            # For RTPurbo, we usually aggregate attention scores across heads and layers
            # Here we take the mean attention from the last token to all tokens
            # Or aggregate all attention maps to find important tokens globally
            
            # Strategy: Aggregate attention scores from all heads in the last layer
            # Shape: [batch, heads, seq, seq] -> [heads, seq, seq]
            attn_map = last_layer_attentions[0].cpu().numpy()
            
            # Aggregate: Mean over heads, then sum over query positions (or just focus on specific query)
            # A common RTPurbo approach is to look at the attention distribution of the *last* token
            # or the average attention received by each token.
            # Let's compute the average attention *received* by each token (sum over query, mean over heads)
            # attn_map[head, query, key]
            # We want to know which keys are important.
            # Sum over query dimension (axis 1) and mean over heads (axis 0)
            if attn_map.ndim == 3:
                # [heads, seq, seq]
                # Sum over query (axis 1) to get total attention received by each key
                key_attention = np.sum(attn_map, axis=1) 
                # Mean over heads
                key_attention = np.mean(key_attention, axis=0)
            else:
                key_attention = attn_map

            # Compute RTPurbo indices
            selected_indices = compute_rtpurbo_indices(key_attention)
            
            # Check for anomaly: Zero RTPurbo tokens
            # This happens if the selection logic fails or k=0 (though k>=1 enforced)
            # Or if the document is too short and logic fails
            is_anomaly = False
            anomaly_reason = None
            
            if len(selected_indices) == 0:
                is_anomaly = True
                anomaly_reason = "Zero RTPurbo tokens selected"
            
            return RTPurboResult(
                doc_id=doc_id,
                total_tokens=input_ids.shape[1],
                selected_indices=selected_indices,
                attention_scores=key_attention,
                is_anomaly=is_anomaly,
                anomaly_reason=anomaly_reason
            )

    except Exception as e:
        logger.error(f"Error processing document {doc_id}: {e}")
        # Return anomaly result on error to prevent pipeline crash
        return RTPurboResult(
            doc_id=doc_id,
            total_tokens=0,
            selected_indices=[],
            is_anomaly=True,
            anomaly_reason=f"Processing error: {str(e)}"
        )

def save_to_hdf5(
    results: List[RTPurboResult],
    output_path: str,
    anomalies_path: str
):
    """
    Save RTPurbo results to HDF5 and log anomalies to CSV.
    
    Args:
        results: List of RTPurboResult objects.
        output_path: Path to output HDF5 file.
        anomalies_path: Path to output anomalies CSV file.
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    os.makedirs(os.path.dirname(anomalies_path), exist_ok=True)

    anomalies = []
    valid_results = []

    for res in results:
        if res.is_anomaly:
            anomalies.append({
                "doc_id": res.doc_id,
                "total_tokens": res.total_tokens,
                "reason": res.anomaly_reason
            })
        else:
            valid_results.append(res)

    # Log anomalies
    logger.info(f"Found {len(anomalies)} anomalies. Logging to {anomalies_path}")
    if anomalies:
        df_anomalies = pd.DataFrame(anomalies)
        df_anomalies.to_csv(anomalies_path, index=False)
    else:
        # Create empty file with headers if none found
        pd.DataFrame(columns=["doc_id", "total_tokens", "reason"]).to_csv(anomalies_path, index=False)

    # Save valid results to HDF5
    logger.info(f"Saving {len(valid_results)} valid results to {output_path}")
    with h5py.File(output_path, 'w') as f:
        for i, res in enumerate(valid_results):
            grp = f.create_group(f"doc_{i}")
            grp.attrs["doc_id"] = res.doc_id
            grp.attrs["total_tokens"] = res.total_tokens
            
            # Save indices
            grp.create_dataset("selected_indices", data=np.array(res.selected_indices, dtype=np.int32))
            
            # Save attention scores if available
            if res.attention_scores is not None:
                grp.create_dataset("attention_scores", data=res.attention_scores)

    logger.info("HDF5 and anomaly logs saved successfully.")

def main():
    """
    Main entry point for extracting ground truth RTPurbo indices.
    """
    # Setup logging
    setup_logging(log_file="data/logs/extract_ground_truth.log")
    
    # Configuration
    model_name = "meta-llama/Meta-Llama-3-8B"
    device = "cpu"
    top_k_ratio = 0.1
    output_h5 = "data/intermediate/attention_maps.h5"
    anomalies_csv = "data/logs/anomalies.csv"
    
    # Load model
    model, tokenizer = load_frozen_model(model_name, device)
    
    # Stream dataset
    logger.info("Starting dataset streaming...")
    all_results = []
    
    # Assuming RULER dataset structure, adjust 'split' and 'text' field as needed
    # Using streaming=True to handle large datasets
    try:
        dataset = stream_ruler_dataset("ruler", split="train", streaming=True)
    except Exception as e:
        logger.error(f"Failed to load RULER dataset: {e}")
        raise

    doc_count = 0
    for batch in dataset:
        # Batch processing
        # Assuming batch is a dict of lists
        # Adjust field names based on actual dataset schema
        if isinstance(batch, dict):
            # Handle list of documents in a batch
            docs = batch.get("text", [])
            ids = batch.get("id", [f"doc_{i}" for i in range(len(docs))])
            
            for i, text in enumerate(docs):
                if not text or not isinstance(text, str):
                    continue
                
                tokens = text.split() # Simple tokenization for now, or use tokenizer
                doc_id = ids[i] if i < len(ids) else f"doc_{doc_count}"
                
                result = process_document(doc_id, tokens, model, tokenizer, device)
                all_results.append(result)
                
                doc_count += 1
                
                # Log progress
                if doc_count % 10 == 0:
                    logger.info(f"Processed {doc_count} documents. Current anomalies: {sum(1 for r in all_results if r.is_anomaly)}")
                    gc.collect()
        
        # Clear memory periodically
        if doc_count % 50 == 0:
            gc.collect()
            if device == "cpu":
                torch.cuda.empty_cache() if torch.cuda.is_available() else None

    # Save results
    save_to_hdf5(all_results, output_h5, anomalies_csv)
    
    logger.info(f"Extraction complete. Total docs: {doc_count}, Anomalies: {sum(1 for r in all_results if r.is_anomaly)}")

if __name__ == "__main__":
    main()
