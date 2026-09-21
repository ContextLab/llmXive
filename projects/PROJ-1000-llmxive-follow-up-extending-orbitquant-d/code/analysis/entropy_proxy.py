"""
Entropy Proxy Module for Semantic Entropy Calculation.

Computes semantic entropy via generative paraphrase sampling using a lightweight
LLM. The process involves:
1. Generating N paraphrases for a given input prompt.
2. Clustering the paraphrases based on semantic similarity (using Sentence-BERT).
3. Calculating the Shannon entropy of the cluster distribution.

This module relies on real data inputs (prompts from data/processed/prompts.csv)
and does not use synthetic fallbacks.
"""

import torch
import numpy as np
from transformers import AutoTokenizer, AutoModelForCausalLM, AutoModel
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from typing import List, Dict, Tuple, Optional
import logging
import os
from pathlib import Path

# Import Config for paths and hyperparameters
from config import Config

logger = logging.getLogger(__name__)

# Constants
DEFAULT_MODEL_NAME = "microsoft/Phi-3-mini-4k-instruct"  # Lightweight, capable of instruction following
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Fast, effective for semantic similarity
DEFAULT_NUM_PARAPHRASES = 10
DEFAULT_MAX_NEW_TOKENS = 64
DEFAULT_TEMPERATURE = 0.7
DEFAULT_SEED = 42

