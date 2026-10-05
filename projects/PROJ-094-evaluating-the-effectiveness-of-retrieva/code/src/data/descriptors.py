"""
Descriptors for code snippets and queries.

Calculates API density, documentation density, and naming consistency scores
for the union of ground truth and retrieved snippets per query.
"""
import os
import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set

import numpy as np
from transformers import AutoTokenizer, AutoModel
import torch

from src.data.models import CodeSnippet

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
API_PATTERNS = [
    r'\b[a-zA-Z_]\w*\s*\(',  # Function calls
    r'\b[a-zA-Z_]\w*\.',     # Attribute access / method calls
    r'import\s+\w+',         # Import statements
    r'from\s+\w+',           # From import statements
]
DOC_PATTERNS = [
    r'"""[\s\S]*?"""',       # Triple-quoted strings (docstrings)
    r"'''[\s\S]*?'''",       # Triple-quoted strings (docstrings)
    r'#\s*[A-Z][a-zA-Z\s]+', # Comments starting with capital letter
]
NAMING_PATTERNS = [
    r'([a-z]+)_([a-z]+)',    # snake_case
    r'([a-z]+)([A-Z][a-z]+)', # camelCase
    r'([A-Z]+)([A-Z][a-z]+)', # PascalCase components
]

# Global model/tokenizer cache
_tokenizer = None
_model = None

def _load_codebert_model():
    """Load CodeBERT-base model and tokenizer (cached)."""
    global _tokenizer, _model
    if _tokenizer is None or _model is None:
        logger.info("Loading CodeBERT-base model and tokenizer...")
        model_name = "microsoft/codebert-base"
        _tokenizer = AutoTokenizer.from_pretrained(model_name)
        _model = AutoModel.from_pretrained(model_name)
        _model.eval()
        logger.info("CodeBERT model loaded successfully.")
    return _tokenizer, _model

def _calculate_api_density(code: str) -> float:
    """
    Calculate API density as the ratio of API-related tokens to total tokens.
    API patterns include function calls, attribute access, imports, etc.
    """
    if not code or not code.strip():
        return 0.0

    total_tokens = len(code.split())
    if total_tokens == 0:
        return 0.0

    api_matches = 0
    for pattern in API_PATTERNS:
        api_matches += len(re.findall(pattern, code))

    return api_matches / total_tokens

def _calculate_doc_density(code: str) -> float:
    """
    Calculate documentation density as the ratio of documentation tokens to total tokens.
    Documentation patterns include docstrings and descriptive comments.
    """
    if not code or not code.strip():
        return 0.0

    total_tokens = len(code.split())
    if total_tokens == 0:
        return 0.0

    doc_matches = 0
    for pattern in DOC_PATTERNS:
        doc_matches += len(re.findall(pattern, code))

    return doc_matches / total_tokens

def _calculate_naming_consistency(code: str) -> float:
    """
    Calculate naming consistency score using CodeBERT embeddings.
    Measures how consistently identifiers follow naming conventions.
    """
    if not code or not code.strip():
        return 0.0

    tokenizer, model = _load_codebert_model()

    # Extract identifiers from code
    identifiers = re.findall(r'\b([a-zA-Z_]\w*)\b', code)
    if not identifiers:
        return 0.0

    # Filter out keywords and common non-identifiers
    keywords = {'def', 'class', 'import', 'from', 'return', 'if', 'else',
                'elif', 'for', 'while', 'try', 'except', 'finally', 'with',
                'as', 'pass', 'break', 'continue', 'and', 'or', 'not', 'in',
                'is', 'lambda', 'yield', 'global', 'nonlocal', 'assert',
                'del', 'True', 'False', 'None'}
    identifiers = [id for id in identifiers if id.lower() not in keywords]

    if not identifiers:
        return 0.0

    # Get embeddings for identifiers
    try:
        inputs = tokenizer(identifiers, return_tensors='pt', padding=True, truncation=True, max_length=128)
        with torch.no_grad():
            outputs = model(**inputs)
            embeddings = outputs.last_hidden_state.mean(dim=1).numpy()

        # Calculate pairwise cosine similarities
        n = len(embeddings)
        if n < 2:
            return 1.0  # Single identifier is perfectly consistent

        similarities = []
        for i in range(n):
            for j in range(i + 1, n):
                norm_i = np.linalg.norm(embeddings[i])
                norm_j = np.linalg.norm(embeddings[j])
                if norm_i > 0 and norm_j > 0:
                    sim = np.dot(embeddings[i], embeddings[j]) / (norm_i * norm_j)
                    similarities.append(sim)

        if not similarities:
            return 0.0

        return float(np.mean(similarities))

    except Exception as e:
        logger.warning(f"Error calculating naming consistency: {e}")
        return 0.0

