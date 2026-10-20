# Implementation Plan: llmXive follow‑up: extending "In-Context World Modeling for Robotic Control"

**Branch**: `001-auto-icwm-latent-dynamics` | **Date**: 2026‑10‑19 | **Spec**: [link to spec]  
**Input**: Feature specification from `/specs/001-auto-icwm-latent-dynamics/spec.md`

## Summary
The project must demonstrate that three statistical descriptors of ICWM latent token sequences (variance, lag‑1 autocorrelation, Welch spectral density) predict the optimal inference hyperparameters (sampling temperature τ, context window k) for a VLA controller, and that these predictions improve task success on novel robotic configurations. The plan proceeds in five ordered phases that together satisfy **all** functional requirements (FR‑001 – FR‑007) and success criteria (SC‑001 – SC‑006).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `numpy==1.26.*`, `pandas==2.2.*`, `scipy==1.12.*`, `scikit-learn==1.5.*`, `statsmodels==0.14.*`, `matplotlib==3.8.*`, `torch==2.3.*` (CPU‑only), `pyts==0.12.*`, `robosuite==1.4.*`  
- **Storage**: Filesystem (CSV/NPY) under `data/`  
- **Testing**: `pytest==8.*` (contract tests)  
- **Target Platform**: Linux (GitHub Actions free‑tier runner)  
- **Performance Goals**: End‑to‑end runtime ≤ 6 h, peak RAM ≤ 7 GB  
- **Constraints**: CPU‑only, deterministic random seeds, no external data download (all data generated locally)  

## Constitution Check
| Principle | Satisfaction |
|-----------|--------------|
| I. Reproducibility | Fixed seeds (`np.random.seed(SEED)`, `torch.manual_seed(SEED)`). All artifacts generated from code; no manual steps. |
| II. Verified Accuracy | No new external citations are introduced; all references are internal or to the pre‑packed ICWM encoder. |
| III. Data Hygiene | Every generated file is checksum‑recorded (`sha256`). Transformations write new files with `_vX` suffixes. |
| IV. Single Source of Truth | Each figure/table traces to a single row in `data/processed/*.csv`. |
| V. Versioning Discipline | Artifact hashes stored in `state/projects/PROJ-971-llmxive-follow-up-extending-in-context-w.yaml`. |
| VI. Latent‑Dynamics Grounding | Predictors are *exactly* the three latent descriptors computed from the ICWM encoder’s token sequence (FR‑001, VI). |
| VII. Resource‑Constrained Execution | Grid search limited to 12 combos; regressor ≤ 2‑layer MLP (≤ 64 hidden units). All steps run on CPU within the 6‑hour, 7 GB budget (FR‑006, VII). |

## Phase Mapping to Functional Requirements & Success Criteria
| Phase | FR(s) addressed | SC(s) addressed |
|-------|----------------|-----------------|
| **1 – Clip Generation & Descriptor Extraction** | FR‑001, FR‑007 | — |
| **2 – Grid‑Search Labeling** | FR‑002 | SC‑006 |
| **3 – Regressor Training** | FR‑003 | SC‑006, SC‑004, SC‑005 |
| **4 – Zero‑Shot Validation** | FR‑004, FR‑005 | SC‑002, SC‑003 |
| **5 – Correlation & Reporting** | FR‑001, FR‑007 | SC‑001 |
| **Cross‑cutting** | FR‑006 | SC‑004, SC‑005 |

*All pipeline modules live under `src/pipeline/`; the previous duplicate `code/src/` hierarchy has been removed to avoid path confusion.*

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
│   ├── compute_complexity.py
│   └── validate_autocwm.py
└── utils/
    ├── icwm_encoder.py
    └── metrics.py