class EntropyProxy:
    """
    Computes semantic entropy for a given prompt by generating paraphrases,
    clustering them, and calculating the entropy of the resulting cluster distribution.
    """

    def __init__(self, config: Config):
        self.config = config
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Initialize LLM for paraphrase generation
        # Using Phi-3-mini as it is lightweight and instruction-following capable
        logger.info(f"Loading LLM for paraphrase generation on {self.device}...")
        self.llm_tokenizer = AutoTokenizer.from_pretrained(DEFAULT_MODEL_NAME, trust_remote_code=True)
        self.llm_model = AutoModelForCausalLM.from_pretrained(
            DEFAULT_MODEL_NAME, 
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            device_map="auto" if self.device == "cuda" else None,
            trust_remote_code=True
        )
        if self.device == "cpu":
            self.llm_model = self.llm_model.to(self.device)
        
        # Initialize Sentence-BERT for semantic clustering
        logger.info(f"Loading Sentence-BERT model for clustering on {self.device}...")
        self.embedding_model = SentenceTransformer(DEFAULT_EMBEDDING_MODEL, device=self.device)

    def _generate_paraphrases(self, prompt: str, n: int = DEFAULT_NUM_PARAPHRASES) -> List[str]:
        """
        Generates N paraphrases for the given prompt using the LLM.
        Uses do_sample=True for stochastic generation.
        """
        paraphrases = []
        
        # Construct instruction for paraphrasing
        # We ask for a list to make parsing easier, or just raw text if we want variety
        instruction = f"Rewrite the following sentence in {n} different ways, maintaining the original meaning. Return only the rewritten sentences, separated by newlines.\n\nSentence: {prompt}"
        
        # Prepare inputs
        messages = [
            {"role": "system", "content": "You are a helpful assistant that rewrites sentences."},
            {"role": "user", "content": instruction}
        ]
        
        # Tokenize
        input_ids = self.llm_tokenizer.apply_chat_template(
            messages, 
            return_tensors="pt", 
            add_generation_prompt=True
        ).to(self.llm_model.device)
        
        # Generate
        # We generate a large block and try to split, or generate one by one.
        # Generating one block with a high max_new_tokens is more efficient.
        with torch.no_grad():
            outputs = self.llm_model.generate(
                input_ids,
                max_new_tokens=DEFAULT_MAX_NEW_TOKENS * n, # Allow enough space for N sentences
                temperature=DEFAULT_TEMPERATURE,
                do_sample=True,
                top_p=0.95,
                pad_token_id=self.llm_tokenizer.eos_token_id
            )
        
        # Decode and split
        generated_text = self.llm_tokenizer.decode(outputs[0][input_ids.shape[1]:], skip_special_tokens=True)
        
        # Heuristic split: try to split by newlines, take first N non-empty lines
        lines = [line.strip() for line in generated_text.split('\n') if line.strip()]
        
        # If the model didn't follow the format perfectly, we might need to fallback
        # or just take what we have. If we have fewer than N, we pad or repeat?
        # Better to fail loudly if we can't get enough distinct outputs, 
        # but for entropy, having < N samples just reduces resolution.
        # We will take up to N unique lines.
        unique_lines = list(dict.fromkeys(lines)) # Preserve order, remove duplicates
        
        if len(unique_lines) < n:
            logger.warning(f"Requested {n} paraphrases but only generated {len(unique_lines)}. Using available.")
        
        return unique_lines[:n]

    def _cluster_paraphrases(self, paraphrases: List[str], k: int = 2) -> List[int]:
        """
        Clusters paraphrases into k groups based on semantic similarity.
        Returns cluster labels for each paraphrase.
        """
        if len(paraphrases) == 0:
            return []
        
        if len(paraphrases) == 1:
            return [0]

        # Determine optimal K if needed, but spec suggests fixed K or heuristic.
        # For entropy calculation, we need a distribution. 
        # A common approach is to use a fixed K (e.g., 2-5) or use DBSCAN.
        # Here we use KMeans with K=min(len, 5) to avoid over-segmentation on small samples.
        actual_k = min(len(paraphrases), 5)
        
        # Get embeddings
        embeddings = self.embedding_model.encode(paraphrases, convert_to_numpy=True)
        
        # Cluster
        kmeans = KMeans(n_clusters=actual_k, random_state=DEFAULT_SEED, n_init='auto')
        labels = kmeans.fit_predict(embeddings)
        
        return labels.tolist()

    def compute_entropy(self, prompt: str, n_samples: int = DEFAULT_NUM_PARAPHRASES) -> float:
        """
        Computes the semantic entropy for a single prompt.
        
        Process:
        1. Generate n_samples paraphrases.
        2. Cluster them.
        3. Compute Shannon entropy of the cluster label distribution.
        
        Returns:
            float: The semantic entropy value.
        """
        # Step 1: Generate Paraphrases
        try:
            paraphrases = self._generate_paraphrases(prompt, n=n_samples)
        except Exception as e:
            logger.error(f"Failed to generate paraphrases for prompt: {prompt[:50]}... Error: {e}")
            raise RuntimeError(f"LLM generation failed: {e}")
        
        if len(paraphrases) == 0:
            logger.warning(f"No paraphrases generated for prompt: {prompt[:50]}... Returning 0 entropy.")
            return 0.0

        # Step 2: Cluster
        labels = self._cluster_paraphrases(paraphrases)
        
        if len(labels) == 0:
            return 0.0

        # Step 3: Compute Entropy
        # Count frequencies
        counts = np.bincount(labels)
        probs = counts / len(labels)
        
        # Shannon Entropy: -sum(p * log(p))
        # Filter out 0 probabilities to avoid log(0)
        probs = probs[probs > 0]
        entropy = -np.sum(probs * np.log2(probs))
        
        return float(entropy)

    def compute_batch_entropy(self, prompts: List[str], n_samples: int = DEFAULT_NUM_PARAPHRASES) -> Dict[str, float]:
        """
        Computes semantic entropy for a batch of prompts.
        
        Args:
            prompts: List of input prompts.
            n_samples: Number of paraphrases to generate per prompt.
        
        Returns:
            Dict mapping prompt text to its entropy score.
        """
        results = {}
        for i, prompt in enumerate(prompts):
            logger.info(f"Processing prompt {i+1}/{len(prompts)}")
            try:
                entropy = self.compute_entropy(prompt, n_samples=n_samples)
                results[prompt] = entropy
            except Exception as e:
                logger.error(f"Skipping prompt due to error: {prompt[:50]}... Error: {e}")
                # We do not return a placeholder; we skip and log.
                # The caller must handle missing keys if strictness is required.
        return results

def main():
    """
    Main entry point to run the entropy proxy on the processed prompts dataset.
    Reads from data/processed/prompts.csv and writes to data/processed/entropy_scores.json
    """
    config = Config()
    
    # Ensure output directory exists
    output_dir = Path(config.data_path) / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    input_file = output_dir / "prompts.csv"
    output_file = output_dir / "entropy_scores.json"
    
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}. Run T006 first.")
    
    logger.info(f"Loading prompts from {input_file}")
    prompts = []
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if 'prompt' in row:
                prompts.append(row['prompt'])
    
    if not prompts:
        raise ValueError("No prompts found in input file.")
    
    logger.info(f"Loaded {len(prompts)} prompts. Initializing EntropyProxy...")
    proxy = EntropyProxy(config)
    
    logger.info("Computing semantic entropy...")
    # Process in batches or one by one? One by one is safer for memory in this loop
    # but we can batch the generation if the LLM supports it. 
    # For simplicity and robustness with the current implementation, we iterate.
    results = proxy.compute_batch_entropy(prompts, n_samples=10)
    
    # Save results
    logger.info(f"Saving results to {output_file}")
    import json
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info("Entropy computation complete.")

if __name__ == "__main__":
    import csv
    import json
    main()
