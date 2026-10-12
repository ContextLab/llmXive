# Research: Predicting Glass Transition Temperature from Compositional Descriptors with Explainable Boosting Machines

**Feature**: `001-predict-tg-from-composition`  
**Date**: 2026-10-11  

## Objective
Demonstrate a reproducible workflow that (i) ingests open polymer structural data, (ii) engineers chemically-informed descriptors, (iii) **conditionally** trains an Explainable Boosting Machine (EBM) when a real $T_g$ target is available, and (iv) validates the model's explanations against **Fractional Free Volume (FFV) and Chain Stiffness** computed via Van Krevelen group contributions (per spec.md FR-005 / SC-002).

## Decision / Rationale
| Decision | Rationale |
|----------|-----------|
| **CPU-only execution** | All required libraries (RDKit, scikit-learn, interpret) have CPU wheels; the free GitHub Actions runner provides only CPU resources. |
| **Open-source data** | No open polymer $T_g$ dataset exists in the verified-datasets list, and the spec's mandated sources (Polymer Genome Project, NIST WebBook) are not programmatically downloadable by the CI runner. This is a **spec-root feasibility flaw (FR-001 BLOCKED — kickback)**. We use the verified open SMILES dataset for descriptor engineering and defer all $T_g$-dependent analysis. |
| **Conditional model training with graceful skip** | Model training, performance evaluation, and interpretability are executed **only if** a column named `experimental_tg` is present in `feature_matrix.csv`. If it is absent, the pipeline **skips the model-related stages with a clear log message** (no fatal error) and completes the descriptor/physical-property stages. This behavior is aligned across plan.md and quickstart.md. |
| **Chunked processing** | If any raw file exceeds the available RAM limit, we stream it (`datasets.load_dataset(..., streaming=True)`) or randomly sample rows with a fixed seed (42), ensuring reproducibility while respecting resource caps. |
| **Statistical rigor** | - 5-fold CV for hyperparameter tuning. <br> - Multiple-comparison correction (Bonferroni) when testing correlations between top features and FFV/Chain Stiffness (SC-002). <br> - Power analysis deferred (`[deferred]`) because the sample size for $T_g$ is currently unknown; this limitation is acknowledged explicitly. |
| **Physical consistency (per spec.md)** | Feature importance will be correlated with **FFV and Chain Stiffness** from `data/physical_properties.csv` (independent of $T_g$) to satisfy spec.md FR-005/SC-002/Principle VI. Note: the ratified project constitution's Principle VI names WLF constants (C₁, C₂) instead; no open WLF dataset exists, so this divergence is **flagged for spec-root kickback** rather than silently substituted. |
| **Sensitivity analysis** | Perturb top-3 descriptors by ±10 % (Gaussian noise, σ = 0.1 × mean) **once** a real $T_g$ target is present; record the standard deviation of predicted $T_g$ shifts (SC-003). |

## Dataset Strategy
| Role | Source | Loader | Notes |
|------|--------|--------|-------|
| **SMILES strings** | https://huggingface.co/datasets/maykcaldas/smiles-transformers/resolve/main/data/test-00000-of-00015-27ed436361d9186e.parquet | `datasets.load_dataset("maykcaldas/smiles-transformers", split="test")` | Provides a large collection of valid SMILES; used for descriptor engineering. Split matches the verified shard URL. |
| **Physical properties (FFV, Chain Stiffness)** | https://huggingface.co/datasets/main-horse/ffv4_dataset_test/resolve/main/data/everything-00000-of-00009-42e3f6f9da399cf0.parquet | `datasets.load_dataset("main-horse/ffv4_dataset_test", split="train")` | Used for cross-checking the Van Krevelen FFV/stiffness calculations. |
| **Polymer $T_g$ values (FR-001)** | **None (BLOCKED — spec-root kickback)** | – | No open, programmatically downloadable polymer $T_g$ dataset exists in the verified-datasets list; the spec's mandated sources (Polymer Genome Project, NIST WebBook) cannot be fetched by the CI runner. All $T_g$-dependent steps are deferred; no placeholder or synthetic $T_g$ column is created. |
| **WLF constants (C₁, C₂)** | **None (open source not available)** | – | The ratified constitution's Principle VI names WLF constants as the validation metric; divergence from spec.md's FFV/Chain Stiffness requirement is flagged for kickback. |

