# Implementation Plan: Evaluating the Impact of Code Generation on Code Review Quality with LLM Assistance

**Branch**: `001-eval-llm-review-quality` | **Date**: 2024-05-21 | **Spec**: `specs/001-eval-llm-review-quality/spec.md`
**Input**: Feature specification from `/specs/001-eval-llm-review-quality/spec.md`

## Summary

This feature implements a computational research pipeline to evaluate the performance of CPU-tractable LLMs (specifically StarCoder-3B) in detecting bugs within GitHub Pull Requests (PRs) compared to human review baselines. The system extracts PR diffs and review metadata from verified datasets, simulates LLM-assisted bug detection with severity classification, aligns findings with human annotations using a strict location-similarity hybrid metric (with line-shift tolerance), and performs statistical testing (McNemar's, Chi-square) to report Precision, Recall, F1, and distributional differences. The implementation strictly adheres to CPU-only constraints (≤7GB RAM, ≤6h runtime) and frames all findings as associational.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `datasets`, `transformers` (CPU-optimized), `scikit-learn`, `scipy`, `pandas`, `pyyaml`, `pytest`, `numpy`  
**Storage**: Local `data/` directory (raw JSON/Parquet, derived CSV, annotations), `results/` (JSON reports)  
**Testing**: `pytest` (unit tests for extraction logic, integration tests for alignment metrics, contract tests for schema validation)  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, ~7GB RAM, No GPU)  
**Project Type**: Research Pipeline / CLI  
**Performance Goals**: Process ≤500 PRs within 6 hours; latency ≤5 min/PR; memory ≤7GB peak.  
**Constraints**: No GPU/CUDA; no 8-bit/4-bit quantization; strict JSON output validation; observability framing (no causal claims).  
**Scale/Scope**: Max PRs from verified datasets; Multiple similarity thresholds.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Action |
|-----------|--------|----------------------|
| **I. Reproducibility** | PASS | Random seeds pinned in `code/`; datasets fetched via canonical HF URLs; `requirements.txt` pins versions. |
| **II. Verified Accuracy** | PASS | All dataset citations restricted to the `# Verified datasets` block; no fabricated URLs. |
| **III. Data Hygiene** | PASS | Raw data stored in `data/raw/` with checksums (SHA-256 in `data/raw/checksums.json`); derived data in `data/derived/`; PII scan integration. |
| **IV. Single Source of Truth** | PASS | Final report metrics computed directly from `data/derived/` alignment results; no manual entry. |
| **V. Versioning Discipline** | PASS | Content hashes tracked in `state/`; artifact updates trigger state timestamp refresh. |
| **VI. Review Data Integrity** | PASS | Raw PR JSONs preserved; human annotations generated via standardized rubric in `code/` and stored in `data/annotations/`; no post-hoc modification. |
| **VII. Evaluation Rigor** | PASS | McNemar's and Chi-square tests implemented as per spec; effect sizes reported; α=0.05 documented; sensitivity to noise analysis included. |

## Project Structure

### Documentation (this feature)

```text
specs/001-eval-llm-review-quality/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (YAML schemas)
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
src/
├── extraction/
│   ├── fetch_prs.py         # Downloads data from HF datasets
│   ├── preprocess.py        # Truncates diffs, handles edge cases, generates annotations
│   └── schema.py            # Dataclass definitions
├── detection/
│   ├── detect_llm_code.py   # Heuristic detection of LLM-generated code (FR-016)
│   └── schema.py            # Detection result schema
├── inference/
│   ├── load_model.py        # CPU-only StarCoder2-3B loader
│   ├── prompt_templates.py  # Standardized bug detection prompts
│   └── run_inference.py     # Batch processing with retry logic
├── analysis/
│   ├── align.py             # Location overlap + cosine similarity logic (with tolerance)
│   ├── metrics.py           # Precision/Recall/F1 calculation (including LLM-only)
│   ├── stats.py             # McNemar's and Chi-square tests
│   └── sensitivity.py       # Threshold sweep (high confidence levels)
├── reporting/
│   └── generate_report.py   # Final JSON/Markdown report generator
├── cli/
│   └── main.py              # Entry point for pipeline execution
├── tests/
│   ├── unit/                # Unit tests for metrics and alignment
│   ├── integration/         # End-to-end small-scale test (5 PRs)
│   └── contract/            # Schema validation tests
└── config/
    └── settings.py          # Hyperparameters, paths, seeds

data/
├── raw/                     # Unmodified JSON/Parquet from HF + checksums.json
├── annotations/             # Standardized human review annotations (rubric-based)
├── derived/                 # Processed PRs, LLM outputs, alignments
└── results/                 # Final statistical reports

contracts/                   # Located under specs/.../contracts/ (YAML schemas)
```

**Structure Decision**: Single project structure selected to minimize overhead for a research pipeline. The `src/` directory is modularized by logical stage (Extraction → LLM Detection → Inference → Analysis → Reporting) to ensure clear data flow and testing boundaries. The `contracts/` directory is nested within the `specs/` feature folder to hold YAML schemas for validation, while `tests/contract/` enforces them.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Triangulated Ground Truth (FR-011)** | Essential for robustness; linked issues alone are noisy, and human comments alone are subjective. | Using only linked issues would inflate false negatives; using only comments lacks verification. Fallback to 'Closed Issue with Bug Label' is used when strict '≥2 reviewers' is impossible. |
| **Hybrid Alignment (FR-012)** | Exact line matching fails on refactored code; similarity alone is too noisy. | Pure line matching misses semantic bug moves; pure similarity allows false positives. Line-shift tolerance (±5 lines) is added to handle diff context. |
| **Threshold Sweep (FR-006)** | Required to demonstrate stability of results against alignment sensitivity. | Single threshold risks reporting an artifact of the specific cutoff rather than model performance. |
| **CPU-Only Constraint** | Mandatory for GitHub Actions Free Tier execution. | GPU/Quantization methods (8-bit) are excluded to ensure reproducibility on free CI runners. |
| **LLM Code Detection (FR-016)** | Required to distinguish human vs. LLM code review performance. | Ignoring this would conflate the two populations, invalidating the comparison. |
| **LLM-Only Reporting (FR-017)** | Required to credit LLMs for finding bugs humans missed. | Standard metrics ignore LLM-only detections, underestimating LLM utility. |