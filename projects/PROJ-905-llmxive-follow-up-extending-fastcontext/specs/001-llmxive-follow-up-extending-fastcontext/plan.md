# Implementation Plan: FastContext-Lite (Deterministic Repository Explorer)

**Branch**: `001-llmxive-fastcontext-lite` | **Date**: 2026-07-14 | **Spec**: `specs/001-llmxive-fastcontext-lite/spec.md`
**Input**: Feature specification from `specs/001-llmxive-fastcontext-lite/spec.md`

## Summary
This plan implements **FastContext-Lite**, a deterministic, rule-augmented retrieval mechanism designed to replace the learned exploration subagent in the original FastContext framework. The objective is to evaluate whether structural regularity in code repositories allows for token-efficient and context-precise retrieval without neural exploration. The implementation involves: (1) static analysis to score repository structural regularity (using `pathlib` for directory structure and AST for imports), (2) splitting SWE-bench repositories into "Regular" and "Irregular" sets via stable sort, (3) executing the deterministic engine (AST-filtered TF-IDF) on CPU, and (4) conducting comparative statistical analysis against the original FastContext baseline (normalized for hardware).

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `datasets` (for streaming SWE-bench), `scikit-learn` (TF-IDF, statsmodels), `pandas`, `numpy`, `tiktoken` (token counting), `networkx` (import graph).
**Dev Dependencies**: `ruff` (linting only, NOT used for retrieval or scoring), `pytest` (testing).
**Storage**: Local file system (`data/raw`, `data/processed`, `data/results`). No external database.
**Testing**: `pytest` with unit tests for scoring logic and integration tests for pipeline execution.
**Target Platform**: GitHub Actions Free Tier (multiple CPU cores, 7GB RAM, CPU-only).
**Project Type**: Research pipeline / CLI tool.
**Performance Goals**: Process a single repository in <10 minutes on CPU; total pipeline <6 hours for the stratified subset.
**Constraints**: Strictly CPU-only execution for FastContext-Lite; baseline may use GPU escape hatch with normalized metrics; streaming data to fit memory; deterministic random seeds.
**Scale/Scope**: Subset of SWE-bench (n=1,000) stratified by structural regularity.

> **Note on Empirics**: Specific dataset sizes, latency targets, and precision thresholds are deferred to the research phase and will be measured against the baseline.

## Constitution Check

*Gates determined based on `projects/PROJ-905-llmxive-follow-up-extending-fastcontext/.specify/memory/constitution.md`*

| Principle | Status | Action Plan |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/`; `requirements.txt` explicitly pins `torch==2.2.0+cpu` to enforce CPU-only execution; dataset fetch uses canonical HuggingFace streaming. |
| **II. Verified Accuracy** | **PASS** | All citations in `research.md` and `plan.md` will be validated against the `# Verified datasets` block (SWE-bench via HF). |
| **III. Data Hygiene** | **PASS** | Raw data (SWE-bench) preserved in `data/raw` with checksums; derivatives in `data/processed` and `data/results`. |
| **IV. Single Source of Truth** | **PASS** | Metrics stored in `data/results/metrics.csv`; paper figures generated programmatically from this source. |
| **V. Versioning Discipline** | **PASS** | Artifact hashes recorded in `state/projects/...yaml` upon each run. |
| **VI. Structural Regularity Stratification** | **PASS** | Explicit implementation of `static_analysis.py` using `pathlib` for test-file placement (relative path distance) and AST for import patterns, generating `regularity_score`. |
| **VII. Latency-Aware Evaluation** | **PASS** | Wall-clock latency measured for FastContext-Lite (CPU); Baseline (4B) measured on CPU or GPU escape hatch, with comparison normalized for hardware efficiency (Tokens/Sec, Precision/Token). |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-fastcontext-lite/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
```

### Source Code (repository root)

```text
projects/PROJ-905-llmxive-follow-up-extending-fastcontext/
├── data/
│   ├── raw/                 # SWE-bench raw artifacts, ground truth annotations
│   ├── processed/           # regularity_scores.csv, stratified_splits.json
│   └── results/             # metrics.csv, statistical_analysis.json
├── code/
│   ├── static_analysis.py   # FR-001: Scoring logic (pathlib for test placement, AST for imports)
│   ├── fastcontext_lite.py  # FR-003: Deterministic engine (AST-filtered TF-IDF, CPU-only)
│   ├── baseline_runner.py   # FR-004: Original FastContext runner (CPU or GPU escape hatch)
│   ├── analysis.py          # FR-005/006: T-tests, segmented regression, degradation calc
│   └── requirements.txt     # Pinned deps (torch==2.2.0+cpu, ruff in dev)
├── tests/
│   ├── unit/
│   │   ├── test_scoring.py
│   │   └── test_tfidf.py
│   └── integration/
│       └── test_pipeline.py
└── state/
    └── projects/PROJ-905-llmxive-follow-up-extending-fastcontext.yaml
```

**Structure Decision**: Adopts the standard research pipeline structure (raw/processed/results) to ensure Data Hygiene (Constitution III) and reproducibility. The `code/` directory contains all executable scripts, avoiding Jupyter notebooks to enforce deterministic execution. `static_analysis.py` explicitly implements the 'test-file placement' logic required by Constitution Principle VI via `pathlib`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Dual Baseline Execution** | Must compare against *original* 4B FastContext, not a distilled version. | Using a distilled model would invalidate latency claims (SC-002) and violate Constitution VII. |
| **Streaming Data Load** | SWE-bench exceeds typical RAM capacity; must stream. | Loading full dataset would crash the GitHub Actions runner. |
| **Stratified Split** | Must isolate "Regular" vs "Irregular" to test the hypothesis. | Random split would confound structural regularity with performance, failing US-1. |
| **Hardware Normalization** | Baseline may require GPU; Lite is CPU. | Direct latency comparison is invalid; must normalize by hardware efficiency. |