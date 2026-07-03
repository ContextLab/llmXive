import os
import hashlib
import tempfile
import zipfile
from typing import Tuple, Optional

import torch
from torch.utils.data import DataLoader, TensorDataset
from datasets import load_dataset

def compute_sha256(filepath: str) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_wikitext_fallback() -> str:
    """
    Fallback download from S3 if HuggingFace fails.
    Returns path to extracted directory or file.
    """
    url = "https://s3.amazonaws.com/research.metamind.io/wikitext/wikitext-2-v1.zip"
    print("Attempting fallback download from S3...")
    
    # Create a temporary directory for download
    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_path = os.path.join(tmp_dir, "wikitext.zip")
        
        try:
            import urllib.request
            urllib.request.urlretrieve(url, zip_path)
            
            # Verify checksum (placeholder logic, real checksum would be known)
            # In a real scenario, we'd compare against a known checksum
            checksum = compute_sha256(zip_path)
            print(f"Downloaded file checksum: {checksum}")
            
            # Extract
            extract_dir = os.path.join(tmp_dir, "extracted")
            os.makedirs(extract_dir, exist_ok=True)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Move extracted content to a persistent location if needed
            # For now, return the path to the extracted folder
            # Note: In a real pipeline, we'd move this to data/raw/
            return extract_dir
        except Exception as e:
            raise RuntimeError(f"Fallback download failed: {e}")

def load_wikitext_dataset() -> Tuple[dict, str]:
    """
    Load WikiText-2 dataset.
    Primary: HuggingFace datasets
    Fallback: S3 download
    
    Returns:
        Tuple of (dataset_dict, data_source_checksum)
    """
    try:
        print("Loading WikiText-2 from HuggingFace datasets...")
        dataset = load_dataset('wikitext', 'wikitext-2-raw-v1')
        
        # Compute a checksum based on the dataset content (simplified)
        # In reality, we might hash the raw text files if downloaded
        # Here we use a placeholder for the checksum logic
        checksum = "hf_wikitext_2_raw_v1_v1" 
        
        return dataset, checksum
    except Exception as e:
        print(f"HuggingFace load failed: {e}. Attempting fallback...")
        extract_dir = download_wikitext_fallback()
        
        # Parse text files manually
        # Expected structure: wikitext-2-raw-v1/ has train.txt, validation.txt, test.txt
        data = {'train': [], 'validation': [], 'test': []}
        
        for split in ['train', 'validation', 'test']:
            file_path = os.path.join(extract_dir, f'wikitext-2-raw-v1/{split}.txt')
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    data[split] = [line.strip() for line in lines if line.strip()]
            else:
                raise FileNotFoundError(f"Expected file {file_path} not found in fallback extraction.")
        
        checksum = compute_sha256(os.path.join(extract_dir, 'wikitext-2-raw-v1/train.txt'))
        return data, checksum

def tokenize_text(texts: list, vocab_size: int = 10000, max_length: int = 128) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Simple tokenization for demonstration.
    In a real scenario, use a proper tokenizer (e.g., from transformers).
    """
    # Build vocabulary
    word_counts = {}
    for text in texts:
        words = text.split()
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
    
    # Sort by frequency and take top vocab_size
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    word_to_idx = {word: idx+1 for idx, (word, _) in enumerate(sorted_words[:vocab_size-1])}
    word_to_idx['<PAD>'] = 0
    word_to_idx['<UNK>'] = len(word_to_idx)
    
    # Convert texts to tensors
    all_tokens = []
    for text in texts:
        words = text.split()
        tokens = [word_to_idx.get(w, word_to_idx['<UNK>']) for w in words]
        # Pad or truncate
        if len(tokens) < max_length:
            tokens = tokens + [0] * (max_length - len(tokens))
        else:
            tokens = tokens[:max_length]
        all_tokens.append(tokens)
    
    # Create input and label tensors (shifted by 1 for next token prediction)
    inputs = torch.tensor(all_tokens)
    labels = torch.roll(inputs, -1, dims=1)
    labels[:, -1] = 0 # Last token has no label, pad it
    
    return inputs, labels

def get_wikitext_dataloader(batch_size: int = 32, seed: int = 42) -> Tuple[DataLoader, DataLoader]:
    """
    Create train and validation dataloaders for WikiText-2.
    
    Args:
        batch_size: Batch size
        seed: Random seed for shuffling
        
    Returns:
        Tuple of (train_loader, val_loader)
    """
    dataset_dict, _ = load_wikitext_dataset()
    
    # Get text data
    train_texts = dataset_dict['train'] if isinstance(dataset_dict, dict) else dataset_dict['train']['text']
    val_texts = dataset_dict['validation'] if isinstance(dataset_dict, dict) else dataset_dict['validation']['text']
    
    # Tokenize
    train_inputs, train_labels = tokenize_text(train_texts)
    val_inputs, val_labels = tokenize_text(val_texts)
    
    # Create datasets
    train_dataset = TensorDataset(train_inputs, train_labels)
    val_dataset = TensorDataset(val_inputs, val_labels)
    
    # Create dataloaders
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    
    return train_loader, val_loader
