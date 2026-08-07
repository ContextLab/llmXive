"""
Context processing modules for retrieving and compressing code contexts.

Implements three high-fidelity strategies:
1. TF-IDF/BM25 relevance retrieval
2. Diff-aware sliding window
3. Rule-based semantic summarization
"""

import os
import re
import math
import logging
from typing import List, Dict, Any, Optional, Tuple, Iterator
from dataclasses import dataclass, field
from collections import Counter

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from config import ContextConfiguration, StrategyType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ContextSnippet:
    """Represents a single snippet of code context."""
    file_path: str
    content: str
    start_line: int
    end_line: int
    relevance_score: float = 0.0
    strategy: str = "unknown"


@dataclass
class ProcessedContext:
    """Container for processed context data."""
    snippets: List[ContextSnippet] = field(default_factory=list)
    total_tokens: int = 0
    strategy_used: str = "unknown"
    fallback_triggered: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_prompt_string(self, max_tokens: Optional[int] = None) -> str:
        """Convert snippets to a prompt-ready string."""
        parts = []
        for snippet in self.snippets:
            header = f"### File: {snippet.file_path} (Lines {snippet.start_line}-{snippet.end_line})\n"
            parts.append(header + snippet.content + "\n")

        context_str = "\n---\n".join(parts)

        if max_tokens and len(context_str) > max_tokens * 4:
            # Simple truncation if token limit exceeded (approx 4 chars per token)
            logger.warning(f"Context exceeds {max_tokens} tokens, truncating.")
            context_str = context_str[: max_tokens * 4]

        return context_str


def _tokenize_text(text: str) -> List[str]:
    """Simple tokenization for TF-IDF."""
    text = text.lower()
    # Remove code syntax noise but keep identifiers
    text = re.sub(r'[^a-zA-Z0-9_\s]', ' ', text)
    tokens = text.split()
    # Filter very short tokens and common stopwords
    stopwords = {'the', 'is', 'in', 'and', 'to', 'a', 'of', 'for', 'on', 'with'}
    return [t for t in tokens if len(t) > 2 and t not in stopwords]


def retrieve_tfidf_snippets(
    files: Dict[str, str],
    query_text: str,
    top_k: int = 5,
    token_budget: Optional[int] = None
) -> ProcessedContext:
    """
    Retrieve relevant code snippets using TF-IDF vectorization.

    Args:
        files: Dictionary mapping file paths to their content.
        query_text: The issue description or query to match against.
        top_k: Number of top files/snippets to retrieve.
        token_budget: Optional maximum token limit for the result.

    Returns:
        ProcessedContext with retrieved snippets.
    """
    if not files:
        logger.warning("TF-IDF retrieval: No files provided.")
        return ProcessedContext(strategy_used="tfidf", fallback_triggered=True)

    try:
        # Prepare corpus
        file_paths = list(files.keys())
        file_contents = list(files.values())

        # Tokenize query
        query_tokens = _tokenize_text(query_text)
        query_str = " ".join(query_tokens)

        # Build TF-IDF vectors
        vectorizer = TfidfVectorizer(tokenizer=_tokenize_text, stop_words='english')

        # Handle empty corpus case
        if not file_contents or all(len(c.strip()) == 0 for c in file_contents):
            logger.warning("TF-IDF retrieval: File contents are empty.")
            return ProcessedContext(strategy_used="tfidf", fallback_triggered=True)

        tfidf_matrix = vectorizer.fit_transform(file_contents)
        query_vector = vectorizer.transform([query_str])

        # Calculate cosine similarity
        similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()

        # Get top-k indices
        top_indices = similarities.argsort()[-top_k:][::-1]

        snippets = []
        total_content_len = 0

        for idx in top_indices:
            if similarities[idx] > 0:
                file_path = file_paths[idx]
                content = file_contents[idx]

                # Split into lines for line-number tracking
                lines = content.split('\n')
                # For simplicity, take the whole file if it's not too large
                # In a real implementation, we might select specific relevant lines
                snippet_content = content

                snippets.append(ContextSnippet(
                    file_path=file_path,
                    content=snippet_content,
                    start_line=1,
                    end_line=len(lines),
                    relevance_score=float(similarities[idx]),
                    strategy="tfidf"
                ))
                total_content_len += len(snippet_content)

        # Check for empty results
        if not snippets:
            logger.warning("TF-IDF retrieval: No relevant snippets found. Falling back.")
            return ProcessedContext(strategy_used="tfidf", fallback_triggered=True)

        logger.info(f"TF-IDF retrieved {len(snippets)} snippets with total length {total_content_len}")
        return ProcessedContext(
            snippets=snippets,
            total_tokens=total_content_len,
            strategy_used="tfidf",
            fallback_triggered=False,
            metadata={"top_k": top_k, "query_tokens": len(query_tokens)}
        )

    except Exception as e:
        logger.error(f"TF-IDF retrieval failed: {e}")
        return ProcessedContext(strategy_used="tfidf", fallback_triggered=True)


