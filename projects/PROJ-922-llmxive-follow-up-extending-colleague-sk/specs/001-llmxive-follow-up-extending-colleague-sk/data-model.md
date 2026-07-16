# Data Model: llmXive follow-up: extending "COLLEAGUE.SKILL"

## Overview

This document defines the data structures, schemas, and storage formats for the `llmXive` follow-up project. All data is stored in `data/` with checksums recorded in `state/`.

## Data Flow

1.  **Generation**: `code/data_generation/profiles.py` and `tasks.py` create raw JSON files.
2.  **Inference**: `code/inference/engine.py` reads raw data, runs models, writes outputs to `data/interim/`.
3.  **Evaluation**: `code/evaluation/metrics.py` reads outputs and raw data, writes metrics to `data/processed/`.
4.  **Analysis**: `code/analysis/stats.py` reads `data/processed/` for statistical modeling.

## Data Entities

### 1. Expert Profile (`data/raw/profiles.jsonl`)

Each line is a JSON object representing an expert.

**Schema**:
```yaml
id: string (UUID)
domain: string (e.g., "coding", "math", "creative")
capability_track:
  rules: list of strings (e.g., "Must use Python 3.11", "No external libraries")
  heuristics: list of strings (e.g., "Prefer list comprehensions", "Check edge cases first")
behavior_track:
  style_keywords: list of strings (e.g., "As an expert...", "Let's break this down")
  tone: string (e.g., "formal", "conversational", "pedagogical")
  forbidden_phrases: list of strings (e.g., "I think", "Maybe")
created_at: string (ISO 8601)
checksum: string (SHA-256)
```

### 2. Task Scenario (`data/raw/tasks.jsonl`)

Each line is a JSON object representing a task.

**Schema**:
```yaml
id: string (UUID)
domain: string (e.g., "coding", "math")
difficulty: string (e.g., "easy", "medium", "hard")
prompt: string (The user input)
context: string (Ground-truth facts, code snippets, or constraints)
ground_truth_source: string (Reference to external source, e.g., "Project Gutenberg: Text X")
ground_truth_rules:
  - string (Expected logical steps)
  - string (Required output format)
hallucination_traps: list of strings (Facts NOT in context but present in external source, used to detect hallucination)
created_at: string (ISO 8601)
checksum: string (SHA-256)
```

### 3. Model Output (`data/interim/outputs/{condition}/{profile_id}_{task_id}.json`)

One file per inference run.

**Schema**:
```yaml
profile_id: string
task_id: string
condition: string (Monolithic, Separated, Generic)
model_name: string
generation_params:
  temperature: float
  max_tokens: int
  seed: int
output_text: string
metadata:
  generation_time_sec: float
  token_count: int
  status: string (success, timeout, error)
```

### 4. Evaluation Metrics (`data/processed/metrics.csv`)

Aggregated metrics for analysis.

**Schema**:
```csv
profile_id,task_id,condition,heuristic_adherence,hallucination_rate,style_consistency,style_deviation_score,generation_time_sec,status
```
- `heuristic_adherence`: 0 or 1.
- `hallucination_rate`: float (0.0 to 1.0, ratio of hallucinated facts).
- `style_consistency`: float (0.0 to 1.0, composite score).
- `style_deviation_score`: float (0.0 to 1.0, deviation from target tone).

## Storage & Hygiene

- **Format**: JSONL for raw data (streaming friendly), CSV for processed metrics.
- **Checksums**: SHA-256 of each file stored in `state/`.
- **PII**: No PII in synthetic data. All profiles are fictional.
- **Versioning**: `data/` files are immutable. New versions are written with timestamps (e.g., `profiles_v1.jsonl`).

## Data Generation Strategy

- **Profiles**: A set of unique profiles, stratified across 5 domains (approximately 2 per domain).
- **Tasks**: A set of unique tasks, stratified across 5 domains.
- **Combinations**: 10 × 50 = 500 unique profile-task pairs.
- **Conditions**: Each pair run under 2 conditions (Monolithic, Separated) = 1,000 total runs.