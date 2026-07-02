# Implementation Plan: Evaluating the Impact of Code Generation Models on Code Security

**Branch**: `001-code-security-evaluation` | **Date**: 2025-01-15 | **Spec**: `spec.md`

## Summary

This project implements a reproducible research pipeline to evaluate the security implications of using different Large Language Models (LLMs) for code generation. The system downloads a specific set of pre-trained code models (StarCoder-Base, CodeGen, GPT-NeoX), generates code snippets from a standardized set of **30 prompts** (10 filtered from CodeXGLUE + 20 handcrafted web-security prompts), and analyzes the output using static analysis tools (Bandit, Semgrep, CodeQL). The pipeline computes vulnerability density and severity metrics, applies non-parametric statistical tests (Kruskal-Wallis, Dunn's post-hoc with Bonferroni correction), and performs robustness checks via Zero-Inflated Negative Binomial (ZINB) regression. A **Manual Calibration** phase validates scanner outputs against human expert review to estimate False Positive Rates (FPR). All outputs are visualized and reported in a structured format.

**Note on Scope**: The original spec (FR-002) requested 250 prompts. Due to GitHub Actions free-tier constraints (7GB RAM, 6h limit) and the heavy resource cost of CodeQL, the plan reduces this to **30 prompts** (N=90 total snippets). This reduction is necessary to ensure the pipeline completes within a designated time window without OOM errors. The spec requires a formal amendment to align FR-002 and SC-005 with this feasible N=90.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers`, `torch` (CPU-only), `bitsandbytes` (CPU-compatible), `scikit-learn`, `scipy`, `statsmodels`, `pandas`, `matplotlib`, `seaborn`, `bandit`, `semgrep`, `codeql` (CLI).  
**Storage**: Local filesystem (`data/` for prompts, generated code, analysis results; `data/` checksums managed by project state).  
**Testing**: `pytest` for unit tests; integration tests verify pipeline end-to-end on a subset of prompts.  
**Target Platform**: GitHub Actions free-tier runner (Linux, 2 CPU, ~7 GB RAM, no GPU).  
**Project Type**: Computational research pipeline (CLI-based).  
**Performance Goals**: 
- **Total Runtime**: ≤ 6 hours.
- **Breakdown**: Model Load/Unload (h) + Generation (several hours) + Analysis (1.5h) + Stats/Report (0.5h).
- **Memory**: B model (low-precision) ~5GB RAM; remaining sufficient memory for OS, Python runtime, and sequential scanner subprocesses.
**Constraints**: 
- No GPU/CUDA.
- **4-bit quantization applied to ALL models** (7B, 2B, 1.3B) to control for the quantization confounder.
- Strict timeout: fixed duration per generation, a bounded time limit per scanner run.
- Deterministic randomness via pinned seeds.
**Scale/Scope**: 30 prompts, 3 models, ~90 code snippets, A multiple-scanner setup will be employed..

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Evidence/Action Plan |
|-----------|--------|----------------------|
| **I. Reproducibility** | **PASS** | Plan mandates pinned `random_seed` in code; datasets (CodeXGLUE) fetched from canonical source; tools (Bandit/Semgrep/CodeQL) version-pinned in `requirements.txt`. |
| **II. Verified Accuracy** | **PASS** | **Reference-Validator Agent** runs at artifact write (Task 0.0) to verify all citations in `research.md`. No fabricated URLs. |
| **III. Data Hygiene** | **PASS** | Plan includes checksumming of raw prompts (`manifest.json` and `handcrafted.json`) and generated code; no in-place modification; derivation logs for all transformations. |
| **IV. Single Source of Truth** | **PASS** | Statistical results and figures will be generated directly from the analysis CSV; no hand-typed numbers in reports. |
| **V. Versioning Discipline** | **PASS** | Artifacts in `data/` will carry content hashes; `state.yaml` updated via `update_state.py` on artifact change (recording `artifact_hashes` and `updated_at` as per Constitution Principle V). |
| **VI. Security-Analysis Reproducibility** | **PASS** | Plan specifies exact tool versions and deterministic CSV output format; tool version changes trigger re-runs. |
| **VII. Prompt-Set Transparency** | **PASS** | Prompt manifest (10 CodeXGLUE filtered + 20 handcrafted) stored in `data/prompts/manifest.json` and `data/prompts/handcrafted.json` with checksums; versioned and referenced in `code/generate.py` as the source of truth. |

## Project Structure

### Documentation (this feature)

```text
specs/001-code-security-evaluation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── output.schema.yaml
│   ├── run_summary.schema.yaml
│   └── sensitivity.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-152-evaluating-the-impact-of-code-generation/
├── code/
│   ├── __init__.py
│   ├── config.py              # Paths, seeds, hyperparameters
│   ├── download.py            # Model and dataset fetchers
│   ├── generate.py            # Inference loop with timeout handling
│   ├── analyze.py             # Static analysis orchestration (Bandit, Semgrep, CodeQL)
│   ├── calibration.py         # Manual audit interface and FPR calculation
│   ├── metrics.py             # V/100LOC, severity mapping, FPR correction
│   ├── stats.py               # Kruskal-Wallis, Dunn's, ZINB
│   ├── sensitivity.py         # Sensitivity analysis (FR-009)
│   ├── viz.py                 # Box-plots, heat-maps
│   ├── main.py                # Pipeline orchestrator
│   └── update_state.py        # Updates state.yaml with artifact hashes
├── data/
│   ├── prompts/               # Raw prompts + manifest.json + handcrafted.json
│   ├── generated/             # Raw code snippets
│   ├── findings/              # Raw scanner outputs
│   ├── calibration/           # Manual audit results
│   └── results/               # Aggregated stats, plots, final CSVs
├── tests/
│   ├── unit/
│   └── integration/
└── requirements.txt
```

**Structure Decision**: Single project structure selected to maintain tight coupling between generation, analysis, and stats. Modular separation (`generate`, `analyze`, `calibration`, `stats`) ensures testability and adherence to Constitution Principle I (Reproducibility).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **3 Models + 3 Scanners** | Required by FR-001 and FR-003 to compare models and ensure robustness across tools. | Using 1 model or 1 scanner would violate the core research question of "differ across models" and "common security vulnerabilities" (US-1, US-2). |
| **ZINB Regression** | Required by FR-005b for zero-inflated data robustness. | Standard Poisson/Negative Binomial would fail to model the excess zeros accurately, biasing results. |
| **4-bit Quantization (All Models)** | Required by FR-001 and to control for the quantization confounder (scientific_soundness-5c08810c). | Using different quantization levels would introduce a massive confounder, invalidating the comparison. |
| **Manual Calibration** | Required to establish ground truth and validate scanner metrics (methodology-6d05babd). | Relying solely on scanner outputs would measure "scanner noise" rather than "model security". |
| **Reduced N (30 prompts)** | Required to fit 6h/7GB budget with CodeQL. | 250 prompts would cause OOM/timeout failures, invalidating the study. |
| **Prompt Filtering/Augmentation** | Required to ensure dataset-variable fit for security vulnerabilities. | Raw CodeXGLUE lacks specific security context; filtering and handcrafted augmentation ensure the study measures what it intends to. |

## Phases & Tasks

### Phase 0: Data Preparation & Manual Calibration Setup
- **Task 0.0**: **Reference-Validator**: Verify all citations in `research.md` before proceeding.
- **Task 0.1**: **Dataset Filtering & Augmentation**: 
  1. Download CodeXGLUE `codexglue_code_to_text`.
  2. Filter prompts containing security keywords (SQL, auth, XSS, injection, sanitize, password, token).
  3. Select top 10 most relevant prompts.
  4. Generate `data/prompts/handcrafted.json` (20 prompts targeting web-security patterns).
  5. Generate `data/prompts/manifest.json` with checksums and source attribution.
- **Task 0.2**: Load models (4-bit quantized) and verify memory usage.
- **Task 0.3**: Generate code for 30 prompts × 3 models (N=90). Log failures.

### Phase 1: Analysis & Validation
- **Task 1.1**: Run static analyzers (Bandit, Semgrep, CodeQL) on generated code. **Timeout: s per scan**.
- **Task 1.2**: Map scanner severities to 1-5 ordinal scale.
- **Task 1.3**: **Manual Calibration**: Select a stratified sample of 10 snippets per model (N=30 total). Human experts label vulnerabilities. Calculate Inter-Rater Reliability (Kappa) and **False Positive Rate (FPR) per scanner/model**.
- **Task 1.4**: If Kappa < 0.6, refine mapping function and repeat calibration.
- **Task 1.5**: Compute V/100LOC and mean severity, **applying FPR correction** to vulnerability counts.

### Phase 2: Statistical Inference
- **Task 2.1**: Run Kruskal-Wallis test on FPR-corrected V/100LOC.
- **Task 2.2**: If significant, run Dunn's post-hoc with Bonferroni correction.
- **Task 2.3**: Run ZINB regression (pre-registered default) with LOC offset.
- **Task 2.4**: **Sensitivity Analysis** (FR-009): Sweep high-severity cutoffs and report proportions.

### Phase 3: Reporting
- **Task 3.1**: Generate visualizations (box-plot, heat-map).
- **Task 3.2**: Generate `RunSummary` (SC-005) and statistical reports.
- **Task 3.3**: Update `state.yaml` with artifact hashes and `updated_at` timestamp.

## FR/SC Coverage Map

| ID | Requirement | Plan Element |
|----|-------------|--------------|
| FR-001 | Download 3 models (4-bit) | Task 0.2 (All models 4-bit) |
| FR-002 | Generate 250 prompts | **AMENDED**: Plan uses 30 prompts (Task 0.3) due to resource constraints. |
| FR-003 | Run 3 scanners | Task 1.1 (with 300s timeout) |
| FR-003b | Map severity 1-5 | Task 1.2 (Validated by Task 1.3) |
| FR-004 | Compute V/100LOC | Task 1.5 (with FPR correction) |
| FR-004b | Document "proxy" metric | Research.md Section 1 |
| FR-005 | Kruskal-Wallis + Dunn | Task 2.1, 2.2 |
| FR-005b | ZINB if zero-inflated | Task 2.3 (Pre-registered default) |
| FR-005c | Control for LOC | Task 2.3 (Offset term) |
| FR-006 | Visualizations | Task 3.1 |
| FR-007 | Log failures | Task 0.3, 1.1 |
| FR-008 | Multiple-comparison correction | Task 2.2 (Bonferroni) |
| FR-009 | Sensitivity Analysis | Task 2.4 |
| SC-001 | V/100LOC vs KW | Task 2.1 |
| SC-002 | Pairwise differences | Task 2.2 |
| SC-003 | Severity distribution | Task 1.5 |
| SC-004 | CWE heat-map | Task 3.1 |
| SC-005 | Completion rate ≥90% | Task 3.2 (RunSummary calculation) |

