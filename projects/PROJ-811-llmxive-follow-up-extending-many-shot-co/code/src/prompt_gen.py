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
        # Use the SBERT model specified in the task description
        self.model_name = self.config.get(
            "embedding_model", "sentence-transformers/all-MiniLM-L-v"
        )
        self.model = SentenceTransformer(self.model_name)

    def load_dags(self, manifest_path: str) -> List[Dict]:
        with open(manifest_path, "r") as f:
            return json.load(f)

    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate SBERT embeddings for a list of texts."""
        return self.model.encode(texts)

    def _save_embeddings(self, embeddings_dict: Dict[str, List[float]]) -> None:
        """
        Save the embeddings dictionary to the canonical location
        ``data/processed/embeddings.json``.
        """
        output_path = Path("data/processed/embeddings.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(embeddings_dict, f, indent=2)
        logging.info(f"Embeddings saved to {output_path}")

    def generate_and_save_embeddings(self, dags: List[Dict]) -> Dict[str, List[float]]:
        """
        Compute embeddings for each example (using the ``text`` field) and
        persist them to ``embeddings.json``.

        Returns:
            A mapping from example ID to the embedding vector (as a list of floats).
        """
        if not dags:
            return {}

        texts = [dag.get("text", "") for dag in dags]
        ids = [dag.get("id") for dag in dags]

        # Generate embeddings for the full example texts
        raw_embeddings = self.generate_embeddings(texts)

        # Convert to a JSON‑serialisable structure
        embeddings_dict = {
            str(example_id): embedding.tolist()
            for example_id, embedding in zip(ids, raw_embeddings)
        }

        self._save_embeddings(embeddings_dict)
        return embeddings_dict

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

        curvature_scores = {}
        for dag in dags:
            text = dag.get("text", "")
            # Simple sentence splitter
            import re

            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if s.strip()]

            if len(sentences) < 2:
                curvature_scores[dag["id"]] = 0.0
                continue

            # Generate embeddings for the sentences of this example
            sentence_embeddings = self.generate_embeddings(sentences)
            score = self.calculate_curvature(sentence_embeddings)
            curvature_scores[dag["id"]] = score

        return curvature_scores

    def sort_original_cds(self, dags: List[Dict], curvature_scores: Dict[str, float]) -> List[Dict]:
        """Sort DAGs by their curvature score (ascending)."""
        dag_with_curvature = [
            (dag, curvature_scores.get(dag["id"], 0.0)) for dag in dags
        ]
        sorted_dags = sorted(dag_with_curvature, key=lambda x: x[1])
        return [dag for dag, _ in sorted_dags]

    def generate_prompts(self, dags: List[Dict], strategy: str):
        if strategy == "original_cds":
            # Step 1: Compute and persist embeddings (T024a)
            self.generate_and_save_embeddings(dags)

            # Step 2: Calculate curvature scores (T024b)
            curvature_scores = self.calculate_all_curvature_scores(dags)

            # Save curvature scores to file (T024b requirement)
            curvature_path = Path("data/processed/curvature_scores.json")
            curvature_path.parent.mkdir(parents=True, exist_ok=True)
            with open(curvature_path, "w") as f:
                json.dump(curvature_scores, f, indent=2)
            logging.info(f"Curvature scores saved to {curvature_path}")

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
    parser.add_argument(
        "--manifest",
        type=str,
        required=True,
        help="Path to the DAG manifest file.",
    )
    parser.add_argument(
        "--strategy",
        type=str,
        default="original_cds",
        choices=[
            "original_cds",
            "logical_ascending",
            "logical_random",
        ],
        help="Prompt generation strategy.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for shuffling.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/prompts.json",
        help="Path to save the generated prompts.",
    )

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Set deterministic seed for the random strategy
    random.seed(args.seed)

    config = {
        "embedding_model": "sentence-transformers/all-MiniLM-L-v",
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
