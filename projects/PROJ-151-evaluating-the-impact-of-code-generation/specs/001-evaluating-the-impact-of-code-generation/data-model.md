# Data Model: Evaluating the Impact of Code Generation Models on Code Review Efficiency

## Key Entities

### 1. Code Snippet
Represents a single function or change block (Human or Generated).

- **id**: `str` (UUID)  
- **origin**: `str` (Enum: `"human"`, `"generated"`)  
- **language**: `str` (Enum: `"python"`, `"java"`)  
- **loc**: `int` (Lines of Code)  
- **cyclomatic_complexity**: `float`  
- **maintainability_index**: `float`  
- **pylint_score**: `float` (0‑10, `null` for Java)  
- **checkstyle_score**: `float` (null for Python)  
- **token_count**: `int`  
- **content_hash**: `str` (SHA256 of the code)  
- **status**: `str` (Enum: `"valid"`, `"invalid_syntax"`, `"trivial"`, `"semantic_failure"`, `"failed"`) – indicates whether the snippet passed the **semantic validity filter**.  
- **context_snapshot**: `str` (Optional, for generated only) – The reconstructed problem context used in the prompt.

### 2. Review Record
Represents a PR review event (human data) or a validation‑study record.

- **id**: `str` (UUID)  
- **snippet_id**: `str` (FK to Code Snippet)  
- **review_time_seconds**: `float` (nullable – missing in primary cohort, present in validation)  
- **comment_count**: `int`  
- **proxy_effort**: `int` – derived field equal to `comment_count` when `review_time_seconds` is null.  
- **perceived_difficulty**: `int` (1‑5 Likert, nullable – present only in validation study)  
- **project_id**: `str` (for random‑effects grouping)  

### 3. Experiment Pair
Links a human snippet to its LLM‑generated counterpart for the **exact same problem instance**.

- **id**: `str` (UUID)  
- **human_snippet_id**: `str`  
- **generated_snippet_id**: `str`  
- **problem_statement**: `str` (derived from the PR title)  
- **context_snapshot**: `str` (The reconstructed context used for generation)

### 4. Provenance Record
Links generated code to generation parameters (FR‑008).

- **id**: `str` (UUID)  
- **generated_snippet_id**: `str`  
- **model_id**: `str` (e.g., `"StarCoder-1B"` or `"CodeGen-350M"`)  
- **prompt_string**: `str` (Full prompt including context)  
- **random_seed**: `int`  
- **timestamp**: `datetime`  
- **generation_file_path**: `str`  

## Data Flow

1. **Ingestion** → `data/processed/prs_filtered.csv` (human PRs).  
2. **Context Reconstruction** → Extract context from diffs.  
3. **Generation** → `data/generated/snippets/` + `data/generated_provenance.csv`.  
4. **Semantic Validity Filter** → snippets flagged with `status`.  
5. **Metrics** → `data/metrics/all_metrics.csv` (includes `status` and language-specific scores).  
6. **Analysis** → `data/models/lmm_results.json`.  
7. **Validation** → `data/models/validation_results.csv` (includes bias analysis).

## File Structure

```
data/
├── raw/
│   └── gerrit_dump.tar.gz
├── processed/
│   ├── prs_filtered.csv
│   └── pairs.csv
├── generated/
│   ├── snippets/
│   │   ├── snip_001.py
│   │   └── …
│   └── …
├── metrics/
│   └── all_metrics.csv
├── models/
│   ├── lmm_results.json
│   └── validation_results.csv
└── provenance/
    └── generated_provenance.csv
```
