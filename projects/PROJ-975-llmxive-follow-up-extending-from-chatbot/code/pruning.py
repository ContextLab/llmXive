import numpy as np
from typing import List, Dict, Any, Tuple
from utils import cosine_similarity

def prune_fr04(library: List[Dict[str, Any]], tasks: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """
    Implements the corrected Skill Pruning heuristic FR-004.
    
    A skill is removed if it is unused (usage_count == 0) AND it is redundant.
    Redundancy is defined as having a cosine similarity > 0.70 with AT LEAST ONE 
    other skill currently in the library (max_cosine_similarity > 0.70).
    
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
            
            # Prune if the skill is highly similar to at least one other retained skill
            if sims and max(sims) > sim_threshold:
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
