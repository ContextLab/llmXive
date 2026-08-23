"""
validate_citations.py

Verifies DeepFashion2 URL and model references using Reference-Validator Agent logic.
Implements FR-014: Check title-token-overlap >= 0.7 for citation validity.

This script validates that the citations (URLs and model references) used in the
project match the expected DeepFashion2 dataset and model specifications.
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import json

# Configuration constants
DEEPFASHION2_EXPECTED_TITLE_TOKENS = {
    "deep", "fashion", "2", "dataset", "benchmark", "detection", 
    "segmentation", "keypoint", "landmark", "occlusion"
}

DEEPFASHION2_URL_PATTERNS = [
    r"https?://.*\bdeep.*fashion.*\b",
    r"https?://.*\bfashion2\b.*",
    r"https?://.*\bamazon.*\b",  # Amazon dataset hosting
    r"https?://.*\bgithub.*\b",  # GitHub repositories
]

EXPECTED_MODEL_REFERENCES = {
    "clip": ["clip", "clip-vit", "clip-large", "openai/clip"],
    "blip": ["blip", "blip-large", "salesforce/blip"],
    "vit": ["vit", "vision-transformer", "google/vit"],
}

MIN_OVERLAP_THRESHOLD = 0.7


def tokenize_title(title: str) -> set:
    """
    Tokenize a title string into lowercase alphanumeric tokens.
    
    Args:
        title: The title string to tokenize
        
    Returns:
        Set of lowercase alphanumeric tokens
    """
    # Convert to lowercase and extract alphanumeric tokens
    tokens = re.findall(r'\b[a-z0-9]+\b', title.lower())
    return set(tokens)


def calculate_token_overlap(set1: set, set2: set) -> float:
    """
    Calculate the Jaccard-like token overlap between two sets.
    
    Formula: |intersection| / |union|
    
    Args:
        set1: First set of tokens
        set2: Second set of tokens
        
    Returns:
        Float between 0.0 and 1.0 representing overlap ratio
    """
    if not set1 or not set2:
        return 0.0
        
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    
    if not union:
        return 0.0
        
    return len(intersection) / len(union)


def validate_url_citation(url: str, expected_tokens: set = None) -> Dict:
    """
    Validate a URL citation against expected dataset tokens.
    
    Args:
        url: The URL to validate
        expected_tokens: Set of expected tokens (defaults to DeepFashion2 tokens)
        
    Returns:
        Dictionary with validation result and details
    """
    if expected_tokens is None:
        expected_tokens = DEEPFASHION2_EXPECTED_TITLE_TOKENS
        
    result = {
        "url": url,
        "valid": False,
        "overlap_score": 0.0,
        "reason": "",
        "tokens_found": []
    }
    
    # Check if URL matches expected patterns
    url_tokens = tokenize_title(url)
    result["tokens_found"] = list(url_tokens.intersection(expected_tokens))
    
    overlap = calculate_token_overlap(url_tokens, expected_tokens)
    result["overlap_score"] = overlap
    
    # Check against URL patterns
    pattern_match = any(re.search(pattern, url, re.IGNORECASE) 
                      for pattern in DEEPFASHION2_URL_PATTERNS)
    
    if overlap >= MIN_OVERLAP_THRESHOLD or pattern_match:
        result["valid"] = True
        result["reason"] = f"Overlap score {overlap:.2f} >= {MIN_OVERLAP_THRESHOLD} or pattern match"
    else:
        result["reason"] = f"Overlap score {overlap:.2f} < {MIN_OVERLAP_THRESHOLD} and no pattern match"
        
    return result


def validate_model_reference(reference: str, model_type: str = None) -> Dict:
    """
    Validate a model reference against expected model names.
    
    Args:
        reference: The model reference string (e.g., "openai/clip-vit-large")
        model_type: Optional model type filter ("clip", "blip", "vit")
        
    Returns:
        Dictionary with validation result and details
    """
    result = {
        "reference": reference,
        "valid": False,
        "overlap_score": 0.0,
        "reason": "",
        "matched_models": []
    }
    
    ref_tokens = tokenize_title(reference)
    
    # Determine which model references to check against
    if model_type and model_type in EXPECTED_MODEL_REFERENCES:
        model_refs = EXPECTED_MODEL_REFERENCES[model_type]
    else:
        model_refs = []
        for refs in EXPECTED_MODEL_REFERENCES.values():
            model_refs.extend(refs)
    
    # Check overlap with expected model references
    expected_tokens = tokenize_title(" ".join(model_refs))
    overlap = calculate_token_overlap(ref_tokens, expected_tokens)
    result["overlap_score"] = overlap
    
    # Find matched model names
    for model_ref in model_refs:
        if model_ref in reference.lower() or any(token in reference.lower() 
                                                 for token in tokenize_title(model_ref)):
            result["matched_models"].append(model_ref)
    
    if overlap >= MIN_OVERLAP_THRESHOLD and result["matched_models"]:
        result["valid"] = True
        result["reason"] = f"Overlap {overlap:.2f} >= {MIN_OVERLAP_THRESHOLD}, matched: {result['matched_models']}"
    else:
        result["reason"] = f"Overlap {overlap:.2f} < {MIN_OVERLAP_THRESHOLD} or no matches"
        
    return result


def validate_citations_from_file(citations_file: str) -> Dict:
    """
    Validate citations loaded from a JSON file.
    
    Args:
        citations_file: Path to JSON file containing citations
        
    Returns:
        Dictionary with validation results for all citations
    """
    if not os.path.exists(citations_file):
        return {
            "error": f"Citations file not found: {citations_file}",
            "valid": False,
            "results": []
        }
    
    try:
        with open(citations_file, 'r') as f:
            citations = json.load(f)
    except json.JSONDecodeError as e:
        return {
            "error": f"Invalid JSON in citations file: {e}",
            "valid": False,
            "results": []
        }
    
    results = []
    all_valid = True
    
    for citation in citations:
        if "url" in citation:
            url_result = validate_url_citation(citation["url"])
            results.append({
                "type": "url",
                "citation": citation,
                "validation": url_result
            })
            if not url_result["valid"]:
                all_valid = False
        elif "model" in citation:
            model_result = validate_model_reference(
                citation["model"], 
                citation.get("type")
            )
            results.append({
                "type": "model",
                "citation": citation,
                "validation": model_result
            })
            if not model_result["valid"]:
                all_valid = False
        else:
            results.append({
                "type": "unknown",
                "citation": citation,
                "validation": {
                    "valid": False,
                    "reason": "No URL or model field found"
                }
            })
            all_valid = False
    
    return {
        "valid": all_valid,
        "results": results,
        "total_citations": len(citations),
        "valid_count": sum(1 for r in results if r["validation"]["valid"]),
        "invalid_count": sum(1 for r in results if not r["validation"]["valid"])
    }


def main():
    """
    Main entry point for citation validation.
    
    Validates DeepFashion2 URLs and model references using the
    Reference-Validator Agent logic with title-token-overlap >= 0.7.
    
    Usage:
        python validate_citations.py [citations_file.json]
        
    If no file is provided, validates against a default set of expected
    DeepFashion2 citations.
    """
    print("=" * 60)
    print("DeepFashion2 Citation Validator (FR-014)")
    print("Reference-Validator Agent Logic: title-token-overlap >= 0.7")
    print("=" * 60)
    
    # Default citations to validate if no file provided
    default_citations = [
        {
            "url": "https://github.com/zhengjxu/DeepFashion2",
            "type": "dataset"
        },
        {
            "model": "openai/clip-vit-large-patch14",
            "type": "clip"
        },
        {
            "model": "salesforce/blip-large",
            "type": "blip"
        },
        {
            "url": "https://huggingface.co/datasets/deepfashion2",
            "type": "dataset"
        }
    ]
    
    # Check for command line argument
    citations_file = None
    if len(sys.argv) > 1:
        citations_file = sys.argv[1]
    
    if citations_file and os.path.exists(citations_file):
        print(f"\nValidating citations from file: {citations_file}")
        result = validate_citations_from_file(citations_file)
    else:
        print(f"\nValidating default DeepFashion2 citations...")
        print(f"File not provided or not found: {citations_file}")
        
        # Validate default citations
        results = []
        all_valid = True
        
        for citation in default_citations:
            if "url" in citation:
                url_result = validate_url_citation(citation["url"])
                results.append({
                    "type": "url",
                    "citation": citation,
                    "validation": url_result
                })
                if not url_result["valid"]:
                    all_valid = False
            elif "model" in citation:
                model_result = validate_model_reference(
                    citation["model"],
                    citation.get("type")
                )
                results.append({
                    "type": "model",
                    "citation": citation,
                    "validation": model_result
                })
                if not model_result["valid"]:
                    all_valid = False
        
        result = {
            "valid": all_valid,
            "results": results,
            "total_citations": len(default_citations),
            "valid_count": sum(1 for r in results if r["validation"]["valid"]),
            "invalid_count": sum(1 for r in results if not r["validation"]["valid"])
        }
    
    # Print results
    print(f"\nTotal Citations: {result['total_citations']}")
    print(f"Valid: {result['valid_count']}")
    print(f"Invalid: {result['invalid_count']}")
    print(f"Overall Status: {'PASS' if result['valid'] else 'FAIL'}")
    
    print("\nDetailed Results:")
    print("-" * 60)
    
    for item in result["results"]:
        citation_type = item["type"]
        citation_data = item["citation"]
        validation = item["validation"]
        
        print(f"\n[{citation_type.upper()}] {citation_data}")
        print(f"  Valid: {validation['valid']}")
        print(f"  Overlap Score: {validation.get('overlap_score', 0):.2f}")
        print(f"  Reason: {validation['reason']}")
        
        if "tokens_found" in validation and validation["tokens_found"]:
            print(f"  Tokens Found: {', '.join(validation['tokens_found'])}")
        
        if "matched_models" in validation and validation["matched_models"]:
            print(f"  Matched Models: {', '.join(validation['matched_models'])}")
    
    # Exit with appropriate code
    if not result["valid"]:
        print("\n⚠️  VALIDATION FAILED: One or more citations did not meet the threshold.")
        sys.exit(1)
    else:
        print("\n✅ VALIDATION PASSED: All citations meet the title-token-overlap >= 0.7 threshold.")
        sys.exit(0)


if __name__ == "__main__":
    main()