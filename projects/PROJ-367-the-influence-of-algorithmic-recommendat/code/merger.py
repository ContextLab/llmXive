"""
Semantic Similarity Merging Module.

Merges categories where the semantic similarity distance is below a configurable threshold
using pre-trained sentence embeddings.
"""
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Set, Tuple, Optional
from pathlib import Path

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from config import ProjectConfig

logger = logging.getLogger(__name__)

def load_embedding_model(model_name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:
    """
    Loads the pre-trained sentence transformer model.

    Args:
        model_name: Name of the model to load from HuggingFace.

    Returns:
        Loaded SentenceTransformer model.
    """
    logger.info(f"Loading embedding model: {model_name}")
    try:
        model = SentenceTransformer(model_name)
        logger.info("Embedding model loaded successfully.")
        return model
    except Exception as e:
        logger.error(f"Failed to load embedding model {model_name}: {e}")
        raise

def get_embeddings(
    categories: List[str], model: SentenceTransformer
) -> np.ndarray:
    """
    Computes embeddings for a list of categories.

    Args:
        categories: List of category strings.
        model: The loaded SentenceTransformer model.

    Returns:
        Numpy array of embeddings (shape: len(categories) x embedding_dim).
    """
    if not categories:
        return np.array([])
    # Encode the categories
    embeddings = model.encode(categories, show_progress_bar=False)
    return embeddings

def compute_pairwise_distances(
    embeddings: np.ndarray, threshold: float
) -> List[Tuple[str, str, float]]:
    """
    Computes pairwise cosine distances and returns pairs below the threshold.

    Args:
        embeddings: Array of embeddings.
        threshold: Similarity threshold. Pairs with similarity > threshold are merged.
                   Note: Distance = 1 - Similarity.

    Returns:
        List of tuples (cat1, cat2, similarity_score) for pairs exceeding threshold.
    """
    if len(embeddings) == 0:
        return []

    # Compute cosine similarity
    # sklearn cosine_similarity expects 2D arrays
    similarities = cosine_similarity(embeddings)

    # We only care about upper triangle (excluding diagonal) to avoid duplicates and self
    n = len(embeddings)
    pairs = []

    for i in range(n):
        for j in range(i + 1, n):
            sim = similarities[i, j]
            if sim > threshold:
                pairs.append((i, j, sim))

    return pairs

def build_merge_map(
    unique_categories: List[str],
    pairs: List[Tuple[int, int, float]],
) -> Dict[str, str]:
    """
    Builds a mapping from original category to merged representative category.
    Uses Union-Find logic implicitly via a simple representative selection.
    For each pair (i, j), we map the lexicographically larger one to the smaller one
    to ensure deterministic merging.

    Args:
        unique_categories: List of unique category strings.
        pairs: List of (idx_i, idx_j, sim) pairs to merge.

    Returns:
        Dict mapping original category -> merged representative category.
    """
    # Initialize parent map for Union-Find
    parent = {cat: cat for cat in unique_categories}

    def find(cat: str) -> str:
        if parent[cat] != cat:
            parent[cat] = find(parent[cat])
        return parent[cat]

    def union(cat1: str, cat2: str):
        root1 = find(cat1)
        root2 = find(cat2)
        if root1 != root2:
            # Deterministic choice: smaller string becomes root
            if root1 < root2:
                parent[root2] = root1
            else:
                parent[root1] = root2

    for idx_i, idx_j, _ in pairs:
        cat_i = unique_categories[idx_i]
        cat_j = unique_categories[idx_j]
        union(cat_i, cat_j)

    # Build final mapping
    merge_map = {}
    for cat in unique_categories:
        root = find(cat)
        merge_map[cat] = root

    return merge_map

def merge_similar_categories(
    df: pd.DataFrame,
    config: ProjectConfig,
    category_col: str = "recommended_categories",
    threshold: Optional[float] = None,
) -> pd.DataFrame:
    """
    Merges similar categories in the specified column based on semantic similarity.

    Args:
        df: Input DataFrame.
        config: Project configuration object.
        category_col: Name of the column containing list of categories (or string representation).
        threshold: Similarity threshold (0.0 to 1.0). Defaults to config value.

    Returns:
        DataFrame with a new column containing merged category lists.
    """
    if threshold is None:
        threshold = config.SEMANTIC_SIMILARITY_THRESHOLD

    logger.info(f"Starting semantic similarity merge with threshold: {threshold}")

    # Extract all unique categories from the column
    # Assuming the column contains lists of strings or string representations of lists
    all_categories = set()
    for val in df[category_col]:
        if isinstance(val, list):
            all_categories.update(val)
        elif isinstance(val, str):
            # Handle potential stringified lists or single categories
            # Simple split by comma if it looks like a list string, otherwise treat as single
            if "," in val:
                parts = [p.strip() for p in val.split(",")]
                all_categories.update(parts)
            else:
                all_categories.add(val)

    unique_categories = sorted(list(all_categories))
    logger.info(f"Found {len(unique_categories)} unique categories.")

    if len(unique_categories) < 2:
        logger.info("Less than 2 unique categories. No merging needed.")
        df = df.copy()
        df[f"{category_col}_merged"] = df[category_col]
        return df

    # Load model
    model = load_embedding_model(config.EMBEDDING_MODEL_NAME)

    # Get embeddings
    embeddings = get_embeddings(unique_categories, model)

    # Find similar pairs
    pairs = compute_pairwise_distances(embeddings, threshold)
    logger.info(f"Found {len(pairs)} pairs with similarity > {threshold}.")

    # Build merge map
    merge_map = build_merge_map(unique_categories, pairs)

    # Apply merge map to the dataframe
    def apply_merge(category_list):
        if isinstance(category_list, str):
            if "," in category_list:
                category_list = [p.strip() for p in category_list.split(",")]
            else:
                category_list = [category_list]

        if not isinstance(category_list, list):
            return category_list

        merged = [merge_map.get(cat, cat) for cat in category_list]
        # Remove duplicates while preserving order (optional, but good for consistency)
        seen = set()
        unique_merged = []
        for item in merged:
            if item not in seen:
                seen.add(item)
                unique_merged.append(item)
        return unique_merged

    df = df.copy()
    df[f"{category_col}_merged"] = df[category_col].apply(apply_merge)

    logger.info("Semantic similarity merge completed.")
    return df

def main():
    """
    Entry point for running the merger module as a script.
    Loads data, merges categories, and saves the result.
    """
    from config import ProjectConfig, setup_logging
    import json

    setup_logging()
    config = ProjectConfig()

    # Load data (assuming T017 output exists)
    input_path = config.DATA_PROCESSED_DIR / "cleaned_data.parquet"
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please run T017 (ingestion) first to generate cleaned_data.parquet.")
        return

    logger.info(f"Loading data from {input_path}")
    df = pd.read_parquet(input_path)

    # Run merge on recommended_categories
    df_merged = merge_similar_categories(df, config, category_col="recommended_categories")

    # Save output
    output_path = config.DATA_PROCESSED_DIR / "merged_categories.parquet"
    logger.info(f"Saving merged data to {output_path}")
    df_merged.to_parquet(output_path, index=False)

    # Log summary
    unique_before = set()
    unique_after = set()
    for val in df["recommended_categories"]:
        if isinstance(val, list): unique_before.update(val)
    for val in df_merged["recommended_categories_merged"]:
        if isinstance(val, list): unique_after.update(val)

    logger.info(f"Unique categories before: {len(unique_before)}")
    logger.info(f"Unique categories after: {len(unique_after)}")
    logger.info(f"Merged {len(unique_before) - len(unique_after)} categories.")

    # Save mapping for reference
    mapping_path = config.DATA_PROCESSED_DIR / "category_merge_map.json"
    # Re-compute map for saving (or extract from function if refactored)
    # For simplicity, re-run logic or store map in function. Here we re-run logic briefly.
    all_cats = sorted(list(set(unique_before)))
    if len(all_cats) > 1:
        model = load_embedding_model(config.EMBEDDING_MODEL_NAME)
        embs = get_embeddings(all_cats, model)
        pairs = compute_pairwise_distances(embs, config.SEMANTIC_SIMILARITY_THRESHOLD)
        merge_map = build_merge_map(all_cats, pairs)
        with open(mapping_path, "w") as f:
            json.dump(merge_map, f, indent=2)
        logger.info(f"Merge map saved to {mapping_path}")

if __name__ == "__main__":
    main()