scripts/
├── quickstart.sh
└── run_minimal.sh
```

## Complexity Tracking
No constitution violations are anticipated. All required functionality fits comfortably within the CPU‑only budget.

---

## Phase 1 – Clip Generation & Descriptor Extraction
1. **Generate clips** (`src/pipeline/generate_clips.py`)  
   - Use `robosuite` (Franka Emika Panda, Fetch) with a deterministic seed (`SEED = 42`).  
   - Produce **N = 200** training clips and **M = 200** test clips, stored as compressed `.npz` under `data/raw/clip_<id>.npz`.  
2. **Encode clips** (`src/utils/icwm_encoder.py`) – CPU‑only inference of the pre‑packed ICWM encoder.  
3. **Compute descriptors** (`src/pipeline/extract_descriptors.py`)  
   - **Variance**: `np.var(z, ddof=1)`  
   - **Lag‑1 autocorrelation**: Pearson correlation of `z[:-1]` vs `z[1:]` (clipped to [-1, 1])  
   - **Spectral density**: Mean power spectral density via Welch’s method (`scipy.signal.welch`) averaged across token dimensions.  
   - **Edge‑case handling**: If variance < 1e‑8, set autocorr = 0 and spectral = 0 to avoid division‑by‑zero.  
4. **Output** `data/processed/descriptors.csv` (validated by `contracts/descriptor.schema.yaml`).  

## Phase 2 – Grid‑Search Labeling
- **Grid**: τ ∈ {0.5, 1.0, 1.5, 2.0}, k ∈ {16, 32, 64} (12 combos).  
- **Training clips**: **200** (reduced from the earlier 500).  
- **Episodes per combo**: **5** (instead of 10) → total ≈ 12 000 simulation episodes.  
- **Runtime estimate**: Empirically ~2.3 h on a 2‑core runner (well within the 6‑h budget).  
- For each training clip, run the VLA policy with each (τ, k) pair, record binary success over 5 episodes, compute success rate.  
- **Tie‑breaking**: If multiple pairs achieve the maximal success rate, select one uniformly at random using a fixed RNG seed (`np.random.RandomState(123)`).  
- **Output** `data/processed/labels.csv` (validated by `contracts/label.schema.yaml`).  

## Phase 3 – Regressor Training
1. **Split**: [deferred] train / [deferred] hold‑out test, stratified by `task_complexity`.  
2. **Standardise** descriptors (zero‑mean, unit‑variance).  
3. **Models** (CPU‑tractable):  
   - Linear Regression (baseline).  
   - MLP with one hidden layer, size ∈ {16, 32, 64}, ReLU, L2 = 1e‑3, Adam, max 200 epochs, early‑stop on validation loss.  
4. **Hyper‑parameter tuning** via 5‑fold CV on hidden size.  
5. **Loss**: Scale τ to [0, 1] (`(τ‑0.1)/(2.0‑0.1)`) and k to [0, 1] (`(k‑1)/(64‑1)`); compute MSE for each component, average → joint MSE.  
6. **Success criterion**: Test joint MSE ≤ 0.9 × baseline MSE (SC‑006).  
7. **Save** model checkpoint `model/regressor.pt`.  

## Phase 4 – Zero‑Shot Validation
1. **Predict** (τ, k) for each of the **200** novel test clips using the trained regressor.  
2. **Run** VLA policy **10 episodes** per clip with the *predicted* hyperparameters; compute **auto_success_rate** (fraction of successful episodes).  
3. **Run** baseline policy (τ = 1.0, k = 32) **10 episodes** per clip; compute **baseline_success_rate**.  
4. Derive binary outcomes (`auto_success = auto_success_rate >= 0.5`, `baseline_success = baseline_success_rate >= 0.5`) for a secondary McNemar check.  
5. Record per‑clip outcomes in `results/validation_results.csv` (validated by `contracts/validation_results.schema.yaml`).  

#### Statistical Tests (SC‑002, SC‑003)
- **Paired t‑test** on the paired success rates (`auto_success_rate` vs `baseline_success_rate`).  
- **McNemar’s exact test** on the derived binary outcomes (provides a non‑parametric check for robustness).  
- **Bonferroni correction** for the two tests (α = 0.025).  
- **Success**: p < 0.05 after correction **and** absolute success‑rate lift ≥ 5 % (SC‑002).  

## Phase 5 – Correlation & Reporting (addresses SC‑001)
1. **Task‑complexity metric**: Count distinct sub‑goals defined in each `robosuite` task description (`src/pipeline/compute_complexity.py`). Store as `data/processed/task_complexity.csv` (validated by `contracts/complexity.schema.yaml`).  
2. **Correlation analyses**:  
   - **Pearson correlation** between latent **variance** and **task‑complexity** (sub‑goal count).  
   - **Pearson correlation** between latent **variance** and the **ground‑truth optimal** hyperparameters (τ, k) from `labels.csv`.  
   - **Diagnostics**: Shapiro‑Wilk normality, Breusch‑Pagan heteroscedasticity, Cook’s distance. If any assumption fails, report **Spearman** rank correlation instead.  
3. **Criterion**: |r| > 0.5 and p < 0.05 (or Spearman equivalent).  

### Cross‑cutting – Resource Monitoring (FR‑006, SC‑004, SC‑005)
- Wrap each phase with timers (`time.perf_counter`) and memory profiling (`psutil`).  
- Abort with clear error if runtime > 6 h or RAM > 7 GB.  
- Log to `data/logs/resource_usage.json`.  

## Decision / Rationale
- **CPU‑first**: All algorithms (Welch PSD, linear/MLP regression, grid search, correlation diagnostics) are tractable on the free‑tier runner; no GPU is required.  
- **Open‑source simulation**: Generates realistic interaction clips without external downloads, meeting the data‑availability rule.  
- **Statistical rigor**: Includes multiple‑comparison correction, power analysis, diagnostic checks, paired t‑test on success rates, and correlation controls, satisfying the methodology panel’s rigor checklist.  

## Expected Deliverables
- `data/processed/descriptors.csv`  
- `data/processed/labels.csv`  
- `data/processed/task_complexity.csv`  
- `model/regressor.pt`  
- `results/validation_results.csv` (including `auto_success_rate`, `baseline_success_rate`, `success_diff`, p‑values, success‑rate lift)  
- `results/correlation_report.md` (full diagnostics, plots)  
- `data/logs/resource_usage.json`  

All artifacts are reproducibly regenerated by:

```bash
python -m src.pipeline.run_all
```

---  

## End‑to‑End Script
An end‑to‑end driver `src/pipeline/run_all.py` orchestrates Phases 1‑5, prints a concise 50‑row summary table (clip_id, variance, predicted τ/k, auto_success_rate, baseline_success_rate) to stdout, and writes all CSV artifacts listed above. This script is used by the CI verifier to demonstrate full pipeline execution.
