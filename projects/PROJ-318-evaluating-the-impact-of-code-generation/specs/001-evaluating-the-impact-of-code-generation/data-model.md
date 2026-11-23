# Data Model Specification
# Project: PROJ-318-evaluating-the-impact-of-code-generation
# Description: Schema definitions for all data artifacts produced and consumed by the pipeline.

## 1. Frozen Repository List
**File**: `data/raw/frozen_repo_list.json`  
**Source**: PyPI JSON API (fetched once, then committed)  
**Schema**: Array of objects
```json
[
  {
    "repo_name": "string",
    "github_url": "string (GitHub HTTPS URL)",
    "star_count": "integer"
  }
]
```
**Constraints**: Fixed number of entries (20 top + ≥ 15 low‑tier); sorted descending by `star_count`.

## 2. Extracted Repository Data (Ground Truth)
**File**: `data/raw/repos/{repo_slug}.json`  
**Source**: AST parser  
**Schema**: Array of objects
```json
[
  {
    "repo_slug": "string",
    "file_path": "string (relative to repo root)",
    "function_name": "string",
    "signature": "string (full Python signature)",
    "human_docstring": "string | null",
    "ast_params": [
      {
        "name": "string",
        "annotation": "string | null",
        "default": "string | null"
      }
    ]
  }
]
```
**Constraints**:
- `human_docstring` must be `null` if absent.
- ≤ 1 000 method records per repository (enforced by extraction script).

## 3. Generation Batch (Intermediate)
**File**: `data/processed/generation_batch_{repo_slug}.json`  
**Source**: LLM generation  
**Schema**: Array of objects (extends Extraction schema)
```json
[
  {
    "repo_slug": "string",
    "file_path": "string",
    "function_name": "string",
    "signature": "string",
    "human_docstring": "string | null",
    "ast_params": [ ... ],
    "generated_docstring": "string | null",
    "generation_status": "string",   // "success", "timeout", or "error"
    "error_message": "string | null"
  }
]
```
**Constraints**:
- `generated_docstring` may be `null` on failure.
- Row count ≤ 1 000 per file.

## 4. Baseline Copy Batch
**File**: `data/processed/baseline_batch_{repo_slug}.json`  
**Source**: Signature‑copy baseline generation  
**Schema**: Array of objects (extends Generation Batch)
```json
[
  {
    "repo_slug": "string",
    "file_path": "string",
    "function_name": "string",
    "signature": "string",
    "human_docstring": "string | null",
    "ast_params": [ ... ],
    "baseline_docstring": "string",   // exact method signature
    "baseline_status": "string"       // always "success"
  }
]
```

## 5. Cleaned Generation Batch
**File**: `data/processed/generation_batch_{repo_slug}_cleaned.json`  
**Source**: Post‑processing (empty‑string handling)  
**Schema**: Array of objects (extends Generation Batch)
```json
[
  {
    "repo_slug": "string",
    "file_path": "string",
    "function_name": "string",
    "signature": "string",
    "human_docstring": "string | null",
    "ast_params": [ ... ],
    "generated_docstring": "string | null",
    "generation_status": "string",
    "error_message": "string | null",
    "needs_review": "boolean",
    "coverage_score": "float",
    "composite_score": "float"
  }
]
```
**Logic**:
- `needs_review` = `true` if `generated_docstring` is empty/whitespace; otherwise `false`.
- `coverage_score` = 0.0 when `needs_review` is `true`; otherwise computed later.
- `composite_score` = 0.0 when `needs_review` is `true`; otherwise computed as `0.4 * coverage_score + 0.6 * description_coverage_score`.

## 6. Aggregated Results
**File**: `data/processed/results.json`  
**Source**: Concatenation of all cleaned batches  
**Schema**: Array of objects (union of cleaned records)
```json
[
  {
    "repo_slug": "string",
    "file_path": "string",
    "function_name": "string",
    "signature": "string",
    "human_docstring": "string | null",
    "ast_params": [ ... ],
    "generated_docstring": "string | null",
    "generation_status": "string",
    "error_message": "string | null",
    "needs_review": "boolean",
    "coverage_score": "float",
    "composite_score": "float"
  }
]
```
**Constraints**:
- Total rows ≤ 20 000 (20 repos × ≤ 1 000 methods).

## 7. Results with Coverage Scores
**File**: `data/processed/results_with_coverage.json`  
**Source**: Coverage calculation step (`analyze.py --step=coverage`)  
**Schema**: Same as Aggregated Results, with guaranteed non‑null `coverage_score` for all non‑review rows and a newly added `description_coverage_score` field (averaged over **all** parameters, zero for undocumented ones).

## 8. Results with Semantic Similarity
**File**: `data/processed/results_with_scores.json`  
**Source**: Semantic similarity step (`analyze.py --step=similarity`)  
**Schema**: Array of objects (extends Results + Similarity)
```json
[
  {
    "repo_name": "string",
    "repo_slug": "string",
    "file_path": "string",
    "function_name": "string",
    "signature": "string",
    "human_docstring": "string | null",
    "ast_params": [ ... ],
    "generated_docstring": "string | null",
    "generation_status": "string",
    "error_message": "string | null",
    "needs_review": "boolean",
    "coverage_score": "float",
    "description_coverage_score": "float",
    "composite_score": "float",
    "semantic_similarity": "float"
  }
]
```

## 9. Human Evaluation Results
**File**: `data/processed/human_eval_results.json`  
**Source**: `human_eval.py` (random Likert rating collection)  
**Schema**:
```json
{
  "sample_size": "integer",
  "average_rating": "float",
  "ratings": [
    {
      "repo_slug": "string",
      "function_name": "string",
      "human_docstring": "string | null",
      "generated_docstring": "string",
      "likert_rating": "integer (1‑5)"
    }
  ]
}
```
**Constraints**: `average_rating` must be ≥ 4.0 to satisfy SC‑007.

## 10. Final Statistical Report
**File**: `data/processed/final_report.json`  
**Source**: Wilcoxon test step (`analyze.py --step=stats`)  
**Schema**: Single object (matches `contracts/results.schema.yaml`)
```json
{
  "total_pairs": "integer",
  "human_scores": [
    "float"
  ],
  "llm_scores": [
    "float"
  ],
  "baseline_scores": [
    "float"
  ],
  "wilcoxon_statistic": "float",
  "wilcoxon_p_value": "float",
  "effect_size": "float",
  "significance": "boolean",
  "execution_time_seconds": "float"
}
```

## 11. State Tracking
**File**: `state/projects/PROJ-318-evaluating-the-impact-of-code-generation.yaml`  
**Schema**: YAML
```yaml
artifact_hashes:
  "data/raw/repos/{repo_slug}.json": "sha256_hash_string"
  # additional entries added automatically after each step
```

---


