# Implementation Plan: llmXive follow-up: extending "FastContext: Training Efficient Repository Explorer for Coding Agents"

**Branch**: `001-llmxive-fastcontext-lite` | **Date**: 2026-07-14 | **Spec**: `spec.md`

## Summary
This project implements a CPU-tractable experimental pipeline to evaluate whether replacing the learned exploration subagent in FastContext with a deterministic, rule-augmented retrieval mechanism (FastContext-Lite) preserves token efficiency and context precision. The core innovation is a "Structural Regularity Score" derived from static analysis (directory layout, test placement, import patterns) to stratify SWE-bench repositories into "Regular" and "Irregular" sets. The plan executes a comparative analysis of FastContext-Lite against a **CPU-tractable distilled neural baseline (large-scale)**, focusing on precision, token usage, and latency, while strictly adhering to free-tier GitHub Actions constraints (limited CPU and RAM).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn` (TF-IDF, stats), `pandas`, `networkx` (Required for import graph analysis), `tqdm`, `pytest`, `transformers` (CPU-only), `datasets`  
**Storage**: Local filesystem (temporary), `data/` for processed CSVs/JSONL  
**Testing**: `pytest` (unit tests for scoring logic, integration tests for pipeline)  
**Target Platform**: Linux (GitHub Actions Free Tier)  
**Project Type**: Research Pipeline / CLI Tool  
**Performance Goals**: Complete analysis of stratified subset within 6 hours; memory footprint < 6GB; no GPU/CUDA dependencies.  
**Constraints**: 
- **CPU-Only**: No `torch` CUDA, no quantization requiring `bitsandbytes`.
- **Data Size**: Must handle SWE-bench subset via chunking/sampling to fit limited RAM.
- **No New Constraints**: All metrics and thresholds defer to spec/sc-001 through SC-005.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Verification Method |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ Compliant | All random seeds pinned in `code/`; `requirements.txt` pins versions; scripts run end-to-end. |
| **II. Verified Accuracy** | ✅ Compliant | Citations in `research.md` restricted to verified dataset URLs (`princeton-nlp/SWE-bench_Lite`) and model IDs (`princeton-nlp/fastcontext-distilled-1.5b`). |
| **III. Data Hygiene** | ✅ Compliant | Raw data checksummed; derivations written to new files; PII scan enforced. |
| **IV. Single Source of Truth** | ✅ Compliant | Metrics in `data/` are the sole source for `paper/` figures; no manual typing. |
| **V. Versioning Discipline** | ✅ Compliant | `code/versioning.py` computes content hashes for all artifacts in `data/` and `code/`, updating `state/` timestamps automatically. |
| **VI. Structural Regularity Stratification** | ✅ Compliant | Plan explicitly implements the split into "Regular"/"Irregular" sets based on static analysis before comparison, with a pilot validation step. |
| **VII. Latency-Aware Evaluation** | ✅ Compliant | Pipeline measures wall-clock latency alongside tokens/precision; both runs under identical CPU constraints. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-fastcontext-lite/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── tasks.md             # Phase 2 output (generated)
└── contracts/           # Phase 1 output
    ├── exploration_log.schema.yaml
    ├── repo_metadata.schema.yaml
    └── statistical_summary.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-905-llmxive-follow-up-extending-fastcontext/
├── data/
│   ├── raw/                  # Downloaded SWE-bench subsets (checksummed)
│   ├── processed/            # Regularity scores, stratified splits
│   └── results/              # Metric logs (JSONL)
├── code/
│   ├── __init__.py
│   ├── static_analysis.py    # FR-001: Regularity scoring (uses networkx for import graphs)
│   ├── stratification.py     # FR-002: Splitting logic
│   ├── versioning.py         # Implements Constitution Principle V (hashing & state updates)
│   ├── fastcontext_lite.py   # FR-003: Deterministic engine (TF-IDF + rules)
│   ├── baseline_runner.py    # Runs the 1.5B distilled baseline (CPU-optimized)
│   ├── metrics_logger.py     # FR-004: Logging precision, tokens, latency
│   ├── analysis.py           # FR-005/FR-006: T-tests, degradation calc, power analysis
│   └── main.py               # Orchestration script
├── tests/
│   ├── unit/
│   │   ├── test_static_analysis.py
│   │   └── test_stratification.py
│   └── integration/
│       └── test_pipeline.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single `code/` directory with modular scripts. `versioning.py` is explicitly placed here to satisfy Constitution Principle V. `tasks.md` is generated into `specs/.../` as a Phase 2 output.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Stratified Split (FR-002)** | Required by Constitution Principle VI to isolate structural regularity. | A random split would confound the "Regular vs. Irregular" hypothesis with dataset bias. |
| **Deterministic Engine (FR-003)** | Required to test the "FastContext-Lite" hypothesis without GPU. | Re-using the neural subagent would fail the "CPU-only" constraint and not test the hypothesis. |
| **Paired T-Test (FR-005)** | Required by SC-005 to establish statistical significance. | Descriptive statistics alone are insufficient for scientific claims about performance differences. |
| **Pilot Validation (New)** | Required to verify that the Regularity Score actually correlates with retrieval difficulty. | A stratification based on an uncorrelated metric would lead to a Type II error (false negative). |
| **Distilled Baseline (New)** | Required to run the neural baseline within 6h/7GB RAM constraints. | The original large-scale model is computationally infeasible on the target hardware.. |

## Phase Breakdown

### Phase 0: Data Acquisition & Verification
- **Goal**: Fetch and verify SWE-bench Lite dataset.
- **Action**: Download `princeton-nlp/SWE-bench_Lite` via `datasets` library.
- **Output**: `data/raw/swe-bench-lite.jsonl` (checksummed).

### Phase 0.5: Pilot Validation (New)
- **Goal**: Verify that `regularity_score` correlates with retrieval difficulty.
- **Action**: Run a simple retrieval baseline on a small sample (n=20) and compute correlation between `regularity_score` and retrieval precision.
- **Decision**: If correlation < 0.3, flag the stratification strategy for review before proceeding.

### Phase 1: Static Analysis & Stratification
- **Goal**: Compute `regularity_score` and split data.
- **Action**: Run `static_analysis.py` (using `networkx` for import graphs) on all repos. Split into "Regular" and "Irregular" sets.
- **Output**: `data/processed/regularity_scores.csv`.

### Phase 2: Execution (Lite & Baseline)
- **Goal**: Generate metric logs.
- **Action**: Run `fastcontext_lite.py` and `baseline_runner.py` (1.5B model) on the stratified sets.
- **Constraint**: Baseline runs on CPU with `transformers` default precision.
- **Output**: `data/results/exploration_logs.jsonl`.

### Phase 3: Statistical Analysis
- **Goal**: Compare metrics.
- **Action**: Run power analysis. If N >= 30, run paired t-test. Else, run Wilcoxon signed-rank test. Calculate degradation on "Irregular" set.
- **Output**: `data/results/statistical_summary.json`.

### Phase 4: Versioning & Reporting
- **Goal**: Finalize artifacts.
- **Action**: Run `versioning.py` to hash all outputs and update `state/`. Generate `tasks.md`.
- **Output**: Updated `state/` and `tasks.md`.

## Risk Mitigation

- **Risk**: Baseline (1.5B) still too slow for full set.
  - **Mitigation**: The plan limits the baseline to the "Regular" set (n=50) for the paired test. The "Irregular" set is analyzed with the Lite engine only, comparing against the theoretical optimum.
- **Risk**: Regularity Score does not correlate with performance.
  - **Mitigation**: Phase 0.5 detects this. If correlation is low, the report will explicitly state that structural regularity is not a predictor of retrieval difficulty, which is a valid scientific finding.
- **Risk**: Insufficient sample size for t-test.
  - **Mitigation**: Power analysis triggers a switch to Wilcoxon test, and the report explicitly states the power limitation.