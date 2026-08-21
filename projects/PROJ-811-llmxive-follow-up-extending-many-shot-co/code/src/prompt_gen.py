import argparse
import json
import logging
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer

class PromptGenerator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model_name = self.config.get("embedding_model", "all-MiniLM-L6-v2")
        self.model = SentenceTransformer(self.model_name)

    def load_dags(self, manifest_path: str) -> List[Dict]:
        with open(manifest_path, "r") as f:
            return json.load(f)

    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate SBERT embeddings for a list of texts."""
        return self.model.encode(texts)

    def calculate_curvature(self, embeddings: np.ndarray) -> float:
        """
        Calculate the 'Curvature Score' as the population variance of
        cosine similarities between adjacent sentence embeddings.
        
        Args:
            embeddings: Array of shape (N, D) where N is number of sentences.
        
        Returns:
            float: The population variance of adjacent cosine similarities.
                   Returns 0.0 if fewer than 2 embeddings exist.
        """
        if len(embeddings) < 2:
            return 0.0
        
        similarities = []
        for i in range(len(embeddings) - 1):
            v1 = embeddings[i]
            v2 = embeddings[i + 1]
            # Cosine similarity
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)
            if norm1 == 0 or norm2 == 0:
                sim = 0.0
            else:
                sim = np.dot(v1, v2) / (norm1 * norm2)
            similarities.append(sim)
        
        similarities = np.array(similarities)
        # Population variance (ddof=0)
        return float(np.var(similarities, ddof=0))

    def calculate_all_curvature_scores(self, dags: List[Dict]) -> Dict[str, float]:
        """
        Calculate curvature scores for ALL examples in the manifest.
        This is the core implementation for T024b.
        
        Args:
            dags: List of DAG entries, each containing at least 'id' and 'text'.
        
        Returns:
            Dict mapping example ID to its calculated curvature score.
        """
        if not dags:
            return {}
        
        texts = [dag.get("text", "") for dag in dags]
        # Generate embeddings for all texts
        embeddings = self.generate_embeddings(texts)
        
        curvature_scores = {}
        for i, dag in enumerate(dags):
            # Calculate curvature for this specific example
            # Note: If 'text' is a single trace, we treat it as one sequence.
            # If the trace was split into steps, we would use those steps.
            # Based on T024a context, we assume 'text' is the full trace or a sequence.
            # For this implementation, we calculate curvature on the single embedding 
            # if it's a single sentence, which yields 0.0. 
            # However, the task implies calculating variance of adjacent similarities.
            # If the input 'text' is a single string, we get 1 embedding -> 0 variance.
            # To make this meaningful, we assume the 'text' field might contain 
            # multiple sentences separated by newlines or that we are processing
            # a batch where we look at adjacent examples? 
            # Re-reading T024b: "Calculate cosine similarity between adjacent sentences in the embeddings"
            # This implies the 'text' itself should be split into sentences, OR
            # we are looking at the sequence of examples in the prompt.
            # Given T024a generates embeddings for "each example", and T024b calculates
            # "adjacent sentences", the most logical interpretation for a single trace
            # is to split the trace into sentences/steps.
            # However, if the 'text' in the DAG is a single block, we might need to split it.
            # Let's assume the 'text' field contains the full trace which might be multi-sentence.
            # We will split by '.' or newlines to get sentences if possible, or treat the whole text as one.
            # BUT, the task says "adjacent sentences in the embeddings".
            # If we have 100 examples, and we embed each example, we have 100 vectors.
            # "Adjacent sentences" likely refers to the sentences *within* a trace if the trace is long.
            # OR, it refers to the sequence of examples in the prompt?
            # "Original CDS" usually implies the semantic flow of the *prompt sequence*.
            # Let's re-read carefully: "Calculate cosine similarity between adjacent sentences in the embeddings (from T024a)"
            # T024a: "compute embeddings for each example".
            # If we have 100 examples, we have 100 embeddings.
            # If we calculate similarity between example i and i+1, that's "adjacent examples".
            # If the task says "sentences", it might imply the text was split into sentences first.
            # Given the ambiguity, the most robust interpretation for "Curvature" in a sequence of examples
            # is the variance of similarities between adjacent *examples* in the sequence.
            # However, the task specifically says "adjacent sentences".
            # Let's assume the 'text' in the DAG is a single string.
            # To get "adjacent sentences", we must split the text into sentences.
            # We will split by common delimiters.
            
            text = dag.get("text", "")
            # Split text into sentences (simple heuristic)
            import re
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            if len(sentences) < 2:
                # Not enough sentences to calculate variance of similarities
                curvature_scores[dag["id"]] = 0.0
                continue
                
            # Generate embeddings for sentences of THIS example
            # This is computationally expensive if done per example for a large dataset.
            # Optimization: If the dataset is large, we might need to batch.
            # For now, we assume the number of sentences per trace is manageable.
            sentence_embeddings = self.generate_embeddings(sentences)
            score = self.calculate_curvature(sentence_embeddings)
            curvature_scores[dag["id"]] = score

        return curvature_scores

    def sort_original_cds(self, dags: List[Dict], curvature_scores: Dict[str, float]) -> List[Dict]:
        """Sort DAGs by their curvature score (ascending)."""
        dag_with_curvature = [(dag, curvature_scores.get(dag["id"], 0.0)) for dag in dags]
        sorted_dags = sorted(dag_with_curvature, key=lambda x: x[1])
        return [dag for dag, _ in sorted_dags]

    def generate_prompts(self, dags: List[Dict], strategy: str):
        if strategy == "original_cds":
            # Calculate curvature scores for all examples
            curvature_scores = self.calculate_all_curvature_scores(dags)
            
            # Save curvature scores to file (T024b requirement)
            output_path = Path("data/processed/curvature_scores.json")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(curvature_scores, f, indent=2)
            logging.info(f"Curvature scores saved to {output_path}")
            
            # Sort by curvature score
            sorted_dags = self.sort_original_cds(dags, curvature_scores)
            return sorted_dags
        elif strategy == "logical_ascending":
            sorted_dags = sorted(dags, key=lambda x: x.get("depth", 0))
            return sorted_dags
        elif strategy == "logical_random":
            random.shuffle(dags)
            return dags
        else:
            raise ValueError(f"Unknown prompt strategy: {strategy}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=str, required=True, help="Path to the DAG manifest file.")
    parser.add_argument("--strategy", type=str, default="original_cds", choices=["original_cds", "logical_ascending", "logical_random"], help="Prompt generation strategy.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for shuffling.")
    parser.add_argument("--output", type=str, default="data/processed/prompts.json", help="Path to save the generated prompts.")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    config = {
        "embedding_model": "all-MiniLM-L6-v2",
    }

    prompt_generator = PromptGenerator(config)

    try:
        dags = prompt_generator.load_dags(args.manifest)
        sorted_dags = prompt_generator.generate_prompts(dags, args.strategy)

        # Ensure output directory exists
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        
        with open(args.output, "w") as f:
            json.dump(sorted_dags, f, indent=4)
        logger.info(f"Prompts saved to {args.output}")

    except Exception as e:
        logger.error(f"Error generating prompts: {e}")
        raise

if __name__ == "__main__":
    main()