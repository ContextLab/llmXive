# Implementation Plan: MobileForge Logic Distillation

**Branch**: `002-mobileforge-logic-distillation` | **Date**: 2026-08-27 | **Spec**: [link]
**Input**: Feature specification from `specs/002-mobileforge-logic-distillation/spec.md`

## Summary

This project investigates whether the "hint-contextualized" feedback signal in Hierarchical Feedback-Guided Policy Optimization (HiFPO) captures transferable *associational* logical reasoning patterns that can be distilled into a lightweight, CPU-tractable model for GUI action planning. The technical approach involves: (1) extracting "failed-then-success" trajectory triples from MobileForge logs, (2) training a T5-small (Encoder-Decoder) model on CPU to predict action sequences from UI states and hints (replacing the spec's 'encoder-only' requirement due to architectural necessity for sequence generation), and (3) evaluating the distilled model against a TinyLlama baseline (evaluated *with* the same hint context) and a 'generic retry' ablation on unseen AndroidWorld tasks. The evaluation includes a paired statistical test (McNemar's) and a sensitivity analysis.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers`, `datasets`, `scikit-learn`, `pandas`, `pytest`, `torch` (CPU-only build)  
**Storage**: Local CSV/Parquet files (intermediate), Hugging Face datasets (source only)  
**Testing**: `pytest` (unit), `pytest` (integration with mock emulator)  
**Target Platform**: Linux (GitHub Actions `ubuntu-22.04` runner)  
**Project Type**: Research pipeline / CLI  
**Performance Goals**: Training ≤6h on CPU; Inference <2s per task  
**Constraints**: No GPU usage for training/inference; Memory ≤7GB; Disk ≤14GB  
**Scale/Scope**: [deferred] training triples (deferred); evaluation tasks

> Empirical specifics (exact counts, dataset sizes) are deferred to the research/implementation phase or cited from the spec.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Evidence/Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned seeds, explicit dataset URLs, and isolated virtualenv. |
| **II. Verified Accuracy** | **PASS** | All dataset citations restricted to the "Verified datasets" block in the prompt. |
| **III. Data Hygiene** | **PASS** | Plan specifies checksumming raw downloads and deriving new files for processed data. |
| **IV. Single Source of Truth** | **PASS** | Metrics trace to `code/evaluation/results.csv`. **Enforcement**: The `stats.py` script reads results via a read-only stream; the `state/` update script computes a SHA-256 hash of `results.csv`. If the hash mismatches the recorded value, the script aborts, preventing manual editing from propagating. |
| **V. Versioning Discipline** | **PASS** | Artifacts will carry content hashes in `state/` updates. |
| **VI. CPU-Only Inference** | **PASS** | Model selection (T5-small) and execution constraints explicitly forbid GPU. |
| **VII. Hint-Specific Ablation** | **PASS** | Evaluation plan includes a 'generic retry' prompt ablation (replacing hint with "Try again") alongside the TinyLlama baseline. |

## Project Structure

### Documentation (this feature)

```text
specs/002-mobileforge-logic-distillation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
```

### Source Code (repository root)

```text
projects/PROJ-930-llmxive-follow-up-extending-mobileforge/
├── code/
│   ├── data/
│   │   ├── download_mobileforge.py    # Fetches raw logs
│   │   ├── extract_triples.py         # Filters for failed-then-success
│   │   └── schema.py                  # Pydantic/JSON schema definitions (ExtractionDataset, etc.)
│   ├── models/
│   │   ├── train_distilled.py         # CPU-only training loop (T5-small)
│   │   └── t5_small_config.json
│   ├── evaluation/
│   │   ├── run_tasks.py               # Executes on Android emulator (headless)
│   │   ├── metrics.py                 # Calculates Success Rate, Efficiency
│   │   ├── stats.py                   # McNemar's test, Observed Effect Size, Sensitivity
│   │   └── ablation.py                # Generic retry prompt comparison
│   └── utils/
│       ├── power_analysis.py          # A priori / Observed effect size logic
│       └── constants.py               # Seeds, thresholds
├── data/
│   ├── raw/                           # Downloaded logs (checksummed)
│   └── processed/                     # Extracted triples, evaluation results
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/                      # Validates against contracts/
└── requirements.txt
```

**Structure Decision**: Single-project structure (`code/` subdirectories) chosen to align with the research pipeline nature (data → model → eval) and simplify dependency management for the CPU-only constraint.

**Contract Mapping**:
- `contracts/extraction_dataset.schema.yaml` is the SSoT for the `ExtractionDataset` entity.
- `contracts/evaluation_result.schema.yaml` is the SSoT for the `EvaluationResult` entity (including ablation results).
- `contracts/statistical_report.schema.yaml` is the SSoT for the `StatisticalReport` entity.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Separate Ablation Script** | Constitution Principle VII requires a specific "generic retry" ablation distinct from the TinyLlama baseline. | Merging ablation into the main eval loop would obscure the specific comparison required by the principle. |
| **T5-small Architecture** | Encoder-only models (BERT) cannot natively generate variable-length action sequences. T5-small (Encoder-Decoder) is required for the output format. | Using BERT would require reformulating the task as classification over a fixed vocabulary, which contradicts the "predict action sequences" goal. |
| **Post-Training Ablation** | Constitution Principle VII requires a specific "generic retry" prompt ablation. | Merging ablation into the main eval loop would obscure the specific comparison required by the principle. |
| **A Priori Power Analysis** | Spec FR-007 (post-hoc) was removed due to tautology. A priori analysis is needed to justify N=500 for binary outcomes. | Post-hoc power analysis is tautological and does not validate sample size sufficiency. |
| **Stress Test** | Selection bias in training data requires a secondary evaluation on ambiguous hints to measure distribution shift. | Ignoring distribution shift would lead to over-optimistic generalization claims. |
| **Confounding Control** | Observational data requires propensity scoring/difficulty matching to rule out confounders. | Simple pairing is insufficient to control for task difficulty and UI complexity. |

## Implementation Phases

### Phase 0: Data Preparation & Filtering
1.  **Download**: Fetch `mobileforge_logs.csv` from the verified Hugging Face URL. Record SHA-256 checksum.
2.  **Extract**: Filter for `initial_status == "failed"` AND `post_hint_status == "success"`. Verify `Corrective_Hint` is purely linguistic (regex).
3.  **Validate**: Ensure ≥ [deferred] valid triples. If <5,000, report shortage and adjust N for power analysis.
4.  **Pre-Training Ablation**: Train a control model on `UI_state` only (no hint) to verify the hint is the primary driver of success.

### Phase 1: Model Training
1.  **Configure**: Initialize T5-small (Encoder-Decoder, ≤100M params) for sequence generation.
2.  **Train**: Train on CPU with `device="cpu"`. Batch size tuned to fit available RAM.
3.  **Validate**: Monitor loss; ensure convergence (final loss ≤ 0.5). If no convergence, flag as "Model Failure".

### Phase 2: Evaluation & Statistical Validation
1.  **Load Tasks**: Load a set of unseen, logically disjoint AndroidWorld tasks.
2.  **Run Distilled Model**: Evaluate on tasks with `Corrective_Hint`.
3.  **Run Baseline**: Evaluate TinyLlama (non-distilled) on tasks with `Corrective_Hint`.
4.  **Run Ablation**: Evaluate Distilled Model on tasks with `Corrective_Hint` replaced by "Try again".
5.  **Stress Test**: Evaluate Distilled Model on a subset of tasks with ambiguous hints (if available).
6.  **Calculate Metrics**: Success Rate, Step Efficiency.
7.  **Statistical Test**: Perform **McNemar's test** (paired binary) comparing Distilled vs. Baseline.
8.  **Sensitivity Analysis**: Sweep `inconsistency_tolerance` {0.01, 0.05, 0.1}.
9.  **Effect Size**: Calculate Cohen's d and report observed power (no post-hoc claim).

### Phase 3: Reporting
1.  **Generate Report**: Compile `statistical_report.json`.
2.  **Verify SSoT**: Ensure all metrics trace to `results.csv` via hash check.

## Risks & Mitigations

| Risk | Mitigation |
| :--- | :--- |
| **Dataset Insufficiency** (<5k triples) | Report actual count; adjust N for power analysis; explicitly state power limitation. |
| **Model Non-Convergence** | Monitor loss; if no convergence, flag as "Model Failure" and analyze dataset quality (ablation). |
| **Emulator Crashes** | Retry logic (limited attempts); mark as "Environment Error" and exclude from success rate. |
| **Hint Ambiguity** | Strict regex filtering to exclude non-linguistic hints; 'Stress Test' for generalization. |
| **Selection Bias** | 'Stress Test' on ambiguous hints; 'Confounding Control' via difficulty matching. |
| **Distribution Shift** | Explicitly report failure rate on ambiguous hints; limit primary claims to 'high-confidence hint' tasks. |
| **Spec Conflict (Encoder-Only)** | Plan uses T5-small (Encoder-Decoder) for sequence generation. Spec.md requires kickback to update FR-002. |
| **Spec Conflict (Post-Hoc Power)** | Plan uses A Priori analysis and observed effect size. Spec.md requires kickback to update Assumptions. |