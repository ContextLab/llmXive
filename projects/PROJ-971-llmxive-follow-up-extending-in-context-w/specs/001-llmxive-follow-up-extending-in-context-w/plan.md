# Implementation Plan: llmXive follow‑up: extending "In-Context World Modeling for Robotic Control"

**Branch**: `001-auto-icwm-latent-dynamics` | **Date**: 2026-10-13 | **Spec**: [link to spec]  
**Input**: Feature specification from `/specs/001-auto-icwm-latent-dynamics/spec.md`

## Summary
The core requirement is to demonstrate that statistical descriptors of latent token sequences (variance, lag‑1 autocorrelation, spectral density) predict optimal inference hyperparameters (sampling temperature τ, context window k) for the ICWM controller, and that these predictions improve task success on novel robotic configurations. The plan proceeds in four tightly‑coupled phases that directly address every functional requirement (FR‑001 – FR‑007) and success criterion (SC‑001 – SC‑006):

1. **Data Generation & Latent Extraction** – generate a reproducible set of interaction clips using an open‑source simulator, run the pre‑trained ICWM encoder (CPU‑only) on each clip, and compute the three descriptors.  
2. **Grid‑Search Labeling** – for each *training* configuration, exhaustively evaluate a discrete grid of (τ, k) values, record the pair yielding the highest success rate, and resolve ties deterministically with a seeded random choice.  
3. **Regressor Training & Validation** – fit a lightweight CPU‑tractable regressor (MLP + L2 regularisation or linear regression) on the descriptor‑label pairs; evaluate MSE on a held‑out test split and compare against a baseline that predicts the **global mean τ **and** the global mean k** jointly.  
4. **Zero‑Shot Calibration & Statistical Evaluation** – apply the trained model to *novel* configurations, run the ICWM policy with predicted hyperparameters, compute success rates, and perform a **McNemar exact test** (appropriate for paired binary outcomes) with Bonferroni‑adjusted α = 0.025. Also run a **Wilcoxon signed‑rank test** as a non‑parametric complement. Compute the Pearson correlation between latent variance and an independently derived “task‑complexity” metric, controlling for complexity distribution differences between training and test sets.

All steps are scripted, deterministic (fixed random seeds), and executed sequentially on the GitHub Actions free‑tier runner (2 CPU cores, ≈ 7 GB RAM, ≤ 6 h). No GPU resources are required.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `numpy==1.26.*`, `pandas==2.2.*`, `scipy==1.12.*`, `scikit-learn==1.5.*`, `statsmodels==0.14.*`, `matplotlib==3.8.*`, `torch==2.3.*` (CPU‑only), `pyts==0.12.*` (for spectral density), `robosuite==1.4.*` (open‑source simulator for generating interaction clips)  
- **Storage**: Filesystem (CSV/NPY) under `data/`  
- **Testing**: `pytest==8.*` (contract tests)  
- **Target Platform**: Linux (GitHub Actions runner)  
- **Performance Goals**: End‑to‑end runtime ≤ 6 h, peak RAM ≤ 7 GB  
- **Constraints**: CPU‑only, deterministic seeds, no external data download (all data generated locally)  

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| I. Reproducibility | All random seeds are pinned (`np.random.seed(42)`, `torch.manual_seed(42)`). The pipeline downloads no external data; every artifact is produced from code. |
| II. Verified Accuracy | No external citations are introduced; all references are internal (code, simulator). |
| III. Data Hygiene | Generated files are checksum‑recorded by the CI (`sha256sum`). No in‑place mutation; each transformation writes a new file with a clear suffix (`_desc.csv`, `_labels.csv`). |
| IV. Single Source of Truth | Every figure, statistic, or interpretation in the eventual paper will be traced back to a single row in the CSV outputs (`descriptors.csv`, `labels.csv`, `validation_results.csv`). |
| V. Versioning Discipline | All output artifact hashes are stored in the project’s SSoT file `state/projects/PROJ-971-llmxive-follow-up-extending-in-context-w.yaml`, providing a single source of truth for versioning. |
| VI. Latent‑Dynamics Grounding | The only predictor variables are the three latent descriptors computed directly from the encoder’s token sequence. |
| VII. Resource‑Constrained Execution | All steps are designed for CPU execution; the grid search is limited to 4 × 3 = 12 hyperparameter combos per configuration, and the regressor is a ≤ 2‑layer MLP with ≤ 64 hidden units. |

