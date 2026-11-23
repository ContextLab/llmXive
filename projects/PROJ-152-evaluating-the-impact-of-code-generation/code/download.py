import hashlib
import json
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple

import config
from datasets import load_dataset

# Security keywords to filter for relevant prompts
SECURITY_KEYWORDS = [
    "sql", "xss", "auth", "injection", "sanitize", "password", "token",
    "credential", "encryption", "vulnerability", "exploit", "bypass",
    "insecure", "hash", "salt", "secret", "api_key", "jwt"
]

def calculate_file_hash(file_path: str) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_codexglue_dataset() -> Any:
    """
    Load the CodeXGLUE text-to-code dataset from HuggingFace.
    Returns the dataset object.
    """
    try:
        # Using the CodeXGLUE text-to-code dataset
        dataset = load_dataset("code_x_glue_tc_text_to_code", split="train")
        return dataset
    except Exception as e:
        raise RuntimeError(f"Failed to load CodeXGLUE dataset: {e}")

def calculate_relevance_score(text: str) -> float:
    """
    Calculate a relevance score based on security keyword matches.
    Returns a float score (higher is more relevant).
    """
    text_lower = text.lower()
    score = 0.0
    for keyword in SECURITY_KEYWORDS:
        # Count occurrences and weight them
        count = text_lower.count(keyword)
        if count > 0:
            # Weight by keyword importance (some keywords are more specific)
            weight = 1.0
            if keyword in ["sql", "xss", "injection", "auth", "password", "token"]:
                weight = 2.0
            elif keyword in ["credential", "encryption", "vulnerability", "exploit"]:
                weight = 1.5
            
            # Add to score (logarithmic scaling to prevent dominance by single keyword)
            score += weight * (1 + 0.5 * count)
    
    return score

def filter_and_score_prompts(dataset: Any) -> List[Dict[str, Any]]:
    """
    Filter prompts containing security keywords and score them.
    Returns a list of dictionaries with prompt data and relevance scores.
    """
    scored_prompts = []
    
    for item in dataset:
        # Get the prompt text (assuming 'prompt' or 'source' field)
        prompt_text = item.get('prompt') or item.get('source') or item.get('code')
        
        if not prompt_text:
            continue
        
        # Check if prompt contains any security keywords
        text_lower = prompt_text.lower()
        if any(keyword in text_lower for keyword in SECURITY_KEYWORDS):
            score = calculate_relevance_score(prompt_text)
            scored_prompts.append({
                'text': prompt_text,
                'score': score,
                'original_item': item
            })
    
    return scored_prompts

def select_top_candidates(scored_prompts: List[Dict[str, Any]], target_count: int = 10) -> List[Dict[str, Any]]:
    """
    Select top candidates by relevance score.
    Returns exactly target_count prompts, or fewer if not enough available.
    """
    # Sort by score descending
    sorted_prompts = sorted(scored_prompts, key=lambda x: x['score'], reverse=True)
    
    # Select top candidates
    selected = sorted_prompts[:target_count]
    
    return selected

def generate_manifest(selected_prompts: List[Dict[str, Any]], output_path: str) -> None:
    """
    Generate the raw manifest JSON file with checksums.
    """
    manifest = {
        'metadata': {
            'source': 'CodeXGLUE text-to-code dataset',
            'filter_criteria': f'Security keywords: {", ".join(SECURITY_KEYWORDS)}',
            'selection_method': 'Top candidates by relevance score',
            'count': len(selected_prompts),
            'generated_at': config.get_timestamp()
        },
        'prompts': []
    }
    
    for i, item in enumerate(selected_prompts):
        prompt_data = item['text']
        
        # Calculate checksums
        content_hash = hashlib.sha256(prompt_data.encode('utf-8')).hexdigest()
        file_hash = calculate_file_hash(output_path) if os.path.exists(output_path) else "pending"
        
        prompt_entry = {
            'prompt_id': f"codexglue_{i:03d}",
            'source': 'CodeXGLUE',
            'text': prompt_data,
            'relevance_score': item['score'],
            'content_hash': content_hash,
            'file_hash': file_hash
        }
        
        manifest['prompts'].append(prompt_entry)
    
    # Write manifest to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

def main():
    """Main function to execute the download and filtering process."""
    print("Starting CodeXGLUE prompt download and filtering...")
    
    # Ensure output directory exists
    output_dir = Path(config.DATA_DIR) / "prompts"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(output_dir / "raw_manifest.json")
    
    # Load dataset
    print("Loading CodeXGLUE dataset...")
    dataset = load_codexglue_dataset()
    print(f"Loaded dataset with {len(dataset)} items")
    
    # Filter and score prompts
    print("Filtering and scoring prompts...")
    scored_prompts = filter_and_score_prompts(dataset)
    print(f"Found {len(scored_prompts)} security-related prompts")
    
    if not scored_prompts:
        raise ValueError("No security-related prompts found in CodeXGLUE dataset")
    
    # Select top candidates (targeting 10 for CodeXGLUE subset)
    target_count = 10
    selected_prompts = select_top_candidates(scored_prompts, target_count)
    print(f"Selected top {len(selected_prompts)} prompts by relevance score")
    
    # Generate manifest
    print(f"Generating manifest at {output_path}...")
    generate_manifest(selected_prompts, output_path)
    
    print(f"Successfully generated raw_manifest.json with {len(selected_prompts)} prompts")
    print("Task T005 completed successfully.")

if __name__ == "__main__":
    main()
