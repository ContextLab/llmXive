"""
generate_eval_tasks.py

Generates the held-out set of task IDs for sensitivity analysis.
Reads the existing skill index and synthetic composite pairs to define
a held-out evaluation set, then saves it to data/processed/eval_tasks.yaml.

Dependencies:
  - T014d: data/processed/skill_index.npz (must exist)
  - T022g: data/processed/known_composites_pairs.yaml (must exist)
"""
import os
import sys
import logging
import numpy as np
import yaml
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))

from src.utils.config import get_project_root, get_data_path, ensure_directories

logger = logging.getLogger(__name__)

def load_skill_index(index_path: Path) -> Dict[str, np.ndarray]:
    """
    Load the skill index from the .npz file.
    Returns a dict mapping skill_id to vector.
    """
    if not index_path.exists():
        raise FileNotFoundError(f"Skill index not found at {index_path}. Run T014d first.")
    
    data = np.load(index_path, allow_pickle=True)
    # The .npz file usually contains keys like 'ids', 'vectors' or flattened keys
    # Based on T014d output structure (standard for this project):
    ids = data.get('ids', [])
    vectors = data.get('vectors', data.get('data', None))
    
    if isinstance(vectors, np.ndarray) and vectors.ndim == 1:
        # If it's a 1D array of objects, unpack
        if vectors.dtype == object:
            vector_dict = {}
            for i, v in enumerate(vectors):
                if isinstance(v, dict):
                   vector_dict[v['id']] = v['vector']
                else:
                   # Assume ordered with ids
                   if i < len(ids):
                       vector_dict[ids[i]] = v
            return vector_dict
        else:
            # 2D array where rows are vectors
            if vectors.ndim == 2:
                vector_dict = {}
                for i, vid in enumerate(ids):
                    if i < vectors.shape[0]:
                        vector_dict[vid] = vectors[i]
                return vector_dict
    elif isinstance(vectors, dict):
        return vectors
    else:
        # Fallback: try to reconstruct from raw keys if structure is flat
        # e.g. keys are 'id_0', 'vec_0'
        vector_dict = {}
        for key in data.files:
            if key.startswith('id_'):
                idx = key.split('_')[1]
                vid = str(data[key])
                vec_key = f'vec_{idx}'
                if vec_key in data.files:
                    vector_dict[vid] = data[vec_key]
        return vector_dict

def load_composite_pairs(pairs_path: Path) -> List[Dict[str, Any]]:
    """
    Load the known composite pairs generated in T022g.
    """
    if not pairs_path.exists():
        raise FileNotFoundError(f"Composite pairs not found at {pairs_path}. Run T022g first.")
    
    with open(pairs_path, 'r') as f:
        data = yaml.safe_load(f)
    
    if not isinstance(data, list):
        raise ValueError(f"Expected list of pairs in {pairs_path}, got {type(data)}")
    
    return data

