import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from sentence_transformers import SentenceTransformer
from utils.config import get_project_root, get_data_dir, set_seed
from retrieval.index_builder import IndexBuilder, IndexEntry

class Retriever:
    """
    Generates queries based solely on the current goal state (no ground-truth metadata).
    Performs semantic retrieval against an in-memory index built from historical snippets.
    """
    
    def __init__(
        self, 
        model_name: str = "all-MiniLM-L6-v2", 
        similarity_threshold: float = 0.65,
        top_k: int = 3,
        seed: int = 42
    ):
        """
        Initialize the retriever.
        
        Args:
            model_name: Name of the SentenceTransformer model to use.
            similarity_threshold: Minimum cosine similarity score to consider a match.
            top_k: Number of top results to return per query.
            seed: Random seed for reproducibility.
        """
        self.model_name = model_name
        self.similarity_threshold = similarity_threshold
        self.top_k = top_k
        self.seed = seed
        
        set_seed(self.seed)
        self.model = SentenceTransformer(self.model_name)
        self.index_builder: Optional[IndexBuilder] = None
        self._index_cache: Optional[List[Dict[str, Any]]] = None
        self._embeddings_cache: Optional[np.ndarray] = None

    def set_index(self, index_builder: IndexBuilder) -> None:
        """
        Attach an IndexBuilder instance to this Retriever.
        
        Args:
            index_builder: The index builder containing the historical snippets.
        """
        self.index_builder = index_builder
        # Pre-compute embeddings for the index if available
        self._rebuild_index_cache()

    def _rebuild_index_cache(self) -> None:
        """Rebuild the internal cache of index entries and their embeddings."""
        if not self.index_builder:
            self._index_cache = []
            self._embeddings_cache = None
            return

        entries = self.index_builder.get_entries()
        if not entries:
            self._index_cache = []
            self._embeddings_cache = None
            return

        self._index_cache = [entry.to_dict() for entry in entries]
        
        # Extract text for embedding
        texts = [entry["text"] for entry in self._index_cache]
        if texts:
            self._embeddings_cache = self.model.encode(texts, convert_to_numpy=True)
        else:
            self._embeddings_cache = None

    def generate_query_from_goal(self, goal_state: Dict[str, Any]) -> str:
        """
        Generate a search query string based SOLELY on the current goal state.
        
        This implementation strictly avoids ground-truth metadata or future context.
        It extracts the primary action intent and relevant object/target from the goal.
        
        Args:
            goal_state: Dictionary containing 'action', 'target', 'context', etc.
        
        Returns:
            A natural language query string suitable for semantic search.
        """
        if not isinstance(goal_state, dict):
            raise ValueError("goal_state must be a dictionary")

        parts = []
        
        # Extract action intent (e.g., "click", "type", "scroll")
        action = goal_state.get("action")
        if action:
            parts.append(f"action {action}")
        
        # Extract target object (e.g., "submit button", "search bar")
        target = goal_state.get("target")
        if target:
            parts.append(f"target {target}")
        
        # Extract immediate context if available (e.g., "on settings page")
        context = goal_state.get("context")
        if context:
            parts.append(f"context {context}")
        
        # If no specific fields found, fallback to a generic goal description
        if not parts:
            goal_desc = goal_state.get("description", goal_state.get("goal", ""))
            if goal_desc:
                parts.append(f"goal: {goal_desc}")
            else:
                # Fallback if completely empty
                parts.append("navigate to desired state")

        query = " ".join(parts)
        return query

    def retrieve(
        self, 
        goal_state: Dict[str, Any], 
        index: Optional[IndexBuilder] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant historical snippets based on the current goal state.
        
        Args:
            goal_state: The current state of the agent's goal.
            index: Optional IndexBuilder instance. If provided, overrides the instance's index.
        
        Returns:
            List of retrieved snippets with similarity scores, sorted descending.
        """
        if index:
            self.set_index(index)
        
        if not self.index_builder or not self._embeddings_cache:
            return []

        # 1. Generate query solely from goal state
        query_text = self.generate_query_from_goal(goal_state)
        
        # 2. Encode query
        query_embedding = self.model.encode([query_text], convert_to_numpy=True)
        
        # 3. Compute cosine similarity
        # Normalize embeddings for cosine similarity
        norm_query = query_embedding / np.linalg.norm(query_embedding, axis=1, keepdims=True)
        norm_index = self._embeddings_cache / np.linalg.norm(self._embeddings_cache, axis=1, keepdims=True)
        
        similarities = np.dot(norm_index, norm_query.T).flatten()
        
        # 4. Filter by threshold and sort
        valid_indices = np.where(similarities >= self.similarity_threshold)[0]
        if len(valid_indices) == 0:
            return []
        
        # Sort by similarity descending
        sorted_indices = valid_indices[np.argsort(similarities[valid_indices])[::-1]]
        
        # 5. Select top_k
        top_indices = sorted_indices[:self.top_k]
        
        results = []
        for idx in top_indices:
            entry = self._index_cache[idx]
            score = float(similarities[idx])
            results.append({
                "entry": entry,
                "similarity_score": score,
                "query_text": query_text
            })
        
        return results

    def main():
        """
        Main entry point for testing the retriever independently.
        Reads a sample trajectory from data, builds an index, and tests retrieval.
        """
        project_root = get_project_root()
        data_dir = get_data_dir()
        
        # Path to synthetic benchmark data (generated by T011)
        trajectories_path = data_dir / "synthetic_benchmark" / "trajectories.jsonl"
        
        if not trajectories_path.exists():
            print(f"Error: Trajectories file not found at {trajectories_path}")
            print("Please run code/data_generation/synthetic_benchmark.py first.")
            sys.exit(1)

        # Load a few trajectories to build an index
        print(f"Loading trajectories from {trajectories_path}...")
        trajectories = []
        with open(trajectories_path, 'r') as f:
            for i, line in enumerate(f):
                if i >= 5: # Load first 5 for demo
                    break
                trajectories.append(json.loads(line))
        
        if not trajectories:
            print("No trajectories found to process.")
            sys.exit(1)

        # Build index from history
        print("Building index from historical snippets...")
        index_builder = IndexBuilder()
        for traj in trajectories:
            traj_id = traj.get("trajectory_id", "unknown")
            steps = traj.get("steps", [])
            for step in steps:
                # Create a historical snippet from step history
                # Format: "Step {step_id}: Action {action} on {target} in {app}"
                snippet_text = f"Step {step.get('step_id', 0)}: Action {step.get('action', 'unknown')} on {step.get('target', 'unknown')} in {step.get('app', 'unknown')}"
                index_builder.add_entry(
                    trajectory_id=traj_id,
                    step_id=step.get("step_id", 0),
                    text=snippet_text,
                    metadata={
                        "action": step.get("action"),
                        "target": step.get("target"),
                        "app": step.get("app")
                    }
                )

        # Initialize Retriever
        retriever = Retriever(model_name="all-MiniLM-L6-v2", similarity_threshold=0.5, top_k=3)
        retriever.set_index(index_builder)

        # Test retrieval with a synthetic goal state
        test_goal = {
            "action": "click",
            "target": "submit button",
            "context": "on checkout page",
            "description": "Complete the purchase"
        }

        print(f"\nTesting retrieval with goal: {test_goal}")
        results = retriever.retrieve(test_goal)

        print(f"\nRetrieved {len(results)} snippets:")
        for i, res in enumerate(results):
            print(f"  [{i+1}] Score: {res['similarity_score']:.4f}")
            print(f"      Text: {res['entry']['text']}")
            print(f"      Query used: {res['query_text']}")
            print()

        # Write results to a JSON file for verification
        output_path = data_dir / "results" / "retrieval_test_results.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump({
                "query_goal": test_goal,
                "generated_query": retriever.generate_query_from_goal(test_goal),
                "results": results
            }, f, indent=2)
        
        print(f"Results saved to {output_path}")

if __name__ == "__main__":
    main()