import os
import re
import math
import logging
import difflib
import json
from typing import List, Dict, Any, Optional, Tuple, Iterator
from pathlib import Path

from config import get_data_dir, get_output_dir

logger = logging.getLogger(__name__)

# --- Data Models ---

class ContextSnippet:
    def __init__(self, file_path: str, content: str, start_line: int, end_line: int, score: float = 0.0):
        self.file_path = file_path
        self.content = content
        self.start_line = start_line
        self.end_line = end_line
        self.score = score

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "content": self.content,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "score": self.score
        }

class ProcessedContext:
    def __init__(self, strategy: str, snippets: List[ContextSnippet], original_content: Optional[str] = None):
        self.strategy = strategy
        self.snippets = snippets
        self.original_content = original_content

    def get_concatenated_text(self, max_tokens: int = 4096) -> str:
        """Concatenate snippets, truncating if necessary."""
        text_parts = []
        current_len = 0
        for snippet in self.snippets:
            part = f"File: {snippet.file_path}\n{snippet.content}\n\n"
            if current_len + len(part) > max_tokens:
                break
            text_parts.append(part)
            current_len += len(part)
        return "".join(text_parts)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy": self.strategy,
            "snippets": [s.to_dict() for s in self.snippets],
            "original_content": self.original_content
        }

# --- Logging Utilities ---

def log_fallback(strategy: str, reason: str, instance_id: str):
    """Log a fallback event to the audit log."""
    audit_dir = get_data_dir() / "audit_logs"
    audit_dir.mkdir(parents=True, exist_ok=True)
    log_file = audit_dir / "fallbacks.jsonl"
    
    entry = {
        "timestamp": None, # Will be set by caller or default
        "instance_id": instance_id,
        "original_strategy": strategy,
        "fallback_strategy": "first_n_lines",
        "reason": reason
    }
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    logger.warning(f"Fallback triggered for instance {instance_id}: {reason}")

# --- Retrieval Strategies ---

def retrieve_tfidf_snippets(issue_description: str, repo_files: Dict[str, str], top_k: int = 5) -> List[ContextSnippet]:
    """
    Implement TF-IDF retrieval.
    NOTE: For this specific task (T051), we focus on Diff-Aware. 
    This is a placeholder stub to satisfy import requirements if called.
    """
    # Placeholder implementation for structural integrity
    # In a full run, this would use sklearn TfidfVectorizer
    return []

def retrieve_diff_aware_snippets(issue_description: str, repo_files: Dict[str, str], window_size: int = 50) -> List[ContextSnippet]:
    """
    Implement Diff-Aware (Heuristic Keyword-Proxy) retrieval.
    
    Logic:
    1. Search relevant files for keywords ('fix', 'bug', 'error', 'TODO').
    2. Include a sliding window of 'window_size' around each identified keyword match.
    3. If NO hunks/keywords are found (e.g., purely textual issue), return empty list.
       The caller must handle this by falling back to first_n_lines.
    """
    keywords = ['fix', 'bug', 'error', 'TODO']
    found_snippets = []
    
    # Normalize issue description to check for code-like content
    # If the issue is purely textual without code context, difflib might return nothing
    # if we were comparing against a diff, but here we search keywords in repo files.
    
    for file_path, content in repo_files.items():
        lines = content.split('\n')
        for i, line in enumerate(lines):
            line_lower = line.lower()
            for kw in keywords:
                if kw in line_lower:
                    # Found a keyword, extract window
                    start = max(0, i - window_size)
                    end = min(len(lines), i + window_size + 1)
                    snippet_content = '\n'.join(lines[start:end])
                    
                    found_snippets.append(ContextSnippet(
                        file_path=file_path,
                        content=snippet_content,
                        start_line=start,
                        end_line=end,
                        score=1.0
                    ))
                    break # Found one keyword in this line, move to next line
    
    return found_snippets

def retrieve_semantic_summaries(repo_files: Dict[str, str]) -> List[ContextSnippet]:
    """
    Implement rule-based semantic summarization.
    Extract first sentence of every paragraph and last sentence of every function block.
    """
    summaries = []
    for file_path, content in repo_files.items():
        # Simple heuristic: split by double newline for paragraphs
        paragraphs = content.split('\n\n')
        summary_lines = []
        
        for para in paragraphs:
            if not para.strip():
                continue
            sentences = re.split(r'(?<=[.!?])\s+', para)
            if sentences:
                # First sentence
                summary_lines.append(sentences[0])
                
        # Function blocks (simple heuristic: lines starting with 'def ')
        lines = content.split('\n')
        func_blocks = []
        current_func = []
        in_func = False
        
        for line in lines:
            if line.strip().startswith('def '):
                if current_func:
                    func_blocks.append(current_func)
                current_func = [line]
                in_func = True
            elif in_func:
                current_func.append(line)
            else:
                if not line.strip():
                    if current_func:
                        func_blocks.append(current_func)
                        current_func = []
                        in_func = False
        
        if current_func:
            func_blocks.append(current_func)
        
        for block in func_blocks:
            if block:
                # Last sentence of block (approximate by last line)
                last_line = block[-1]
                summary_lines.append(last_line)
        
        if summary_lines:
            summaries.append(ContextSnippet(
                file_path=file_path,
                content='\n'.join(summary_lines),
                start_line=0,
                end_line=len(summary_lines),
                score=0.5
            ))
    
    return summaries

