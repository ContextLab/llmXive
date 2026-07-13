import os
import json
import logging
import re
from typing import Dict, Any, List, Optional, Tuple, Set
from utils.validation import validate_explanation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def normalize_text(text: str) -> str:
    """
    Normalize text for comparison: lowercase, remove punctuation, collapse whitespace.
    """
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def calculate_jaccard_similarity(set1: Set[str], set2: Set[str]) -> float:
    """
    Calculate Jaccard similarity coefficient between two sets.
    Returns 0.0 if both sets are empty.
    """
    if not set1 and not set2:
        return 0.0
    if not set1 or not set2:
        return 0.0
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    if union == 0:
        return 0.0
    return intersection / union

def extract_symbolic_trace(explanation_data: Dict[str, Any]) -> str:
    """
    Extract the symbolic trace from an explanation data structure.
    The symbolic trace is expected to be in the 'symbolic_trace' field.
    """
    if not explanation_data:
        return ""
    
    # Try to get the symbolic trace directly
    if 'symbolic_trace' in explanation_data:
        trace = explanation_data['symbolic_trace']
        if isinstance(trace, list):
            return " ".join(str(step) for step in trace)
        return str(trace)
    
    # Fallback: look for rule applications
    if 'rule_applications' in explanation_data:
        rules = explanation_data['rule_applications']
        if isinstance(rules, list):
            return " ".join(str(rule) for rule in rules)
        return str(rules)
    
    return ""

def extract_neural_narrative(explanation_data: Dict[str, Any]) -> str:
    """
    Extract the neural narrative from an explanation data structure.
    The neural narrative is expected to be in the 'neural_narrative' or 'text' field.
    """
    if not explanation_data:
        return ""
    
    # Try primary field
    if 'neural_narrative' in explanation_data:
        narrative = explanation_data['neural_narrative']
        if isinstance(narrative, list):
            return " ".join(narrative)
        return str(narrative)
    
    # Fallback to 'text' field
    if 'text' in explanation_data:
        narrative = explanation_data['text']
        if isinstance(narrative, list):
            return " ".join(narrative)
        return str(narrative)
    
    return ""

