# Implementation Plan: llmXive follow-up: extending "Qwen-Image-Flash: Beyond Objective Design"

**Branch**: `001-llmxive-follow-up` | **Date**: 2026-07-12 | **Spec**: `specs/001-llmxive-follow-up-extending-qwen-image-f/spec.md`
**Input**: Feature specification from `specs/001-llmxive-follow-up-extending-qwen-image-f/spec.md`

## Summary

This project implements a CPU‑tractable research pipeline to investigate the **Coherence over Diversity** hypothesis in synthetic logical reasoning. The pipeline generates a controlled‑entropy dataset, validates trace consistency, distills a <100 M‑parameter student model from a teacher's 10‑step chain‑of‑thought (CoT) traces, and statistically evaluates whether the Low‑Entropy training regime yields faster convergence and higher accuracy. All steps are constrained to run on a GitHub Actions free‑tier runner (standard CPU and memory resources) within a fixed wall‑clock budget.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU‑only wheel), `transformers` (small models), `scikit-learn`, `scipy`, `pandas`, `numpy`, `pyyaml`  
**Storage**: Local `data/` directory (synthetic CSV/JSONL), schemas defined in `contracts/`  
**Testing**: `pytest` (unit tests for generator, integration tests for pipeline)  
**Target Platform**: Linux (GitHub Actions free‑tier runner)  
**Constraints**: No CUDA, no bitsandbytes, no large‑model training; student model < 100 M parameters; max RAM < 7 GB; total runtime < 6 h.

## Constitution Check

