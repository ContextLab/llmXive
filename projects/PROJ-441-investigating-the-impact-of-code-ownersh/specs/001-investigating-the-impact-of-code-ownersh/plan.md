# Implementation Plan: Investigating the Impact of Code Ownership on LLM Code Understanding

**Branch**: `001-code-ownership-llm-understanding` | **Date**: 2026-07-10 | **Spec**: `specs/001-code-ownership-llm-understanding/spec.md`
**Input**: Feature specification from `/specs/001-code-ownership-llm-understanding/spec.md`

## Summary

This plan implements a research pipeline to quantify the correlation between socio-technical code ownership (measured by LOC-weighted Gini coefficient of commit distribution) and LLM code understanding performance (measured by BLEU score on Code-to-Text tasks). The approach involves extracting ownership metrics from git histories up to the specific commit of the snippet, calculating code complexity controls, running inference on a CPU-tractable StarCoder2-3B model (4-bit quantized), and performing Linear Mixed-Effects Regression with robustness checks.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `gitpython`, `radon`, `scikit-learn`, `transformers`, `torch` (CPU-only), `pandas`, `scipy`, `pyyaml`, `statsmodels`, `bitsandbytes` (CPU wheel)  
**Storage**: Local filesystem (`data/`, `data/raw/`, `data/processed/`)  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, 7GB RAM)  
**Project Type**: Research Pipeline / CLI Tool  
**Performance Goals**: Complete full pipeline (30 repos, 150 snippets) in ≤ 6 hours on CPU.  
**Constraints**: No GPU; StarCoder2-3B MUST run in 4-bit quantization using `bitsandbytes` CPU implementation; explicit model unloading required; total RAM usage ≤ 7 GB.  
**Scale/Scope**: A representative set of repositories (Java/Python), with a maximum of 5 snippets per repo (fallback to 3 or 2 if time/memory constraints threaten completion).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned `requirements.txt`, random seeds, and canonical data sources. |
| **II. Verified Accuracy** | **PASS** | Phase 0 explicitly runs Reference-Validator Agent; all dataset references restricted to verified sources. |
| **III. Data Hygiene** | **PASS** | Phase 0 calculates SHA256 checksums of raw data and records them in `state/...yaml`. |
| **IV. Single Source of Truth** | **PASS** | Output schemas in `contracts/` ensure all results trace to specific data rows. |
| **V. Versioning Discipline** | **PASS** | Artifact hashes will be recorded in state files upon completion. |
| **VI. Socio-Technical Metric Isolation** | **PASS** | Plan separates git extraction (Phase 1) from LLM inference (Phase 3) entirely. |
| **VII. Benchmark Grounding Independence** | **PASS** | LLM scores derived from Code-to-Text ground truth; ownership metrics from git log up to snippet commit. |

## Project Structure

### Documentation (this feature)

```text
specs/001-code-ownership-llm-understanding/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Input: Schemas for validation (provided)
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── main.py              # Entry point for pipeline
├── extractors/
│   ├── __init__.py
│   ├── git_metrics.py   # FR-001: LOC-weighted Gini, developer count
│   └── complexity.py    # FR-002: Cyclomatic, doc density
├── inference/
│   ├── __init__.py
│   └── runner.py        # FR-003: LLM inference (StarCoder2-3B 4-bit), BLEU
├── analysis/
│   ├── __init__.py
│   └── regression.py    # FR-004, FR-006, FR-007: LMM, Sensitivity, VIF
└── utils/
    ├── config.py        # Seed pinning
    └── logger.py

data/
├── raw/                 # Cloned repos, raw git logs
├── processed/           # JSON metrics, inferred scores
└── results/             # Regression tables, plots

tests/
├── unit/
├── integration/
└── contract/
```

**Structure Decision**: Single `code/` directory with modular sub-packages for extraction, inference, and analysis to ensure isolation of concerns as per Constitution Principle VI.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **StarCoder2-3B 4-bit Quantization on CPU** | Required by FR-003. Fits 7GB RAM only with strict 4-bit quantization and model unloading. | Full precision (FP16/FP32) exceeds memory budget, causing OOM. Other models (CodeBERT) violate FR-003. |
| **LOC-Weighted Gini** | Commit count is a noisy proxy for ownership; LOC is more accurate. | Commit-only Gini may misrepresent actual code ownership contribution. |
| **Linear Mixed-Effects Model (LMM)** | Snippet-level analysis (n=150) with repo random effects increases power and handles clustering. | Aggregating to repo-level (n=30) results in underpowered regression (power < 0.20). |
| **Temporal Alignment** | Ensures ownership metric reflects the state of code at the time of the snippet. | Calculating Gini on full history introduces temporal mismatch bias. |
| **Sensitivity Analysis (FR-007)** | Required to prove robustness of Gini aggregation window. | Single-window analysis is insufficient for scientific validity per SC-003. |
| **VIF Calculation (SC-005)** | Required to validate independence of predictors. | Ignoring collinearity risks spurious correlation claims. |
| **Logit Transformation of BLEU** | BLEU is bounded [[deferred]]; standard regression assumes normal residuals. | Untransformed BLEU scores often violate normality assumptions of OLS. |