*All URLs are taken directly from the verified-datasets block; no unverified sources are introduced.*

## Methodology Overview
1. **Data Ingestion** (`code/ingest.py`)  
   - Download SMILES parquet and physical-properties parquet via `datasets`.  
   - Compute SHA-256 checksums; store in `data/checksums.json`.  
   - Retry logic: up to 3 attempts, 30 s back-off.  

2. **Descriptor Engineering** (`code/descriptors.py`)  
   - Load SMILES with RDKit (CPU).  
   - Compute: elemental mass fractions, functional-group counts (via SMARTS), estimated molecular weight.  
   - Median impute missing numeric values; apply `StandardScaler`.  
   - Output `data/processed/feature_matrix.csv` (no $T_g$ column).  

3. **Physical Property Calculation** (`code/physical_properties.py`)  
   - Compute FFV and Chain Stiffness using Van Krevelen group contributions (documented in `docs/van_krevelen.md`).  
   - Save `data/physical_properties.csv` with checksum.  

4. **Conditional Model Training** (`code/train_ebm.py`)  
   - If `experimental_tg` exists in `feature_matrix.csv`, load it and perform 5-fold CV; grid-search λ ∈ {0.01,0.1,1.0} and interaction depth ∈ {1,2}.  
   - Select model with highest mean CV R²; serialize to `outputs/models/ebm_model.pkl` and write metadata.  
   - If the column is absent, **log a clear message that model-related stages are being skipped (graceful skip, not a fatal error)** and exit the training stage cleanly. This behavior is aligned across plan.md and quickstart.md.  

5. **Interpretability** (`code/interpret.py`) *(conditional)*  
   - Extract main effects and interaction terms via `interpret.globals.ebm`.  
   - Generate Partial Dependence Plots for all main effects; top-3 interaction surface plots.  
   - Save figures under `outputs/figures/`; each figure logs the input data checksum and generating script (SSoT).  

6. **Validation & Sensitivity** (`code/validate.py`) *(conditional)*  
   - **Primary validation (per spec.md FR-005/SC-002)**: correlate the top-3 feature importances with **FFV and Chain Stiffness** from `data/physical_properties.csv` (Pearson $r$). Apply Bonferroni correction (α = 0.05/3).  
   - **Sensitivity analysis** (deferred): perturb top-3 descriptors ±10 % and recompute predictions; report std-dev of Δ$T_g$.  
   - Summarize in `outputs/reports/validation_report.md`.  
   - The ratified constitution's Principle VI (WLF constants) cannot be executed (no open WLF dataset); this divergence is flagged for kickback.  

7. **Resource Guardrails** (`code/utils.py`)  
   - Prior to heavy steps, check file sizes; if > 7 GB, switch to streaming mode or randomly sample (seed = 42).  
   - GitHub Actions workflow enforces `timeout-minutes: 360` (6 h).  

## Expected Deliverables (when $T_g$ data available)
- **Feature matrix** (`data/processed/feature_matrix.csv`) – conforms to `contracts/feature_matrix.schema.yaml`.  
- **Physical properties** (`data/physical_properties.csv`).  
- **Trained EBM model** (`outputs/models/ebm_model.pkl`) – conforms to `contracts/model_output.schema.yaml`.  
- **Interpretability figures** (`outputs/figures/`).  
- **Validation report** (`outputs/reports/validation_report.md`).  

*When an open $T_g$ dataset becomes available, re-run the pipeline; no code changes are required.*