def validate_symbolic_trace_structure(trace_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate that a symbolic trace has the expected structure:
    - Contains a list of rule applications
    - Each rule application has a 'rule_name' and 'description'
    - The trace is deterministic (no randomness)
    
    Returns (is_valid, error_message)
    """
    if not trace_data:
        return False, "Trace data is empty"
    
    required_fields = ['rule_applications', 'problem_id']
    for field in required_fields:
        if field not in trace_data:
            return False, f"Missing required field: {field}"
    
    rules = trace_data.get('rule_applications', [])
    if not isinstance(rules, list):
        return False, "rule_applications must be a list"
    
    if len(rules) == 0:
        return False, "rule_applications cannot be empty"
    
    for i, rule in enumerate(rules):
        if not isinstance(rule, dict):
            return False, f"Rule application at index {i} is not a dictionary"
        
        if 'rule_name' not in rule:
            return False, f"Rule application at index {i} missing 'rule_name'"
        
        if 'description' not in rule:
            return False, f"Rule application at index {i} missing 'description'"
    
    return True, "Valid symbolic trace structure"

def validate_distinctness(symbolic_trace: str, neural_narrative: str, threshold: float = 0.3) -> Tuple[bool, float, Dict[str, Any]]:
    """
    Validate that symbolic traces are distinct from neural outputs.
    
    This addresses Rockmore's concern about "concrete mathematical objects" by ensuring
    that the symbolic layer (rule-based, deterministic) is fundamentally different
    from the neural layer (statistical, narrative-based).
    
    Args:
        symbolic_trace: The extracted symbolic trace text
        neural_narrative: The extracted neural narrative text
        threshold: Maximum allowed Jaccard similarity (default 0.3)
    
    Returns:
        Tuple of (is_distinct, similarity_score, details_dict)
    """
    if not symbolic_trace or not neural_narrative:
        logger.warning("Empty symbolic trace or neural narrative provided")
        return False, 0.0, {"error": "Empty input"}
    
    # Normalize both texts
    norm_symbolic = normalize_text(symbolic_trace)
    norm_neural = normalize_text(neural_narrative)
    
    # Tokenize into sets of words
    words_symbolic = set(norm_symbolic.split())
    words_neural = set(norm_neural.split())
    
    # Calculate Jaccard similarity
    jaccard_sim = calculate_jaccard_similarity(words_symbolic, words_neural)
    
    # Check against threshold
    is_distinct = jaccard_sim < threshold
    
    details = {
        "jaccard_similarity": jaccard_sim,
        "threshold": threshold,
        "symbolic_word_count": len(words_symbolic),
        "neural_word_count": len(words_neural),
        "common_words": len(words_symbolic.intersection(words_neural)),
        "is_distinct": is_distinct
    }
    
    if not is_distinct:
        logger.warning(f"Symbolic and neural outputs too similar (Jaccard: {jaccard_sim:.3f} > {threshold})")
    else:
        logger.info(f"Symbolic and neural outputs are distinct (Jaccard: {jaccard_sim:.3f})")
    
    return is_distinct, jaccard_sim, details

def validate_explanation_pair(
    symbolic_explanation: Dict[str, Any],
    neuro_symbolic_explanation: Dict[str, Any],
    threshold: float = 0.3
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that a symbolic explanation and its corresponding neuro-symbolic explanation
    have distinct symbolic and neural components.
    
    This ensures that the neuro-symbolic approach doesn't merely add a narrative layer
    to the same underlying content, addressing the concern about "post-hoc rationalization".
    
    Args:
        symbolic_explanation: The purely symbolic explanation data
        neuro_symbolic_explanation: The neuro-symbolic explanation data
        threshold: Maximum allowed Jaccard similarity (default 0.3)
    
    Returns:
        Tuple of (is_valid, validation_report)
    """
    report = {
        "problem_id": symbolic_explanation.get("problem_id", "unknown"),
        "checks": []
    }
    
    # Extract components
    symbolic_trace = extract_symbolic_trace(symbolic_explanation)
    neural_narrative = extract_neural_narrative(neuro_symbolic_explanation)
    
    # Validate symbolic trace structure first
    trace_valid, trace_error = validate_symbolic_trace_structure(symbolic_explanation)
    if not trace_valid:
        report["checks"].append({
            "check": "symbolic_trace_structure",
            "passed": False,
            "error": trace_error
        })
        return False, report
    
    report["checks"].append({
        "check": "symbolic_trace_structure",
        "passed": True
    })
    
    # Validate distinctness
    is_distinct, similarity, details = validate_distinctness(
        symbolic_trace, neural_narrative, threshold
    )
    
    report["checks"].append({
        "check": "symbolic_neural_distinctness",
        "passed": is_distinct,
        "details": details
    })
    
    # Overall validation
    all_passed = all(check["passed"] for check in report["checks"])
    
    return all_passed, report

def main():
    """
    Main function to run distinctness validation on explanation pairs.
    This script is designed to be run as a standalone validation tool.
    """
    logger.info("Starting distinctness validation")
    
    # Example usage - in practice, this would load from files
    sample_symbolic = {
        "problem_id": "test_001",
        "rule_applications": [
            {"rule_name": "Commutativity", "description": "a + b = b + a"},
            {"rule_name": "Associativity", "description": "(a + b) + c = a + (b + c)"}
        ],
        "result": 10
    }
    
    sample_neuro_symbolic = {
        "problem_id": "test_001",
        "neural_narrative": "The solution involves rearranging the terms and grouping them appropriately.",
        "symbolic_trace": sample_symbolic["rule_applications"]
    }
    
    is_valid, report = validate_explanation_pair(sample_symbolic, sample_neuro_symbolic)
    
    print(json.dumps(report, indent=2))
    
    if not is_valid:
        logger.error("Validation failed")
        return 1
    
    logger.info("Validation passed")
    return 0

if __name__ == "__main__":
    exit(main())
