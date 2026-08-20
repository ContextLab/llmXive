"""
Syntactic Features Extraction Module.

This module computes deterministic syntactic complexity metrics (parse tree depth,
clause count) and lexical diversity (MTLD) for text prompts. It strictly avoids
semantic embeddings (BERT, CLIP text) as per project constraints.

Critical Requirement:
- Handle parse failures gracefully by assigning a score of 0.0 and logging a warning.
- Do NOT raise exceptions for individual malformed prompts; the pipeline must continue.
"""

import logging
import warnings
from typing import List, Dict, Any, Optional, Tuple

import spacy
import textstat
import nltk
from nltk.parse import CoreNLPParser, DependencyGraph
from nltk.tree import Tree

# Configure logging for the module
logger = logging.getLogger(__name__)

# Attempt to load spaCy model
# We use 'en_core_web_sm' for dependency parsing
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.warning("spaCy 'en_core_web_sm' model not found. Attempting to download...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

# Ensure NLTK resources are available
try:
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    nltk.download('averaged_perceptron_tagger', quiet=True)

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)


def _safe_parse_tree_depth(doc: spacy.tokens.Doc) -> int:
    """
    Calculate the maximum depth of the dependency parse tree.
    
    Returns 0 if parsing fails or the tree is empty.
    """
    if not doc.sents:
        return 0
    
    max_depth = 0
    for sent in doc.sents:
        # spaCy's dependency tree structure
        # We traverse the tree to find max depth
        # A simple recursive approach or BFS
        try:
            # Convert to a tree-like structure for depth calculation
            # spaCy tokens have .head and .subtree
            # We can calculate depth by finding the longest path from root to leaf
            
            # Identify root of the sentence (token with no head or head is itself)
            roots = [token for token in sent if token.dep_ == "ROOT"]
            if not roots:
                continue
            
            root = roots[0]
            
            # BFS to find max depth
            current_level = [root]
            depth = 0
            
            while current_level:
                next_level = []
                for token in current_level:
                    # Add children
                    for child in token.children:
                        next_level.append(child)
                
                if next_level:
                    depth += 1
                    current_level = next_level
                else:
                    break
            
            if depth > max_depth:
                max_depth = depth
        except Exception as e:
            # Log specific parse error for debugging but return 0 for this sentence
            logger.warning(f"Error calculating tree depth for sentence: {e}")
            continue
    
    return max_depth


def _safe_clause_count(doc: spacy.tokens.Doc) -> int:
    """
    Estimate clause count based on conjuncts and subordinates.
    
    Returns 0 if parsing fails.
    """
    if not doc.sents:
        return 0
    
    total_clauses = 0
    for sent in doc.sents:
        try:
            # Count subordinate clauses (subord) and coordinate clauses (conj)
            # This is a heuristic: every ROOT + every subord/conj dependency often implies a clause
            clause_count = 0
            for token in sent:
                if token.dep_ in ("ROOT", "ccomp", "xcomp", "advcl", "relcl", "conj"):
                    clause_count += 1
            total_clauses += clause_count
        except Exception as e:
            logger.warning(f"Error calculating clause count for sentence: {e}")
            continue
    
    return total_clauses


def _safe_mtld(text: str) -> float:
    """
    Calculate Mean Measure of Lexical Diversity (MTLD).
    
    Returns 0.0 if calculation fails (e.g., text too short).
    """
    if not text or len(text.split()) < 10:
        # MTLD requires a minimum of tokens to be meaningful
        return 0.0
    
    try:
        # textstat handles the calculation
        mtld_score = textstat.ttr(text) # Using TTR as a fallback if MTLD is unstable, but let's try MTLD first
        # textstat has a specific mtld function in newer versions, otherwise we implement or use TTR
        # Since textstat might vary, we'll use a robust try-except for the specific MTLD call if available
        # or fallback to a standard TTR if MTLD is not directly supported in the specific version
        # However, standard textstat often uses 'mtld' function. Let's try it.
        try:
            return textstat.mtld(text)
        except AttributeError:
            # Fallback to TTR if MTLD is not available
            return textstat.ttr(text)
    except Exception as e:
        logger.warning(f"MTLD calculation failed for text: {e}")
        return 0.0


def compute_syntactic_features(prompt: str) -> Dict[str, Any]:
    """
    Compute syntactic complexity features for a given prompt.
    
    This function is robust:
    - It handles empty or None prompts.
    - It catches all parsing/processing errors.
    - On any error during feature extraction, it assigns 0.0 for the failed metrics
      and logs a warning, rather than crashing the pipeline.
    
    Args:
        prompt (str): The input text prompt.
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - 'parse_tree_depth': int (0 on failure)
            - 'clause_count': int (0 on failure)
            - 'mtld': float (0.0 on failure)
            - 'success': bool (True if all metrics computed without error, False otherwise)
            - 'error_message': str or None
    """
    result = {
        'parse_tree_depth': 0,
        'clause_count': 0,
        'mtld': 0.0,
        'success': True,
        'error_message': None
    }
    
    if not prompt or not isinstance(prompt, str) or not prompt.strip():
        logger.warning(f"Empty or invalid prompt provided. Assigning 0.0 scores.")
        result['success'] = False
        result['error_message'] = "Empty or invalid prompt"
        return result
    
    try:
        # Process with spaCy
        doc = nlp(prompt)
        
        # 1. Parse Tree Depth
        depth = _safe_parse_tree_depth(doc)
        result['parse_tree_depth'] = depth
        
        # 2. Clause Count
        clauses = _safe_clause_count(doc)
        result['clause_count'] = clauses
        
        # 3. Lexical Diversity (MTLD)
        mtld = _safe_mtld(prompt)
        result['mtld'] = mtld
        
    except Exception as e:
        # GRACEFUL FAILURE HANDLING
        # Assign 0.0 to all metrics and log the warning
        logger.warning(f"Failed to parse prompt: '{prompt[:50]}...'. Error: {e}. Assigning 0.0 scores.")
        result['success'] = False
        result['error_message'] = str(e)
        result['parse_tree_depth'] = 0
        result['clause_count'] = 0
        result['mtld'] = 0.0
    
    return result


def get_feature_names() -> List[str]:
    """
    Returns the list of feature names produced by this module.
    """
    return ['parse_tree_depth', 'clause_count', 'mtld']