"""
code/features.py
Implements linguistic and syntactic feature extraction for captions.
"""
import math
import logging
import time
import os
import sys
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

import pandas as pd
import numpy as np
import spacy
from transformers import AutoTokenizer, AutoModel
import torch

# Project root and config imports
from config import get_project_root, get_paths, BERT_TIMEOUT_SECONDS
from utils.logging import get_logger
from utils.errors import DataSchemaError, ModelInferenceError

# Constants
BERT_MODEL_NAME = "bert-base-uncased"
SPACY_MODEL_NAME = "en_core_web_sm"

# Global caches for expensive resources
_SPACY_MODEL = None
_BERT_TOKENIZER = None
_BERT_MODEL = None

logger = get_logger(__name__)

def get_spacy_model():
    """Load or retrieve the cached spaCy model."""
    global _SPACY_MODEL
    if _SPACY_MODEL is None:
        logger.info(f"Loading spaCy model: {SPACY_MODEL_NAME}")
        try:
            _SPACY_MODEL = spacy.load(SPACY_MODEL_NAME)
        except OSError:
            logger.error(f"spaCy model '{SPACY_MODEL_NAME}' not found. Run: python -m spacy download {SPACY_MODEL_NAME}")
            raise
    return _SPACY_MODEL

def get_bert_resources():
    """Load or retrieve cached BERT tokenizer and model."""
    global _BERT_TOKENIZER, _BERT_MODEL
    if _BERT_TOKENIZER is None:
        logger.info(f"Loading BERT model: {BERT_MODEL_NAME}")
        _BERT_TOKENIZER = AutoTokenizer.from_pretrained(BERT_MODEL_NAME)
        _BERT_MODEL = AutoModel.from_pretrained(BERT_MODEL_NAME)
        _BERT_MODEL.eval()
        # Force CPU-only as per Constitution
        _BERT_MODEL.to("cpu")
    return _BERT_TOKENIZER, _BERT_MODEL

def compute_linguistic_uncertainty_proxy(caption: str) -> float:
    """
    Compute linguistic uncertainty proxy using BERT perplexity.
    Returns ln(perplexity).
    """
    tokenizer, model = get_bert_resources()

    start_time = time.time()
    try:
        inputs = tokenizer(caption, return_tensors="pt", truncation=True, padding=True)
        inputs = {k: v.to("cpu") for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits

        # Calculate perplexity
        # Shift logits and labels for next token prediction
        shift_logits = logits[..., :-1, :].contiguous()
        shift_labels = inputs["input_ids"][..., 1:].contiguous()

        # Flatten for loss calculation
        loss_fct = torch.nn.CrossEntropyLoss(reduction="none")
        per_token_loss = loss_fct(shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1))

        # Reshape back to sequence length
        sequence_length = shift_labels.size(1)
        per_token_loss = per_token_loss.view(shift_labels.size(0), sequence_length)

        # Average loss over the sequence (excluding padding if any, but simplified here)
        # Mask out padding tokens (input_ids == pad_token_id)
        attention_mask = inputs["attention_mask"]
        mask = attention_mask[..., 1:].bool() # Shifted mask
        masked_loss = per_token_loss * mask.float()
        num_tokens = mask.float().sum(dim=1)

        # Avoid division by zero
        num_tokens = torch.clamp(num_tokens, min=1)
        avg_loss = masked_loss.sum(dim=1) / num_tokens

        perplexity = torch.exp(avg_loss).item()
        ln_perplexity = math.log(perplexity)

        elapsed = time.time() - start_time
        if elapsed > BERT_TIMEOUT_SECONDS:
            raise TimeoutError(f"BERT inference exceeded {BERT_TIMEOUT_SECONDS}s limit")

        return ln_perplexity

    except TimeoutError:
        raise
    except Exception as e:
        raise ModelInferenceError(f"BERT inference failed: {str(e)}") from e

def compute_syntactic_depth(caption: str) -> int:
    """
    Compute syntactic depth using spaCy dependency tree depth.
    """
    doc = get_spacy_model()(caption)

    if len(doc) == 0:
        return 0

    # Find the root of the dependency tree
    roots = [token for token in doc if token.dep_ == "ROOT"]
    if not roots:
        return 0

    root = roots[0]

    # Calculate max depth from root
    def get_depth(token):
        if not list(token.children):
            return 0
        return 1 + max(get_depth(child) for child in token.children)

    depth = get_depth(root)
    return depth

def compute_noun_phrase_density(caption: str) -> float:
    """
    Compute noun phrase density (number of NPs / number of tokens).
    """
    doc = get_spacy_model()(caption)

    if len(doc) == 0:
        return 0.0

    noun_phrases = list(doc.noun_chunks)
    num_nps = len(noun_phrases)
    num_tokens = len(doc)

    if num_tokens == 0:
        return 0.0

    return num_nps / num_tokens

def compute_token_diversity(caption: str) -> float:
    """
    Compute token diversity (type-token ratio).
    """
    doc = get_spacy_model()(caption)

    if len(doc) == 0:
        return 0.0

    tokens = [token.lemma_.lower() for token in doc if not token.is_space and not token.is_punct]
    if not tokens:
        return 0.0

    unique_tokens = set(tokens)
    return len(unique_tokens) / len(tokens)