def _load_snippets_from_jsonl(file_path: Path) -> List[CodeSnippet]:
    """Load CodeSnippet objects from a JSONL file."""
    snippets = []
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return snippets

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    data = json.loads(line)
                    snippet = CodeSnippet(
                        query_id=data.get('query_id', ''),
                        code=data.get('code', ''),
                        docstring=data.get('docstring', ''),
                        language=data.get('language', 'python'),
                        is_ground_truth=data.get('is_ground_truth', False)
                    )
                    snippets.append(snippet)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON line in {file_path}: {line}")

    return snippets

def _load_snippets_from_csv(file_path: Path) -> List[CodeSnippet]:
    """Load CodeSnippet objects from a CSV file."""
    import csv
    snippets = []
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return snippets

    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                snippet = CodeSnippet(
                    query_id=row.get('query_id', ''),
                    code=row.get('code', ''),
                    docstring=row.get('docstring', ''),
                    language=row.get('language', 'python'),
                    is_ground_truth=row.get('is_ground_truth', 'False').lower() == 'true'
                )
                snippets.append(snippet)
            except Exception as e:
                logger.warning(f"Error parsing CSV row in {file_path}: {e}")

    return snippets

def load_snippets(data_dir: Path) -> List[CodeSnippet]:
    """
    Load all snippets from a directory (JSONL or CSV).
    Supports both train and test processed data directories.
    """
    snippets = []

    # Try JSONL first
    jsonl_file = data_dir / "snippets.jsonl"
    if jsonl_file.exists():
        snippets.extend(_load_snippets_from_jsonl(jsonl_file))

    # Try CSV as fallback
    csv_file = data_dir / "snippets.csv"
    if csv_file.exists():
        snippets.extend(_load_snippets_from_csv(csv_file))

    if not snippets:
        logger.warning(f"No snippets found in {data_dir}")

    return snippets

def compute_descriptors_for_query(
    query_id: str,
    ground_truth_snippets: List[CodeSnippet],
    retrieved_snippets: List[CodeSnippet]
) -> Dict[str, Any]:
    """
    Compute descriptors for a query by analyzing the union of ground truth
    and retrieved snippets.

    Args:
        query_id: The query identifier
        ground_truth_snippets: List of ground truth CodeSnippet objects
        retrieved_snippets: List of retrieved CodeSnippet objects (top-K)

    Returns:
        Dictionary containing:
            - query_id
            - api_density: float
            - doc_density: float
            - naming_consistency: float
            - snippet_count: int (total unique snippets analyzed)
    """
    # Combine and deduplicate snippets by code content
    all_snippets = ground_truth_snippets + retrieved_snippets
    unique_codes = {}
    for snippet in all_snippets:
        if snippet.code not in unique_codes:
            unique_codes[snippet.code] = snippet

    if not unique_codes:
        return {
            'query_id': query_id,
            'api_density': 0.0,
            'doc_density': 0.0,
            'naming_consistency': 0.0,
            'snippet_count': 0
        }

    # Aggregate descriptors across all unique snippets
    api_densities = []
    doc_densities = []
    naming_consistencies = []

    for snippet in unique_codes.values():
        code_text = snippet.code + " " + (snippet.docstring or "")

        api_d = _calculate_api_density(code_text)
        doc_d = _calculate_doc_density(code_text)
        naming_c = _calculate_naming_consistency(code_text)

        api_densities.append(api_d)
        doc_densities.append(doc_d)
        naming_consistencies.append(naming_c)

    return {
        'query_id': query_id,
        'api_density': float(np.mean(api_densities)) if api_densities else 0.0,
        'doc_density': float(np.mean(doc_densities)) if doc_densities else 0.0,
        'naming_consistency': float(np.mean(naming_consistencies)) if naming_consistencies else 0.0,
        'snippet_count': len(unique_codes)
    }