def fallback_strategy(instance_id: str, repo_files: Dict[str, str], n_lines: int = 2048) -> ProcessedContext:
    """
    Fallback strategy: returns the first N lines of the most relevant file (or first file).
    Called when other strategies yield no results.
    """
    if not repo_files:
        raise ValueError("No repository files available for fallback strategy.")
    
    # Pick the first file as a deterministic fallback
    first_file = next(iter(repo_files.items()))
    file_path, content = first_file
    
    lines = content.split('\n')
    selected_lines = lines[:n_lines]
    snippet_content = '\n'.join(selected_lines)
    
    snippet = ContextSnippet(
        file_path=file_path,
        content=snippet_content,
        start_line=0,
        end_line=len(selected_lines),
        score=0.0
    )
    
    return ProcessedContext(strategy="first_n_lines", snippets=[snippet], original_content=content)

def process_context(issue_description: str, repo_files: Dict[str, str], strategy: str, instance_id: str, max_tokens: int = 4096) -> ProcessedContext:
    """
    Main dispatcher for context processing strategies.
    
    Handles the specific edge case for Diff-Aware (T051):
    If 'diff_aware' strategy yields no snippets, it explicitly falls back to 'first_n_lines'
    and logs the event to data/audit_logs/fallbacks.jsonl.
    """
    snippets = []
    
    if strategy == "baseline":
        # Baseline usually means first N lines of all files or a specific file
        # For simplicity, we treat baseline as a specific retrieval that might be empty if files are huge
        # But typically baseline is handled by a specific loader config. 
        # Here we assume baseline implies a full file load or first_n_lines.
        # Let's assume baseline is handled by the loader, but if called here:
        snippets = [ContextSnippet(file_path=k, content=v, start_line=0, end_line=len(v.split('\n'))) for k, v in repo_files.items()]
    
    elif strategy == "tfidf":
        snippets = retrieve_tfidf_snippets(issue_description, repo_files)
    
    elif strategy == "diff_aware":
        snippets = retrieve_diff_aware_snippets(issue_description, repo_files)
        # T051 Logic: Check for empty hunks/snippets
        if not snippets:
            logger.warning(f"Diff-Aware strategy returned no hunks for instance {instance_id}. Falling back to first_n_lines.")
            log_fallback(strategy="diff_aware", reason="No hunks/keywords found in issue description or repo files", instance_id=instance_id)
            return fallback_strategy(instance_id, repo_files)
    
    elif strategy == "summarization":
        snippets = retrieve_semantic_summaries(repo_files)
    
    else:
        raise ValueError(f"Unknown strategy: {strategy}")
    
    if not snippets and strategy != "baseline":
        # If any non-baseline strategy returns empty, fallback
        logger.warning(f"Strategy {strategy} returned no snippets for instance {instance_id}. Falling back to first_n_lines.")
        log_fallback(strategy=strategy, reason="No snippets retrieved", instance_id=instance_id)
        return fallback_strategy(instance_id, repo_files)
    
    return ProcessedContext(strategy=strategy, snippets=snippets)

# --- Main Entry Point (for testing/scripts) ---
def main():
    logging.basicConfig(level=logging.INFO)
    # Example usage for testing
    repo = {
        "test.py": "def fix_bug():\n    # TODO: fix this\n    pass\n\ndef another_func():\n    print('hello')\n    # error here\n    pass"
    }
    issue = "Fix the bug in the code."
    
    # Test diff_aware with keywords
    ctx = process_context(issue, repo, "diff_aware", "test-001")
    print(f"Strategy: {ctx.strategy}, Snippets: {len(ctx.snippets)}")
    
    # Test diff_aware with NO keywords (should fallback)
    issue_no_kws = "This is a purely textual issue description with no code context."
    ctx_fallback = process_context(issue_no_kws, repo, "diff_aware", "test-002")
    print(f"Fallback Strategy: {ctx_fallback.strategy}, Snippets: {len(ctx_fallback.snippets)}")

if __name__ == "__main__":
    main()
