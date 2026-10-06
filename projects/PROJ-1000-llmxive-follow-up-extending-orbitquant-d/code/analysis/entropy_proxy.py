import torch
import numpy as np
from transformers import AutoTokenizer, AutoModelForCausalLM, AutoModel
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from typing import List, Dict, Tuple, Optional
import argparse
import logging
import json
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EntropyProxy:
    """
    Computes semantic entropy via generative paraphrase sampling.
    
    Supports a "scaled" mode for memory-constrained environments (e.g., Kaggle GPU)
    by limiting the number of paraphrase samples per prompt and the number of prompts
    processed.
    """
    
    def __init__(
        self,
        model_name: str = "facebook/opt-125m",
        device: str = "cuda",
        sample_size: int = 10,
        prompt_count: int = 500,
        use_scaled_mode: bool = False
    ):
        """
        Initialize the EntropyProxy.
        
        Args:
            model_name: HuggingFace model identifier for the lightweight LLM.
            device: Device to run the model on ('cuda' or 'cpu').
            sample_size: Number of paraphrase samples to generate per prompt.
            prompt_count: Maximum number of diverse prompts to process.
            use_scaled_mode: If True, enforces strict limits (sample_size=5, prompt_count=200)
                             regardless of passed arguments, to ensure VRAM < 12GB.
        """
        self.device = device
        self.sample_size = sample_size
        self.prompt_count = prompt_count
        self.use_scaled_mode = use_scaled_mode
        
        # Enforce scaled mode constraints if enabled
        if self.use_scaled_mode:
            self.sample_size = 5
            self.prompt_count = 200
            logger.info(f"Scaled mode enabled: sample_size={self.sample_size}, prompt_count={self.prompt_count}")
        
        logger.info(f"Initializing EntropyProxy with sample_size={self.sample_size}, prompt_count={self.prompt_count}")
        
        # Load tokenizer and model
        logger.info(f"Loading model: {model_name} on {device}")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                device_map=device if device == "cuda" else None
            )
            if device == "cpu":
                self.model = self.model.to(device)
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise RuntimeError(f"Model loading failed: {e}")
        
        # Load sentence transformer for clustering paraphrases
        logger.info("Loading sentence transformer for clustering...")
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        logger.info("EntropyProxy initialized successfully.")

    def generate_paraphrases(self, prompt: str) -> List[str]:
        """
        Generate multiple paraphrases for a given prompt.
        
        Args:
            prompt: The input text prompt.
            
        Returns:
            A list of generated paraphrase strings.
        """
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        paraphrases = []
        
        # Generate multiple samples
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=50,
                num_return_sequences=self.sample_size,
                do_sample=True,
                temperature=0.8,
                top_p=0.95,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        for i in range(self.sample_size):
            # Handle case where generation might be shorter than requested samples
            if i < outputs.shape[0]:
                generated_ids = outputs[i, inputs['input_ids'].shape[1]:]
                text = self.tokenizer.decode(generated_ids, skip_special_tokens=True)
                paraphrases.append(text.strip())
            else:
                # Fallback if model didn't generate enough sequences
                paraphrases.append(prompt)
                
        return paraphrases

    def compute_entropy(self, prompt: str) -> float:
        """
        Compute semantic entropy for a single prompt.
        
        1. Generate N paraphrases.
        2. Embed them using sentence transformer.
        3. Cluster into K groups.
        4. Compute entropy of cluster distribution.
        
        Args:
            prompt: Input prompt string.
            
        Returns:
            Semantic entropy score (float).
        """
        # Generate paraphrases
        paraphrases = self.generate_paraphrases(prompt)
        
        if not paraphrases:
            logger.warning(f"No paraphrases generated for prompt: {prompt[:50]}...")
            return 0.0
        
        # Embed paraphrases
        embeddings = self.sentence_model.encode(paraphrases, convert_to_numpy=True)
        
        # Cluster embeddings
        # Use min(sample_size, number_of_paraphrases) clusters, but cap at sample_size
        n_clusters = min(len(paraphrases), self.sample_size)
        if n_clusters < 2:
            return 0.0
            
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(embeddings)
        
        # Compute cluster distribution
        unique, counts = np.unique(labels, return_counts=True)
        probabilities = counts / len(labels)
        
        # Compute entropy
        entropy = -np.sum(probabilities * np.log2(probabilities + 1e-10))
        
        return float(entropy)

    def compute_entropy_batch(self, prompts: List[str]) -> Dict[str, float]:
        """
        Compute entropy for a batch of prompts.
        
        Args:
            prompts: List of prompt strings.
            
        Returns:
            Dictionary mapping prompt index to entropy score.
        """
        # Limit number of prompts if in scaled mode or explicit limit
        effective_prompts = prompts[:self.prompt_count]
        logger.info(f"Processing {len(effective_prompts)} prompts (limit: {self.prompt_count})")
        
        results = {}
        for i, prompt in enumerate(effective_prompts):
            try:
                entropy = self.compute_entropy(prompt)
                results[str(i)] = entropy
                if (i + 1) % 10 == 0:
                    logger.info(f"Processed {i + 1}/{len(effective_prompts)} prompts")
            except Exception as e:
                logger.error(f"Failed to compute entropy for prompt {i}: {e}")
                results[str(i)] = 0.0
                
        return results

