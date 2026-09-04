"""
Data loading and processing module.

Contains loaders for SWE-bench datasets and context processing utilities.
"""
from data.loader import ClawSweBenchLoader, ParsedIssue
from data.context_processors import (
    ContextSnippet,
    ProcessedContext,
    retrieve_tfidf_snippets,
    retrieve_diff_aware_snippets,
    retrieve_semantic_summaries,
    process_context
)

__all__ = [
    'ClawSweBenchLoader',
    'ParsedIssue',
    'ContextSnippet',
    'ProcessedContext',
    'retrieve_tfidf_snippets',
    'retrieve_diff_aware_snippets',
    'retrieve_semantic_summaries',
    'process_context'
]
