# Implementation Plan: Evaluating the Impact of Code Generation on Long-Term Code Maintainability

**Branch**: `001-code-maintainability-impact` | **Date**: 2026-06-29 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-code-maintainability-impact/spec.md`

## Summary

This feature implements a longitudinal study to determine if code associated with LLM generation tags exhibits different maintainability characteristics (churn, bug fix latency) compared to human-written code. The approach involves: (1) identifying active repositories via GitHub API, (2) tagging code blocks using a CPU-optimized CodeBERT classifier (treated as a probabilistic proxy), (3) performing propensity score matching with repository-level covariates to control for context, (4) extracting longitudinal metrics over a multi-month window, and (5) conducting Linear Mixed-Effects Model (LMM) analysis to account for hierarchical data structure. All processing is constrained to CPU-only execution on free-tier GitHub Actions runners with limited vCPU and RAM resources.

> **Critical Methodological Note**: The study relies on a classifier to assign "LLM" vs "Human" labels. This introduces measurement error. The analysis explicitly treats the classifier output as a probabilistic construct. A **Sensitivity Analysis** is mandated to quantify how misclassification rates (derived from the ground truth subset) bias the effect size. The results are framed as "Associations between LLM-tagged code and maintainability" rather than "Causal effects of LLM generation."

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers`, `onnxruntime`, `radon`, `scikit-learn`, `pandas`, `requests`, `matplotlib`, `statsmodels`, `datasets`  
**Storage**: Local filesystem (`data/` for raw/processed data), GitHub API (external)  
**Testing**: `pytest` (unit/integration), contract validation via YAML schemas  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Data science pipeline / Research tool  
**Performance Goals**: Complete full pipeline within 6 hours; memory usage < 7GB; disk usage < 14GB  
**Constraints**: No GPU; no large-LLM inference; shallow git clones; sampling for manual verification  
**Scale/Scope**: A substantial number of repositories; ~k code blocks; -month historical window  

> **Runtime Safety**: The GitHub Actions free-tier has a hard timeout. The pipeline is configured with a timeout setting in the workflow. The `01_data_curation.py` script includes a checkpoint mechanism: if interrupted, it resumes from the last saved repo. If the 6-hour limit is approached, the script automatically reduces the sample size to ensure a valid result set is produced.

> **Dataset Constraint Note**: The spec requires a dataset of *LLM-generated vs Human-written code blocks* with *longitudinal maintenance history*. The "Verified datasets" block contains text-generation datasets and static code dumps, but **none** contain the required longitudinal git history or paired human/LLM labels with maintenance events. This plan treats the "Verified datasets" as **unusable** for the primary analysis and instead relies on **live GitHub API calls** to construct the dataset dynamically, as mandated by FR-001. The verified URLs are only referenced for potential auxiliary text-generation benchmarks if the live API fails to yield sufficient data, but the primary data source is the live GitHub ecosystem.

## Constitution Check

| Principle | Compliance Status | Notes |
|-----------|-------------------|-------|
| I. Reproducibility | **Pass** | Random seeds pinned; `requirements.txt` used; data checksums enforced. |
| II. Verified Accuracy | **Pass** | All dataset sources (GitHub API) are live and verifiable; no hallucinated URLs used for primary data. |
| III. Data Hygiene | **Pass** | Raw data preserved; derivations written to new files; PII scan enabled. **Ground truth files (`data/ground_truth/manual_labels.csv`) are checksummed immediately after creation and recorded in `state/`.** |
| IV. Single Source of Truth | **Pass** | All stats trace to `data/` rows; no hand-typed numbers in paper. |
| V. Versioning Discipline | **Pass** | Content hashes tracked in `state/`; artifacts updated on change. Ground truth checksums included. |
| VI. Longitudinal Data Integrity | **Pass** | Immutable snapshots of git history; gaps documented. **Statistical analysis uses Linear Mixed-Effects Models (LMM) to handle hierarchical data, superseding the spec's Wilcoxon reference which is methodologically insufficient for clustered data.** |
| VII. Classification Ground Truth | **Pass** | Random subset selected for manual verification; **Sensitivity Analysis** performed to quantify bias; metrics calculated. |

## Project Structure

### Documentation (this feature)

```text
specs/001-code-maintainability-impact/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-247-evaluating-the-impact-of-code-generation/
├── data/
│   ├── raw/             # Raw GitHub API dumps, git logs
│   ├── processed/       # Matched pairs, metrics
│   └── ground_truth/    # Manual verification labels (checksummed)
├── code/
│   ├── 01_data_curation.py
│   ├── 02_metric_extraction.py
│   ├── 03_analysis.py
│   ├── utils/
│   │   ├── github_client.py
│   │   ├── classifier.py
│   │   └── matching.py
│   └── requirements.txt
├── tests/
│   ├── unit/
│   └── contract/
└── docs/
    └── paper/
```

**Structure Decision**: Single project structure with modular `code/` directory. Separation of `raw/` and `processed/` ensures data hygiene (Constitution Principle III). `utils/` isolates complex logic (GitHub API, ONNX inference, matching).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Linear Mixed-Effects Model (LMM) | Required to account for non-independence of blocks within repositories (Constitution VI, Panel Concern). | Wilcoxon Signed-Rank test assumes independence; using it would violate statistical assumptions and produce invalid p-values. |
| Repository Stratification | Required to control for "confounding by repository" (Panel Concern). | Simple matching on block-level metrics fails to account for systemic repo-level biases (e.g., tutorial vs. production). |
| Sensitivity Analysis | Required to quantify bias from classifier uncertainty (Panel Concern). | Treating classifier output as absolute truth ignores measurement error, leading to potentially spurious conclusions. |
| ONNX Runtime | Required for CPU-only inference of CodeBERT (Constitution + Compute Feasibility). | Standard `transformers` with PyTorch would be too slow/heavy for 6-hour limit on CPU. |
| Shallow Git Clone | Required to fit 7GB RAM and 6-hour limit. | Full clone would exceed disk/memory limits and timeout. |

## Methodological Rigor & Panel Concerns Addressed

### 1. Classifier Validity & Circular Validation
- **Mitigation**: The plan does not treat the "origin_label" as ground truth. It is a "probabilistic proxy."
- **Action**: A **Sensitivity Analysis** is performed. We calculate the misclassification rate from the ground truth subset. We then re-run the LMM with the effect size adjusted for this error rate (using standard measurement error correction formulas) to report a "bias-corrected" confidence interval.

### 2. Confounding by Repository
- **Mitigation**: Propensity score matching includes **repository-level covariates** (stars, age, contributor count) in addition to block-level metrics.
- **Action**: Matching is performed **within** repositories (stratified) where possible. If not, a random effect for `repo_id` is used in the LMM.

### 3. Survivorship & Linking Bias
- **Mitigation**: We explicitly analyze the rate of issue linking for LLM vs. Human blocks.
- **Action**: If a significant difference in linking rates is found, the latency analysis is stratified by "linked" vs "unlinked" blocks, and results are qualified as "for tracked issues only."

### 4. Statistical Validity (LMM vs Wilcoxon)
- **Mitigation**: The Constitution requires "Longitudinal Data Integrity" and handling of hierarchical data.
- **Action**: We use a Linear Mixed-Effects Model (LMM) with `repo_id` as a random intercept. This supersedes the Wilcoxon test mentioned in the spec (which will be updated in a kickback).

### 5. Ground Truth Integrity
- **Mitigation**: Manual verification is not just a check; it is a critical artifact.
- **Action**: `data/ground_truth/manual_labels.csv` is checksummed and recorded in `state/` immediately after manual entry. This ensures it is versioned and immutable.
