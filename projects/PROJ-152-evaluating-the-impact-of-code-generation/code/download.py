"""
Download and filter CodeXGLUE prompts for security-related code generation tasks.

This script fetches the CodeXGLUE code-to-code dataset from HuggingFace,
filters for prompts containing security-related keywords, scores them by
relevance, selects the top 10 candidates, and generates a manifest with checksums.
"""
import hashlib
import json
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Import config for path constants
import config

# Security keywords to filter prompts
SECURITY_KEYWORDS = [
    "sql", "xss", "auth", "injection", "sanitize", "password", "token",
    "credential", "encryption", "decryption", "hash", "salt", "vulnerability",
    "exploit", "malware", "firewall", "ssl", "tls", "jwt", "oauth"
]

# Relevance scoring weights
EXACT_MATCH_WEIGHT = 10
PARTIAL_MATCH_WEIGHT = 5

def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_codexglue_dataset() -> List[Dict[str, Any]]:
    """
    Load the CodeXGLUE code-to-code dataset from HuggingFace.
    
    Returns:
        List of prompt dictionaries with 'prompt', 'source', 'target' fields.
    """
    try:
        from datasets import load_dataset
    except ImportError:
        raise ImportError(
            "The 'datasets' package is required. Install it with: "
            "pip install datasets"
        )

    # Load the code_to_code dataset from CodeXGLUE
    # Using a subset for efficiency as per resource constraints
    dataset = load_dataset("codeparrot/codeXGLUE", "code-to-code", split="train")
    
    # Convert to list of dicts for easier processing
    prompts = []
    for item in dataset:
        prompts.append({
            "prompt": item.get("source", ""),
            "target": item.get("target", ""),
            "source_repo": item.get("source_repo", "unknown"),
            "target_repo": item.get("target_repo", "unknown"),
        })
    
    return prompts

def calculate_relevance_score(text: str) -> int:
    """
    Calculate a relevance score for a text based on security keywords.
    
    Args:
        text: The text to score.
        
    Returns:
        An integer score representing relevance to security topics.
    """
    text_lower = text.lower()
    score = 0
    
    for keyword in SECURITY_KEYWORDS:
        if keyword in text_lower:
            # Check for exact word match
            if re.search(rf'\b{keyword}\b', text_lower):
                score += EXACT_MATCH_WEIGHT
            else:
                score += PARTIAL_MATCH_WEIGHT
    
    return score

def filter_and_score_prompts(prompts: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], int]]:
    """
    Filter prompts for security keywords and score them by relevance.
    
    Args:
        prompts: List of prompt dictionaries.
        
    Returns:
        List of tuples (prompt_dict, score) sorted by score descending.
    """
    scored_prompts = []
    
    for prompt in prompts:
        # Combine prompt and target for scoring
        text_to_score = f"{prompt.get('prompt', '')} {prompt.get('target', '')}"
        
        score = calculate_relevance_score(text_to_score)
        
        # Only include prompts with non-zero security relevance
        if score > 0:
            scored_prompts.append((prompt, score))
    
    # Sort by score descending
    scored_prompts.sort(key=lambda x: x[1], reverse=True)
    
    return scored_prompts

def select_top_candidates(
    scored_prompts: List[Tuple[Dict[str, Any], int]], 
    n: int = 10
) -> List[Tuple[Dict[str, Any], int]]:
    """
    Select the top N candidates by relevance score.
    
    Args:
        scored_prompts: List of (prompt, score) tuples.
        n: Number of candidates to select.
        
    Returns:
        List of top N (prompt, score) tuples.
    """
    return scored_prompts[:n]

def generate_manifest(
    selected_prompts: List[Tuple[Dict[str, Any], int]],
    output_path: Path
) -> Dict[str, Any]:
    """
    Generate a manifest JSON file with checksums for selected prompts.
    
    Args:
        selected_prompts: List of (prompt_dict, score) tuples.
        output_path: Path to write the manifest file.
        
    Returns:
        The manifest dictionary.
    """
    manifest = {
        "metadata": {
            "source": "CodeXGLUE code-to-code dataset",
            "filter_criteria": "Security keywords",
            "selection_method": "Top N by relevance score",
            "n_selected": len(selected_prompts),
            "keywords_used": SECURITY_KEYWORDS,
            "generated_at": str(config.get_timestamp())
        },
        "prompts": []
    }
    
    for idx, (prompt, score) in enumerate(selected_prompts):
        # Create a unique ID for each prompt
        prompt_id = f"codexglue_{idx:04d}"
        
        # Calculate checksum of the prompt content
        content_str = f"{prompt.get('prompt', '')}{prompt.get('target', '')}"
        checksum = hashlib.sha256(content_str.encode('utf-8')).hexdigest()
        
        prompt_entry = {
            "id": prompt_id,
            "source": prompt.get("prompt", ""),
            "target": prompt.get("target", ""),
            "source_repo": prompt.get("source_repo", "unknown"),
            "target_repo": prompt.get("target_repo", "unknown"),
            "relevance_score": score,
            "checksum": checksum,
            "source_type": "codexglue"
        }
        
        manifest["prompts"].append(prompt_entry)
    
    # Write manifest to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    return manifest

def main():
    """Main entry point for the download script."""
    print("Starting CodeXGLUE prompt download and filtering...")
    
    # Ensure output directory exists
    output_dir = Path(config.DATA_PROMPTS_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "raw_manifest.json"
    
    try:
        # Load dataset
        print("Loading CodeXGLUE dataset...")
        prompts = load_codexglue_dataset()
        print(f"Loaded {len(prompts)} prompts from CodeXGLUE.")
        
        # Filter and score
        print("Filtering and scoring prompts for security relevance...")
        scored_prompts = filter_and_score_prompts(prompts)
        print(f"Found {len(scored_prompts)} security-relevant prompts.")
        
        if not scored_prompts:
            raise ValueError("No security-relevant prompts found in the dataset.")
        
        # Select top candidates
        selected_count = 10  # As per N=30 total scope (10 CodeXGLUE + 20 handcrafted)
        top_prompts = select_top_candidates(scored_prompts, n=selected_count)
        print(f"Selected top {len(top_prompts)} candidates.")
        
        # Generate manifest
        print(f"Generating manifest at {output_path}...")
        manifest = generate_manifest(top_prompts, output_path)
        
        # Verify the file was created
        if output_path.exists():
            file_hash = calculate_file_hash(output_path)
            print(f"Manifest created successfully. SHA256: {file_hash}")
            print(f"Total prompts in manifest: {len(manifest['prompts'])}")
        else:
            raise RuntimeError("Manifest file was not created.")
            
    except Exception as e:
        print(f"Error during download and filtering: {e}")
        raise

if __name__ == "__main__":
    main()
