import json
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from code.config.settings import get_paths, ensure_directories
from code.src.detection.schema import LLMCodeDetectionResult, ConfidenceLevel

logger = logging.getLogger(__name__)

# Heuristic patterns for LLM-generated code
# Based on common artifacts found in LLM output
HEURISTIC_PATTERNS = [
    # Common LLM explanations in comments
    r'# Here is a function to...',
    r'# This function calculates...',
    r'# This method handles...',
    r'# The following code implements...',
    r'# We use this to...',
    r'# Note: This code was generated...',
    r'# Implementation of...',
    r'# Helper function for...',
    r'# Utility function to...',
    
    # Structured patterns often seen in LLM output
    r'```python',
    r'```java',
    r'```javascript',
    r'```typescript',
    r'```c',
    r'```cpp',
    
    # Generic boilerplate often added by LLMs
    r'# TODO: Implement this',
    r'# FIXME: This needs work',
    r'# XXX: Review this',
    r'# WARNING: Check this',
    
    # Comment patterns indicating generated code
    r'# Generated code',
    r'# AI generated',
    r'# LLM generated',
    r'# Model output',
]

# Regex for detecting "Here is" style introductions in comments
INTRO_PATTERNS = [
    r'# Here is the code',
    r'# Here is the implementation',
    r'# Here is the function',
    r'# Here is the class',
    r'# Here is the solution',
    r'# Below is the code',
    r'# Below is the implementation',
]

# Patterns for code blocks that look like they were pasted from an LLM
CODE_BLOCK_PATTERNS = [
    r'```.*\n[\s\S]*?\n```',  # Markdown code blocks
]

def calculate_confidence(matches: List[str], total_lines: int, diff_hunks: int) -> float:
    """
    Calculate confidence score for LLM-generated code detection.
    
    Args:
        matches: List of matched heuristic patterns
        total_lines: Total number of lines in the diff
        diff_hunks: Number of diff hunks
        
    Returns:
        Confidence score between 0.0 and 1.0
    """
    if total_lines == 0:
        return 0.0
    
    # Base confidence from pattern matches
    match_ratio = len(matches) / max(total_lines, 1)
    
    # Adjust for number of hunks (more hunks with matches = higher confidence)
    hunk_factor = min(diff_hunks / 5.0, 1.0)  # Normalize around 5 hunks
    
    # Weighted combination
    confidence = 0.6 * match_ratio + 0.4 * hunk_factor
    
    # Cap at 1.0
    return min(confidence, 1.0)

def detect_llm_generated_code(diff_text: str) -> Tuple[bool, ConfidenceLevel, List[str]]:
    """
    Detect if a diff contains LLM-generated code using heuristics.
    
    Args:
        diff_text: The raw diff text from a PR
        
    Returns:
        Tuple of (is_llm_generated, confidence_level, matched_patterns)
    """
    matches = []
    lines = diff_text.split('\n')
    total_lines = len(lines)
    
    # Check each line for heuristic patterns
    for line in lines:
        line_lower = line.lower()
        for pattern in HEURISTIC_PATTERNS:
            if re.search(pattern, line_lower, re.IGNORECASE):
                if pattern not in matches:
                    matches.append(pattern)
                    break
        
        # Check intro patterns
        for intro_pattern in INTRO_PATTERNS:
            if re.search(intro_pattern, line_lower, re.IGNORECASE):
                if intro_pattern not in matches:
                    matches.append(intro_pattern)
                    break
        
        # Check code block patterns
        for block_pattern in CODE_BLOCK_PATTERNS:
            if re.search(block_pattern, line, re.IGNORECASE):
                if block_pattern not in matches:
                    matches.append(block_pattern)
                    break
    
    # Count diff hunks
    diff_hunks = diff_text.count('@@') // 2  # Each hunk has two @@ markers (start/end)
    diff_hunks = max(diff_hunks, 1)
    
    # Calculate confidence
    confidence_score = calculate_confidence(matches, total_lines, diff_hunks)
    
    # Map score to confidence level
    if confidence_score >= 0.8:
        confidence_level = ConfidenceLevel.HIGH
    elif confidence_score >= 0.5:
        confidence_level = ConfidenceLevel.MEDIUM
    elif confidence_score >= 0.2:
        confidence_level = ConfidenceLevel.LOW
    else:
        confidence_level = ConfidenceLevel.NONE
    
    is_llm_generated = confidence_level in [ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM]
    
    return is_llm_generated, confidence_level, matches