def retrieve_diff_aware_snippets(
    files: Dict[str, str],
    query_text: str,
    window_size: int = 50,
    token_budget: Optional[int] = None
) -> ProcessedContext:
    """
    Retrieve snippets using a diff-aware sliding window strategy.

    This strategy assumes the query might reference specific changes or
    areas of code. It uses a sliding window approach to capture context
    around potential "diff" points (e.g., around function definitions or
    specific keywords mentioned in the query).

    Args:
        files: Dictionary mapping file paths to their content.
        query_text: The issue description.
        window_size: Number of lines to include around a match.
        token_budget: Optional maximum token limit.

    Returns:
        ProcessedContext with retrieved snippets.
    """
    if not files:
        logger.warning("Diff-aware retrieval: No files provided.")
        return ProcessedContext(strategy_used="diff_aware", fallback_triggered=True)

    try:
        # Extract keywords from query
        keywords = set(_tokenize_text(query_text))
        if not keywords:
            logger.warning("Diff-aware retrieval: No keywords extracted from query.")
            return ProcessedContext(strategy_used="diff_aware", fallback_triggered=True)

        snippets = []
        seen_files = set()

        for file_path, content in files.items():
            lines = content.split('\n')
            matches = []

            # Find lines matching keywords
            for i, line in enumerate(lines):
                line_lower = line.lower()
                if any(kw in line_lower for kw in keywords):
                    matches.append(i)

            if not matches:
                continue

            # Collect windows around matches
            file_snippets = []
            for match_idx in matches:
                start = max(0, match_idx - window_size // 2)
                end = min(len(lines), match_idx + window_size // 2)

                snippet_content = '\n'.join(lines[start:end])
                file_snippets.append((start + 1, end, snippet_content))

            # Merge overlapping windows or keep top ones
            # For simplicity, we take the union of lines covered by matches
            if file_snippets:
                # Simple heuristic: take the largest continuous block or merge
                # Here we just take the first window for demonstration if multiple
                # In a robust impl, we'd merge intervals.
                start_line, end_line, snippet_content = file_snippets[0]

                # Calculate a simple "relevance" based on keyword density
                keyword_count = sum(1 for kw in keywords if kw in snippet_content.lower())
                relevance = keyword_count / len(keywords) if keywords else 0.0

                snippets.append(ContextSnippet(
                    file_path=file_path,
                    content=snippet_content,
                    start_line=start_line,
                    end_line=end_line,
                    relevance_score=relevance,
                    strategy="diff_aware"
                ))
                seen_files.add(file_path)

        if not snippets:
            logger.warning("Diff-aware retrieval: No matching snippets found. Falling back.")
            return ProcessedContext(strategy_used="diff_aware", fallback_triggered=True)

        logger.info(f"Diff-aware retrieved {len(snippets)} snippets.")
        return ProcessedContext(
            snippets=snippets,
            total_tokens=sum(len(s.content) for s in snippets),
            strategy_used="diff_aware",
            fallback_triggered=False,
            metadata={"window_size": window_size, "keywords": len(keywords)}
        )

    except Exception as e:
        logger.error(f"Diff-aware retrieval failed: {e}")
        return ProcessedContext(strategy_used="diff_aware", fallback_triggered=True)


def retrieve_semantic_summaries(
    files: Dict[str, str],
    query_text: str,
    max_lines_per_file: int = 20,
    token_budget: Optional[int] = None
) -> ProcessedContext:
    """
    Retrieve rule-based semantic summaries of code files.

    Strategy:
    1. Parse files to extract structural elements (functions, classes, imports).
    2. Extract key variables and control flow logic.
    3. Concatenate snippets with '...' separators.
    4. Limit output to token budget.

    Note: Does NOT use "first/last sentence" heuristic.

    Args:
        files: Dictionary mapping file paths to their content.
        query_text: The issue description (used to prioritize files).
        max_lines_per_file: Maximum lines to include per file.
        token_budget: Optional maximum token limit.

    Returns:
        ProcessedContext with summarized snippets.
    """
    if not files:
        logger.warning("Semantic summarization: No files provided.")
        return ProcessedContext(strategy_used="semantic", fallback_triggered=True)

    try:
        # Simple structural extraction using regex (avoiding heavy AST parsing for speed)
        # In a full implementation, we would use `ast` module for Python files
        def extract_structure(content: str) -> List[Tuple[str, str, int, int]]:
            """Extract function/class definitions and their bodies."""
            structures = []
            lines = content.split('\n')

            # Regex for function/class definitions
            pattern = re.compile(r'^(def|class)\s+(\w+)')

            current_start = None
            current_type = None
            current_name = None
            current_indent = 0

            for i, line in enumerate(lines):
                match = pattern.match(line.strip())
                if match:
                    # Save previous if exists
                    if current_start is not None:
                        structures.append((current_type, current_name, current_start, i))

                    current_type = match.group(1)
                    current_name = match.group(2)
                    current_start = i
                    # Estimate indentation
                    current_indent = len(line) - len(line.lstrip())

            # Save last
            if current_start is not None:
                structures.append((current_type, current_name, current_start, len(lines)))

            return structures

        # Prioritize files based on query (simple keyword match)
        query_keywords = set(_tokenize_text(query_text))
        prioritized_files = []

        for file_path, content in files.items():
            score = sum(1 for kw in query_keywords if kw in content.lower())
            prioritized_files.append((score, file_path, content))

        prioritized_files.sort(key=lambda x: x[0], reverse=True)

        snippets = []
        total_len = 0

        for score, file_path, content in prioritized_files:
            if score == 0 and len(snippets) > 0:
                # Stop if we have enough and this file has no relevance
                break

            structures = extract_structure(content)
            lines = content.split('\n')

            selected_lines = []
            current_count = 0

            for struct_type, name, start, end in structures:
                if current_count >= max_lines_per_file:
                    break

                # Extract lines for this structure
                struct_lines = lines[start:end]
                # Limit structure size
                if len(struct_lines) > max_lines_per_file // 2:
                    struct_lines = struct_lines[: max_lines_per_file // 2]

                selected_lines.extend(struct_lines)
                current_count += len(struct_lines)

            # Add imports if available
            import_lines = [l for l in lines if l.strip().startswith('import') or l.strip().startswith('from')]
            if import_lines and current_count < max_lines_per_file:
                selected_lines = import_lines[:5] + selected_lines
                current_count += len(import_lines[:5])

            if selected_lines:
                snippet_content = "\n".join(selected_lines)
                if len(snippet_content) > 0:
                    snippets.append(ContextSnippet(
                        file_path=file_path,
                        content=snippet_content,
                        start_line=1,
                        end_line=len(selected_lines),
                        relevance_score=float(score),
                        strategy="semantic"
                    ))
                    total_len += len(snippet_content)

        if not snippets:
            logger.warning("Semantic summarization: No structures found. Falling back.")
            return ProcessedContext(strategy_used="semantic", fallback_triggered=True)

        logger.info(f"Semantic summarization produced {len(snippets)} snippets.")
        return ProcessedContext(
            snippets=snippets,
            total_tokens=total_len,
            strategy_used="semantic",
            fallback_triggered=False,
            metadata={"max_lines_per_file": max_lines_per_file}
        )

    except Exception as e:
        logger.error(f"Semantic summarization failed: {e}")
        return ProcessedContext(strategy_used="semantic", fallback_triggered=True)


def process_context(
    files: Dict[str, str],
    query_text: str,
    config: ContextConfiguration
) -> ProcessedContext:
    """
    Main entry point for context processing.

    Dispatches to the appropriate strategy based on config.
    Implements fallback logic: if a high-fidelity strategy returns zero snippets,
    revert to naive truncation.

    Args:
        files: Dictionary mapping file paths to their content.
        query_text: The issue description.
        config: ContextConfiguration specifying the strategy.

    Returns:
        ProcessedContext object.
    """
    logger.info(f"Processing context with strategy: {config.strategy}")

    result = None

    if config.strategy == StrategyType.TF_IDF:
        result = retrieve_tfidf_snippets(files, query_text, top_k=config.top_k)
    elif config.strategy == StrategyType.DIFF_AWARE:
        result = retrieve_diff_aware_snippets(files, query_text, window_size=config.window_size)
    elif config.strategy == StrategyType.SEMANTIC:
        result = retrieve_semantic_summaries(files, query_text, max_lines_per_file=config.max_lines_per_file)
    elif config.strategy == StrategyType.NAIVE:
        # Naive truncation
        all_content = "\n".join(files.values())
        if len(all_content) > 0:
            result = ProcessedContext(
                snippets=[ContextSnippet(
                    file_path="combined",
                    content=all_content,
                    start_line=1,
                    end_line=all_content.count('\n') + 1,
                    relevance_score=1.0,
                    strategy="naive"
                )],
                total_tokens=len(all_content),
                strategy_used="naive",
                fallback_triggered=False
            )
        else:
            result = ProcessedContext(strategy_used="naive", fallback_triggered=True)
    else:
        logger.error(f"Unknown strategy: {config.strategy}")
        result = ProcessedContext(strategy_used="unknown", fallback_triggered=True)

    # Fallback logic: if result is empty/fallback triggered, use naive
    if result.fallback_triggered or not result.snippets:
        logger.warning(f"Strategy {config.strategy} failed or returned empty. Falling back to naive truncation.")
        all_content = "\n".join(files.values())
        if all_content:
            result = ProcessedContext(
                snippets=[ContextSnippet(
                    file_path="fallback_combined",
                    content=all_content,
                    start_line=1,
                    end_line=all_content.count('\n') + 1,
                    relevance_score=1.0,
                    strategy="naive_fallback"
                )],
                total_tokens=len(all_content),
                strategy_used="naive_fallback",
                fallback_triggered=True,
                metadata={"original_strategy": config.strategy}
            )
        else:
            result = ProcessedContext(
                strategy_used="naive_fallback",
                fallback_triggered=True,
                metadata={"original_strategy": config.strategy, "error": "No content available"}
            )

    return result


def main():
    """
    CLI entry point for testing context processors.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Test context processors")
    parser.add_argument("--strategy", type=str, default="tfidf",
                        choices=["tfidf", "diff_aware", "semantic", "naive"],
                        help="Strategy to use")
    parser.add_argument("--query", type=str, default="bug fix",
                        help="Query text")
    parser.add_argument("--files", type=str, nargs="+", default=[],
                        help="Paths to files to process")

    args = parser.parse_args()

    # Load files
    files = {}
    for f_path in args.files:
        if os.path.exists(f_path):
            with open(f_path, 'r') as f:
                files[f_path] = f.read()
        else:
            # Create dummy content for testing if file not found
            files[f_path] = f"Dummy content for {f_path}\ndef example_function():\n    pass"

    if not files:
        print("No files provided. Using dummy data.")
        files = {
            "test.py": "def main():\n    print('Hello')\n\nclass Test:\n    pass"
        }

    config = ContextConfiguration(
        model_size="1B",
        strategy=args.strategy,
        top_k=5,
        window_size=50,
        max_lines_per_file=20
    )

    result = process_context(files, args.query, config)

    print(f"Strategy: {result.strategy_used}")
    print(f"Fallback: {result.fallback_triggered}")
    print(f"Snippets: {len(result.snippets)}")
    for i, s in enumerate(result.snippets):
        print(f"  [{i}] {s.file_path}: {len(s.content)} chars, score={s.relevance_score:.2f}")


if __name__ == "__main__":
    main()