# Data Model: llmXive follow-up: extending "Code2LoRA: Hypernetwork-Generated Adapters for Code Language Models under Software Evolution"

## 1. Overview

This document defines the data structures, schemas, and relationships for the AST-based adapter generation pipeline. The model ensures reproducibility, traceability, and compliance with the project constitution.

## 2. Core Entities

### 2.1 Repository
A collection of Python source files representing a specific code evolution task.

- **Attributes**:
  - `repo_id`: Unique identifier (hash of repo content or commit hash).
  - `commit_hash`: Git commit hash.
  - `source_files`: List of file paths.
  - `feature_vector`: Numerical vector derived from AST metrics.

### 2.2 Feature Vector
A fixed-length numerical representation of a repository's syntactic properties.

- **Attributes**:
  - `repo_id`: Foreign key to Repository.
  - `cyclomatic_complexity`: Average cyclomatic complexity across files.
  - `depth_of_inheritance`: Average depth of inheritance tree.
  - `import_centrality`: Degree centrality of the import graph.
  - `token_histogram`: Frequency distribution of token types.
  - `metadata`: JSON blob with parsing stats (e.g., files skipped, errors).

### 2.3 Adapter
The generated LoRA weight matrix specific to a repository.

- **Attributes**:
  - `adapter_id`: Unique identifier.
  - `repo_id`: Foreign key to Repository.
  - `base_model`: Name/version of the base LLM used.
  - `hypernetwork_config`: JSON blob with MLP architecture details.
  - `weights_path`: Path to `.safetensors` or `.bin` file.
  - `generation_time_ms`: Latency of adapter generation.
  - `accuracy`: Exact-match score on test set (post-evaluation).

### 2.4 Test Case
An assertion-completion task from RepoPeftBench.

- **Attributes**:
  - `task_id`: Unique identifier.
  - `repo_id`: Foreign key to Repository.
  - `assertion`: Ground-truth assertion code.
  - `predicted_assertion`: Model-generated assertion.
  - `exact_match`: Boolean (True/False).
  - `failure_mode`: Classification of error (if any).

## 3. Data Flow

1. **Raw Data**: `data/raw/ood_test.parquet` (RepoPeftBench).
2. **Feature Extraction**: `code/feature_extractor/ast_parser.py` → `data/processed/feature_vectors.jsonl`.
3. **Adapter Generation**: `code/hypernetwork/adapter_generator.py` → `data/adapters/{repo_id}.safetensors`.
4. **Evaluation**: `code/evaluation/runner.py` → `data/results/{repo_id}_results.json`.
5. **Aggregation**: `code/evaluation/sensitivity.py` → `data/results/sensitivity_curve.csv`.

## 4. Constraints & Invariants

- **Immutability**: Raw data is never modified. Derivations are written to new files.
- **Checksums**: All files in `data/` are checksummed (SHA-256) and recorded in `state/`.
- **Determinism**: Feature extraction must yield identical results for identical source code (Constitution Principle VI).
- **Memory Limit**: Feature vector construction must not exceed 6 GB RAM (FR-008).

## 5. Schema Definitions

See `contracts/` directory for machine-readable schemas.
