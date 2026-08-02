"""
Prompt generation module for creating few-shot prompts with different ordering strategies.
Implements Logical Ascending, Logical Random, and Original CDS (Semantic Curvature) strategies.
"""
import random
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer

from code.src.parser_utils import load_json_file, save_json_file
from code.src.config import get_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PromptGenerator:
    """
    Generates few-shot prompts based on different ordering strategies.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or get_config()
        self.seed = None
        self.strategy = None
        self.sbert_model = None
        self._load_sbert()
    
    def _load_sbert(self):
        """Load SBERT model for semantic curvature calculation."""
        try:
            # Use a lightweight model suitable for CPU
            model_name = self.config.get('model', {}).get('sbert', 'all-MiniLM-L6-v2')
            logger.info(f"Loading SBERT model: {model_name}")
            self.sbert_model = SentenceTransformer(model_name)
        except Exception as e:
            logger.error(f"Failed to load SBERT model: {e}")
            self.sbert_model = None
    
    def set_seed(self, seed: int):
        """Set the random seed for deterministic shuffling."""
        self.seed = seed
        random.seed(seed)
        if self.sbert_model:
            # SBERT might have internal randomness, but we set global seed
            np.random.seed(seed)
    
    def set_strategy(self, strategy: str):
        """Set the ordering strategy."""
        if strategy not in ["logical_ascending", "logical_random", "original_cds"]:
            raise ValueError(f"Unknown strategy: {strategy}")
        self.strategy = strategy
    
    def _calculate_curvature_scores(self, examples: List[Dict[str, Any]]) -> List[float]:
        """
        Calculate Semantic Curvature Score for each example.
        Algorithm: Compute sentence embeddings, calculate cosine similarity between adjacent sentences,
        then compute the variance of these similarities.
        """
        if not self.sbert_model:
            logger.warning("SBERT model not loaded, returning zero curvature scores")
            return [0.0] * len(examples)
        
        curvature_scores = []
        
        for example in examples:
            trace = example.get('trace', '')
            if not trace:
                curvature_scores.append(0.0)
                continue
            
            # Split trace into sentences (simple split by period for now)
            sentences = [s.strip() for s in trace.split('.') if s.strip()]
            
            if len(sentences) < 2:
                curvature_scores.append(0.0)
                continue
            
            # Get embeddings
            try:
                embeddings = self.sbert_model.encode(sentences, convert_to_numpy=True)
                
                # Calculate cosine similarities between adjacent sentences
                similarities = []
                for i in range(len(embeddings) - 1):
                    # Cosine similarity
                    dot_product = np.dot(embeddings[i], embeddings[i+1])
                    norm = np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[i+1])
                    if norm == 0:
                        similarities.append(0.0)
                    else:
                        similarities.append(dot_product / norm)
                
                # Variance of similarities
                if len(similarities) > 0:
                    variance = np.var(similarities)
                    curvature_scores.append(variance)
                else:
                    curvature_scores.append(0.0)
                    
            except Exception as e:
                logger.warning(f"Failed to calculate curvature for example: {e}")
                curvature_scores.append(0.0)
        
        return curvature_scores
    
    def _sort_logical_ascending(self, examples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort examples by Logical Difficulty Score (max path depth) in ascending order."""
        return sorted(examples, key=lambda x: x.get('logical_difficulty', 0))
    
    def _shuffle_logical_random(self, examples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Shuffle examples deterministically with the set seed."""
        shuffled = examples.copy()
        random.shuffle(shuffled)
        return shuffled
    
    def _sort_original_cds(self, examples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort examples by Original CDS (Semantic Curvature) score."""
        curvature_scores = self._calculate_curvature_scores(examples)
        
        # Attach scores to examples
        examples_with_scores = [
            (ex, score) for ex, score in zip(examples, curvature_scores)
        ]
        
        # Sort by curvature score (ascending or descending? Spec says "Original CDS" sorting)
        # Assuming ascending order for consistency with logical ascending
        sorted_examples = sorted(examples_with_scores, key=lambda x: x[1])
        
        return [ex for ex, _ in sorted_examples]
    
    def generate_prompts(self, examples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate prompts for the given examples based on the current strategy.
        Returns a list of prompt objects.
        """
        if self.strategy is None:
            raise ValueError("Strategy not set. Call set_strategy() first.")
        
        if self.seed is None:
            raise ValueError("Seed not set. Call set_seed() first.")
        
        # Sort/shuffle examples based on strategy
        if self.strategy == "logical_ascending":
            sorted_examples = self._sort_logical_ascending(examples)
        elif self.strategy == "logical_random":
            sorted_examples = self._shuffle_logical_random(examples)
        elif self.strategy == "original_cds":
            sorted_examples = self._sort_original_cds(examples)
        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")
        
        # Generate prompt objects
        prompts = []
        for i, example in enumerate(sorted_examples):
            prompt_text = self._assemble_prompt(example, i)
            prompts.append({
                "index": i,
                "seed": self.seed,
                "strategy": self.strategy,
                "example_id": example.get('id', f'example_{i}'),
                "prompt": prompt_text,
                "metadata": {
                    "logical_difficulty": example.get('logical_difficulty', 0),
                    "curvature_score": example.get('curvature_score', 0) if self.strategy == "original_cds" else None
                }
            })
        
        return prompts
    
    def _assemble_prompt(self, example: Dict[str, Any], index: int) -> str:
        """
        Assemble a single prompt from an example.
        This is a simplified version; actual template might be more complex.
        """
        question = example.get('question', '')
        trace = example.get('trace', '')
        answer = example.get('answer', '')
        
        # Simple template
        prompt = f"""
        Question: {question}
        
        Thought Process:
        {trace}
        
        Answer: {answer}
        """.strip()
        
        return prompt

def main():
    """Main entry point for testing the prompt generator."""
    config = get_config()
    generator = PromptGenerator(config)
    
    # Load sample data for testing
    # This would normally come from the DAG manifest
    sample_examples = [
        {"id": "1", "question": "What is 2+2?", "trace": "Step 1: Add 2 and 2. Step 2: Result is 4.", "answer": "4", "logical_difficulty": 1},
        {"id": "2", "question": "What is 3*3?", "trace": "Step 1: Multiply 3 by 3. Step 2: Result is 9.", "answer": "9", "logical_difficulty": 2},
        {"id": "3", "question": "What is 5-2?", "trace": "Step 1: Subtract 2 from 5. Step 2: Result is 3.", "answer": "3", "logical_difficulty": 1},
    ]
    
    # Test logical ascending
    generator.set_seed(42)
    generator.set_strategy("logical_ascending")
    prompts = generator.generate_prompts(sample_examples)
    print("Logical Ascending:")
    for p in prompts:
        print(f"  {p['example_id']}: depth={p['metadata']['logical_difficulty']}")
    
    # Test logical random
    generator.set_seed(42)
    generator.set_strategy("logical_random")
    prompts = generator.generate_prompts(sample_examples)
    print("\nLogical Random (seed=42):")
    for p in prompts:
        print(f"  {p['example_id']}")
    
    # Test original_cds
    generator.set_seed(42)
    generator.set_strategy("original_cds")
    prompts = generator.generate_prompts(sample_examples)
    print("\nOriginal CDS:")
    for p in prompts:
        print(f"  {p['example_id']}: curvature={p['metadata'].get('curvature_score')}")

if __name__ == "__main__":
    main()