## Implementation Phases

### Phase 0: Pre-flight Validation & Data Hygiene (Constitution Compliance)
1.  **Reference Validation**: Run `Reference-Validator Agent` on all dataset citations. Block if any are unverified.
2.  **Data Checksumming**: Download raw datasets (CodeXGLUE) and clone repos. Calculate SHA256 checksums. Record hashes in `state/projects/PROJ-441-.../artifact_hashes` map.
3.  **Environment Setup**: Install `requirements.txt` (pinned versions). Verify `bitsandbytes` CPU wheel availability.

### Phase 1: Ownership Metric Extraction (FR-001, Temporal Alignment)
1.  **Input**: List of 30 repository URLs + CodeXGLUE sample metadata.
2.  **Temporal Alignment**: For each snippet, identify the specific commit SHA in the source repo (via file hash matching). Checkout that commit.
3.  **Process**:
    - Run `git log` up to the target commit.
    - Calculate **LOC-weighted Gini Coefficient** (using `git blame` to attribute lines to authors).
    - Calculate unique developer count and max author share.
4.  **Output**: `OwnershipMetrics` JSON per repo/commit.
5.  **Edge Case Handling**: If git history is missing or commit not found, set metrics to `null` and exclude.

### Phase 2: Complexity & Documentation Controls (FR-002)
1.  **Input**: Code snippets from Phase 1 repos (at target commit).
2.  **Process**:
    - Parse snippets using `radon` for Cyclomatic Complexity (CC).
    - Calculate Documentation Density = (Comment Lines) / (Total Lines).
3.  **Output**: `CodeSnippet` metrics JSON.
4.  **Edge Case Handling**: Non-Python/Java files are skipped.

### Phase 3: LLM Inference & Scoring (FR-003, Memory Management)
1.  **Model**: `bigcode/starcoder2-3b` (4-bit quantized via `bitsandbytes`).
2.  **Constraint**: Run on CPU. **Strategy**:
    - Load model with `device_map="cpu"`, `load_in_4bit=True`.
    - **Batch Size**: 1.
    - **Context Truncation**: Limit input to a manageable sequence length..
    - **Memory Management**: After each snippet inference, `del model; torch.cuda.empty_cache()` (if applicable) or `gc.collect()` and reload for next batch to prevent memory leak.
    - **Fallback**: If runtime > 5 hours or OOM occurs, reduce snippets per repo to 3, then 2.
3.  **Task**: Code-to-Text generation.
4.  **Metric**: BLEU score against ground truth.
5.  **Retry Logic**: Retry inference up to 2 times on timeout (FR-005).

### Phase 4: Statistical Analysis (FR-004, FR-006, FR-007, SC-005)
1.  **Model**: Linear Mixed-Effects Model (LMM): `BLEU ~ Gini + CC + DocDensity + (1|Repository)`.
    - **Transformation**: Apply Logit transformation to BLEU scores.
    - **Non-Linearity**: Add `Gini^2` term; perform Likelihood Ratio Test.
2.  **Unit of Analysis**: Snippet (n=150), with Repository as random effect.
3.  **Correction**: Apply Bonferroni or FDR if multiple models/languages are tested (FR-006).
4.  **Sensitivity**: Sweep Gini window over a broad range of values commits

Reference: N/A
Research Question: How does the choice of Gini window size affect model performance?
Method: Systematic parameter sweep across varying window sizes. (FR-007).
5.  **Collinearity Check**: Calculate VIF. If VIF ≥ 5, report limitation (SC-005).
6.  **Residual Check**: Shapiro-Wilk test for normality. If failed, run Spearman rank correlation as sensitivity.

## Compute Feasibility

- **Hardware**: Multiple CPU, 7GB RAM.
- **Strategy**:
  - Strict 4-bit quantization.
  - Model unloading between snippets.
  - Progressive sample reduction (5 -> 3 -> 2 snippets/repo) if 6h limit threatened.
  - No GPU usage.
  - Total runtime monitored; auto-stop if > 5.5h.