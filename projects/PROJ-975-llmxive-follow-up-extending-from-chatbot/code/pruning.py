import numpy as np
from typing import List, Dict, Any, Tuple
from utils import cosine_similarity

def prune_fr04(library: List[Dict[str, Any]], tasks: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """
    Implements the Skill Pruning heuristic FR-004.
    
    Removes a skill only if:
    1. usage_count == 0
    2. min_cosine_similarity_to_any_other_skill_in_library > 0.70 (meaning it is redundant 
       relative to every other skill in the current library).
    
    Args:
        library: The current active skill library (list of skill dictionaries).
        tasks: The full set of tasks used to calculate false pruning.
        
    Returns:
        A tuple of (pruned_library, false_prune_count).
    """
    if len(library) < 2:
        # Cannot calculate similarity to others if only one skill exists
        return library, 0

    skills_to_remove = set()
    sim_threshold = 0.70

    # Identify candidates for pruning
    for i, skill_i in enumerate(library):
        if skill_i.get('usage_count', 0) == 0:
            # Calculate similarities to all other skills in the library
            sims = []
            vec_i = np.array(skill_i['embedding_vector'])
            
            for j, skill_j in enumerate(library):
                if i == j:
                    continue
                vec_j = np.array(skill_j['embedding_vector'])
                sims.append(cosine_similarity(vec_i, vec_j))
            
            # Prune only if the minimum similarity is above the threshold (redundant with all)
            if sims and min(sims) > sim_threshold:
                skills_to_remove.add(skill_i['skill_id'])

    # Calculate false_prune_count: pruned skills that are part of any task's ground truth
    false_prune_count = 0
    for skill_id in skills_to_remove:
        is_ground_truth = False
        for task in tasks:
            if skill_id in task.get('ground_truth_path', []):
                is_ground_truth = True
                break
        if is_ground_truth:
            false_prune_count += 1

    # Construct the pruned library
    pruned_library = [s for s in library if s['skill_id'] not in skills_to_remove]
    
    return pruned_library, false_prune_count
