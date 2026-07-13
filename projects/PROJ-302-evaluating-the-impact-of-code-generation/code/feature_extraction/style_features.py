"""
Feature extraction module for computing style metrics required for classification (FR-009).

This module calculates various code style metrics including indentation patterns,
naming conventions, line length distribution, and comment density.
These metrics are used as covariates for propensity score matching and
classification of code snippets as LLM-like or Human.

Output: Updates `data/processed/generated_snippets.parquet` with new style columns.
"""
import os
import sys
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Pattern
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "generated_snippets.parquet"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "generated_snippets.parquet"

# Regex patterns for style analysis
INDENT_PATTERN: Pattern = re.compile(r'^(\s+)')
LINE_LENGTH_PATTERN: Pattern = re.compile(r'^.{100,}$')
NAME_PATTERN: Pattern = re.compile(r'^[a-z_][a-z0-9_]*$')  # snake_case
UPPER_NAME_PATTERN: Pattern = re.compile(r'^[A-Z][A-Z0-9_]*$')  # UPPER_CASE
CAMEL_NAME_PATTERN: Pattern = re.compile(r'^[a-z][a-zA-Z0-9]*$')  # camelCase
PASCAL_NAME_PATTERN: Pattern = re.compile(r'^[A-Z][a-zA-Z0-9]*$')  # PascalCase

def calculate_indentation_consistency(lines: List[str]) -> float:
    """
    Calculate indentation consistency score (0.0 to 1.0).
    Higher score means more consistent indentation.
    """
    if not lines:
        return 0.0
    
    indents = []
    for line in lines:
        if line.strip():
            match = INDENT_PATTERN.match(line)
            if match:
                indents.append(len(match.group(1)))
    
    if not indents:
        return 1.0  # No indented lines, consider consistent
    
    # Calculate variance normalized by mean
    mean_indent = np.mean(indents)
    if mean_indent == 0:
        return 1.0
    
    variance = np.var(indents)
    cv = np.sqrt(variance) / mean_indent  # Coefficient of variation
    
    # Convert to consistency score (1.0 - normalized CV)
    # Cap at 0 for very inconsistent
    score = max(0.0, 1.0 - cv)
    return min(1.0, score)

def calculate_line_length_stats(lines: List[str]) -> Dict[str, float]:
    """
    Calculate line length statistics.
    """
    if not lines:
        return {
            'mean_line_length': 0.0,
            'max_line_length': 0.0,
            'long_lines_ratio': 0.0,
            'std_line_length': 0.0
        }
    
    lengths = [len(line) for line in lines]
    long_lines = sum(1 for l in lengths if l > 100)
    
    return {
        'mean_line_length': float(np.mean(lengths)),
        'max_line_length': float(max(lengths)),
        'long_lines_ratio': float(long_lines / len(lines)),
        'std_line_length': float(np.std(lengths))
    }

def calculate_naming_convention_distribution(lines: List[str]) -> Dict[str, float]:
    """
    Calculate distribution of naming conventions used in the code.
    """
    # Extract potential identifiers
    identifiers = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', '\n'.join(lines))
    
    if not identifiers:
        return {
            'snake_case_ratio': 0.0,
            'camel_case_ratio': 0.0,
            'pascal_case_ratio': 0.0,
            'upper_case_ratio': 0.0,
            'mixed_case_ratio': 0.0
        }
    
    snake_count = sum(1 for name in identifiers if NAME_PATTERN.match(name) and '_' in name)
    camel_count = sum(1 for name in identifiers if CAMEL_NAME_PATTERN.match(name))
    pascal_count = sum(1 for name in identifiers if PASCAL_NAME_PATTERN.match(name))
    upper_count = sum(1 for name in identifiers if UPPER_NAME_PATTERN.match(name))
    
    total = len(identifiers)
    
    return {
        'snake_case_ratio': float(snake_count / total),
        'camel_case_ratio': float(camel_count / total),
        'pascal_case_ratio': float(pascal_count / total),
        'upper_case_ratio': float(upper_count / total),
        'mixed_case_ratio': float(1.0 - (snake_count + camel_count + pascal_count + upper_count) / total)
    }

def calculate_comment_density(lines: List[str]) -> float:
    """
    Calculate comment density (ratio of comment lines to total lines).
    """
    if not lines:
        return 0.0
    
    comment_lines = 0
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('#') or stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('**'):
            comment_lines += 1
    
    return float(comment_lines / len(lines))

def calculate_blank_line_ratio(lines: List[str]) -> float:
    """
    Calculate ratio of blank lines to total lines.
    """
    if not lines:
        return 0.0
    
    blank_lines = sum(1 for line in lines if not line.strip())
    return float(blank_lines / len(lines))

def calculate_function_length_distribution(lines: List[str]) -> Dict[str, float]:
    """
    Estimate function length distribution based on blank line separators.
    """
    if not lines:
        return {
            'avg_function_length': 0.0,
            'max_function_length': 0.0,
            'function_count': 0.0
        }
    
    # Simple heuristic: group lines by blank lines
    blocks = []
    current_block = []
    
    for line in lines:
        if not line.strip():
            if current_block:
                blocks.append(len(current_block))
                current_block = []
        else:
            current_block.append(line)
    
    if current_block:
        blocks.append(len(current_block))
    
    if not blocks:
        return {
            'avg_function_length': 0.0,
            'max_function_length': 0.0,
            'function_count': 0.0
        }
    
    return {
        'avg_function_length': float(np.mean(blocks)),
        'max_function_length': float(max(blocks)),
        'function_count': float(len(blocks))
    }

