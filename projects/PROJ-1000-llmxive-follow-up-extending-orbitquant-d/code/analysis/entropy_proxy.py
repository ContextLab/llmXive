import torch
import numpy as np
from transformers import AutoTokenizer, AutoModelForCausalLM
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from typing import List, Dict, Optional
import logging
import json
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EntropyProxy:
    def __init__(self, model_name: str = "facebook/opt-125m", device: str = "cpu", sample_size: int = 5, prompt_count: int = 200, use_scaled_mode: bool = False):
        self.device = device
        self.sample_size = 5 if use_scaled_mode else sample_size
        self.prompt_count = 200 if use_scaled_mode else prompt_count
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name).to(device)
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')

    def compute_entropy(self, prompt: str) -> float:
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=20,
                num_return_sequences=self.sample_size,
                do_sample=True,
                temperature=0.8,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        paraphrases = []
        for i in range(self.sample_size):
            if i < outputs.shape[0]:
                text = self.tokenizer.decode(outputs[i, inputs['input_ids'].shape[1]:], skip_special_tokens=True)
                paraphrases.append(text.strip())
            else:
                paraphrases.append(prompt)
        
        embeddings = self.sentence_model.encode(paraphrases, convert_to_numpy=True)
        n_clusters = min(len(paraphrases), self.sample_size)
        if n_clusters < 2: return 0.0
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(embeddings)
        unique, counts = np.unique(labels, return_counts=True)
        probs = counts / len(labels)
        return float(-np.sum(probs * np.log2(probs + 1e-10)))

def compute_semantic_entropy(prompt: str, num_samples: int = 5) -> Optional[float]:
    """
    Wrapper function to compute semantic entropy.
    """
    try:
        proxy = EntropyProxy(sample_size=num_samples, use_scaled_mode=True)
        return proxy.compute_entropy(prompt)
    except Exception as e:
        logger.error(f"Entropy proxy failure: {e}")
        log_path = Path("data/proxy_failures.json")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a") as f:
            json.dump({"prompt": prompt, "error": str(e)}, f)
            f.write("\n")
        return None

def main():
    print(f"Entropy for 'a cat': {compute_semantic_entropy('a cat')}")

if __name__ == "__main__":
    main()
