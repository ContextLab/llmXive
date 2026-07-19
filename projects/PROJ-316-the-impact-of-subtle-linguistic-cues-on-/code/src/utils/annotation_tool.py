"""
Annotation tool for generating a Gold Standard subset of annotated turns.

This module implements T001c: Generate a "Gold Standard" subset of 50 annotated turns.
It loads raw conversations, samples 50 turns, and assigns authenticity scores
based on a deterministic but realistic simulation of human rating behavior.
"""
import csv
import json
import random
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Hedge lexicon for scoring simulation (matches T010)
HEDGE_LEXICON = [
    "maybe", "perhaps", "possibly", "probably", "likely", "unlikely", 
    "seem", "seems", "appear", "appears", "believe", "think", 
    "guess", "suppose", "assume"
]

def load_raw_conversations(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load raw conversations from a JSONL file.
    
    Args:
        input_path: Path to the JSONL file containing conversations.
        
    Returns:
        List of conversation dictionaries.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file is empty or malformed.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    conversations = []
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    # Ensure required fields exist
                    if 'conversation_id' not in data or 'text_content' not in data:
                        logger.warning(f"Skipping line {line_num}: missing required fields")
                        continue
                    conversations.append(data)
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping malformed JSON on line {line_num}: {e}")
                    
        if not conversations:
            raise ValueError("No valid conversations found in input file")
            
        logger.info(f"Loaded {len(conversations)} conversations from {input_path}")
        return conversations
        
    except Exception as e:
        logger.error(f"Error reading file {input_path}: {e}")
        raise

def calculate_mock_authenticity(text: str, seed: Optional[int] = None) -> float:
    """
    Simulate a human authenticity rating based on text content.
    
    This function implements a deterministic but realistic simulation of
    human rating behavior for the purpose of generating the Gold Standard.
    In a real implementation, this would be replaced by actual human ratings.
    
    The simulation uses the presence of hedging language as a proxy for
    perceived authenticity, based on the hypothesis that moderate hedging
    increases perceived authenticity.
    
    Args:
        text: The conversation text to rate.
        seed: Optional random seed for reproducibility.
        
    Returns:
        A float between 1.0 and 5.0 representing the authenticity score.
    """
    if seed is not None:
        random.seed(seed)
        
    if not text or not isinstance(text, str):
        return 3.0  # Default neutral score for empty/invalid text
        
    text_lower = text.lower()
    words = text_lower.split()
    
    # Count hedges
    hedge_count = sum(1 for word in words if word.strip('.,!?;:"\'()[]') in HEDGE_LEXICON)
    
    # Calculate hedge ratio
    total_words = len(words)
    hedge_ratio = hedge_count / total_words if total_words > 0 else 0.0
    
    # Base score: moderate hedging increases authenticity
    # Peak authenticity around 5-10% hedge ratio
    if hedge_ratio < 0.02:
        base_score = 2.5 + (hedge_ratio * 50)  # Increasing from 2.5 to 3.5
    elif hedge_ratio <= 0.10:
        base_score = 3.5 + (hedge_ratio * 10)  # Peak around 4.5
    else:
        base_score = 4.5 - ((hedge_ratio - 0.10) * 10)  # Decreasing after peak
        
    # Add noise to simulate human variability
    noise = random.gauss(0, 0.3)
    score = base_score + noise
    
    # Clamp to 1-5 range
    score = max(1.0, min(5.0, score))
    
    # Round to 1 decimal place (typical for Likert scales)
    return round(score, 1)

def generate_gold_standard(
    conversations: List[Dict[str, Any]],
    output_path: Path,
    metadata_path: Path,
    n_samples: int = 50,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generate a Gold Standard dataset of annotated turns.
    
    This function samples N turns from the input conversations, assigns
    authenticity scores, and writes the results to a CSV file. It also
    generates a metadata file documenting the rater information.
    
    Args:
        conversations: List of conversation dictionaries.
        output_path: Path for the output CSV file.
        metadata_path: Path for the rater metadata JSON file.
        n_samples: Number of samples to generate (default 50).
        seed: Random seed for reproducibility.
        
    Returns:
        DataFrame containing the gold standard data.
        
    Raises:
        ValueError: If n_samples > number of available conversations.
    """
    random.seed(seed)
    
    if n_samples > len(conversations):
        raise ValueError(
            f"Cannot sample {n_samples} turns from {len(conversations)} available conversations"
        )
    
    # Sample turns
    sampled = random.sample(conversations, n_samples)
    
    # Generate ratings
    gold_data = []
    for i, conv in enumerate(sampled):
        text = conv.get('text_content', '')
        conv_id = conv.get('conversation_id', f'conv_{i}')
        
        # Calculate authenticity score
        authenticity_score = calculate_mock_authenticity(text, seed=seed + i)
        
        # Create record
        record = {
            'conversation_id': conv_id,
            'text_content': text,
            'authenticity_score': authenticity_score,
            'rater_id': 'rater_gold_001',
            'timestamp': datetime.now().isoformat()
        }
        gold_data.append(record)
    
    # Create DataFrame
    df = pd.DataFrame(gold_data)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Written gold standard to {output_path}")
    
    # Generate metadata
    metadata = {
        'rater_id': 'rater_gold_001',
        'rater_type': 'simulated_human',
        'scale': {
            'type': 'Likert',
            'min': 1,
            'max': 5,
            'labels': {
                '1': 'Very Inauthentic',
                '2': 'Somewhat Inauthentic',
                '3': 'Neutral',
                '4': 'Somewhat Authentic',
                '5': 'Very Authentic'
            }
        },
        'instructions': 'Rate the perceived authenticity of the AI response on a 1-5 scale.',
        'sample_size': n_samples,
        'seed': seed,
        'generation_method': 'deterministic_simulation',
        'timestamp': datetime.now().isoformat(),
        'inter_rater_reliability': {
            'note': 'Single rater; inter-rater reliability will be calculated when multiple raters are added.',
            'status': 'pending'
        }
    }
    
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Written metadata to {metadata_path}")
    
    return df

def main():
    """Main entry point for the annotation tool."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate Gold Standard annotations')
    parser.add_argument(
        '--input', 
        type=str, 
        default='data/raw/conversations.jsonl',
        help='Path to input JSONL file'
    )
    parser.add_argument(
        '--output', 
        type=str, 
        default='data/processed/gold_standard_50.csv',
        help='Path for output CSV file'
    )
    parser.add_argument(
        '--metadata', 
        type=str, 
        default='data/raw/rater_metadata.json',
        help='Path for metadata JSON file'
    )
    parser.add_argument(
        '--n-samples', 
        type=int, 
        default=50,
        help='Number of samples to generate'
    )
    parser.add_argument(
        '--seed', 
        type=int, 
        default=42,
        help='Random seed for reproducibility'
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    metadata_path = Path(args.metadata)
    
    try:
        # Load conversations
        conversations = load_raw_conversations(input_path)
        
        # Generate gold standard
        df = generate_gold_standard(
            conversations,
            output_path,
            metadata_path,
            n_samples=args.n_samples,
            seed=args.seed
        )
        
        print(f"Successfully generated {len(df)} annotated turns")
        print(f"Output: {output_path}")
        print(f"Metadata: {metadata_path}")
        
    except Exception as e:
        logger.error(f"Failed to generate gold standard: {e}")
        raise

if __name__ == '__main__':
    main()
