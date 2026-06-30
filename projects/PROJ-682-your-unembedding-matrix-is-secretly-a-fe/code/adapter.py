import os
import json
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForCausalLM
from datasets import load_dataset
import matplotlib
matplotlib.use('Agg') # Non-interactive backend for CPU
import matplotlib.pyplot as plt

# Ensure data and figures directories exist
os.makedirs("data", exist_ok=True)
os.makedirs("figures", exist_ok=True)

def load_small_model():
    """
    Loads a small decoder-only model suitable for CPU inference.
    Using TinyLlama-1.1B as a proxy for the LLM backbone.
    """
    model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    print(f"Loading model: {model_name} (CPU mode)...")
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id
    
    # Load model in float32 for CPU stability, though bf16/fp16 might work
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float32,
        device_map="cpu",
        low_cpu_mem_usage=True
    )
    model.eval()
    
    return model, tokenizer

def get_unembedding_matrix(model):
    """
    Extracts the unembedding matrix (W_unembedding) from the model.
    In HuggingFace causal LMs, this is usually the lm_head.weight.
    """
    if hasattr(model, "lm_head"):
        return model.lm_head.weight
    elif hasattr(model, "embed_tokens"):
        # Some models tie weights or use embed_tokens as unembedding
        return model.embed_tokens.weight.T
    else:
        raise ValueError("Could not find unembedding matrix in model structure.")

def filter_embeddings(embeddings, unembedding_matrix, tokenizer, k=50):
    """
    Implements the core EmbedFilter logic:
    1. Project embeddings to vocabulary space: E @ W.T
    2. Identify high-frequency dimensions (approximated by magnitude or fixed top-k).
       *Note: The paper suggests filtering dimensions corresponding to frequent tokens.*
       For this CPU demo, we will mask the top-k dimensions with the highest absolute values
       across the batch (simulating "high-frequency" activation) or simply the first k
       if we assume a specific ordering (not strictly true, but a valid proxy for the mechanism).
       
       A better proxy for the "uninformative tokens" without a frequency table is to 
       assume the paper's claim: the unembedding matrix *encodes* these. 
       We will mask the top-k dimensions of the projected logits that are consistently high.
       
       Simplified for this demo: We will mask the top-k dimensions of the projected 
       vector that have the highest mean absolute value across the batch.
    3. Project back: Filtered_Logits @ W
    """
    # embeddings: [batch, hidden_dim]
    # unembedding_matrix: [vocab_size, hidden_dim]
    
    batch_size, hidden_dim = embeddings.shape
    
    # 1. Project to vocab space
    # logits = embeddings @ W.T  => [batch, vocab]
    logits = embeddings @ unembedding_matrix.T
    
    # 2. Identify "noisy" dimensions (high frequency tokens)
    # Approximation: Find the k dimensions in the logit space that have the highest 
    # mean absolute value across the batch. These are likely the "frequent" ones.
    mean_abs = torch.mean(torch.abs(logits), dim=0) # [vocab]
    _, top_k_indices = torch.topk(mean_abs, k)
    
    # Create a mask (1 = keep, 0 = filter)
    mask = torch.ones_like(logits)
    mask[:, top_k_indices] = 0
    
    # Apply mask
    filtered_logits = logits * mask
    
    # 3. Project back to hidden space
    # filtered_embeddings = filtered_logits @ W  => [batch, hidden]
    # W is [vocab, hidden], so filtered_logits (batch, vocab) @ W.T? 
    # Wait: W_unembedding is usually [vocab, hidden]. 
    # Projection back: filtered_logits @ W_unembedding (if W is [vocab, hidden])
    # But standard linear: y = x @ W.T. So if we have logits (batch, vocab), 
    # and we want hidden, we do logits @ W_unembedding.T? 
    # No: x (hidden) -> x @ W.T (vocab). 
    # Reverse: logit (vocab) -> logit @ W (hidden).
    
    filtered_embeddings = filtered_logits @ unembedding_matrix
    
    return filtered_embeddings

def compute_similarity(embeddings_1, embeddings_2):
    """Compute cosine similarity between two sets of embeddings."""
    # Normalize
    norm1 = F.normalize(embeddings_1, p=2, dim=-1)
    norm2 = F.normalize(embeddings_2, p=2, dim=-1)
    return torch.matmul(norm1, norm2.T)

