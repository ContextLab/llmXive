# Implementation Plan: Socratic Transformers (Negative Selection on Belief)

**Branch**: `582-socratic-transformers` | **Date**: 2026-06-29 | **Spec**: `specs/582-socratic-transformers/spec.md`
**Input**: Feature specification from `/specs/582-socratic-transformers/spec.md`

## Summary

This plan implements a selectionist mechanism to improve LLM reasoning by applying **negative selection on belief**. Rather than "teaching" the model correct answers, the system generates multiple reasoning paths, subjects them to adversarial critique (identifying logical contradictions), and fine-tunes the model to reject (avoid) the belief space associated with failed outputs. The implementation adheres to strict CPU-first constraints (Low-bit quantization, LoRA) and uses GSM8K and MATH datasets to generate Static, Dialogue (Selection), and Ablation (Neutral Critique) training sets. Statistical analysis (Independent Samples t-tests with Bonferroni correction) will compare the three conditions across multiple independent runs to isolate the effect of the adversarial signal.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `datasets` (Hugging Face), `transformers` (v4.40+), `peft` (LoRA), `bitsandbytes` (4-bit quantization), `scikit-learn` (stats), `accelerate` (CPU/Device management), `pytest` (testing).  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/results`) with checksums; no external DB.  
**Testing**: `pytest` with unit tests for data generation logic and integration tests using a **deterministic small-scale subset** of GSM8K to ensure reproducibility.  
**Target Platform**: Linux (GitHub Actions Free Tier: Multiple CPU, substantial RAM, GB Disk) with a GPU escape hatch (Kaggle) for the actual fine-tuning step if the model size exceeds CPU RAM.  
**Project Type**: Computational Research / ML Pipeline.  
**Performance Goals**: Complete data generation and fine-tuning within 6 hours on CPU (scaled) or 9 hours on Kaggle GPU.  
**Constraints**: Must run on free-tier CI; no external API keys; strict memory limits (limited RAM); Low-bit quantization mandatory for base model.  
**Scale/Scope**: A variable number of examples per condition (scaled to fit memory), fine-tuning on a small subset (e.g., -2GB of data) to ensure feasibility. **5 independent training runs (seeds)** per condition for statistical power.

> **Note on Compute**: The plan assumes a CPU-first approach for data generation and statistical analysis. The fine-tuning step (US2) is the only component that may require the GPU escape hatch (Kaggle) if the base model (e.g., LlamaB-4bit) exceeds 7GB RAM even with quantization. If the CPU run fails with OOM (exit code or "CUDA out of memory"), the runner will automatically offload to Kaggle.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Action / Rationale |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Compliant** | All seeds pinned in `code/`; datasets fetched via `datasets.load_dataset` from verified URLs; no manual intervention. Integration tests use deterministic small-scale data. |
| **II. Verified Accuracy** | **Compliant** | All dataset URLs (GSM8K, MATH, MMLU) are from the verified block; no invented citations. |
| **III. Data Hygiene** | **Compliant** | Raw data preserved; derivations (Static/Dialogue/Ablation tuples) written to new files with checksums recorded in `state/`. |
| **IV. Single Source of Truth** | **Compliant** | All results trace to `data/results`; no hand-typed statistics in the paper. |
| **V. Versioning Discipline** | **Compliant** | Content hashes used for artifacts; `updated_at` timestamp updated on changes. |
| **VI. Evaluation Integrity** | **Compliant** | Held-out benchmarks (GSM8K test, MMLU, MATH) strictly separated from training data generation. |
| **VII. Adversarial Dialogue Quality** | **Compliant** | A quality gate (T091 equivalent) will be implemented to discard trivial/neutral critiques before training. Logic: length > 20 tokens, no repetition (BLEU < 0.8), and revised answer differs from initial (unless "No error" noted). |

## Project Structure

### Documentation (this feature)

```text
specs/582-socratic-transformers/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── data_tuple.schema.yaml
│   ├── evaluation_metrics.schema.yaml
│   └── ...
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-582-socratic-transformers-dialogue-based-sel/
├── code/
│   ├── src/
│   │   ├── __init__.py
│   │   ├── data/
│   │   │   ├── __init__.py
│   │   │   ├── loader.py          # Downloads GSM8K/MATH/MMLU
│   │   │   ├── generator.py       # Creates Static/Dialogue/Ablation tuples
│   │   │   └── quality_gate.py    # Validates adversarial content
│   │   ├── model/
│   │   │   ├── __init__.py
│   │   │   ├── trainer.py         # LoRA fine-tuning (CPU/GPU aware)
│   │   │   └── quantizer.py       # 4-bit loading logic
│   │   ├── eval/
│   │   │   ├── __init__.py
│   │   │   └── metrics.py         # Accuracy, t-tests, Bonferroni
│   │   └── utils/
│   │       ├── config.py          # Seeds, model IDs, paths
│   │       └── io.py              # Checksumming, JSONL handling
│   ├── tests/
│   │   ├── unit/
│   │   │   └── test_generator.py
│   │   └── integration/
│   │       └── test_training.py
│   ├── requirements.txt
│   └── run_pipeline.sh            # Entry point
├── data/
│   ├── raw/                       # Downloaded datasets (checksummed)
│   ├── processed/                 # Generated tuples (Static/Dialogue/Ablation)
│   └── results/                   # Evaluation metrics, logs
└── state/
    └── projects/PROJ-582-.../
        └── artifact_hashes.yaml   # Checksums for all data
```

**Structure Decision**: Single project structure (`code/src`) is selected to minimize overhead. The `data` directory is strictly read-only for raw data and write-only for processed results to satisfy Data Hygiene. The `state` directory tracks hashes for reproducibility.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **GPU Escape Hatch** | Low-bit quantization of large-scale models on constrained RAM is feasible., but LoRA fine-tuning activation memory may exceed limits. | Pure CPU fine-tuning might OOM or take >24h. The Kaggle offload (triggered by exit code 137 or "CUDA out of memory") is the only honest path to results. |
| **Ablation Condition** | Required to isolate the effect of *content* vs. *token length*. | A simple "Static vs. Selection" comparison cannot rule out that the extra tokens in the dialogue (critique) are the cause of improvement. |
| **Quality Gate** | Prevents "degenerate generation" (trivial critiques) from polluting training data. | Without a gate, the model might learn to ignore noise, confounding the "negative selection" hypothesis. |
| **Multiple Runs** | Required for statistical power (t-test). | A single run per condition yields a single scalar, making a t-test impossible. Multiple runs per condition ensure a distribution. |
| **Balanced Sampling** | Required to prevent confounding by sample size. | If Selection yields fewer valid tuples, the comparison is confounded. Regeneration ensures equal N. |
| **Hard Timeout** | Required by FR-008 to prevent infinite loops. | Without a timeout, a stuck process could exceed the 6h CI limit. |