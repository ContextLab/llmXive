"""
Ground Truth Extraction Module for llmXive.

This module implements the frozen Llama-3-8B attention map generator and RTPurbo indexer.
It processes the RULER dataset to extract attention patterns and identify RTPurbo tokens.
"""

import os
import gc
import logging
import h5py
import numpy as np
import torch
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

# Local imports from project structure
from lib.logging_config import get_logger, log_stage_start, log_stage_end, log_anomaly
from data.download import stream_ruler_dataset

# Configure logger
logger = get_logger(__name__)

@dataclass
class RTPurboResult:
    """Container for RTPurbo selection results."""
    token_indices: List[int]
    attention_scores: List[float]
    document_id: str
    is_anomaly: bool = False
    anomaly_reason: Optional[str] = None

def load_frozen_model(model_name: str = "meta-llama/Meta-Llama-3-8B") -> torch.nn.Module:
    """
    Load a frozen Llama-3-8B model for inference.

    Requirements:
    - Sets requires_grad=False for all parameters
    - Wraps in torch.no_grad() context during usage
    - Uses CPU-only quantization (int8) if available to fit RAM constraints
    - Verifies model is frozen before returning

    Args:
        model_name: HuggingFace model identifier

    Returns:
        Frozen transformer model ready for inference
    """
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from transformers import set_seed
    except ImportError:
        logger.error("transformers library not found. Please install: pip install transformers")
        raise

    logger.info(f"Loading model: {model_name}")

    # Set seed for reproducibility
    set_seed(42)

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True,
        use_fast=True
    )

    # Configure model loading for memory efficiency
    # Use 8-bit quantization if bitsandbytes is available, otherwise use standard float16 on CPU
    # Note: For strict CPU-only environments without GPU, we use float32 but with careful memory management
    # and strict sampling limits.

    device = torch.device("cpu")
    torch_dtype = torch.float32  # Default for CPU

    try:
        # Try 8-bit quantization if bitsandbytes is installed
        import bitsandbytes as bnb
        logger.info("Using 8-bit quantization for memory efficiency")
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            trust_remote_code=True,
            load_in_8bit=True,
            device_map="cpu",
            torch_dtype=torch.float32
        )
    except ImportError:
        logger.warning("bitsandbytes not found. Using standard float32 model. "
                     "Ensure strict sampling limits are enforced to fit RAM.")
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            trust_remote_code=True,
            torch_dtype=torch_dtype,
            low_cpu_mem_usage=True,
            use_cache=False  # Disable KV cache to save memory
        )
        model = model.to(device)

    # CRITICAL: Freeze all parameters
    logger.info("Freezing model parameters...")
    for param in model.parameters():
        param.requires_grad = False

    # Verify model is frozen
    has_grad = any(p.requires_grad for p in model.parameters())
    if has_grad:
        logger.error("Model verification failed: some parameters still require gradients.")
        raise RuntimeError("Model is not properly frozen.")
    else:
        logger.info("Model successfully frozen: requires_grad is False for all parameters.")

    # Set model to evaluation mode
    model.eval()

    return model, tokenizer

def compute_rtpurbo_indices(
    attention_map: np.ndarray,
    token_ids: np.ndarray,
    threshold: float = 0.01
) -> Tuple[List[int], List[float]]:
    """
    Compute RTPurbo-selected token indices based on attention map.

    RTPurbo (Random Token Purging based on attention) selects tokens that
    have high attention scores relative to the query.

    Args:
        attention_map: Shape (num_layers, num_heads, seq_len, seq_len)
        token_ids: Shape (seq_len,)
        threshold: Attention score threshold for selection

    Returns:
        Tuple of (selected_indices, attention_scores)
    """
    # Use the last layer, average over heads
    # Shape: (seq_len, seq_len)
    last_layer_attention = attention_map[-1, :, :, :]
    avg_attention = np.mean(last_layer_attention, axis=0)

    # For each token, compute its average attention from all other tokens
    # This captures how "important" a token is in the context
    importance_scores = np.mean(avg_attention, axis=0)

    # Select tokens above threshold
    selected_indices = []
    selected_scores = []

    for idx, score in enumerate(importance_scores):
        if score > threshold:
            selected_indices.append(int(idx))
            selected_scores.append(float(score))

    return selected_indices, selected_scores