def extract_style_features(code_text: str) -> Dict[str, Any]:
    """
    Extract all style features from a code snippet.
    
    Args:
        code_text: The code snippet as a string
        
    Returns:
        Dictionary of style metrics
    """
    if not code_text or not code_text.strip():
        return {
            'style_indentation_consistency': 0.0,
            'style_mean_line_length': 0.0,
            'style_max_line_length': 0.0,
            'style_long_lines_ratio': 0.0,
            'style_std_line_length': 0.0,
            'style_snake_case_ratio': 0.0,
            'style_camel_case_ratio': 0.0,
            'style_pascal_case_ratio': 0.0,
            'style_upper_case_ratio': 0.0,
            'style_mixed_case_ratio': 0.0,
            'style_comment_density': 0.0,
            'style_blank_line_ratio': 0.0,
            'style_avg_function_length': 0.0,
            'style_max_function_length': 0.0,
            'style_function_count': 0.0,
            'total_lines': 0
        }
    
    lines = code_text.split('\n')
    
    # Calculate all metrics
    indentation_consistency = calculate_indentation_consistency(lines)
    line_length_stats = calculate_line_length_stats(lines)
    naming_distribution = calculate_naming_convention_distribution(lines)
    comment_density = calculate_comment_density(lines)
    blank_line_ratio = calculate_blank_line_ratio(lines)
    function_length_dist = calculate_function_length_distribution(lines)
    
    return {
        'style_indentation_consistency': indentation_consistency,
        'style_mean_line_length': line_length_stats['mean_line_length'],
        'style_max_line_length': line_length_stats['max_line_length'],
        'style_long_lines_ratio': line_length_stats['long_lines_ratio'],
        'style_std_line_length': line_length_stats['std_line_length'],
        'style_snake_case_ratio': naming_distribution['snake_case_ratio'],
        'style_camel_case_ratio': naming_distribution['camel_case_ratio'],
        'style_pascal_case_ratio': naming_distribution['pascal_case_ratio'],
        'style_upper_case_ratio': naming_distribution['upper_case_ratio'],
        'style_mixed_case_ratio': naming_distribution['mixed_case_ratio'],
        'style_comment_density': comment_density,
        'style_blank_line_ratio': blank_line_ratio,
        'style_avg_function_length': function_length_dist['avg_function_length'],
        'style_max_function_length': function_length_dist['max_function_length'],
        'style_function_count': function_length_dist['function_count'],
        'total_lines': len(lines)
    }

def process_dataset(
    input_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    batch_size: int = 100
) -> pd.DataFrame:
    """
    Process a dataset of code snippets and extract style features.
    
    Args:
        input_path: Path to input parquet file (default: generated_snippets.parquet)
        output_path: Path to output parquet file (default: same as input)
        batch_size: Number of rows to process at once
        
    Returns:
        DataFrame with added style features
    """
    if input_path is None:
        input_path = INPUT_PATH
    if output_path is None:
        output_path = OUTPUT_PATH
        
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading dataset from {input_path}")
    df = pd.read_parquet(input_path)
    
    # Check for required column
    if 'code_content' not in df.columns and 'content' not in df.columns:
        raise ValueError("Dataset must contain 'code_content' or 'content' column")
    
    code_col = 'code_content' if 'code_content' in df.columns else 'content'
    logger.info(f"Processing {len(df)} rows using column '{code_col}'")
    
    # Extract style features for each row
    all_features = []
    
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i+batch_size]
        logger.info(f"Processing batch {i//batch_size + 1} ({len(batch)} rows)")
        
        for idx, row in batch.iterrows():
            code_text = row[code_col] if pd.notna(row[code_col]) else ""
            features = extract_style_features(str(code_text))
            all_features.append(features)
    
    # Create DataFrame of features
    features_df = pd.DataFrame(all_features)
    
    # Combine with original data
    result_df = pd.concat([df.reset_index(drop=True), features_df], axis=1)
    
    logger.info(f"Extracted {len(features_df.columns)} style features")
    logger.info(f"Saving result to {output_path}")
    
    # Save to parquet
    result_df.to_parquet(output_path, index=False)
    
    logger.info(f"Successfully processed {len(result_df)} rows")
    return result_df

def main():
    """Main entry point for style feature extraction."""
    logger.info("Starting style feature extraction (T017)")
    
    try:
        df = process_dataset()
        
        # Print summary statistics
        style_cols = [col for col in df.columns if col.startswith('style_')]
        logger.info(f"Style columns added: {style_cols}")
        
        if len(df) > 0:
            logger.info("Sample feature values:")
            sample = df[style_cols].iloc[0].to_dict()
            for k, v in sample.items():
                logger.info(f"  {k}: {v:.4f}" if isinstance(v, float) else f"  {k}: {v}")
        
        logger.info("T017 completed successfully")
        
    except Exception as e:
        logger.error(f"Error during style feature extraction: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()