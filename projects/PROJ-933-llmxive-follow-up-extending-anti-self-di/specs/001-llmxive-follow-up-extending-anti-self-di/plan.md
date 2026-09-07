# Implementation Plan: llmXive follow-up: extending "Anti-Self-Distillation for Reasoning RL via Pointwise Mutual Information"

**Branch**: `001-llmxive-followup` | **Date**: 2026-08-01 | **Spec**: `spec.md`

## Summary

This project extends the "Anti-Self-Distillation" (AntiSD) mechanism to non-verifiable reasoning domains (e.g., ethical dilemmas, open-ended creativity) where no single ground-truth solution exists. Instead of a single target, the system simulates a "privileged context" (one sampled rationale) and a "target distribution" (the set of remaining diverse rationales). The core innovation is the use of a **deliberation reward** derived from ascending Jensen-Shannon (JS) divergence between the student's output and the average teacher distribution (computed from all unselected rationales).

The implementation targets a **CPU-only** GitHub Actions runner (2 vCPU, 7GB RAM) using a small transformer (e.g., DistilBERT or TinyLlama) for feasibility. It will ingest UltraFeedback and Dolly datasets, filter for prompts with ≥4 distinct traces, simulate the training environment, and validate the hypothesis that AntiSD preserves reasoning diversity and deliberation markers compared to standard self-distillation.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU), `transformers`, `datasets`, `scikit-learn`, `nltk` (for BLEU), `sentence-transformers` (for semantic similarity), `pandas`, `numpy`, `matplotlib`.  
**Storage**: Local ephemeral storage in `/tmp` for dataset shards; outputs written to `data/` and `results/`.  
**Testing**: `pytest` for unit tests; custom integration tests for the training loop gradient inversion.  
**Target Platform**: Linux (GitHub Actions free-tier runner).  
**Project Type**: Computational Research / Machine Learning Pipeline.  
**Performance Goals**: Complete training and analysis within 6 hours; peak RAM < 6.5 GB.  
**Constraints**: No GPU available for primary training; must use streaming or sampling for large datasets; strict 5.5h timeout.  
**Scale/Scope**: Processing ~30-50 prompts with 250 training steps each; generating ~1500 trajectories total.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Action/Reference |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Compliant** | Plan mandates pinned seeds in `code/` and canonical dataset sources (HuggingFace). `requirements.txt` will pin versions. |
| **II. Verified Accuracy** | **Compliant** | Citations restricted to the "Verified datasets" block in the prompt. No fabricated URLs. |
| **III. Data Hygiene** | **Compliant** | Plan includes checksumming of downloaded datasets in `data/`. No in-place modification; derivations are new files. |
| **IV. Single Source of Truth** | **Compliant** | All metrics (BLEU, JS Divergence, Deliberation counts) will be computed by code and stored in `data/` JSON/CSV. Paper will reference these files. |
| **V. Versioning Discipline** | **Compliant** | Artifacts will carry content hashes; `state/` file updated on changes. |
| **VI. Multi-Solution Context Simulation** | **Compliant** | Plan explicitly details the random sampling of one "privileged context" and retention of others as the target distribution (FR-002, FR-014). |
| **VII. Token-Level Entropy & Diversity** | **Compliant** | Plan includes specific logic to count deliberation tokens ("Wait", "However") and compute pairwise BLEU/Semantic similarity (FR-005, FR-009). |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-followup/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    ├── training_output.schema.yaml
    └── analysis_results.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-933-llmxive-followup-extending-anti-self-di/code/
├── data/
│   ├── download.py          # Scripts to fetch and checksum datasets
│   ├── preprocess.py        # Filter prompts with ≥4 traces, split context
│   └── raw/                 # Downloaded parquet/jsonl files
├── models/
│   ├── anti_sd_loop.py      # Custom PyTorch training loop with gradient inversion
│   ├── inference_only.py    # Teacher distribution computation
│   └── metrics.py           # BLEU, JS Divergence, Deliberation token counting
├── analysis/
│   ├── statistical_test.py  # Wilcoxon signed-rank test
│   └── visualize.py         # Plotting loss curves, diversity metrics
├── config/
│   └── settings.yaml        # Seeds, hyperparameters, timeout limits
├── main.py                  # Orchestration script
└── requirements.txt
```

**Structure Decision**: A single monolithic `code/` directory is chosen for simplicity and to minimize overhead on the CI runner. The separation into `data/`, `models/`, and `analysis/` aligns with the logical flow of the research pipeline (Ingest → Train → Analyze) and satisfies the "Single Source of Truth" principle by keeping raw data and derived results distinct.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Custom Training Loop** | FR-008 requires token-level gradient inversion (ascending JS divergence) which standard RL libraries (e.g., `stable-baselines3`) do not support out-of-the-box. | Using a pre-built RL library would require complex hacking or would fail to implement the specific "AntiSD" gradient inversion logic defined in the spec. |
| **Streaming/Sampling** | Datasets (UltraFeedback) exceed the 7GB RAM limit if fully loaded. | Loading the full dataset would cause OOM crashes on the free-tier runner. Streaming or strict sampling is the only feasible path. |
| **Wilcoxon Test** | FR-017 mandates non-parametric testing due to likely non-normal distributions. | A t-test assumes normality which cannot be guaranteed for small sample sizes of complex LLM outputs. |

## Phase Breakdown

### Phase 0: Research & Data Verification
*   **Goal**: Verify dataset availability and variable fit.
*   **FR-001, FR-016**: Verify UltraFeedback/Dolly contain ≥4 traces per prompt.
*   **FR-014**: Verify ability to run "Inference-Only Pass" on CPU.
*   **Output**: `research.md` confirming dataset strategy and feasibility.

### Phase 1: Data Model & Contracts
*   **Goal**: Define schemas for data ingestion, training outputs, and analysis results.
*   **FR-002, FR-005**: Define structure for "Privileged Context" vs "Target Distribution".
*   **Output**: `data-model.md`, `contracts/*.schema.yaml`.

### Phase 2: Implementation (Code Generation)
*   **Goal**: Generate the Python scripts for data loading, the custom training loop, and analysis.
*   **FR-003, FR-004**: Implement JS divergence calculation and gradient inversion.
*   **FR-007, FR-013**: Implement 5.5h timeout and power analysis.
*   **Output**: Python code in `code/`.

### Phase 3: Execution & Validation
*   **Goal**: Run the pipeline on CI, collect metrics, and validate against success criteria.
*   **SC-001, SC-003**: Compute Pearson correlation and Wilcoxon p-values.
*   **SC-005**: Monitor RAM usage.
*   **Output**: Final results in `data/` and `paper/`.
