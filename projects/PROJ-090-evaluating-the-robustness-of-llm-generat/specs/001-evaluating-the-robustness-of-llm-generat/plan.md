# Implementation Plan: Evaluating the Robustness of LLM-Generated Code to Input Perturbations

**Branch**: `001-evaluating-robustness-llm-code` | **Date**: 2026-07-03 | **Spec**: `specs/001-evaluating-the-robustness-of-llm-generat/spec.md`
**Input**: Feature specification from `/specs/001-evaluating-the-robustness-of-llm-generat/spec.md`

## Summary

This project evaluates the robustness of LLM-generated code by measuring the degradation in functional correctness (pass@1) when prompts are subjected to high-fidelity, semantically-preserving perturbations (synonym substitution, typo injection, syntactic rephrasing). The technical approach involves: (1) downloading the HumanEval dataset; (2) generating perturbed variants and filtering them via `sentence-transformers/all-MiniLM-L6-v2` cosine similarity (>0.95, with a fallback to >0.90 if yield is low); (3) executing a Low-bit quantized StarCoder-3B model on CPU (fixed seed, temperature=0) to generate code; (4) sandboxing execution to capture pass/fail results; and (5) performing statistical analysis (Mixed-Effects Logistic Regression as primary, McNemar's test as secondary) to quantify robustness gaps while correcting for multiple comparisons.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers`, `datasets`, `sentence-transformers`, `bitsandbytes` (CPU-compatible build), `scikit-learn`, `statsmodels`, `pandas`  
**Storage**: Local `data/` directory (checksummed), JSONL/CSV logs  
**Testing**: `pytest` (unit tests for perturbation logic, mock execution for sandbox, **and validation against contract schemas in `contracts/`**)  
**Target Platform**: Linux (GitHub Actions free-tier: Multiple CPU, moderate RAM, no GPU)  
**Project Type**: Research Pipeline / CLI  
**Performance Goals**: Total runtime ≤ 6 hours; Memory ≤ 7 GB per process  
**Constraints**: No GPU; CPU-only quantization; strict timeouts (bounded generation, bounded execution); strict semantic similarity threshold (0.95, with fallback to >0.90)  
**Scale/Scope**: HumanEval tasks; **A single perturbation per task (a limited sample size)** to ensure runtime feasibility (A set of original samples and a corresponding set of perturbed samples).

> **Spec Note**: Success Criteria SC-003 and SC-006 in the source spec contain missing numeric values ('-hour' and undefined 'feasibility limit'). The plan assumes a 6-hour limit and a Sample size limit based on the compute constraints and scope defined in the spec's "Compute feasibility" section. These are flagged as spec-root causes for correction.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | All random seeds pinned in `code/`. HumanEval fetched from canonical HF URL. `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **Pass** | Citations in `research.md` restricted to verified URLs in the project input block. No invented dataset links. |
| **III. Data Hygiene** | **Pass** | Raw HumanEval and perturbation logs stored in `data/` with checksums. No in-place modification; derivations written to new files. |
| **IV. Single Source of Truth** | **Pass** | All statistics in the final report will be generated programmatically from `data/` logs, not hand-typed. |
| **V. Versioning Discipline** | **Pass** | Artifacts will be hashed; `state/projects/PROJ-090-evaluating-the-robustness-of-llm-generat.yaml` updated on change. |
| **VI. Secure Execution** | **Pass** | Sandbox execution with network disabled and A timeout is enforced per test case.. |
| **VII. Perturbation Traceability** | **Pass** | Perturbation type and raw similarity scores logged. **Transformation scripts are versioned and their content hashes are recorded in the state file.** |

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-robustness-llm-code/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Static source file (moved to docs/ to resolve ambiguity)
```

### Source Code (repository root)

```text
projects/PROJ-090-evaluating-the-robustness-of-llm-generat/
├── code/
│   ├── __init__.py
│   ├── data/
│   │   ├── download_humaneval.py
│   │   └── generate_perturbations.py
│   ├── model/
│   │   ├── inference.py
│   │   └── sandbox.py
│   ├── analysis/
│   │   ├── statistics.py
│   │   └── error_classifier.py
│   └── main.py
├── data/
│   ├── raw/
│   ├── processed/
│   └── logs/
├── docs/
│   └── tasks.md         # Static source file moved here
├── tests/
│   ├── unit/
│   └── integration/
└── requirements.txt
```

**Structure Decision**: Single project structure (`code/` subdirectory) selected to minimize overhead for a research pipeline. This aligns with the "CLI/Research" nature of the project, ensuring data flows linearly from `download` -> `perturb` -> `infer` -> `analyze`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **CPU-Only Quantization** | Required by GH Actions free-tier constraints (no GPU). | Standard 16-bit/32-bit models would exceed 7GB RAM, causing OOM failures. |
| **Mixed-Effects Model** | Required to account for clustering (perturbations nested within tasks). | Standard logistic regression would violate independence assumptions, inflating Type I error. |
| **Semantic Similarity Filter** | Required to ensure perturbations are "high-fidelity" (non-misleading). | Unfiltered perturbations might introduce semantic shifts, confounding the "robustness" metric with "misunderstanding." |
| **Reduced Sample Size (1 perturbation/task)** | Required to meet 6-hour CI limit with CPU inference. | 3 perturbations/task would exceed runtime budget, risking incomplete data. |
| **Human Spot-Check** | Required to validate semantic equivalence against embedding model bias. | Embedding model alone is insufficient ground truth; manual review is necessary for validity. |

## Execution Flow

1.  **Data Ingestion**: Download HumanEval.
2.  **Perturbation**: Generate variants (up to 5 per task, select 1 best > 0.95). **Human Spot-Check**: A subset of generated perturbations is manually reviewed to verify semantic equivalence. If the error rate exceeds a threshold, the threshold is adjusted.
3.  **Inference**: Run StarCoder2-3B (4-bit, CPU, seed=42, temp=0).
4.  **Execution**: Sandbox run with s timeout.
5.  **Analysis**: McNemar's (if power sufficient) and Mixed-Effects models.