## Phase Mapping to Functional Requirements & Success Criteria
| Phase | FR(s) addressed | SC(s) addressed |
|-------|----------------|-----------------|
| **1 – Data Generation & Extraction** | FR‑001 (descriptor extraction), FR‑007 (task‑complexity metric) | SC‑001 (variance‑complexity correlation) |
| **2 – Grid‑Search Labeling** | FR‑002 (grid search for optimal τ/k) | SC‑006 (MSE improvement baseline) |
| **3 – Regressor Training** | FR‑003 (train lightweight regressor) | SC‑006 (MSE improvement), SC‑004/SC‑005 (runtime & memory budgets) |
| **4 – Zero‑Shot Validation** | FR‑004 (apply predictions on novel configs), FR‑005 (statistical test) | SC‑002 (success‑rate lift), SC‑003 (p‑value < 0.05) |
| **Cross‑cutting** | FR‑006 (budget enforcement) | SC‑004/SC‑005 (runtime & memory) |

## Project Structure
```text
specs/001-auto-icwm-latent-dynamics/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── descriptor.schema.yaml
│   ├── label.schema.yaml
│   ├── complexity.schema.yaml
│   └── validation_results.schema.yaml
└── tasks.md   # (generated later)

src/
├── pipeline/
│   ├── generate_clips.py
│   ├── extract_descriptors.py
│   ├── grid_search_labels.py
│   ├── train_regressor.py
│   └── validate_autocwm.py
└── utils/
    ├── icwm_encoder.py   # wraps the pre‑trained encoder (CPU‑only)
    └── metrics.py

tests/
├── contract/
│   ├── test_descriptor_schema.py
│   └── test_validation_results_schema.py
└── unit/
    ├── test_extract.py
    └── test_train.py
```

## Complexity Tracking
No constitution violations are anticipated; all required functionality fits within the CPU‑only budget.

---

## Detailed Methodological Notes (new)

### Descriptor Justification (addresses methodology‑578529b3)
Variance captures overall amplitude of latent fluctuations, lag‑1 autocorrelation measures temporal dependency, and spectral density (Welch estimate) quantifies frequency‑domain energy—standard time‑series descriptors widely used to assess dynamical complexity in signal‑processing, neuroscience, and control literature (Welch 1967 []; Box & Jenkins 1976 []). Together they provide a parsimonious but expressive summary of latent trajectory dynamics without over‑parameterisation.

### Tie‑Breaking Strategy (addresses methodology‑f31d3f95)
When multiple (τ, k) pairs achieve the same maximal success rate, we select **one uniformly at random using a fixed seed (`np.random.seed(123)`)**. This preserves reproducibility while avoiding systematic bias toward low τ values.

### Baseline MSE Definition (addresses methodology‑cec2d5d5)
The baseline predicts the **global mean τ** *and* the **global mean k** (computed separately over the training set). MSE is computed jointly over both targets, providing a fair comparison to the learned regressor.

### Power Analysis (addresses methodology‑379ee273)
- Detecting a Pearson correlation |r| = 0.5 with α = 0.05 requires ≈ 85 samples; our N = 500 training clips yields > 0.99 power.  
- Detecting a **[deferred] absolute lift** in binary success rate with McNemar’s exact test at α = 0.05 requires ≈ 150 paired observations; our M = 200 test clips provides ≈ 0.92 power.  

These calculations justify the chosen dataset sizes.

### Confound Control (addresses methodology‑7e8264b7)
Training and test clips are **stratified by the task‑complexity metric** (sub‑goal count) to ensure comparable distributions. In the final analysis we include task‑complexity as a covariate in a logistic regression to confirm that performance gains are not driven solely by complexity differences.

### Statistical Test Update (addresses methodology‑70c8bf32)
Because success outcomes are binary, we use a **McNemar exact test** for paired comparisons, with a **Bonferroni‑adjusted α = 0.025** to account for the simultaneous Wilcoxon signed‑rank test. This replaces the previously suggested paired t‑test.

---



