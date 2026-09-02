"""
Parse ROCStories corpus to extract or infer event boundaries.

This module implements task T019a:
- Reads data/text/rocstories_sample.jsonl (produced by T019)
- If 'event_boundaries' field exists, validates and uses it
- Otherwise, uses sentence segmentation to approximate boundaries
- Saves to data/text/rocstories_sample_boundaries.jsonl
"""
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import sys
import os

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging_config import get_logger, info, error, warning, log_error

logger = get_logger(__name__)


def detect_sentence_boundaries(text: str) -> List[int]:
    """
    Detect sentence boundaries using simple heuristics.
    
    Returns a list of character indices where sentences end.
    Handles common punctuation: . ! ?
    
    Args:
        text: Input story text
        
    Returns:
        List of character indices marking sentence endings
    """
    boundaries = []
    # Pattern matches sentence-ending punctuation followed by space or end of string
    pattern = r'[.!?](?:\s|$)'
    
    for match in re.finditer(pattern, text):
        boundaries.append(match.start())
    
    return boundaries


def infer_event_boundaries(text: str) -> List[Dict[str, Any]]:
    """
    Infer event boundaries from sentence segmentation.
    
    Approximates events by grouping sentences into chunks.
    Each event is represented as a boundary marker with start/end positions.
    
    Args:
        text: Input story text
        
    Returns:
        List of event boundary dictionaries with 'start', 'end', 'type' fields
    """
    if not text or not text.strip():
        return []
    
    sentence_ends = detect_sentence_boundaries(text)
    
    if not sentence_ends:
        # No sentence boundaries found, treat entire text as one event
        return [{
            'start': 0,
            'end': len(text),
            'type': 'sentence',
            'confidence': 0.5
        }]
    
    events = []
    start = 0
    
    for end_pos in sentence_ends:
        # Each sentence is treated as an event boundary
        events.append({
            'start': start,
            'end': end_pos + 1,  # Include the punctuation
            'type': 'sentence',
            'confidence': 0.8
        })
        start = end_pos + 1
    
    # Handle any remaining text after last sentence
    if start < len(text):
        events.append({
            'start': start,
            'end': len(text),
            'type': 'sentence',
            'confidence': 0.6
        })
    
    return events


def parse_rocstories_with_boundaries(
    input_path: str,
    output_path: str,
    force_reparse: bool = False
) -> int:
    """
    Parse ROCStories JSONL file and add event boundaries.
    
    Args:
        input_path: Path to input JSONL file (from T019)
        output_path: Path to output JSONL file
        force_reparse: If True, recompute boundaries even if they exist
        
    Returns:
        Number of stories processed
    """
    input_file = Path(input_path)
    output_file = Path(output_path)
    
    if not input_file.exists():
        error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    processed_count = 0
    
    logger.info(f"Reading stories from {input_path}")
    
    with open(input_file, 'r', encoding='utf-8') as infile:
        stories = []
        for line_num, line in enumerate(infile, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                story_data = json.loads(line)
            except json.JSONDecodeError as e:
                error(f"JSON decode error at line {line_num}: {e}")
                raise ValueError(f"Invalid JSON at line {line_num}: {e}")
            
            # Check if we need to parse boundaries
            has_boundaries = 'event_boundaries' in story_data
            
            if has_boundaries and not force_reparse:
                # Use existing boundaries if present and not forcing reparse
                info(f"Line {line_num}: Using existing event_boundaries")
            else:
                # Infer boundaries from text
                story_text = story_data.get('story', '')
                if not story_text:
                    warning(f"Line {line_num}: Missing 'story' field, skipping")
                    continue
                
                boundaries = infer_event_boundaries(story_text)
                story_data['event_boundaries'] = boundaries
                info(f"Line {line_num}: Inferred {len(boundaries)} event boundaries")
            
            stories.append(story_data)
            processed_count += 1
    
    # Write output
    logger.info(f"Writing {processed_count} stories to {output_path}")
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for story in stories:
            json.dump(story, outfile, ensure_ascii=False)
            outfile.write('\n')
    
    logger.info(f"Successfully processed {processed_count} stories")
    return processed_count


def validate_boundaries(input_path: str) -> bool:
    """
    Validate that the output file has correct structure.
    
    Args:
        input_path: Path to the output JSONL file
        
    Returns:
        True if validation passes, False otherwise
    """
    file_path = Path(input_path)
    
    if not file_path.exists():
        error(f"Output file not found: {input_path}")
        return False
    
    count = 0
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                error(f"Invalid JSON at line {line_num}")
                return False
            
            if 'event_boundaries' not in data:
                error(f"Missing 'event_boundaries' at line {line_num}")
                return False
            
            boundaries = data['event_boundaries']
            if not isinstance(boundaries, list):
                error(f"'event_boundaries' is not a list at line {line_num}")
                return False
            
            for i, boundary in enumerate(boundaries):
                if 'start' not in boundary or 'end' not in boundary:
                    error(f"Boundary {i} missing start/end at line {line_num}")
                    return False
                
                if not isinstance(boundary['start'], int) or not isinstance(boundary['end'], int):
                    error(f"Boundary {i} start/end not integers at line {line_num}")
                    return False
            
            count += 1
    
    logger.info(f"Validation passed for {count} stories")
    return True


def main():
    """Main entry point for event boundary parsing."""
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent
    input_path = project_root / "data" / "text" / "rocstories_sample.jsonl"
    output_path = project_root / "data" / "text" / "rocstories_sample_boundaries.jsonl"
    
    logger.info("Starting event boundary parsing (T019a)")
    
    try:
        processed = parse_rocstories_with_boundaries(
            str(input_path),
            str(output_path),
            force_reparse=False
        )
        
        logger.info(f"Processed {processed} stories")
        
        # Validate output
        if validate_boundaries(str(output_path)):
            logger.info("Validation successful")
        else:
            error("Validation failed")
            sys.exit(1)
            
    except FileNotFoundError as e:
        error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        error(f"Value error: {e}")
        sys.exit(1)
    except Exception as e:
        error(f"Unexpected error: {e}")
        log_error("E001", f"Unexpected error in T019a: {e}")
        sys.exit(1)
    
    logger.info("T019a completed successfully")


if __name__ == "__main__":
    main()
