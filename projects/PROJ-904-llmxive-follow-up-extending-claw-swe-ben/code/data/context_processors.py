import os
import re
import math
import logging
import difflib
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
except ImportError:
    TfidfVectorizer = None

@dataclass
class ContextSnippet:
    content: str
    score: float
    source: str

@dataclass
class ProcessedContext:
    snippets: List[ContextSnippet]
    total_tokens: int

def log_fallback(strategy: str, reason: str):
    logging.warning(f"Fallback to {strategy}: {reason}")

def retrieve_tfidf_snippets(text: str, query: str, top_k: int = 5) -> List[ContextSnippet]:
    if TfidfVectorizer is None:
        raise ImportError("scikit-learn is required for TF-IDF retrieval")
    
    vectorizer = TfidfVectorizer(sublinear_tf=True, max_df=0.95)
    try:
        tfidf_matrix = vectorizer.fit_transform([text, query])
        scores = tfidf_matrix[0].toarray()[0, 1:]
        # Simplified snippet extraction
        return [ContextSnippet(content=text[:100], score=scores[0], source="tfidf")]
    except Exception as e:
        logging.error(f"TF-IDF retrieval failed: {e}")
        return []

def retrieve_diff_aware_snippets(text: str, keywords: List[str] = None) -> List[ContextSnippet]:
    if not keywords:
        keywords = ['fix', 'bug', 'error', 'TODO']
    
    snippets = []
    for kw in keywords:
        if kw in text.lower():
            snippets.append(ContextSnippet(content=f"...{kw}...", score=1.0, source="diff_aware"))
    return snippets

def retrieve_semantic_summaries(text: str) -> List[ContextSnippet]:
    # First sentence of paragraph, last sentence of function
    paragraphs = text.split('\n\n')
    snippets = []
    for para in paragraphs:
        sentences = para.split('.')
        if sentences:
            snippets.append(ContextSnippet(content=sentences[0], score=0.5, source="summary"))
    return snippets

def fallback_strategy(retrieved: List[ContextSnippet], full_text: str) -> List[ContextSnippet]:
    if not retrieved:
        log_fallback("first_n_lines", "No snippets retrieved")
        return [ContextSnippet(content=full_text[:500], score=0.0, source="fallback")]
    return retrieved

def process_context(text: str, strategy: str, config: Dict[str, Any]) -> ProcessedContext:
    snippets = []
    if strategy == "tfidf":
        snippets = retrieve_tfidf_snippets(text, config.get("query", ""), config.get("top_k", 5))
    elif strategy == "diff_aware":
        snippets = retrieve_diff_aware_snippets(text, config.get("keywords"))
    elif strategy == "semantic_summary":
        snippets = retrieve_semantic_summaries(text)
    
    if not snippets:
        snippets = fallback_strategy(snippets, text)
    
    total_tokens = sum(len(s.content.split()) for s in snippets)
    return ProcessedContext(snippets=snippets, total_tokens=total_tokens)

def main():
    logging.basicConfig(level=logging.INFO)
    text = "This is a test code block with some keywords like fix and bug."
    result = process_context(text, "tfidf", {"query": "test", "top_k": 3})
    logging.info(f"Processed context: {len(result.snippets)} snippets")

if __name__ == "__main__":
    main()