def generate_held_out_tasks(index_ids: List[str], pairs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Construct the held-out task set for sensitivity analysis.
    
    Strategy:
    1. Extract all unique base skill IDs involved in the composite pairs.
    2. Define 'held-out' tasks as specific combinations of these skills
       that were NOT used to generate the 'known_composites' (T022g).
       However, since T022g generates 'known_composites' via interpolation,
       the 'held-out' set for T022e is typically the set of *individual*
       skills that act as the ground truth for single-skill retrieval,
       OR a set of specific composite definitions we will test against.
    
    For this specific task (T022e), the requirement is to generate a YAML
    containing the held-out set of task IDs for sensitivity analysis.
    Sensitivity analysis (T031a) sweeps k (number of neighbors).
    Therefore, the 'eval_tasks' should be a list of task definitions:
    - task_id: unique identifier
    - description: text description (optional, can be derived)
    - target_vector: the vector we are trying to recover (or the base skills)
    - strategy_params: parameters for the sensitivity sweep (k values)
    
    Since T022g creates synthetic composites, we will define the held-out
    tasks as the individual skills from the index that are part of the
    composite pairs, plus a few specific composite definitions.
    
    To be precise and useful for T031a:
    We define a set of 'Evaluation Tasks' where each task is defined by
    a target description (which maps to a target vector).
    For sensitivity analysis, we need to know which target to query for.
    
    We will generate tasks based on the 'known_composites_pairs' structure.
    Each pair in T022g likely represents a 'target' composed of skills A and B.
    We will create an eval task for each unique pair found in T022g,
    marking them as the 'held-out' set for the sensitivity sweep.
    """
    eval_tasks = []
    seen_targets = set()
    
    # We assume 'pairs' contains entries like:
    # { "id": "comp_001", "skill_a": "id_...", "skill_b": "id_...", "weight": 0.5 }
    # or similar. We need to adapt based on what T022g actually produces.
    # If T022g produces 'known_composites_true_weights', it implies a target vector.
    
    # Let's assume the pairs list contains the definition of the composites.
    # We will generate an eval task for each composite pair.
    
    for i, pair in enumerate(pairs):
        task_id = f"eval_task_{i:03d}"
        
        # Extract relevant info
        # If pair has 'id', use it; otherwise generate one
        composite_id = pair.get('id', f"composite_{i:03d}")
        
        # We need a target description or vector.
        # For sensitivity analysis, we need to query the DB.
        # We will assume the pair contains the necessary metadata to identify the target.
        
        task_def = {
            "task_id": task_id,
            "source_id": composite_id,
            "type": "composite",
            "description": f"Sensitivity analysis task for composite {composite_id}",
            "params": {
                "k_values": [1, 3, 5, 10]  # Standard sweep values for T031a
            }
        }
        
        # If the pair contains specific skill IDs, include them for reference
        if 'skill_a' in pair:
            task_def["params"]["base_skills"] = [pair['skill_a'], pair.get('skill_b', 'N/A')]
        
        eval_tasks.append(task_def)
    
    # If no pairs were loaded or processed, fall back to using individual skills from index
    # as single-skill evaluation tasks (k=1 case)
    if not eval_tasks and index_ids:
        logger.warning("No composite pairs found. Generating single-skill eval tasks.")
        for i, skill_id in enumerate(index_ids[:10]): # Limit to 10 for brevity
            task_def = {
                "task_id": f"eval_single_{i:03d}",
                "source_id": skill_id,
                "type": "single_skill",
                "description": f"Sensitivity analysis task for single skill {skill_id}",
                "params": {
                    "k_values": [1, 3, 5, 10]
                }
            }
            eval_tasks.append(task_def)

    return eval_tasks

def save_eval_tasks(tasks: List[Dict[str, Any]], output_path: Path):
    """
    Save the generated eval tasks to a YAML file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    output_data = {
        "generated_at": "T022e",
        "description": "Held-out set of task IDs for sensitivity analysis (US2)",
        "tasks": tasks
    }
    
    with open(output_path, 'w') as f:
        yaml.dump(output_data, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Saved {len(tasks)} eval tasks to {output_path}")

def main():
    """
    Main entry point for T022e.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    root = get_project_root()
    data_path = get_data_path()
    
    # Define paths
    index_path = data_path / "processed" / "skill_index.npz"
    pairs_path = data_path / "processed" / "known_composites_pairs.yaml"
    output_path = data_path / "processed" / "eval_tasks.yaml"
    
    # Ensure directories
    ensure_directories()
    
    logger.info("Starting T022e: Generate Eval Tasks for Sensitivity Analysis")
    
    try:
        # Load dependencies
        logger.info(f"Loading skill index from {index_path}...")
        skill_index = load_skill_index(index_path)
        index_ids = list(skill_index.keys())
        logger.info(f"Loaded {len(index_ids)} skills from index.")
        
        logger.info(f"Loading composite pairs from {pairs_path}...")
        pairs = load_composite_pairs(pairs_path)
        logger.info(f"Loaded {len(pairs)} composite pairs.")
        
        # Generate tasks
        logger.info("Generating held-out evaluation tasks...")
        eval_tasks = generate_held_out_tasks(index_ids, pairs)
        
        # Save
        logger.info(f"Saving eval tasks to {output_path}...")
        save_eval_tasks(eval_tasks, output_path)
        
        logger.info("T022e completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Missing required dependency: {e}")
        return 1
    except Exception as e:
        logger.error(f"Error during execution: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
