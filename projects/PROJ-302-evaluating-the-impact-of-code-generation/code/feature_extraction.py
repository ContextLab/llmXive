"""
Feature extraction module for the evaluation pipeline (T005).

This script reads all PR‑level data (human PRs and LLM‑generated snippets),
computes the five covariates required for propensity‑score matching and
writes them to ``data/processed/merged_features.parquet``.  It also writes
``data/processed/covariate_config.json`` containing the exact list of
covariates in the required order.

Expected input files (must exist before this script runs):
  * ``data/raw/<owner>_<repo>.parquet`` – human PR metadata (one file per repo)
  * ``data/synthetic/context_based.parquet`` – LLM context‑based cohort
  * ``data/synthetic/prompt_based.parquet`` – LLM prompt‑only cohort

Each input record must contain at least:
  - a unique identifier (``pr_id`` for human PRs, ``snippet_id`` for LLM rows)
  - a ``code`` column (or ``generated_code`` / ``content``) holding the source code
  - a ``repo_id`` or ``owner_repo`` column identifying the repository
  - optional ``ci_build_time`` (seconds) – if missing the field is set to NaN

The script performs the following per‑row calculations:

  * **LOC** – number of non‑empty, non‑comment lines.
  * **Cyclomatic complexity** – mean CC value across all functions/classes
    (using ``radon.complexity.cc_visit``).  If the parser cannot analyse the
    snippet the complexity is set to NaN.
  * **CI build duration** – taken directly from the input column if present.
  * **Repository activity level** – total number of PRs (human + LLM) observed
    for the repository; this scalar is attached to every row belonging to that
    repository.
  * **Semantic similarity** – cosine similarity between the snippet embedding
    (``sentence‑transformers/all‑MiniLM‑L6‑v2``) and the centroid embedding of
    all snippets from the same repository.

All values are written to the ``merged_features.parquet`` file with the
schema required by ``contracts/dataset.schema.yaml`` and the covariate list
``["file_size_loc","complexity_score","repo_activity_level","ci_build_time",
"semantic_similarity"]`` is saved to ``covariate_config.json``.
"""

import json
import logging
from pathlib import Path
from typing import List, Tuple

import pandas as pd
import numpy as np
from radon.complexity import cc_visit
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from llmxive_toolkit import paths, get_logger

log: logging.Logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _find_code_column(df: pd.DataFrame) -> str:
    """Return the column name that holds the source code."""
    candidates = ["code", "generated_code", "content", "snippet", "source_code"]
    for col in candidates:
        if col in df.columns:
            return col
    raise ValueError("No code column found in dataframe; expected one of "
                     f"{candidates}. Columns present: {list(df.columns)}")

def _loc_from_code(code: str) -> int:
    """Count non‑empty, non‑comment lines."""
    if not isinstance(code, str):
        return 0
    lines = code.splitlines()
    count = 0
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            count += 1
    return count

def _complexity_from_code(code: str) -> float:
    """Return average cyclomatic complexity; NaN if parsing fails."""
    try:
        results = cc_visit(code)
        if not results:
            return np.nan
        complexities = [r.complexity for r in results]
        return float(np.mean(complexities))
    except Exception as e:
        log.debug(f"Cyclomatic complexity parsing failed: {e}")
        return np.nan

def _embed_snippets(snippets: List[str],
                    model: SentenceTransformer) -> np.ndarray:
    """Batch embed a list of code snippets."""
    # SentenceTransformer handles batching internally.
    return model.encode(snippets, convert_to_numpy=True, show_progress_bar=False)

# ----------------------------------------------------------------------
# Main processing function
# ----------------------------------------------------------------------
def _load_all_input_data() -> pd.DataFrame:
    """Load human PRs and both synthetic cohorts into a single DataFrame."""
    data_frames = []

    # Human PRs – any parquet under data/raw
    raw_dir = paths.data("raw")
    for parquet_path in raw_dir.glob("*.parquet"):
        log.info(f"Loading human PR data from {parquet_path}")
        df = pd.read_parquet(parquet_path)
        df["author_type"] = "human"
        data_frames.append(df)

    # Context‑based LLM cohort
    ctx_path = paths.data("synthetic", "context_based.parquet")
    if ctx_path.exists():
        log.info(f"Loading context‑based cohort from {ctx_path}")
        df_ctx = pd.read_parquet(ctx_path)
        df_ctx["author_type"] = "llm_context"
        data_frames.append(df_ctx)
    else:
        log.warning("Context‑based cohort file not found – skipping.")

    # Prompt‑only LLM cohort
    prompt_path = paths.data("synthetic", "prompt_based.parquet")
    if prompt_path.exists():
        log.info(f"Loading prompt‑only cohort from {prompt_path}")
        df_prompt = pd.read_parquet(prompt_path)
        df_prompt["author_type"] = "llm_prompt"
        data_frames.append(df_prompt)
    else:
        log.warning("Prompt‑only cohort file not found – skipping.")

    if not data_frames:
        raise FileNotFoundError(
            "No input parquet files found in data/raw or data/synthetic."
        )
    merged = pd.concat(data_frames, ignore_index=True, sort=False)
    return merged