def process_document(
    model: torch.nn.Module,
    tokenizer: Any,
    document: Dict[str, Any],
    max_length: int = 2048,
    attention_threshold: float = 0.01
) -> RTPurboResult:
    """
    Process a single document to extract attention maps and RTPurbo indices.

    Args:
        model: Frozen Llama-3-8B model
        tokenizer: Associated tokenizer
        document: Dictionary containing 'id' and 'text'
        max_length: Maximum sequence length to process
        attention_threshold: Threshold for RTPurbo selection

    Returns:
        RTPurboResult containing indices and scores
    """
    doc_id = document.get("id", "unknown")
    text = document.get("text", "")

    if not text or len(text.strip()) == 0:
        logger.warning(f"Document {doc_id} is empty. Skipping.")
        return RTPurboResult(
            token_indices=[],
            attention_scores=[],
            document_id=doc_id,
            is_anomaly=True,
            anomaly_reason="Empty document"
        )

    # Tokenize
    try:
        inputs = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=max_length,
            padding=False
        )
    except Exception as e:
        logger.error(f"Tokenization failed for {doc_id}: {e}")
        return RTPurboResult(
            token_indices=[],
            attention_scores=[],
            document_id=doc_id,
            is_anomaly=True,
            anomaly_reason=f"Tokenization error: {str(e)}"
        )

    input_ids = inputs["input_ids"]
    seq_len = input_ids.shape[1]

    # Check for zero tokens (edge case)
    if seq_len == 0:
        logger.warning(f"Document {doc_id} resulted in zero tokens.")
        return RTPurboResult(
            token_indices=[],
            attention_scores=[],
            document_id=doc_id,
            is_anomaly=True,
            anomaly_reason="Zero tokens after tokenization"
        )

    # Run inference with torch.no_grad()
    logger.debug(f"Processing document {doc_id} (length: {seq_len})")

    with torch.no_grad():
        try:
            outputs = model(
                input_ids=input_ids,
                output_attentions=True,
                return_dict=True
            )
        except Exception as e:
            logger.error(f"Inference failed for {doc_id}: {e}")
            return RTPurboResult(
                token_indices=[],
                attention_scores=[],
                document_id=doc_id,
                is_anomaly=True,
                anomaly_reason=f"Inference error: {str(e)}"
            )

    # Extract attention maps
    # attention_states: List of (num_layers, num_heads, seq_len, seq_len)
    attention_states = outputs.attentions

    # Convert to numpy for storage
    # Shape: (num_layers, num_heads, seq_len, seq_len)
    attention_array = np.stack([attn.numpy() for attn in attention_states], axis=0)

    # Compute RTPurbo indices
    selected_indices, selected_scores = compute_rtpurbo_indices(
        attention_array,
        input_ids.numpy()[0],
        threshold=attention_threshold
    )

    # Check for anomaly: zero RTPurbo tokens
    if len(selected_indices) == 0:
        logger.warning(f"Document {doc_id} has zero RTPurbo tokens. Flagging as anomaly.")
        return RTPurboResult(
            token_indices=[],
            attention_scores=[],
            document_id=doc_id,
            is_anomaly=True,
            anomaly_reason="Zero RTPurbo tokens selected"
        )

    # Store attention array for saving
    # We'll return it separately or handle in save_to_hdf5
    # For now, return the result and handle storage separately

    return RTPurboResult(
        token_indices=selected_indices,
        attention_scores=selected_scores,
        document_id=doc_id,
        is_anomaly=False
    ), attention_array