def extract_features_batch(captions: List[str]) -> pd.DataFrame:
    """
    Extract all features for a batch of captions.
    Handles edge cases: short captions, BERT failures, timeouts.
    Logs exclusions to data/logs/exclusions.log.
    Returns a DataFrame with valid records.
    """
    paths = get_paths()
    log_dir = paths.logs if hasattr(paths, 'logs') else Path(get_project_root()) / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    exclusion_log_path = log_dir / "exclusions.log"

    logger.info(f"Starting batch feature extraction for {len(captions)} captions.")

    valid_records = []
    exclusion_reasons = defaultdict(int)

    for i, caption in enumerate(captions):
        caption_id = f"cap_{i:06d}"
        row = {"caption_id": caption_id, "caption": caption}

        # 1. Check for short/empty captions (FR-011)
        if not caption or len(caption.split()) < 2:
            exclusion_reasons["TOO_SHORT"] += 1
            with open(exclusion_log_path, "a") as f:
                f.write(f"{caption_id}|TOO_SHORT|{caption[:50]}...\n")
            continue

        # 2. Compute Linguistic Uncertainty (FR-001)
        try:
            row["linguistic_uncertainty_proxy"] = compute_linguistic_uncertainty_proxy(caption)
        except TimeoutError:
            exclusion_reasons["TIMEOUT_EXCEEDED"] += 1
            with open(exclusion_log_path, "a") as f:
                f.write(f"{caption_id}|TIMEOUT_EXCEEDED|{caption[:50]}...\n")
            continue
        except ModelInferenceError:
            exclusion_reasons["BERT_FAILURE"] += 1
            with open(exclusion_log_path, "a") as f:
                f.write(f"{caption_id}|BERT_FAILURE|{caption[:50]}...\n")
            continue
        except Exception as e:
            # Catch-all for unexpected errors
            exclusion_reasons["UNEXPECTED_ERROR"] += 1
            logger.warning(f"Unexpected error for {caption_id}: {e}")
            with open(exclusion_log_path, "a") as f:
                f.write(f"{caption_id}|UNEXPECTED_ERROR|{caption[:50]}...\n")
            continue

        # 3. Compute Syntactic Depth (FR-002)
        try:
            depth = compute_syntactic_depth(caption)
            if depth == 0 and len(caption.split()) > 2:
                # If it's long but depth is 0, something weird happened, but we'll keep it.
                # If it was short, we already excluded it.
                pass
            row["syntactic_depth"] = depth
        except Exception as e:
            exclusion_reasons["SYNTAX_FAILURE"] += 1
            with open(exclusion_log_path, "a") as f:
                f.write(f"{caption_id}|SYNTAX_FAILURE|{caption[:50]}...\n")
            continue

        # 4. Compute Noun Phrase Density (FR-007)
        try:
            row["noun_phrase_density"] = compute_noun_phrase_density(caption)
        except Exception as e:
            exclusion_reasons["NP_DENSITY_FAILURE"] += 1
            with open(exclusion_log_path, "a") as f:
                f.write(f"{caption_id}|NP_DENSITY_FAILURE|{caption[:50]}...\n")
            continue

        # 5. Compute Token Diversity
        try:
            row["token_diversity"] = compute_token_diversity(caption)
        except Exception as e:
            exclusion_reasons["DIVERSITY_FAILURE"] += 1
            with open(exclusion_log_path, "a") as f:
                f.write(f"{caption_id}|DIVERSITY_FAILURE|{caption[:50]}...\n")
            continue

        valid_records.append(row)

        if (i + 1) % 1000 == 0:
            logger.info(f"Processed {i + 1}/{len(captions)} captions. Valid: {len(valid_records)}")

    logger.info(f"Batch extraction complete. Valid: {len(valid_records)}, Excluded: {len(captions) - len(valid_records)}")
    logger.info(f"Exclusion breakdown: {dict(exclusion_reasons)}")

    return pd.DataFrame(valid_records)

def main():
    """
    Main entry point for feature extraction script.
    Reads from data/raw/pick-a-pic.parquet (or equivalent) and writes to data/processed/features.csv.
    """
    paths = get_paths()
    input_path = paths.raw / "pick-a-pic.parquet"
    output_path = paths.processed / "features.csv"

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading dataset from {input_path}")

    try:
        df = pd.read_parquet(input_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Input file not found: {input_path}. Run data/download.py first.")
    except Exception as e:
        raise RuntimeError(f"Failed to load dataset: {e}")

    if "caption" not in df.columns:
        raise ValueError(f"Dataset must contain 'caption' column. Found: {df.columns.tolist()}")

    captions = df["caption"].tolist()
    logger.info(f"Extracting features for {len(captions)} captions.")

    features_df = extract_features_batch(captions)

    # Merge with original IDs if available
    if "id" in df.columns:
        # Assuming order is preserved
        features_df["id"] = df.head(len(features_df))["id"].values
        # Reorder columns
        cols = ["id", "caption_id", "caption", "linguistic_uncertainty_proxy", "syntactic_depth", "noun_phrase_density", "token_diversity"]
        features_df = features_df[[c for c in cols if c in features_df.columns]]

    logger.info(f"Saving features to {output_path}")
    features_df.to_csv(output_path, index=False)

    logger.info(f"Feature extraction complete. Output: {output_path}")
    return features_df

if __name__ == "__main__":
    # Setup logging
    from utils.logging import setup_logging
    setup_logging()
    main()