def main():
    print("Starting EmbedFilter CPU Adaptation...")
    
    # 1. Load Model
    model, tokenizer = load_small_model()
    unembedding_matrix = get_unembedding_matrix(model)
    print(f"Unembedding matrix shape: {unembedding_matrix.shape}")
    
    # 2. Load Small Dataset
    # We use a tiny subset of a standard STS task to verify the metric.
    # Using 'sentence-transformers/stsb' or similar small dataset.
    # If mteb is not available, we use a simple HF dataset.
    try:
        # Try to load a small subset of a standard dataset
        dataset = load_dataset("sentence-transformers/stsb", split="validation")
        # Take only the first 50 pairs
        dataset = dataset.select(range(50))
    except Exception as e:
        print(f"Could not load STSB: {e}. Falling back to synthetic-like real text snippets.")
        # Fallback: Small hardcoded list of real text pairs
        from datasets import Dataset
        data = {
            "sentence1": [
                "A man is playing a guitar.",
                "A group of people are dancing.",
                "The dog is running in the park.",
                "A woman is reading a book.",
                "A car is driving on the highway."
            ] * 10,
            "sentence2": [
                "Someone is strumming an instrument.",
                "People are moving to music.",
                "A canine is jogging outside.",
                "A female is looking at pages.",
                "An automobile is traveling on the road."
            ] * 10
        }
        dataset = Dataset.from_dict(data)
    
    print(f"Loaded {len(dataset)} examples.")
    
    sentences_a = dataset["sentence1"]
    sentences_b = dataset["sentence2"]
    
    # 3. Tokenize and Encode
    # We use mean pooling of the last hidden state as the base embedding
    batch_size = 16
    all_embeds_a = []
    all_embeds_b = []
    
    model.eval()
    with torch.no_grad():
        for i in range(0, len(sentences_a), batch_size):
            batch_a = sentences_a[i:i+batch_size]
            batch_b = sentences_b[i:i+batch_size]
            
            # Tokenize
            enc_a = tokenizer(batch_a, padding=True, truncation=True, return_tensors="pt")
            enc_b = tokenizer(batch_b, padding=True, truncation=True, return_tensors="pt")
            
            # Forward pass
            out_a = model(**enc_a)
            out_b = model(**enc_b)
            
            # Mean Pooling (ignoring padding)
            def mean_pooling(model_output, attention_mask):
                token_embeddings = model_output.last_hidden_state
                input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
                return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
            
            emb_a = mean_pooling(out_a, enc_a['attention_mask'])
            emb_b = mean_pooling(out_b, enc_b['attention_mask'])
            
            all_embeds_a.append(emb_a)
            all_embeds_b.append(emb_b)
            
    embeddings_a = torch.cat(all_embeds_a, dim=0)
    embeddings_b = torch.cat(all_embeds_b, dim=0)
    
    # 4. Apply EmbedFilter
    # Filter top 50 dimensions (approximate "frequent tokens")
    k_filter = 50
    filtered_emb_a = filter_embeddings(embeddings_a, unembedding_matrix, tokenizer, k=k_filter)
    filtered_emb_b = filter_embeddings(embeddings_b, unembedding_matrix, tokenizer, k=k_filter)
    
    # 5. Compute Metrics
    # Standard Cosine Similarity
    sim_std = compute_similarity(embeddings_a, embeddings_b)
    mean_sim_std = torch.diag(sim_std).mean().item()
    
    # Filtered Cosine Similarity
    sim_filt = compute_similarity(filtered_emb_a, filtered_emb_b)
    mean_sim_filt = torch.diag(sim_filt).mean().item()
    
    print(f"Standard Mean Similarity: {mean_sim_std:.4f}")
    print(f"Filtered Mean Similarity (k={k_filter}): {mean_sim_filt:.4f}")
    
    # 6. Write Outputs
    results = {
        "task": "STS_Scaled",
        "samples": len(sentences_a),
        "filter_k": k_filter,
        "standard_similarity": mean_sim_std,
        "filtered_similarity": mean_sim_filt,
        "improvement": mean_sim_filt - mean_sim_std
    }
    
    with open("data/similarity_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # 7. Plot
    plt.figure(figsize=(8, 5))
    categories = ["Standard", "Filtered (k=50)"]
    scores = [mean_sim_std, mean_sim_filt]
    colors = ['skyblue', 'salmon']
    
    bars = plt.bar(categories, scores, color=colors, edgecolor='black')
    plt.ylabel("Mean Cosine Similarity")
    plt.title("EmbedFilter Effect on Small Scale (TinyLlama)")
    plt.ylim(0, 1)
    
    # Add value labels
    for bar, score in zip(bars, scores):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
                 f'{score:.3f}', ha='center', va='bottom', fontsize=12)
        
    plt.savefig("figures/similarity_comparison.png", dpi=150, bbox_inches='tight')
    plt.close()
    
    print("Done. Artifacts written to data/ and figures/")

if __name__ == "__main__":
    main()
