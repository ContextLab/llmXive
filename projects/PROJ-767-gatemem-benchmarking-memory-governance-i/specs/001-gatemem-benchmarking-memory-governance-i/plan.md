# Implementation Plan: GateMem Benchmarking Memory Governance

**Branch**: `001-gate-mem-benchmark` | **Date**: 2026-06-30 | **Spec**: `specs/001-gatemem-benchmark/spec.md`
**Input**: Feature specification from `/specs/001-gatemem-benchmark/spec.md`

## Summary

GateMem benchmarks memory governance in multi-principal shared-memory agents by simulating $N$ distinct principals (ranging from small to large scales) injecting synthetic memory items into a shared context. The system executes a deterministic loop where an open-weight LLM (CPU-quantized via `llama.cpp`) handles Utility, Access Control, and **Active Suppression** tasks. Success is measured by a composite Governance Score and statistical trend analysis using **Linear Mixed-Effects Models (LMM)** across $N$, ensuring reproducibility via rule-based evaluation and strict data hygiene.

*Note: This plan implements the corrected methodology (LMM, Active Suppression) to address statistical and construct validity concerns. The source specification (spec.md) currently contains conflicting requirements (FR-005, SC-004) mandating Chi-squared and 'Active Forgetting'. This plan flags these as **Spec-Root Cause** contradictions requiring spec update for full alignment.*

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `transformers` (CPU mode), `llama-cpp-python` (GGUF inference), `sentence-transformers` (semantic verification), `pandas`, `statsmodels` (LMM), `pytest`
**Storage**: Local JSON/Parquet files under `data/`
**Testing**: `pytest` with fixed random seeds
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, 7GB RAM)
**Project Type**: Research CLI / Benchmarking Suite
**Performance Goals**: Complete full experimental run (all $N$, 5 seeds) within 6 hours on CPU-only runner.
**Constraints**: No CUDA, no GPU, no 8-bit/4-bit quantization requiring CUDA. Max context window sufficient for standard document lengths (truncation handled gracefully).
**Scale/Scope**: $N \in \{ \text{small even integers} \}$, 500 items/principal, 5 seeds.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Verification / Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | Random seeds pinned in `code/`. External datasets fetched from canonical sources. |
| **II. Verified Accuracy** | PASS | All dataset URLs verified against the "Verified datasets" block in the prompt. No invented URLs. |
| **III. Data Hygiene** | PASS | `data/` files will be checksummed. No in-place modification; derivations create new files. |
| **IV. Single Source of Truth** | PASS | All metrics trace to `data/` rows and `code/` blocks. No hand-typed stats in paper. |
| **V. Versioning Discipline** | PASS | Artifacts will carry content hashes; `state` file updated by **Advancement-Evaluator Agent** upon change as per Principle V. |
| **VI. Multi-Principal Isolation** | PASS | Evaluation harness includes specific LMM interaction term to verify statistical independence of Principal A responses from Principal B presence. |
| **VII. Deterministic Evaluation** | PASS | Scoring uses regex/keyword + semantic verification (sentence-transformers). No LLM-as-judge. |

## Project Structure

### Documentation (this feature)

```text
specs/001-gatemem-benchmark/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Downstream artifact (Phase 2), not a current dependency
```

### Source Code (repository root)

```text
projects/PROJ-767-gatemem-benchmarking-memory-governance-i/
├── code/
│   ├── __init__.py
│   ├── config.py          # Hyperparameters, seeds, N values
│   ├── data_gen.py        # Synthetic memory generation (FR-001, FR-007)
│   ├── runner.py          # Task loop execution (FR-003, FR-006)
│   ├── evaluator.py       # Rule-based + Semantic eval (FR-004, FR-008, FR-009)
│   ├── metrics.py         # Governance score & LMM stats (FR-005, corrected)
│   └── main.py            # Entry point
├── data/
│   ├── raw/               # Downloaded datasets (checksummed)
│   ├── generated/         # Synthetic memory JSONs
│   └── results/           # Log files, metrics CSVs
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
└── requirements.txt       # Pinned dependencies
```

**Structure Decision**: Single `code/` directory with modular scripts for data generation, execution, and analysis. This minimizes overhead for CPU-only CI and aligns with the "CLI/Research" nature of the project.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Semantic Verification (FR-009)** | Keyword matching alone fails on paraphrased refusals. | Pure regex is brittle; LLM-as-judge violates Constitution Principle VII. Sentence-transformers provide deterministic, reproducible semantic checks. |
| **Linear Mixed-Effects Model (LMM)** | Required to analyze continuous Governance Score with small sample size (5 seeds). | Chi-squared test is invalid for continuous composites; simple t-tests cannot handle >2 groups with random effects. |
| **GGUF Quantization** | Required for CPU-only inference within 6h limit. | FP16/FP32 inference on 7GB RAM is impossible for 8B models; 8-bit requires CUDA (forbidden). |
| **Active Suppression** | Model cannot physically delete data from context. | 'Active Forgetting' is a construct validity failure; 'Suppression' accurately describes attention modulation. |

## Statistical Power & Methodology Note

**Concern**: The design (5 seeds per N, N=4 groups) results in a small sample size (N=20).
**Mitigation**: 
1. Use **Linear Mixed-Effects Models (LMM)** to maximize power by modeling random effects (seeds).
2. Report **Effect Sizes** (Cohen's d) and **95% Confidence Intervals** alongside p-values.
3. If LMM results are inconclusive, perform a **Bayesian Analysis** as a sensitivity check to extract maximum information from the limited data.
4. **Power Limitation Acknowledgement**: The plan explicitly states that the study is underpowered to detect small effect sizes and focuses on large, robust trends.

**Spec-Root Cause Flag**: The source specification (spec.md) mandates a "Chi-squared test for trend" on the Governance Score (FR-005, SC-004). This plan implements LMM as the scientifically valid alternative. **The spec must be updated to align with this corrected methodology.**