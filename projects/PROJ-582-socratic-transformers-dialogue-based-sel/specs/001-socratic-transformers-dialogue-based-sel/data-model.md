# Data Model: Socratic Transformers (PROJ-582)

## 1. Overview

This document defines the data structures, schemas, and flow for the Socratic Transformers project. All data artifacts are stored in `data/` and versioned via checksums.

## 2. Directory Structure

```text
data/
├── raw/
│   ├── gsm8k_train.parquet      # Downloaded GSM8K train
│   ├── gsm8k_test.parquet       # Downloaded GSM8K test
│   ├── math_train.parquet       # Downloaded MATH train
│   └── checksums.json           # SHA256 hashes for all raw files
├── processed/
│   ├── static/
│   │   ├── gsm8k_static.jsonl   # Static QA tuples
│   │   └── math_static.jsonl
│   ├── dialogue/
│   │   ├── gsm8k_dialogue.jsonl # (Q, A_init, Critique, A_rev)
│   │   └── math_dialogue.jsonl
│   ├── ablation/
│   │   ├── gsm8k_ablation.jsonl # (Q, A_init, Distractor, A_rev)
│   │   └── math_ablation.jsonl
│   └── train_splits/
│       ├── selection_train.jsonl
│       ├── ablation_train.jsonl
│       └── static_train.jsonl
└── results/
    ├── metrics.json             # Accuracy, p-values, effect sizes
    ├── training_logs/           # Loss curves, logs
    └── evaluation_plots/        # Generated figures
```

## 3. Data Schemas

### 3.1 Raw Dataset Schema (Inherited)
- **GSM8K**: `question` (str), `answer` (str)
- **MATH**: `problem` (str), `solution` (str)

### 3.2 Static Tuple Schema
```json
{
  "id": "string",
  "source": "gsm8k" | "math",
  "question": "string",
  "answer": "string",
  "split": "train" | "test"
}
```

### 3.3 Dialogue Tuple Schema (Selection Condition)
```json
{
  "id": "string",
  "source": "gsm8k" | "math",
  "question": "string",
  "initial_answer": "string",
  "critique": "string",
  "revised_answer": "string",
  "critique_type": "logical_contradiction" | "unsupported_assumption" | "calculation_error",
  "quality_score": "float (0.0-1.0)"
}
```

### 3.4 Ablation Tuple Schema
```json
{
  "id": "string",
  "source": "gsm8k" | "math",
  "question": "string",
  "initial_answer": "string",
  "critique": "string",  // Syntactic Distractor (equivalent length/complexity)
  "revised_answer": "string",
  "token_count": "int",
  "complexity_score": "float" // Estimated syntactic complexity (e.g., parse tree depth)
}
```

### 3.5 Evaluation Metrics Schema
```json
{
  "experiment_id": "string",
  "condition": "selection" | "ablation" | "static",
  "dataset": "gsm8k_test" | "mmlu_stem",
  "accuracy": "float",
  "samples": "int",
  "timestamp": "ISO8601"
}
```

## 4. Data Flow

1. **Download**: `src/data/download.py` fetches raw data from verified URLs and computes checksums.
2. **Static Extraction**: `src/data/static_extractor.py` converts raw data to `static/*.jsonl`.
3. **Dialogue Generation**:
   - `src/data/generate_dialogue.py` generates `(Q, A_init, Critique, A_rev)` tuples using a **frozen Critic Model**.
   - **Quality Gate**: Tuples with `quality_score < 0.7` are discarded.
4. **Ablation Generation**: `src/data/ablation.py` replaces critiques with **Syntactic Distractors** of matching token length and complexity.
5. **Splitting**: Data is split into `train` and `test` sets (strict separation).
6. **Training**: `src/train/train_loop.py` consumes `train_splits/*.jsonl`.
7. **Evaluation**: `src/utils/metrics.py` computes accuracy on `test` sets.
8. **Aggregation**: Results written to `results/metrics.json`.

## 5. Data Integrity & Hygiene

- **Checksums**: All raw files are checksummed. Any change invalidates downstream artifacts.
- **Immutability**: `data/raw/` files are never modified. Derivations are written to new files in `data/processed/`.
- **PII**: No PII expected in GSM8K/MATH. Automated scan performed on `data/processed/` before commit.
- **Versioning**: Each generated file includes a `generated_at` timestamp and `source_hash` (hash of input data).