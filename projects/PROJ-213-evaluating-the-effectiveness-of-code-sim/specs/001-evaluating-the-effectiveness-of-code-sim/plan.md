# Implementation Plan: Evaluating the Effectiveness of Code Simplification on LLM Performance

**Branch**: `[001-eval-code-simplification]` | **Date**: 2026-06-24 | **Spec**: `spec.md`

## Summary

Assess whether automated code-simplification (dead-code removal, boolean reduction) produces **differences in** pass@1 accuracy and inference latency of a small pre-trained code model on the HumanEval benchmark. The approach uses an AST-based preprocessing pipeline, paired benchmark execution (raw vs. simplified), and paired McNemar's test (for binary pass@1) plus Wilcoxon signed-rank tests (for continuous metrics) with Bonferroni correction for three hypotheses. **All claims are framed as associational differences, not causal improvements.**

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `datasets`, `transformers`, `llama-cpp-python`, `ast`, `scipy`, `matplotlib`, `pandas`  
**Storage**: Local files under `data/` (HumanEval JSONL, results CSVs, logs)  
**Testing**: `pytest` for unit tests; end-to-end benchmark scripts  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: CLI/research pipeline  
**Performance Goals**: ≤6h total runtime, ≤7GB RAM, ≤14GB disk  
**Constraints**: No GPU/CUDA; CPU-only inference; per-sample timeout limit  
**Scale/Scope**: HumanEval **full set**; alternative benchmark (MBPP/APPS) would require spec amendment

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Plan Element Addressing It |
|-----------|--------|---------------------------|
| **I. Reproducibility** | PASS | Random seeds pinned in `code/`; HumanEval fetched from pinned HuggingFace version; `requirements.txt` pins all dependencies; CI runs on fresh runner. |
| **II. Verified Accuracy** | PARTIAL PASS | HumanEval from `datasets.load_dataset('openai_humaneval')` verified (HuggingFace official). StarCoder GGUF source [deferred] pending verification. Validation gate blocks Phase 1 until all citations verified. |
| **III. Data Hygiene** | PASS | Raw data preserved unchanged; derivations written to new files; checksums recorded in `state/` map. |
| **IV. Single Source of Truth** | PASS | All figures/statistics trace to exactly one row in `data/` and one block in `code/`; no hand-typed numbers. |
| **V. Versioning Discipline** | PASS | Every artifact carries content hash; artifact changes update `state/` timestamp. |
| **VI. Code Simplification Determinism** | PASS | AST transformations deterministic; random seed fixed in `code/`; identical output for given input. |
| **VII. Performance Evaluation Rigor** | PASS | Metrics: pass@1, token count, wall-clock time; McNemar's test (binary), Wilcoxon (continuous); p<0.05 threshold; same subset for raw/simplified. |

## Project Structure

### Documentation (this feature)

```text
specs/[001-eval-code-simplification]/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-213-evaluating-the-effectiveness-of-code-sim/
├── data/
│   ├── raw/                 # Downloaded HumanEval (unchanged)
│   ├── processed/           # Simplified code, results CSVs
│   └── logs/                # parse_failures.log, flagged_snippets.csv
├── code/
│   ├── __init__.py
│   ├── download.py          # FR-001: HumanEval fetch
│   ├── simplify.py          # FR-002: AST preprocessing
│   ├── inference.py         # FR-003, FR-004, FR-009: Model run + metrics
│   ├── analyze.py           # FR-005, FR-006: Statistical tests + report
│   └── main.py              # Orchestration CLI
├── tests/
│   ├── unit/                # Unit tests for simplify, analyze
│   ├── contract/            # Schema validation tests
│   └── integration/         # End-to-end pipeline tests
├── requirements.txt         # Pinned dependencies
└── README.md                # Quickstart reference
```

**Structure Decision**: Single project structure (DEFAULT) chosen because this is a CLI/research pipeline, not a web/mobile service. All code lives under `code/`, data under `data/`, tests under `tests/`.

## Complexity Tracking

> No violations requiring justification; all complexity justified by spec requirements.

## Phase Order & Dependencies

| Phase | Tasks | Dependencies | Output |
|-------|-------|--------------|--------|
| **Phase 0: Research** | Dataset verification, model feasibility check, **power analysis (FR-010)**, statistical design | None | `research.md` |
| **Phase 1: Design** | Data model, schemas, quickstart, contract tests | Phase 0 complete | `data-model.md`, `quickstart.md`, `contracts/` |
| **Phase 2: Implementation** | Code for download, simplify, inference, analyze | Phase 1 complete | `code/` scripts |
| **Phase 3: Validation** | Unit tests, contract tests, CI run | Phase 2 complete | Test reports |
| **Phase 4: Analysis** | **Conditional on SC-003**: token reduction measured for all problems; McNemar's + Wilcoxon tests, report generation | Phase 3 complete | `analysis_report.pdf` |

## FR/SC Coverage Matrix

| ID | Type | Plan Phase/Step Addressing It |
|----|------|-------------------------------|
| FR-001 | Data fetch | Phase 2: `download.py` - HumanEval from HuggingFace |
| FR-002 | AST simplification | Phase 2: `simplify.py` - dead-code removal, boolean reduction |
| FR-003 | Inference setup | Phase 2: `inference.py` - quantized StarCoder via llama.cpp on CPU |
| FR-004 | Metrics logging | Phase 2: `inference.py` - record token_count, inference_time_ms to CSV |
| FR-005 | Statistical test | Phase 2: `analyze.py` - McNemar's (pass@1) + Wilcoxon (time) + Bonferroni (3 hypotheses) |
| FR-006 | Report generation | Phase 2: `analyze.py` - PDF with tables, figures |
| FR-007 | Parse failure logging | Phase 2: `simplify.py` - log to `parse_failures.log` with required fields |
| FR-008 | Semantic change detection | Phase 2: `simplify.py` - run test harness, write to `flagged_snippets.csv` |
| FR-009 | Inference timeout | Phase 2: `inference.py` - 30s timeout, log with failure flag |
| FR-010 | Power justification | **Phase 0**: `research.md` - document minimum detectable effect for n=164 |
| SC-001 | Pass@1 comparison | Phase 4: McNemar's test on accuracy, report odds ratio with Bonferroni correction |
| SC-002 | Latency ratio | Phase 4: Wilcoxon test on inference time, report rank-biserial with Bonferroni correction |
| SC-003 | Token reduction | Phase 4: Compute token_count ratio for **all problems** (descriptive, not gating); Bonferroni correction applies |
| SC-004 | Report PDF | Phase 4: Generate `analysis_report.pdf` with all required content |
| SC-005 | Drop rate ≤5% | Phase 4: Calculate drop rate from parse failures + semantic changes; **if >5%, document limitation and proceed** (no expansion possible; spec amendment needed for alternative benchmark) |

**SC-003 Clarification**: Token reduction is measured for ALL paired problems (including those with simplification failures). It is a descriptive metric, not a selection gate. Accuracy/latency analysis proceeds on the full paired dataset regardless of token reduction outcome.

**SC-005 Remediation**: If >5% drop rate, document the limitation in the final report. Full HumanEval (164 problems) is the maximum available; expansion is not possible. Alternative benchmarks (MBPP, APPS) would require spec amendment.