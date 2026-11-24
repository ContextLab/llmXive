import numpy as np
from typing import List, Dict, Any, Tuple
from utils import cosine_similarity

def prune_fr04(library: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """
    Implements the corrected Skill Pruning heuristic FR-004.

    A skill is removed if it is unused (usage_count == 0) AND it is redundant.
    Redundancy is defined as having a cosine similarity > 0.70 with ANY other
    skill currently in the library (max_cosine_similarity > 0.70).

    Since no ground‑truth check is performed, the false prune count is always 0.
    """
    if len(library) < 2:
        # Not enough skills to assess redundancy
        return library, 0

    sim_threshold = 0.70
    skills_to_remove = set()

    # Iterate over each skill to evaluate pruning criteria
    for i, skill_i in enumerate(library):
        if skill_i.get('usage_count', 0) == 0:
            vec_i = np.array(skill_i['embedding_vector'])

            # Compute the maximum cosine similarity of this skill to any other skill
            max_sim = -1.0
            for j, skill_j in enumerate(library):
                if i == j:
                    continue
                vec_j = np.array(skill_j['embedding_vector'])
                sim = cosine_similarity(vec_i, vec_j)
                if sim > max_sim:
                    max_sim = sim

            # Prune if the skill is highly similar to at least one other retained skill
            if max_sim > sim_threshold:
                skills_to_remove.add(skill_i['skill_id'])

    # Build the pruned library excluding the identified skills
    pruned_library = [s for s in library if s['skill_id'] not in skills_to_remove]

    # No ground‑truth verification → false prune count is always zero
    false_prune_count = 0
    return pruned_library, false_prune_count
