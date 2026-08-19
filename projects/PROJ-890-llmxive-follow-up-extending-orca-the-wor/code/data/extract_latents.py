import os
import sys
import logging
import time
import csv
import json
from pathlib import Path

import torch
from transformers import AutoModel, AutoTokenizer
from datasets import load_dataset

from config import ensure_directories, get_config
from data.models import PhysicalScenario, LatentVector, CounterfactualEdit

class OrcaLatentDataset:
    def __init__(self, tokenizer):
        # Load the dataset (replace with your actual data loading logic)
        try:
            self.dataset = load_dataset("allenai/orca", split="train[:100]")  # Example: using a small subset for demonstration
        except Exception as e:
            logging.error(f"Error loading Orca dataset: {e}")
            raise

        self.tokenizer = tokenizer

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, idx):
        data_item = self.dataset[idx]
        video_id = data_item["id"]  # Assuming 'id' is the video ID
        prompt = data_item["text"]   # Assuming 'text' holds the prompt

        return {"video_id": video_id, "prompt": prompt}


def load_frozen_orca_model():
    """Loads a pre-trained frozen Orca model."""
    try:
      model_name = "microsoft/orca-mini-3b"  # Replace with the actual model name
      tokenizer = AutoTokenizer.from_pretrained(model_name)
      model = AutoModel.from_pretrained(model_name).eval()

      return model, tokenizer
    except Exception as e:
        logging.error(f"Error loading model and tokenizer: {e}")
        raise


def process_batch(batch, model):
    """Processes a batch of data using the Orca model."""
    texts = [item["prompt"] for item in batch]
    encoded_inputs = tokenizer(texts, padding=True, truncation=True, return_tensors="pt")

    with torch.no_grad():
        outputs = model(**encoded_inputs)
        # Extract the latent vectors (e.g., from the last hidden state)
        latents = outputs.last_hidden_state[:, 0, :].cpu().numpy() # shape (batch_size, embedding_dim)

    return latents


def run_extraction_pipeline(dataset, model):
  """Runs the complete extraction pipeline."""
  pass