def _compute_repo_activity(df: pd.DataFrame) -> pd.Series:
    """Map each row to the total number of PRs observed for its repository."""
    # Normalise repository identifier – many datasets use 'repo_id' or 'owner_repo'
    repo_id_col = None
    for cand in ["repo_id", "owner_repo", "repository", "repo"]:
        if cand in df.columns:
            repo_id_col = cand
            break
    if repo_id_col is None:
        raise ValueError("Repository identifier column not found in merged data.")
    activity = df.groupby(repo_id_col).size()
    return df[repo_id_col].map(activity).astype(int)

def main() -> None:
    """Entry point for the feature‑extraction stage."""
    # ------------------------------------------------------------------
    # 1. Load raw data
    # ------------------------------------------------------------------
    log.info("Starting feature extraction (T005).")
    merged_df = _load_all_input_data()

    # ------------------------------------------------------------------
    # 2. Identify the code column
    # ------------------------------------------------------------------
    code_col = _find_code_column(merged_df)

    # ------------------------------------------------------------------
    # 3. Compute LOC and cyclomatic complexity
    # ------------------------------------------------------------------
    log.info("Computing LOC and cyclomatic complexity.")
    merged_df["file_size_loc"] = merged_df[code_col].apply(_loc_from_code)
    merged_df["complexity_score"] = merged_df[code_col].apply(_complexity_from_code)

    # ------------------------------------------------------------------
    # 4. CI build time – keep existing column or set NaN
    # ------------------------------------------------------------------
    if "ci_build_time" not in merged_df.columns:
        merged_df["ci_build_time"] = np.nan
    else:
        # Ensure numeric type
        merged_df["ci_build_time"] = pd.to_numeric(
            merged_df["ci_build_time"], errors="coerce"
        )

    # ------------------------------------------------------------------
    # 5. Repository activity level
    # ------------------------------------------------------------------
    log.info("Computing repository activity levels.")
    merged_df["repo_activity_level"] = _compute_repo_activity(merged_df)

    # ------------------------------------------------------------------
    # 6. Semantic similarity to repository centroid
    # ------------------------------------------------------------------
    log.info("Computing semantic similarity scores.")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    # Prepare embeddings per row
    snippets = merged_df[code_col].fillna("").astype(str).tolist()
    embeddings = _embed_snippets(snippets, model)

    # Compute centroid per repository
    repo_id_col = None
    for cand in ["repo_id", "owner_repo", "repository", "repo"]:
        if cand in merged_df.columns:
            repo_id_col = cand
            break
    if repo_id_col is None:
        raise ValueError("Repository identifier column not found for similarity step.")

    # Build a mapping from repo -> centroid vector
    repo_to_indices = {}
    for idx, repo in enumerate(merged_df[repo_id_col]):
        repo_to_indices.setdefault(repo, []).append(idx)

    centroids = {}
    for repo, idxs in repo_to_indices.items():
        repo_vecs = embeddings[idxs]
        centroids[repo] = np.mean(repo_vecs, axis=0, keepdims=True)

    # Cosine similarity of each snippet to its repo centroid
    sim_scores = np.empty(len(merged_df))
    for repo, idxs in repo_to_indices.items():
        repo_centroid = centroids[repo]  # shape (1, dim)
        snippet_vecs = embeddings[idxs]   # shape (n, dim)
        sims = cosine_similarity(snippet_vecs, repo_centroid).flatten()
        sim_scores[idxs] = sims

    # Clip to the theoretical range just in case of numerical noise
    merged_df["semantic_similarity"] = np.clip(sim_scores, -1.0, 1.0)

    # ------------------------------------------------------------------
    # 7. Keep only the columns required by the downstream schema
    # ------------------------------------------------------------------
    required_columns = [
        "pr_id", "snippet_id", "author_type", "file_size_loc",
        "complexity_score", "repo_activity_level", "ci_build_time",
        "semantic_similarity"
    ]
    # Some datasets use 'pr_id' for human rows and 'snippet_id' for LLM rows;
    # ensure at least one identifier column exists.
    identifier_cols = [c for c in ["pr_id", "snippet_id"] if c in merged_df.columns]
    if not identifier_cols:
        raise ValueError("Neither 'pr_id' nor 'snippet_id' found in input data.")
    # Build final dataframe
    final_df = merged_df[identifier_cols + [
        "author_type",
        "file_size_loc",
        "complexity_score",
        "repo_activity_level",
        "ci_build_time",
        "semantic_similarity"
    ]].copy()

    # ------------------------------------------------------------------
    # 8. Write outputs
    # ------------------------------------------------------------------
    out_parquet = paths.data("processed", "merged_features.parquet")
    out_parquet.parent.mkdir(parents=True, exist_ok=True)
    final_df.to_parquet(out_parquet, index=False)
    log.info(f"Merged features written to {out_parquet}")

    covariate_config = [
        "file_size_loc",
        "complexity_score",
        "repo_activity_level",
        "ci_build_time",
        "semantic_similarity"
    ]
    config_path = paths.data("processed", "covariate_config.json")
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(covariate_config, f, indent=2)
    log.info(f"Covariate config written to {config_path}")

if __name__ == "__main__":
    main()
