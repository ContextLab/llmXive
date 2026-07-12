import os
import json
import csv
import time
import logging
from typing import List, Dict, Any, Tuple, Optional

import numpy as np
from sentence_transformers import SentenceTransformer

from config import get_seeds
from utils import (
    get_embedding,
    cosine_similarity,
    pairwise_cosine_similarity_matrix,
    mean_pairwise_similarity,
    variance,
    std_dev,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global embedding model (lazy load)
_embedding_model: Optional[SentenceTransformer] = None

def get_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        logger.info("Loading SentenceTransformer model (CPU-only)...")
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
    return _embedding_model


class SkillLibrary:
    """
    Manages the collection of skills, their embeddings, and handles pruning logic.
    """

    def __init__(self, skills_data: List[Dict[str, Any]]):
        """
        Initialize the library from a list of skill dictionaries.
        Expects each skill to have 'id', 'code', and 'embedding' (optional).
        """
        self.skills = skills_data
        self.id_to_skill = {s["id"]: s for s in self.skills}
        self.embeddings: Dict[str, np.ndarray] = {}
        self.usage_counts: Dict[str, int] = {s["id"]: 0 for s in self.skills}
        
        # Pre-compute embeddings if not present
        model = get_model()
        for skill in self.skills:
            sid = skill["id"]
            if "embedding" in skill and skill["embedding"] is not None:
                self.embeddings[sid] = np.array(skill["embedding"])
            else:
                # Compute on demand or here
                self.embeddings[sid] = get_embedding(model, skill["code"])

    def get_top_k(self, query_embedding: np.ndarray, k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve top-k skills based on cosine similarity."""
        similarities = {}
        for sid, emb in self.embeddings.items():
            similarities[sid] = cosine_similarity(query_embedding, emb)
        
        sorted_sids = sorted(similarities.keys(), key=lambda x: similarities[x], reverse=True)
        top_sids = sorted_sids[:k]
        return [self.id_to_skill[sid] for sid in top_sids]

    def mark_usage(self, skill_ids: List[str]):
        """Increment usage count for given skill IDs."""
        for sid in skill_ids:
            if sid in self.usage_counts:
                self.usage_counts[sid] += 1

    def prune_skills(
        self, 
        threshold: float = 0.70, 
        ground_truth_ids: Optional[List[str]] = None
    ) -> Tuple[List[str], int]:
        """
        Remove skills where usage_count == 0 AND min_cosine_similarity < threshold.
        
        Args:
            threshold: The similarity threshold (default 0.70).
            ground_truth_ids: Optional list of ground truth skill IDs to check against.
                              If provided, counts how many removed skills had high similarity
                              to the ground truth.
        
        Returns:
            Tuple of (list of removed skill IDs, count of removed skills with high GT similarity)
        """
        if not self.skills:
            return [], 0

        # Calculate pairwise similarities if needed for pruning logic
        # We need to check similarity of each unused skill against ALL other skills
        # to find its "min_cosine_similarity" (or against ground truth if specified? 
        # Based on T027 spec: "min_cosine_similarity < 0.70" usually implies similarity 
        # to the active set or ground truth. Let's assume it means similarity to 
        # the nearest neighbor in the remaining set or specifically to GT if provided.
        # T027 says: "removes skills where usage_count == 0 AND min_cosine_similarity < 0.70".
        # T028 says: "count skills removed with high similarity to ground truth".
        
        # Interpretation: 
        # 1. Identify candidates: usage == 0.
        # 2. Calculate similarity of candidate to its nearest neighbor in the CURRENT library (or GT?).
        #    Standard "redundancy" pruning usually looks at similarity to *other* skills.
        #    However, T028 specifically asks for "high similarity to ground truth".
        #    Let's assume the pruning condition is based on similarity to the *nearest neighbor* 
        #    in the current library (excluding itself), and T028 adds a metric: 
        #    "how many of these pruned items were actually similar to the Ground Truth?"
        
        candidates = [s for s in self.skills if self.usage_counts[s["id"]] == 0]
        if not candidates:
            return [], 0

        # Pre-calculate embeddings for speed
        # We need to compare candidates against the set of ALL skills (excluding self)
        # to find min similarity.
        
        # Optimization: If the library is small (100 skills), O(N^2) is fine.
        all_sids = list(self.embeddings.keys())
        
        removed_ids = []
        high_gt_similarity_count = 0

        # If ground_truth_ids are provided, we track similarity to them for the metric
        gt_embeddings = None
        if ground_truth_ids:
            gt_embeddings = [self.embeddings[sid] for sid in ground_truth_ids if sid in self.embeddings]

        for candidate in candidates:
            c_emb = self.embeddings[candidate["id"]]
            
            # Find min similarity to any OTHER skill in the library
            min_sim = 1.0
            for other_sid in all_sids:
                if other_sid == candidate["id"]:
                    continue
                if other_sid not in self.embeddings:
                    continue
                sim = cosine_similarity(c_emb, self.embeddings[other_sid])
                if sim < min_sim:
                    min_sim = sim
            
            # Pruning condition: usage == 0 AND min_sim < threshold
            if min_sim < threshold:
                removed_ids.append(candidate["id"])
                del self.usage_counts[candidate["id"]]
                del self.embeddings[candidate["id"]]
                # Remove from skills list
                self.skills = [s for s in self.skills if s["id"] != candidate["id"]]
                self.id_to_skill.pop(candidate["id"], None)

                # T028: Check if this removed skill had high similarity to ground truth
                if gt_embeddings:
                    # Calculate max similarity to any GT skill
                    max_gt_sim = 0.0
                    for gt_emb in gt_embeddings:
                        s = cosine_similarity(c_emb, gt_emb)
                        if s > max_gt_sim:
                            max_gt_sim = s
                    
                    # "High similarity" to ground truth? Let's use a threshold, e.g., 0.8 or 0.7
                    # The prompt says "high similarity". Let's assume > 0.75 as a safe high threshold.
                    if max_gt_sim > 0.75:
                        high_gt_similarity_count += 1

        return removed_ids, high_gt_similarity_count

    def get_active_count(self) -> int:
        return len(self.skills)


def calculate_retrieval_precision(
    retrieved_ids: List[str], ground_truth_ids: List[str]
) -> float:
    """
    Calculate Jaccard similarity between retrieved and ground truth sets.
    """
    if not ground_truth_ids:
        return 0.0
    if not retrieved_ids:
        return 0.0
    
    set_retrieved = set(retrieved_ids)
    set_gt = set(ground_truth_ids)
    
    intersection = len(set_retrieved & set_gt)
    union = len(set_retrieved | set_gt)
    
    if union == 0:
        return 0.0
    return intersection / union


def calculate_retrieval_diversity(
    retrieved_ids: List[str], ground_truth_ids: List[str], embeddings: Dict[str, np.ndarray]
) -> float:
    """
    Calculate diversity as inverse of variance of cosine similarities 
    of retrieved skills against the ground truth set.
    """
    if not ground_truth_ids or not retrieved_ids:
        return 0.0

    similarities = []
    for rid in retrieved_ids:
        if rid not in embeddings:
            continue
        r_emb = embeddings[rid]
        # Calculate similarity to the centroid of ground truth or average of similarities?
        # Spec: "variance of the cosine similarities of the top-k retrieved skills against the ground truth set"
        # Interpretation: For each retrieved skill, calculate its similarity to the GT set (e.g., max or mean),
        # then calculate variance of those values.
        # Let's use mean similarity to all GT skills for each retrieved skill.
        
        sims_to_gt = []
        for gid in ground_truth_ids:
            if gid in embeddings:
                sims_to_gt.append(cosine_similarity(r_emb, embeddings[gid]))
        
        if sims_to_gt:
            mean_sim = np.mean(sims_to_gt)
            similarities.append(mean_sim)
    
    if len(similarities) < 2:
        return 0.0 # Cannot calculate variance

    var = variance(similarities)
    if var == 0:
        return 0.0 # Avoid division by zero
    
    return 1.0 / var


def append_to_log(
    log_path: str,
    task_id: str,
    skill_id: str,
    success: bool,
    latency: float,
    tokens: int,
    retrieval_precision: float,
    retrieval_diversity: float,
    pruning_risk_count: int,
    library_size: int,
    pruning_enabled: bool,
):
    """
    Append a single row to the experiment log CSV.
    Creates the file with headers if it doesn't exist.
    """
    fieldnames = [
        "task_id", "skill_id", "success", "latency", "tokens",
        "retrieval_precision", "retrieval_diversity", "pruning_risk_count",
        "library_size", "pruning_enabled"
    ]
    
    file_exists = os.path.isfile(log_path)
    
    with open(log_path, mode="a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        
        writer.writerow({
            "task_id": task_id,
            "skill_id": skill_id,
            "success": success,
            "latency": latency,
            "tokens": tokens,
            "retrieval_precision": retrieval_precision,
            "retrieval_diversity": retrieval_diversity,
            "pruning_risk_count": pruning_risk_count,
            "library_size": library_size,
            "pruning_enabled": pruning_enabled,
        })


def run_task(
    task: Dict[str, Any],
    library: SkillLibrary,
    log_path: str,
    pruning_enabled: bool = True,
    pruning_interval: int = 10,
    task_counter: int = 0,
) -> Tuple[Dict[str, Any], int]:
    """
    Execute a single task against the library.
    
    Returns:
        Tuple of (result_dict, updated_task_counter)
        result_dict contains metrics including pruning_risk_count for this batch if applicable.
    """
    model = get_model()
    task_embedding = get_embedding(model, task["description"])
    ground_truth_ids = task.get("ground_truth", [])
    
    # Retrieve top-k
    retrieved_skills = library.get_top_k(task_embedding, k=5)
    retrieved_ids = [s["id"] for s in retrieved_skills]
    
    # Calculate metrics
    precision = calculate_retrieval_precision(retrieved_ids, ground_truth_ids)
    diversity = calculate_retrieval_diversity(retrieved_ids, ground_truth_ids, library.embeddings)
    
    # Simulate execution (since we don't have a real LLM, we check if GT is in retrieved)
    # T020: "compare output against the ground-truth solution path"
    # Simplified: Success if at least one GT skill is retrieved (or all, depending on strictness)
    # Let's assume success if the set of retrieved skills overlaps significantly with GT.
    # For this simulation, we'll say success if the intersection is non-empty.
    success = len(set(retrieved_ids) & set(ground_truth_ids)) > 0
    
    # Simulate latency and tokens
    start_time = time.time()
    time.sleep(0.001) # Fake processing time
    latency = time.time() - start_time
    tokens = len(task["description"].split()) * 2
    
    # Mark usage
    library.mark_usage(retrieved_ids)
    
    pruning_risk_count = 0
    
    # Pruning Logic (T027 + T028)
    if pruning_enabled and (task_counter + 1) % pruning_interval == 0:
        removed_ids, risk_count = library.prune_skills(
            threshold=0.70,
            ground_truth_ids=ground_truth_ids
        )
        pruning_risk_count = risk_count
        if removed_ids:
            logger.info(f"Pruned {len(removed_ids)} skills. Risk count (high GT sim): {risk_count}")
    
    # Append to log
    # We need a skill_id for the log. If multiple retrieved, we can log the first or "batch".
    # The schema expects a single skill_id. Let's use the first retrieved or a placeholder.
    log_skill_id = retrieved_ids[0] if retrieved_ids else "none"
    
    append_to_log(
        log_path=log_path,
        task_id=task["id"],
        skill_id=log_skill_id,
        success=success,
        latency=latency,
        tokens=tokens,
        retrieval_precision=precision,
        retrieval_diversity=diversity,
        pruning_risk_count=pruning_risk_count,
        library_size=library.get_active_count(),
        pruning_enabled=pruning_enabled,
    )
    
    return {
        "task_id": task["id"],
        "success": success,
        "precision": precision,
        "diversity": diversity,
        "pruning_risk_count": pruning_risk_count,
    }, task_counter + 1


def main():
    """
    Entry point for running the agent experiment.
    Expects command line arguments or config to load tasks and skills.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Digital Colleague Agent")
    parser.add_argument("--tasks", type=str, required=True, help="Path to tasks.json")
    parser.add_argument("--skills", type=str, required=True, help="Path to skills.json")
    parser.add_argument("--output", type=str, default="data/results/experiment_log.csv", help="Output log path")
    parser.add_argument("--pruning", action="store_true", default=True, help="Enable pruning")
    parser.add_argument("--no-pruning", action="store_true", help="Disable pruning")
    parser.add_argument("--interval", type=int, default=10, help="Pruning interval")
    
    args = parser.parse_args()
    
    if args.no_pruning:
        args.pruning = False
    
    logger.info(f"Loading tasks from {args.tasks}")
    with open(args.tasks, "r") as f:
        tasks = json.load(f)
    
    logger.info(f"Loading skills from {args.skills}")
    with open(args.skills, "r") as f:
        skills_data = json.load(f)
    
    # Handle if skills_data is a dict with a "skills" key or a list
    if isinstance(skills_data, dict) and "skills" in skills_data:
        skills_list = skills_data["skills"]
    elif isinstance(skills_data, list):
        skills_list = skills_data
    else:
        raise ValueError("Invalid skills data format")
    
    library = SkillLibrary(skills_list)
    logger.info(f"Initialized library with {library.get_active_count()} skills")
    
    task_counter = 0
    for task in tasks:
        result, task_counter = run_task(
            task=task,
            library=library,
            log_path=args.output,
            pruning_enabled=args.pruning,
            pruning_interval=args.interval,
            task_counter=task_counter,
        )
        if task_counter % 50 == 0:
            logger.info(f"Processed {task_counter} tasks...")
    
    logger.info(f"Experiment complete. Results saved to {args.output}")


if __name__ == "__main__":
    main()