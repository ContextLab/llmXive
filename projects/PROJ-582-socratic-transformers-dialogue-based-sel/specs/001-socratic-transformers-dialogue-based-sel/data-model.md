# Data Model: Socratic Transformers

## 1. Overview

This document defines the data schemas for the Socratic Transformers project. All data is stored in JSONL format for streaming compatibility. Checksums (SHA-256) are recorded for every file in `data/`.

## 2. Raw Data Schema

### 2.1 GSM8K (Source)
- **Source**: `https://huggingface.co/datasets/openai/gsm8k`
- **Format**: Parquet (converted to JSONL for processing)
- **Fields**:
  - `question`: `string` (The math problem)
  - `answer`: `string` (The ground truth solution with steps)

### 2.2 MATH-500 (Evaluation)
- **Source**: `https://huggingface.co/datasets/HuggingFaceH4/MATH-500`
- **Format**: JSONL
- **Fields**:
  - `problem`: `string`
  - `solution`: `string`
  - `level`: `string` (optional)
  - `type`: `string` (optional)

### 2.3 MMLU-STEM (Evaluation)
- **Source**: `https://huggingface.co/datasets/cais/mmlu`
- **Format**: JSONL
- **Fields**:
  - `question`: `string`
  - `choices`: `array[string]`
  - `answer`: `string` (index of correct choice)

## 3. Processed Data Schema

### 3.1 Static Tuples (Augmented)
- **Path**: `data/processed/static_tuples.jsonl`
- **Schema**:
  ```yaml
  question: string
  initial_answer: string
  critique: string # Neutral placeholder, same token length as typical critique
  revised_answer: string # Same as initial_answer
  condition: "static"
  quality_score: float # 1.0 (always passes)
  ```

### 3.2 Dialogue Tuples (Selection Condition)
- **Path**: `data/processed/dialogue_tuples.jsonl`
- **Schema**:
  ```yaml
  question: string
  initial_answer: string
  critique: string
  revised_answer: string
  condition: "selection"
  quality_score: float # 0.0 to 1.0, output of quality gate
  is_correct_initial: boolean # True if initial answer was correct
  ```

### 3.3 Ablation Tuples (Ablation Condition)
- **Path**: `data/processed/ablation_tuples.jsonl`
- **Schema**:
  ```yaml
  question: string
  initial_answer: string
  critique: string # Shuffled version of selection critique, same token count
  revised_answer: string
  condition: "ablation"
  quality_score: float
  token_count: integer # Exact token count of the critique
  ```

## 4. Results Schema

### 4.1 Evaluation Metrics
- **Path**: `data/results/metrics.json`
- **Schema**:
  ```yaml
  run_id: string
  condition: string
  dataset: string
  accuracy: float
  count: int
  seed: int
  ```

### 4.2 Statistical Tests
- **Path**: `data/results/statistics.json`
- **Schema**:
  ```yaml
  test_type: string # e.g., "independent_t_test"
  comparison: string # e.g., "selection_vs_ablation"
  statistic: float
  p_value: float
  corrected_p_value: float # Bonferroni corrected
  significant: boolean
  effect_size: float # Cohen's d
  ```

## 5. Data Hygiene Rules

1.  **Immutability**: Raw data files in `data/raw` are never modified.
2.  **Checksums**: Every file in `data/` has a corresponding SHA-256 hash stored in `state/artifact_hashes.yaml`.
3.  **Derivation**: Any transformation (e.g., generating critiques) must produce a new file with a new hash.
4.  **PII**: No personally identifiable information is allowed. GSM8K, MATH, and MMLU are synthetic/academic and PII-free.