def main():
    """
    Main entry point for entropy proxy computation with scaled mode support.
    
    Parses command-line arguments for sample_size and prompt_count,
    enforces scaled mode constraints, and logs the exact counts used.
    """
    parser = argparse.ArgumentParser(description="Compute semantic entropy with optional scaled mode")
    parser.add_argument(
        "--sample-size", 
        type=int, 
        default=10, 
        help="Number of paraphrase samples per prompt (default: 10)"
    )
    parser.add_argument(
        "--prompt-count", 
        type=int, 
        default=500, 
        help="Number of diverse prompts to process (default: 500)"
    )
    parser.add_argument(
        "--scaled-mode",
        action="store_true",
        help="Enable scaled mode for Kaggle GPU (limits sample_size=5, prompt_count=200)"
    )
    parser.add_argument(
        "--input-csv",
        type=str,
        default="data/processed/diverse_prompts.csv",
        help="Path to input CSV with prompts"
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default="data/processed/entropy_scores.json",
        help="Path to output JSON file"
    )
    
    args = parser.parse_args()
    
    # Log configuration
    logger.info(f"Arguments: sample_size={args.sample_size}, prompt_count={args.prompt_count}, scaled_mode={args.scaled_mode}")
    
    # Initialize proxy
    proxy = EntropyProxy(
        sample_size=args.sample_size,
        prompt_count=args.prompt_count,
        use_scaled_mode=args.scaled_mode
    )
    
    # Log exact counts used (after potential scaling)
    logger.info(f"Final configuration: sample_size={proxy.sample_size}, prompt_count={proxy.prompt_count}")
    
    # Load prompts from CSV
    prompts = []
    if os.path.exists(args.input_csv):
        import csv
        with open(args.input_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'caption' in row:
                    prompts.append(row['caption'])
                elif 'prompt' in row:
                    prompts.append(row['prompt'])
        
        logger.info(f"Loaded {len(prompts)} prompts from {args.input_csv}")
    else:
        logger.warning(f"Input file {args.input_csv} not found. Using dummy prompts for demonstration.")
        prompts = [f"Dummy prompt {i}" for i in range(args.prompt_count)]
    
    # Compute entropy
    results = proxy.compute_entropy_batch(prompts)
    
    # Save results
    output_path = Path(args.output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"Entropy scores saved to {args.output_json}")
    logger.info(f"Processed {len(results)} prompts with {proxy.sample_size} samples each")
    
    # Explicitly log the deliverable requirement
    logger.info(f"DELIVERABLE: Script executed with --sample-size={args.sample_size} and --prompt-count={args.prompt_count}")
    logger.info(f"DELIVERABLE: Actual counts used: sample_size={proxy.sample_size}, prompt_count={proxy.prompt_count}")

if __name__ == "__main__":
    main()