def process_pr_diffs(pr_data: List[Dict[str, Any]]) -> List[LLMCodeDetectionResult]:
    """
    Process PR data to detect LLM-generated code in diffs.
    
    Args:
        pr_data: List of PR dictionaries with 'diff' field
        
    Returns:
        List of LLMCodeDetectionResult objects
    """
    results = []
    
    for pr in pr_data:
        pr_id = pr.get('pr_id', 'unknown')
        repo = pr.get('repo', 'unknown')
        diff_text = pr.get('diff', '')
        
        if not diff_text:
            logger.warning(f"No diff found for PR {pr_id} in {repo}")
            result = LLMCodeDetectionResult(
                pr_id=pr_id,
                repo=repo,
                llm_code_flag=False,
                confidence=ConfidenceLevel.NONE,
                matched_patterns=[],
                file_paths=[],
                error_message=None
            )
            results.append(result)
            continue
        
        try:
            is_llm, confidence, patterns = detect_llm_generated_code(diff_text)
            
            # Extract file paths from diff if possible
            file_paths = []
            for line in diff_text.split('\n'):
                if line.startswith('diff --git'):
                    # Extract file path from diff header
                    parts = line.split(' ')
                    if len(parts) >= 3:
                        file_path = parts[2].lstrip('b/')
                        file_paths.append(file_path)
            
            result = LLMCodeDetectionResult(
                pr_id=pr_id,
                repo=repo,
                llm_code_flag=is_llm,
                confidence=confidence,
                matched_patterns=patterns,
                file_paths=file_paths,
                error_message=None
            )
            results.append(result)
            
            if is_llm:
                logger.info(f"Detected LLM code in PR {pr_id} ({repo}) with {confidence.value} confidence")
            
        except Exception as e:
            logger.error(f"Error processing PR {pr_id}: {str(e)}")
            result = LLMCodeDetectionResult(
                pr_id=pr_id,
                repo=repo,
                llm_code_flag=False,
                confidence=ConfidenceLevel.NONE,
                matched_patterns=[],
                file_paths=[],
                error_message=str(e)
            )
            results.append(result)
    
    return results

def main():
    """Main entry point for LLM code detection."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get paths
    paths = get_paths()
    ensure_directories()
    
    # Load raw PR data
    raw_data_path = paths['data_raw'] / 'pr_data.json'
    
    if not raw_data_path.exists():
        logger.error(f"Raw PR data not found at {raw_data_path}")
        return
    
    logger.info(f"Loading PR data from {raw_data_path}")
    
    with open(raw_data_path, 'r', encoding='utf-8') as f:
        pr_data = json.load(f)
    
    logger.info(f"Loaded {len(pr_data)} PRs")
    
    # Process PRs
    results = process_pr_diffs(pr_data)
    
    # Save results
    output_path = paths['data_derived'] / 'llm_detections.json'
    
    logger.info(f"Saving detection results to {output_path}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump([result.to_dict() for result in results], f, indent=2)
    
    # Summary
    llm_count = sum(1 for r in results if r.llm_code_flag)
    total_count = len(results)
    
    logger.info(f"Detection complete: {llm_count}/{total_count} PRs flagged as LLM-generated")
    logger.info(f"Results saved to {output_path}")

if __name__ == '__main__':
    main()