| Principle | Status | Verification Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds pinned; `requirements.txt` version‑locked; data checksummed. |
| **II. Verified Accuracy** | **PASS** | No external dataset URLs are cited; all data is synthetically generated. |
| **III. Data Hygiene** | **PASS** | Synthetic data generated programmatically; checksums recorded; no PII. |
| **IV. Single Source of Truth** | **PASS** | All statistics derived from `data/` logs; no hand‑typed numbers. |
| **V. Versioning Discipline** | **PASS** | Artifact hashes tracked; `updated_at` timestamps updated on change. |
| **VI. Controlled Entropy** | **PASS** | Generator explicitly parameterizes entropy; metadata flags included; pre‑training entropy validation performed. |
| **VII. CPU‑Bound Constraint** | **PASS** | Student model < 100 M params; CPU‑only training; runtime budgeted; fail‑fast on timeout. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-follow-up-extending-qwen-image-f/
├── plan.md               # This file
├── research.md           # Phase 0 output
├── data-model.md         # Phase 1 output
├── quickstart.md         # Phase 1 output
├── contracts/
│   ├── synthetic_problem.schema.yaml
│   ├── distillation_run.schema.yaml
│   └── statistical_result.schema.yaml
└── tasks.md              # Phase 2 output (created later)
```

### Source Code (repository root)

```text
projects/PROJ-845-llmxive-follow-up-extending-qwen-image-f/
├── data/
│   ├── raw/                  # Generated synthetic data (train & test)
│   │   ├── high_entropy.csv
│   │   ├── low_entropy.csv
│   │   ├── target_specific.csv
│   │   └── test_set.csv
│   └── processed/            # Tokenized tensors, logs, etc.
├── code/
│   ├── __init__.py
│   ├── generators/
│   │   └── logic_generator.py      # Rule‑based entropy‑controlled generator
│   ├── models/
│   │   ├── teacher.py              # Teacher CoT trace generator (mock LLM)
│   │   └── student.py              # Small transformer (<100 M params)
│   ├── training/
│   │   └── distill_loop.py         # CPU‑only KL‑divergence training
│   ├── analysis/
│   │   ├── metrics.py              # Entropy, accuracy utilities
│   │   └── stats.py                # ANOVA, t‑tests, Bonferroni correction
│   └── main.py                     # Pipeline orchestrator
├── tests/
│   ├── unit/
│   │   └── test_generator.py
│   └── integration/
│       └── test_pipeline.py
├── requirements.txt
└── README.md
```

**Structure Decision**: A single‑project layout keeps the pipeline lightweight and ensures all phases can be executed sequentially within the CI constraints.

## Phase Overview (ordered for compute feasibility)

1. **Generate Synthetic Data (Phase 0)**  
   - `logic_generator.py` creates three training subsets (High, Low, Target) and a **Generalization Set** (`test_set.csv`) with **equal** numbers of each entropy level and structural distinctness from training data.  
   - Each problem is written as a `SyntheticProblem` record with `entropy_level`, `entropy_score`, `structure_type`, and `set_type` (`train` or `test_generalization`).

2. **Validate Entropy (Phase 0‑A)**  
   - Compute per‑sample entropy scores; perform a two‑sample t‑test confirming `mean(high) > mean(low)` (p < 0.05).  
   - Halt pipeline if the test fails.

3. **Generate Teacher Traces (Phase 1)**  
   - Teacher model produces multi-step CoT traces for every training problem.  
   - Store traces alongside the problem record.

4. **Trace‑Consistency Validation (Phase 1‑A)**  
   - Compute **trace entropy** (Shannon entropy of token‑level probability distribution).  
   - Flag a problem as `trace_consistent = true` iff the trace entropy aligns with problem entropy (high‑entropy problems → high trace entropy, low‑entropy → low).  
   - Filter out inconsistent samples; only `trace_consistent` records are used for distillation (satisfies FR‑009).

5. **Validate Generalization Set Structure (Phase 1‑B)**  
   - Verify that the Generalization Set contains `structure_type` values distinct from any in the training set.  
   - Ensure the Generalization Set is stratified by `structure_type` and `entropy_level` to prevent confounding (addresses methodology-4223fb8c).

6. **Distillation (Phase 2)**  
   - Three independent runs: one per entropy subset (High, Low, Target).  
   - **Explicit Mapping**: *The three `DistillationRun` entities correspond directly to the High, Low, and Target entropy subsets defined in the data model.*  
   - Student model learns via token‑level KL‑divergence against the teacher's probability distribution (aligned by padding/truncating to equal length, with masking for length mismatch).  
   - Early stopping when validation loss ≤ 0.1 (threshold‑based convergence).  
   - Record `convergence_epoch`, `training_loss_curve`, `final_accuracy`, `total_runtime_seconds`, `peak_ram_gb`, and `status`.

7. **Evaluation (Phase 3)**  
   - Evaluate each student on the **Generalization Set** (500 + problems).  
   - Log accuracy and number of epochs to reach the loss threshold.

8. **Statistical Analysis (Phase 4)**  
   - **ANOVA** on final accuracies across the three models.  
   - **Pairwise t‑tests** on convergence epochs.  
   - Apply **Bonferroni correction** to *all* p‑values (ANOVA and t‑tests) (FR‑007).  
   - Produce `StatisticalResult` records with corrected p-values and `correction_method: "bonferroni"`.

9. **Report Generation (Phase 5)**  
   - `report_generator.py` creates a human‑readable summary and a JSON report.  
   - **FR-006 Enforcement**: The report explicitly states: "Findings are causal regarding the effect of entropy on performance within the synthetic domain." (FR‑006).

10. **Fail‑Fast Mechanisms**  
    - If total wall‑clock time exceeds 5.5 h, the pipeline exits with code 1.  
    - Non‑convergent runs are logged with `status: failed_non_converge` and included in the statistical analysis as worst‑case epoch counts (FR‑005).

## Compute Feasibility Summary

- **Model Size**: Student model ≈ 45 M parameters (DistilBERT‑base‑uncased).  
- **Batch Size**: 16 (fits comfortably in ≤ 7 GB RAM).  
- **Epoch Limit**: 20 with early stopping on loss ≤ 0.1.  
- **Estimated Runtime**: ≈ 1.5 h per distillation run → total ≈ 4.5 h + overhead < 6 h.  

## Decision Rationale

- **Synthetic Data**: Only a rule‑based generator can guarantee strict entropy control (FR‑001, VI).  
- **CPU‑Only**: Directly addresses the "edge‑device" research question (FR‑003, VII).  
- **KL‑Divergence Alignment**: Token‑level alignment with masking avoids mismatched output spaces (addresses scientific‑soundness‑a1104208).  
- **Statistical Rigor**: Power analysis, Bonferroni correction, and balanced Generalization Set ensure valid inference (FR‑005, FR‑007, FR‑008).  

--- 

*All functional requirements (FR‑001 – FR‑009) and success criteria (SC‑001 – SC‑006) are covered by the phases above.*