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

def _extract_first_sentences(text: str) -> List[str]:
    """
    Extract the first sentence of every paragraph.
    Paragraphs are separated by double newlines.
    """
    paragraphs = text.split('\n\n')
    sentences = []
    # Simple sentence splitter: split on ., !, ?
    sentence_enders = re.compile(r'([.!?])\s+')
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        # Find the first sentence
        match = sentence_enders.search(para)
        if match:
            first_sent = para[:match.end()].strip()
            if first_sent:
                sentences.append(first_sent)
        else:
            # If no sentence ender, take the whole paragraph as a "sentence"
            if para:
                sentences.append(para)
    return sentences

def _extract_last_function_sentences(text: str) -> List[str]:
    """
    Extract the last sentence of every function block.
    Function blocks are defined by 'def ' keyword and indentation.
    """
    lines = text.split('\n')
    function_blocks = []
    current_block = []
    in_function = False
    base_indent = 0

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_function:
                current_block.append(line)
            continue

        # Detect function definition
        if re.match(r'^def\s+\w+\s*\(', line):
            if in_function and current_block:
                function_blocks.append('\n'.join(current_block))
            in_function = True
            current_block = [line]
            # Determine base indent (though 'def' usually starts at 0 or module level)
            base_indent = len(line) - len(line.lstrip())
        elif in_function:
            # Check if we are still inside the function (indentation > base)
            current_indent = len(line) - len(line.lstrip())
            if current_indent > base_indent or stripped.startswith('def '):
                # If we hit a new 'def' at same level, it's a new function (handled above)
                # If indentation is greater, we are inside
                current_block.append(line)
            else:
                # Indentation dropped, function ended
                if current_block:
                    function_blocks.append('\n'.join(current_block))
                in_function = False
                current_block = []
                # Re-evaluate current line if it's code
                if stripped:
                    # This line belongs to the next block (not function)
                    pass

    if in_function and current_block:
        function_blocks.append('\n'.join(current_block))

    last_sentences = []
    sentence_enders = re.compile(r'([.!?])\s+')

    for block in function_blocks:
        block_text = block.strip()
        if not block_text:
            continue
        
        # Find the last sentence in the block
        # We look for the last occurrence of a sentence ender
        matches = list(sentence_enders.finditer(block_text))
        if matches:
            last_match = matches[-1]
            last_sent = block_text[last_match.start():last_match.end()].strip()
            if last_sent:
                last_sentences.append(last_sent)
        else:
            # If no sentence ender, take the last line or whole block
            lines_in_block = block_text.split('\n')
            if lines_in_block:
                last_sentences.append(lines_in_block[-1].strip())

    return last_sentences

def retrieve_semantic_summaries(query: str, file_history: List[Dict[str, Any]], max_tokens: int = 1000) -> List[ContextSnippet]:
    """
    Retrieve snippets using rule-based semantic summarization.
    Logic:
    1. Extract the first sentence of every paragraph.
    2. Extract the last sentence of every function block (defined by indentation or 'def').
    3. Concatenate with '...' separator.
    4. Truncate to context window (max_tokens approximated by word count).
    """
    summaries = []
    
    for file_info in file_history:
        content = file_info.get("content", "")
        if not content:
            continue

        # 1. First sentences of paragraphs
        first_sents = _extract_first_sentences(content)
        
        # 2. Last sentences of function blocks
        last_func_sents = _extract_last_function_sentences(content)
        
        # Combine
        all_parts = first_sents + last_func_sents
        
        if not all_parts:
            continue

        # Join with '...'
        summary_text = "...".join(all_parts)
        
        # Truncate to max_tokens (approximate: 1 token ~ 1 word for this heuristic)
        words = summary_text.split()
        if len(words) > max_tokens:
            words = words[:max_tokens]
            summary_text = " ".join(words)
        
        if summary_text.strip():
            summaries.append(ContextSnippet(content=summary_text, score=1.0))

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
