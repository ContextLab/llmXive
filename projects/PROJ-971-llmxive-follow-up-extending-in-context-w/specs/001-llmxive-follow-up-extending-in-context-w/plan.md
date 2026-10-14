# Implementation Plan: llmXive follow‑up: extending "In-Context World Modeling for Robotic Control"

**Branch**: `001-auto-icwm-latent-dynamics` | **Date**: 2026‑10‑14 | **Spec**: [link to spec]  
**Input**: Feature specification from `/specs/001-auto-icwm-latent-dynamics/spec.md`

## Summary
The project must demonstrate that three statistical descriptors of latent token sequences (variance, lag‑1 autocorrelation, spectral density) predict the optimal inference hyperparameters (sampling temperature τ, context window k) for the ICWM controller, and that these predictions improve task success on novel robotic configurations. The plan proceeds in five tightly‑coupled phases that directly address every functional requirement (FR‑001 – FR‑007) and success criterion (SC‑001 – SC‑006).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `numpy==1.26.*`, `pandas==2.2.*`, `scipy==1.12.*`, `scikit-learn==1.5.*`, `statsmodels==0.14.*`, `matplotlib==3.8.*`, `torch==2.3.*` (CPU‑only), `pyts==0.12.*`, `robosuite==1.4.*`  
- **Storage**: Filesystem (CSV/NPY) under `data/`  
- **Testing**: `pytest==8.*` (contract tests)  
- **Target Platform**: Linux (GitHub Actions runner)  
- **Performance Goals**: End‑to‑end runtime ≤ 6 h, peak RAM ≤ 7 GB  
- **Constraints**: CPU‑only, deterministic seeds, no external data download (all data generated locally)  

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| I. Reproducibility | Fixed random seeds (e.g., `np.random.seed(SEED)`, `torch.manual_seed(SEED)`). All artifacts generated from code; no external downloads. |
| II. Verified Accuracy | No new external citations are introduced. |
| III. Data Hygiene | Every generated file is checksum‑recorded; transformations write new files with explicit suffixes. |
| IV. Single Source of Truth | All figures, statistics, and interpretations trace back to a single row in the CSV outputs (`descriptors.csv`, `labels.csv`, `validation_results.csv`). |
| V. Versioning Discipline | Output artifact hashes are stored in `state/projects/PROJ-971-llmxive-follow-up-extending-in-context-w.yaml`. |
| VI. Latent‑Dynamics Grounding | Predictors are exactly the three latent descriptors computed from the encoder’s token sequence. |
| VII. Resource‑Constrained Execution | Grid search limited to 12 combos per configuration; regressor is ≤ 2‑layer MLP with ≤ 64 hidden units. All steps run on CPU within the 6‑hour budget. |

## Phase Mapping to Functional Requirements & Success Criteria
| Phase | FR(s) addressed | SC(s) addressed |
|-------|----------------|-----------------|
| 1 – Data Generation & Extraction | FR‑001, FR‑007 | SC‑001 (via Phase 5) |
| 2 – Grid‑Search Labeling | FR‑002 | SC‑006 |
| 3 – Regressor Training | FR‑003 | SC‑006, SC‑004, SC‑005 |
| 4 – Zero‑Shot Validation | FR‑004, FR‑005 | SC‑002, SC‑003 |
| 5 – Correlation Analysis & Reporting | FR‑001, FR‑007 | SC‑001 |
| Cross‑cutting | FR‑006 | SC‑004, SC‑005 |

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
└── tasks.md   # generated later

src/
├── pipeline/
│   ├── generate_clips.py
│   ├── extract_descriptors.py
│   ├── grid_search_labels.py
│   ├── train_regressor.py
│   └── validate_autocwm.py
└── utils/
    ├── icwm_encoder.py
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


## Phase Details

### Phase 1 – Data Generation & Extraction
- Generate a sizable set of training clips and a corresponding set of test clips (using a fixed seed) via `robosuite`.  
- Encode each clip, compute variance, lag‑1 autocorrelation, and Welch spectral density.  
- Edge‑case handling for near‑zero variance (set autocorr = 0, spectral = 0).  
- Output `data/processed/descriptors.csv`.

### Phase 2 – Grid‑Search Labeling
- Exhaustive search over τ ∈ {0.5, 1.0, 1.5, 2.0} and k ∈ {16, 32, 64}.  
- For each training clip, run the VLA policy, record binary success, compute success rate.  
- Tie‑breaking: deterministic random choice with fixed seed.  
- Output `data/processed/labels.csv`.

### Phase 3 – Regressor Training
- Train both Linear Regression (baseline) and a 1‑hidden‑layer MLP (≤ 64 units, L2 = 1e‑3).  
- Features are standardised (zero‑mean, unit‑variance).  
- Hyper‑parameter tuning via 5‑fold CV on hidden size {16, 32, 64}.  
- Baseline MSE defined as the average of squared errors on τ and k after scaling τ to [0,1] and k to [0,1]; joint MSE = mean of the two components.  
- Require test MSE ≤ 0.9 × baseline MSE (SC‑006).  
- Output `model/regressor.pt`.

### Phase 4 – Zero‑Shot Validation
- Apply regressor to 200 novel test clips.  
- Run VLA policy with predicted (τ, k) and with fixed baseline (τ = 1.0, k = 32).  
- Record binary success, compute `results/validation_results.csv`.  
- Perform McNemar exact test and Wilcoxon signed‑rank test with Bonferroni‑corrected α = 0.025 (SC‑002, SC‑003).

### Phase 5 – Correlation Analysis & Reporting (addresses SC‑001)
- Compute Pearson correlation between latent variance and task‑complexity.  
- Additionally compute **partial correlation** controlling for task‑complexity when relating variance to hyperparameter performance, using `statsmodels.stats.partial_corr`.  
- Perform diagnostic checks: Shapiro‑Wilk normality test on residuals, Breusch‑Pagan heteroscedasticity test, and influence analysis (Cook’s distance).  
- If assumptions violated, report **Spearman** rank correlation as a robustness check.  
- Summarise results in `results/correlation_report.md` and include plots (scatter with regression line, residuals).  

### Cross‑cutting – Resource Monitoring (FR‑006, SC‑004, SC‑005)
- Wrap each phase with timers (`time.perf_counter`) and memory profiling (`psutil`).  
- Abort with clear error if runtime > 6 h or RAM > 7 GB.  
- Log to `data/logs/resource_usage.json`.

### Decision / Rationale
- **CPU‑first**: All computations (Welch PSD, linear/MLP regression, grid search over ≤ 12 combos, correlation diagnostics) are tractable on the free‑tier runner.  
- **Open‑source simulation**: Generates realistic interaction clips without external data download, meeting the data‑availability rule.  
- **Statistical rigor**: Partial correlation, diagnostic checks, Bonferroni correction, explicit power analysis, and stratified sampling ensure robust inference.

## Expected Deliverables
- `data/processed/descriptors.csv`  
- `data/processed/labels.csv`  
- Trained model checkpoint `model/regressor.pt`  
- `results/validation_results.csv` (including success rates, p‑values, correlation)  
- `results/correlation_report.md` (full diagnostics)  
- `data/logs/resource_usage.json`  

All artifacts are reproducibly regenerated by:

```bash
python -m src.pipeline.run_all
```

---

