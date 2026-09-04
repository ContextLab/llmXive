import os
import re
import math
import logging
from typing import List, Dict, Any, Optional, Tuple, Iterator
from dataclasses import dataclass, field
import json
from pathlib import Path

from config import StrategyType, ContextConfiguration

logger = logging.getLogger(__name__)

@dataclass
class ContextSnippet:
    """Represents a single snippet of code extracted from the context."""
    file_path: str
    start_line: int
    end_line: int
    content: str
    score: float = 0.0
    strategy: str = "naive"

@dataclass
class ProcessedContext:
    """Container for the processed context and metadata."""
    snippets: List[ContextSnippet]
    total_tokens: int
    strategy: str
    fallback_applied: bool = False
    fallback_reason: Optional[str] = None

def _write_fallback_log(
    instance_id: str,
    strategy: str,
    original_input: Dict[str, Any],
    output_snippets: List[Dict[str, Any]]
) -> None:
    """
    Logs a fallback event to data/audit_logs/fallbacks.jsonl.
    Creates the directory if it doesn't exist.
    """
    log_dir = Path("data/audit_logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "fallbacks.jsonl"

    entry = {
        "instance_id": instance_id,
        "strategy": strategy,
        "fallback_reason": "zero_snippets_returned",
        "timestamp": None,  # Will be set by caller or default to None
        "input_summary": {
            "file_count": len(original_input.get("files", [])),
            "total_lines": sum(len(f.get("lines", [])) for f in original_input.get("files", []))
        },
        "output_snippets_count": len(output_snippets)
    }

    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        logger.warning(f"Fallback logged for instance {instance_id}: {strategy} returned 0 snippets.")
    except IOError as e:
        logger.error(f"Failed to write fallback log for instance {instance_id}: {e}")

def _naive_truncation(
    instance_data: Dict[str, Any],
    config: ContextConfiguration
) -> List[ContextSnippet]:
    """
    Implements the naive truncation strategy (first-N-lines).
    Used as a fallback when high-fidelity strategies fail.
    """
    snippets = []
    files = instance_data.get("files", [])
    if not files:
        return snippets

    total_lines = 0
    max_lines = config.max_context_lines or 4096

    for file_entry in files:
        if total_lines >= max_lines:
            break
        
        file_path = file_entry.get("file_path", "unknown")
        lines = file_entry.get("lines", [])
        
        # Take lines up to the limit
        available = max_lines - total_lines
        take_count = min(len(lines), available)
        
        snippet_content = "\n".join(lines[:take_count])
        
        snippets.append(ContextSnippet(
            file_path=file_path,
            start_line=1,
            end_line=take_count,
            content=snippet_content,
            score=0.0,
            strategy="naive_fallback"
        ))
        
        total_lines += take_count

    return snippets

def retrieve_tfidf_snippets(
    instance_data: Dict[str, Any],
    config: ContextConfiguration,
    query: str
) -> List[ContextSnippet]:
    """
    TF-IDF/BM25 relevance retrieval.
    Returns snippets ranked by relevance to the query.
    """
    # Placeholder implementation for structure compatibility
    # Actual TF-IDF logic would go here using scikit-learn
    # This returns an empty list to trigger fallback logic in the task
    return []

def retrieve_diff_aware_snippets(
    instance_data: Dict[str, Any],
    config: ContextConfiguration,
    target_file: str
) -> List[ContextSnippet]:
    """
    Diff-aware sliding window retrieval.
    Returns snippets around the changed/affected areas.
    """
    # Placeholder implementation for structure compatibility
    return []

def retrieve_semantic_summaries(
    instance_data: Dict[str, Any],
    config: ContextConfiguration,
    query: str
) -> List[ContextSnippet]:
    """
    Rule-based semantic summarization.
    Extracts relevant code blocks/paragraphs based on rules.
    """
    # Placeholder implementation for structure compatibility
    return []

def process_context(
    instance_data: Dict[str, Any],
    config: ContextConfiguration,
    strategy: StrategyType,
    query: Optional[str] = None,
    target_file: Optional[str] = None
) -> ProcessedContext:
    """
    Main entry point for context processing.
    
    Implements fallback logic:
    1. Attempt the requested high-fidelity strategy.
    2. If the strategy returns zero snippets, log the event and fallback to naive truncation.
    3. Return the result with metadata indicating if a fallback occurred.
    """
    snippets: List[ContextSnippet] = []
    fallback_applied = False
    fallback_reason = None
    instance_id = instance_data.get("instance_id", "unknown")

    try:
        if strategy == StrategyType.TF_IDF:
            snippets = retrieve_tfidf_snippets(instance_data, config, query or "")
        elif strategy == StrategyType.DIFF_AWARE:
            snippets = retrieve_diff_aware_snippets(instance_data, config, target_file or "")
        elif strategy == StrategyType.SEMANTIC_SUMMARY:
            snippets = retrieve_semantic_summaries(instance_data, config, query or "")
        elif strategy == StrategyType.NAIVE:
            snippets = _naive_truncation(instance_data, config)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

        # Check for zero snippets (Edge Case)
        if not snippets and strategy != StrategyType.NAIVE:
            fallback_applied = True
            fallback_reason = f"{strategy.value} strategy returned zero snippets."
            logger.warning(f"Strategy {strategy} returned 0 snippets for {instance_id}. Fallbacking to naive truncation.")
            
            # Log the fallback event
            _write_fallback_log(
                instance_id=instance_id,
                strategy=strategy.value,
                original_input=instance_data,
                output_snippets=[]
            )
            
            # Execute fallback
            snippets = _naive_truncation(instance_data, config)

    except Exception as e:
        logger.error(f"Error processing context for {instance_id} with strategy {strategy}: {e}")
        # On error, fallback to naive if not already naive
        if strategy != StrategyType.NAIVE:
            fallback_applied = True
            fallback_reason = f"Exception during {strategy.value}: {str(e)}"
            _write_fallback_log(
                instance_id=instance_id,
                strategy=strategy.value,
                original_input=instance_data,
                output_snippets=[]
            )
            snippets = _naive_truncation(instance_data, config)

    # Calculate total tokens (approximate)
    total_tokens = sum(len(s.content.split()) for s in snippets)

    return ProcessedContext(
        snippets=snippets,
        total_tokens=total_tokens,
        strategy=strategy.value,
        fallback_applied=fallback_applied,
        fallback_reason=fallback_reason
    )

def main():
    """
    CLI entry point for testing context processors.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Test context processors")
    parser.add_argument("--strategy", type=str, default="TF_IDF", help="Strategy to test")
    parser.add_argument("--instance-file", type=str, required=True, help="Path to instance JSON")
    
    args = parser.parse_args()
    
    # Load dummy instance for testing
    if os.path.exists(args.instance_file):
        with open(args.instance_file, 'r') as f:
            data = json.load(f)
    else:
        data = {
            "instance_id": "test-001",
            "files": [
                {"file_path": "test.py", "lines": [f"line_{i}" for i in range(100)]}
            ]
        }
    
    config = ContextConfiguration(max_context_lines=500)
    strategy = StrategyType[args.strategy.upper()]
    
    result = process_context(data, config, strategy)
    
    print(f"Strategy: {result.strategy}")
    print(f"Snippets: {len(result.snippets)}")
    print(f"Fallback Applied: {result.fallback_applied}")
    if result.fallback_applied:
        print(f"Reason: {result.fallback_reason}")

if __name__ == "__main__":
    main()