def save_to_hdf5(
    results: List[Tuple[RTPurboResult, np.ndarray]],
    output_path: str,
    anomalies: List[Dict[str, Any]]
) -> None:
    """
    Save attention maps and RTPurbo results to HDF5 format.

    Args:
        results: List of (RTPurboResult, attention_array) tuples
        output_path: Path to output HDF5 file
        anomalies: List of anomaly records to log
    """
    logger.info(f"Saving {len(results)} results to {output_path}")

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with h5py.File(output_path, 'w') as hf:
        # Create datasets for metadata and attention maps
        meta_group = hf.create_group("metadata")
        attention_group = hf.create_group("attention_maps")

        anomaly_list = []

        for idx, (result, attn_array) in enumerate(results):
            # Save metadata
            meta = meta_group.create_group(f"doc_{idx}")
            meta.create_dataset("doc_id", data=result.document_id)
            meta.create_dataset("is_anomaly", data=result.is_anomaly)
            if result.anomaly_reason:
                meta.create_dataset("anomaly_reason", data=result.anomaly_reason)
            meta.create_dataset("num_selected_tokens", data=len(result.token_indices))

            # Save token indices
            if result.token_indices:
                meta.create_dataset("selected_indices", data=np.array(result.token_indices))
                meta.create_dataset("attention_scores", data=np.array(result.attention_scores))

            # Save attention map (if not anomaly)
            if not result.is_anomaly and attn_array is not None:
                attn_group.create_dataset(
                    f"doc_{idx}",
                    data=attn_array,
                    compression="gzip",
                    compression_opts=4
                )

            # Track anomalies
            if result.is_anomaly:
                anomaly_list.append({
                    "document_id": result.document_id,
                    "reason": result.anomaly_reason or "Unknown"
                })

        # Save anomalies to a separate dataset within the file for reference
        if anomaly_list:
            anomaly_ds = hf.create_dataset("anomalies", data=[
                f"{a['document_id']}:{a['reason']}" for a in anomaly_list
            ])
            logger.info(f"Logged {len(anomaly_list)} anomalies in HDF5 file")

    # Also write anomalies to CSV log file
    if anomalies:
        anomalies_path = "data/logs/anomalies.csv"
        os.makedirs(os.path.dirname(anomalies_path), exist_ok=True)
        with open(anomalies_path, 'w', newline='') as f:
            import csv
            writer = csv.DictWriter(f, fieldnames=["document_id", "reason"])
            writer.writeheader()
            writer.writerows(anomalies)
        logger.info(f"Anomalies written to {anomalies_path}")

def main():
    """
    Main entry point for ground truth extraction.

    This function:
    1. Loads the frozen Llama-3-8B model
    2. Streams the RULER dataset
    3. Processes each document to extract attention maps and RTPurbo indices
    4. Saves results to data/intermediate/attention_maps.h5
    5. Logs anomalies to data/logs/anomalies.csv
    """
    log_stage_start("extract_ground_truth")

    output_path = "data/intermediate/attention_maps.h5"
    anomalies = []

    try:
        # Load frozen model
        model, tokenizer = load_frozen_model()

        # Verify model is frozen
        assert not any(p.requires_grad for p in model.parameters()), \
            "Model verification failed: requires_grad is not False"

        logger.info("Model loaded and verified frozen.")

        # Stream dataset
        logger.info("Starting dataset streaming...")
        doc_count = 0
        results = []

        # Use a small sample for demonstration if full dataset is too large
        # In production, this would process the full stream
        stream = stream_ruler_dataset()

        for doc in stream:
            try:
                # Process document
                result, attn_array = process_document(
                    model,
                    tokenizer,
                    doc,
                    max_length=1024,  # Limit sequence length for memory
                    attention_threshold=0.01
                )

                if result.is_anomaly:
                    anomalies.append({
                        "document_id": result.document_id,
                        "reason": result.anomaly_reason
                    })
                    log_anomaly(f"Document {result.document_id}: {result.anomaly_reason}")
                else:
                    results.append((result, attn_array))

                doc_count += 1

                # Log progress every 10 documents
                if doc_count % 10 == 0:
                    logger.info(f"Processed {doc_count} documents. "
                              f"Valid: {len(results)}, Anomalies: {len(anomalies)}")

                # Periodic garbage collection to manage memory
                if doc_count % 50 == 0:
                    gc.collect()

            except Exception as e:
                logger.error(f"Error processing document {doc.get('id', 'unknown')}: {e}")
                anomalies.append({
                    "document_id": doc.get('id', 'unknown'),
                    "reason": f"Processing error: {str(e)}"
                })
                continue

        logger.info(f"Processing complete. Total: {doc_count}, Valid: {len(results)}, Anomalies: {len(anomalies)}")

        # Save results
        if results:
            save_to_hdf5(results, output_path, anomalies)
            logger.info(f"Successfully saved attention maps to {output_path}")
        else:
            logger.warning("No valid results to save.")

    except Exception as e:
        logger.error(f"Fatal error in extract_ground_truth: {e}")
        raise
    finally:
        log_stage_end("extract_ground_truth")

if __name__ == "__main__":
    main()