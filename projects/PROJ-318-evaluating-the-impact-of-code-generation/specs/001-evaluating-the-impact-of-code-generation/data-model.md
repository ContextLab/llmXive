# Data Model Specification
# Project: PROJ-318-evaluating-the-impact-of-code-generation
# Description: Schema definitions for all data artifacts produced and consumed by the pipeline.

## 1. Raw Repository List
**File**: `data/raw/frozen_repo_list.json`
**Source**: PyPI/HuggingFace (T010)
**Schema**: Array of objects
```json
[
 {
 "repo_url": "string (GitHub URL)",
 "github_url": "string (GitHub URL)",
 "star_count": "integer"
 }
]
```
**Constraints**: Must contain exactly 20 items. Sorted deterministically by star count.

## 2. Extracted Repository Data (Ground Truth)
**File**: `data/raw/repos/{repo_slug}.json`
**Source**: AST Parser (T017, T018)
**Schema**: Array of objects
```json
[
 {
 "repo_slug": "string",
 "file_path": "string (relative to repo root)",
 "function_name": "string",
 "signature": "string (full function signature)",
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
- `human_docstring` MUST be `null` (not empty string) if no docstring exists.
- Array length per file MUST be <= 1000 (enforced by T018).
- `ast_params` is a list of parameter objects extracted from the AST.

## 3. Generation Batch (Intermediate)
**File**: `data/processed/generation_batch_{repo_slug}.json`
**Source**: LLM Generation (T024)
**Schema**: Array of objects (extends Extraction schema)
```json
[
 {
 "repo_slug": "string",
 "file_path": "string",
 "function_name": "string",
 "signature": "string",
 "human_docstring": "string | null",
 "ast_params": [... ],
 "generated_docstring": "string | null"
 }
]
```
**Constraints**:
- `generated_docstring` may be empty string, whitespace, or null if generation failed or produced no text.
- Row count <= 1000 per file.

## 4. Cleaned Generation Batch (Intermediate)
**File**: `data/processed/generation_batch_{repo_slug}_cleaned.json`
**Source**: Post-Processing (T027)
**Description**: Intermediate schema for records after empty/whitespace docstring handling.
**Schema**: Array of objects (extends Generation Batch schema)
```json
[
 {
 "repo_slug": "string",
 "file_path": "string",
 "function_name": "string",
 "signature": "string",
 "human_docstring": "string | null",
 "ast_params": [
 {
 "name": "string",
 "annotation": "string | null",
 "default": "string | null"
 }
 ],
 "generated_docstring": "string | null",
 "needs_review": "boolean",
 "coverage_score": "float"
 }
]
```
**Field Definitions**:
- `needs_review`: `true` if `generated_docstring` is empty or whitespace-only; `false` otherwise.
- `coverage_score`: `0.0` if `needs_review` is `true`; otherwise calculated based on parameter matching (T033).
- **Logic**:
 ```python
 if not generated_docstring.strip():
 needs_review = True
 coverage_score = 0.0
 else:
 needs_review = False
 coverage_score = <calculated value later> # Initially 0.0 or placeholder if not yet calculated
 ```
**Constraints**:
- This file is the input for the aggregation step (T026).
- All records from the input batch file MUST be present here.

## 5. Aggregated Results
**File**: `data/processed/results.json`
**Source**: Aggregation (T026)
**Schema**: Array of objects (union of all cleaned batches)
```json
[
 {
 "repo_slug": "string",
 "file_path": "string",
 "function_name": "string",
 "signature": "string",
 "human_docstring": "string | null",
 "ast_params": [... ],
 "generated_docstring": "string | null",
 "needs_review": "boolean",
 "coverage_score": "float"
 }
]
```
**Constraints**:
- Total row count <= 20,000 (20 repos * 1000 methods).
- Must preserve `ast_params` from raw extraction.

## 6. Results with Coverage Scores
**File**: `data/processed/results_with_coverage.json`
**Source**: Analysis Step: Coverage (T033)
**Schema**: Array of objects (extends Aggregated Results)
```json
[
 {
 "repo_slug": "string",
 "file_path": "string",
 "function_name": "string",
 "signature": "string",
 "human_docstring": "string | null",
 "ast_params": [... ],
 "generated_docstring": "string | null",
 "needs_review": "boolean",
 "coverage_score": "float",
 "parse_error": "boolean (optional)"
 }
]
```
**Field Definitions**:
- `coverage_score`: Calculated as `(matched params / total ast_params)`.
- `parse_error`: `true` if `docstring_parser` failed to parse the generated docstring.

## 7. Results with Semantic Similarity
**File**: `data/processed/results_with_scores.json`
**Source**: Analysis Step: Similarity (T034)
**Schema**: Array of objects (extends Results with Coverage)
```json
[
 {
 "repo_slug": "string",
 "file_path": "string",
 "function_name": "string",
 "signature": "string",
 "human_docstring": "string | null",
 "ast_params": [... ],
 "generated_docstring": "string | null",
 "needs_review": "boolean",
 "coverage_score": "float",
 "parse_error": "boolean (optional)",
 "semantic_similarity": "float"
 }
]
```
**Field Definitions**:
- `semantic_similarity`: Cosine similarity between human and generated docstring embeddings.

## 8. Final Statistical Report
**File**: `data/processed/final_report.json`
**Source**: Analysis Step: Stats (T037)
**Schema**: Single object
```json
{
 "total_methods": "integer",
 "human_coverage_mean": "float",
 "llm_coverage_mean": "float",
 "wilcoxon_statistic": "float",
 "wilcoxon_pvalue": "float",
 "small_sample_warning": "boolean"
}
```

## 9. State Tracking
**File**: `state/projects/PROJ-318-evaluating-the-impact-of-code-generation.yaml`
**Schema**: YAML
```yaml
artifact_hashes:
 "data/raw/repos/{repo_slug}.json": "sha256_hash_string"
...
```