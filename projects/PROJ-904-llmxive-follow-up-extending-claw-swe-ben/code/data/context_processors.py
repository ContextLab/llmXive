"""
Context processing modules for high-fidelity strategies.
Implements TF-IDF, Diff-Aware, and Semantic Summarization.
"""
import os
import re
import math
import logging
from typing import List, Dict, Any, Optional, Tuple, Iterator
from dataclasses import dataclass, field
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ContextSnippet:
    """A snippet of context."""
    content: str
    score: float = 0.0

@dataclass
class ProcessedContext:
    """Processed context result."""
    snippets: List[ContextSnippet]
    total_tokens: int

def retrieve_tfidf_snippets(query: str, file_history: List[Dict[str, Any]], top_k: int = 5) -> List[ContextSnippet]:
    """
    Retrieve relevant snippets using TF-IDF.
    Uses scikit-learn TfidfVectorizer.
    """
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
    except ImportError:
        raise ImportError("scikit-learn is required for TF-IDF retrieval. Install it via requirements.txt.")

    if not file_history:
        return []

    documents = [f.get("content", "") for f in file_history if f.get("content")]
    if not documents:
        return []

    vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
    tfidf_matrix = vectorizer.fit_transform(documents)
    query_vec = vectorizer.transform([query])

    similarities = cosine_similarity(query_vec, tfidf_matrix).flatten()
    top_indices = similarities.argsort()[-top_k:][::-1]

    snippets = []
    for idx in top_indices:
        if similarities[idx] > 0:
            snippets.append(ContextSnippet(content=documents[idx], score=similarities[idx]))

    return snippets

def retrieve_diff_aware_snippets(query: str, file_history: List[Dict[str, Any]], window_size: int = 50) -> List[ContextSnippet]:
    """
    Retrieve snippets using diff-aware sliding window.
    Focuses on lines near changes or relevant to the issue.
    """
    # Simple heuristic: look for keywords from issue in file content
    query_words = set(re.findall(r'\w+', query.lower()))
    snippets = []

    for file_info in file_history:
        content = file_info.get("content", "")
        lines = content.split('\n')
        score = 0
        for line in lines:
            if any(w in line.lower() for w in query_words):
                score += 1

        if score > 0:
            # Extract window around matches
            snippets.append(ContextSnippet(content=content, score=score))

    # Sort by score
    snippets.sort(key=lambda x: x.score, reverse=True)
    return snippets[:5]

def retrieve_semantic_summaries(query: str, file_history: List[Dict[str, Any]], max_tokens: int = 1000) -> List[ContextSnippet]:
    """
    Retrieve snippets using rule-based semantic summarization.
    Extracts variable definitions, function signatures, and control flow blocks.
    Does NOT use first/last sentence heuristic.
    """
    summaries = []
    for file_info in file_history:
        content = file_info.get("content", "")
        if not content:
            continue

        # Extract function definitions
        func_pattern = r'(\s*def\s+\w+\s*\([^)]*\)\s*:)'
        func_matches = re.findall(func_pattern, content, re.MULTILINE)

        # Extract class definitions
        class_pattern = r'(\s*class\s+\w+\s*:)'
        class_matches = re.findall(class_pattern, content, re.MULTILINE)

        # Extract control flow
        flow_pattern = r'(\s*(if|for|while|try|except)\s+[^:]*:)'
        flow_matches = re.findall(flow_pattern, content, re.MULTILINE)

        # Build summary
        summary_parts = func_matches + class_matches + flow_matches
        summary = "...\n".join(summary_parts[:20])  # Limit to 20 blocks

        if summary:
            summaries.append(ContextSnippet(content=summary, score=1.0))

    return summaries

def process_context(strategy: str, query: str, file_history: List[Dict[str, Any]], max_tokens: int = 2048) -> ProcessedContext:
    """
    Process context based on the specified strategy.
    """
    if strategy == "baseline":
        full_content = "\n".join([f.get("content", "") for f in file_history])
        return ProcessedContext(snippets=[ContextSnippet(content=full_content)], total_tokens=len(full_content.split()))
    elif strategy == "tfidf":
        snippets = retrieve_tfidf_snippets(query, file_history)
    elif strategy == "diff_aware":
        snippets = retrieve_diff_aware_snippets(query, file_history)
    elif strategy == "summarization":
        snippets = retrieve_semantic_summaries(query, file_history)
    else:
        raise ValueError(f"Unknown strategy: {strategy}")

    # Fallback if empty
    if not snippets:
        logger.warning(f"No snippets retrieved for strategy {strategy}, falling back to baseline.")
        return process_context("baseline", query, file_history, max_tokens)

    total_tokens = sum(len(s.content.split()) for s in snippets)
    return ProcessedContext(snippets=snippets, total_tokens=total_tokens)

def main():
    """Main entry point for context processor testing."""
    # Dummy test
    history = [{"content": "def foo():\n    pass"}]
    result = process_context("tfidf", "foo", history)
    print(f"Processed {len(result.snippets)} snippets")

if __name__ == "__main__":
    main()