def compute_all_descriptors(
    processed_data_dir: Path,
    retrieval_results_path: Path,
    output_path: Path
) -> None:
    """
    Compute descriptors for all queries in the dataset.

    Args:
        processed_data_dir: Directory containing processed snippets (JSONL/CSV)
        retrieval_results_path: Path to results.csv containing retrieval results
        output_path: Path to save the descriptors JSON file
    """
    logger.info(f"Loading snippets from {processed_data_dir}")
    all_snippets = load_snippets(processed_data_dir)

    # Organize snippets by query_id
  #   ground_truth: query_id -> list of snippets
  #   retrieved: query_id -> list of snippets (from results.csv)
    ground_truth_map = {}
    for snippet in all_snippets:
        if snippet.is_ground_truth:
            if snippet.query_id not in ground_truth_map:
                ground_truth_map[snippet.query_id] = []
            ground_truth_map[snippet.query_id].append(snippet)

    # Load retrieval results to get top-K retrieved snippets
    retrieved_map = {}
    if retrieval_results_path.exists():
        import csv
        with open(retrieval_results_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                query_id = row.get('query_id', '')
                method = row.get('method', '')
                if method == 'rag':  # Use RAG results as the retrieved set
                    if query_id not in retrieved_map:
                        retrieved_map[query_id] = []
                    # Parse retrieved codes from the row (assuming they're stored)
                    # This assumes the results.csv has a 'retrieved_codes' or similar field
                    # If not, we may need to adjust based on actual schema
                    retrieved_codes_str = row.get('retrieved_codes', '[]')
                    try:
                        retrieved_codes = json.loads(retrieved_codes_str)
                        for code in retrieved_codes:
                            snippet = CodeSnippet(
                                query_id=query_id,
                                code=code,
                                docstring="",
                                language='python',
                                is_ground_truth=False
                            )
                            retrieved_map[query_id].append(snippet)
                    except json.JSONDecodeError:
                        logger.warning(f"Could not parse retrieved codes for query {query_id}")

    # Compute descriptors for each query
    descriptors = []
    processed_query_ids = set()

    # Process queries that have ground truth
    for query_id in ground_truth_map.keys():
        gt_snippets = ground_truth_map[query_id]
        retrieved_snippets = retrieved_map.get(query_id, [])

        desc = compute_descriptors_for_query(query_id, gt_snippets, retrieved_snippets)
        descriptors.append(desc)
        processed_query_ids.add(query_id)

    # Process queries that only have retrieved results (edge case)
    for query_id in retrieved_map.keys():
        if query_id not in processed_query_ids:
            retrieved_snippets = retrieved_map[query_id]
            desc = compute_descriptors_for_query(query_id, [], retrieved_snippets)
            descriptors.append(desc)

    # Save descriptors to output file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(descriptors, f, indent=2)

    logger.info(f"Descriptors saved to {output_path}")
    logger.info(f"Processed {len(descriptors)} queries")

def main():
    """Main entry point for descriptor computation."""
    import argparse

    parser = argparse.ArgumentParser(description="Compute code descriptors for correlation analysis")
    parser.add_argument(
        "--processed-data-dir",
        type=Path,
        default=Path("data/processed/test"),
        help="Directory containing processed snippets"
    )
    parser.add_argument(
        "--retrieval-results",
        type=Path,
        default=Path("results/results.csv"),
        help="Path to results.csv containing retrieval results"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/descriptors.json"),
        help="Path to save descriptors output"
    )

    args = parser.parse_args()

    compute_all_descriptors(
        processed_data_dir=args.processed_data_dir,
        retrieval_results_path=args.retrieval_results,
        output_path=args.output
    )

if __name__ == "__main__":
    main()
