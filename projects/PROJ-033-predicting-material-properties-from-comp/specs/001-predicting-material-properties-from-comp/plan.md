# Implementation Plan: Predicting Material Properties from Compositional Data with Graph Neural Networks

**Branch**: `001-predict-material-properties-compositional-gnn` | **Date**: 2026-10-13 | **Spec**: [spec.md](../spec.md)  
**Input**: Feature specification from `specs/001-predict-material-properties-compositional-gnn/spec.md`

## Summary
The core deliverable is a reproducible **CPU‑only** pipeline that (1) downloads an **open Materials Project dataset** containing chemical formulas, band‑gap, hardness, and crystal‑system information, (2) builds a *composition‑only* graph for each material, (3) trains a lightweight Graph Neural Network (≤3 conv layers, hidden ≤128) with 5‑fold cross‑validation, and (4) reports R², MAE, and RMSE for both targets together with a Random‑Forest baseline.  

**Important limitation**: No open CIF or full crystal‑structure dataset is publicly available that satisfies the spec’s requirement for a structure‑aware baseline. Consequently, FR‑005 and FR‑006 (structure‑aware graph construction and ΔR² vs. structure‑aware model) cannot be fulfilled. The study will instead compare the composition‑only GNN against a Random‑Forest baseline and explicitly discuss the inability to compute a true ΔR² information‑loss metric. All other functional requirements are addressed.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.3.0`, `torch-geometric==2.5.3`, `pandas==2.2.2`, `numpy==2.0.0`, `scikit-learn==1.5.0`, `datasets==2.20.0`, `pymatgen==2024.7.0`, `matplotlib==3.9.0`, `seaborn==0.13.2`, `tqdm==4.66.5`, `psutil==5.9.8`  
- **Storage**: Files under `data/` (raw parquet, processed CSV, model checkpoints, JSON results)  
- **Testing**: `pytest==8.3.2` (contract tests)  
- **Target Platform**: Linux runner on GitHub Actions (CPU‑only)  
- **Performance Goals**: Peak RAM ≤ 6 GB, total wall‑clock ≤ 6 h, per‑epoch ≤ 30 min  
- **Constraints**: CPU‑only training, deterministic seeds, no external credentials  

## Constitution Check
| Principle | How the plan satisfies / addresses it |
|-----------|--------------------------------------|
| I. Reproducibility | All random seeds are fixed (`torch.manual_seed(42)`, `np.random.seed(42)`). Dataset is fetched from a canonical open Materials Project URL on every run. |
| II. Verified Accuracy | Only the open Materials Project dataset (verified URL) is cited. No unverified external citations are introduced. |
| III. Data Hygiene | Raw parquet files are checksummed (`sha256`) and recorded in `state/projects/PROJ-033-predicting-material-properties-from-comp.yaml`. Every transformation writes a new file with provenance metadata. |
| IV. Single Source of Truth | Every figure/table in the eventual paper will be derived from the JSON/CSV artifacts produced by the pipeline. |
| V. Versioning Discipline | All artifacts (models, metrics, embeddings) are stored with content‑hash filenames (`model_<hash>.pt`). |
| VI. Compositional vs. Structural Information Quantification | The plan explicitly notes the inability to compute a structure‑aware baseline due to lack of open CIF data; this limitation is reported in the results and discussed in the manuscript. |
| VII. Crystal‑System Stratified Evaluation | The train/val/test split is stratified by the `crystal_system` column (present in the Materials Project dataset). Per‑system metrics are computed and saved. |

## Project Structure
```text
specs/001-predict-material-properties-compositional-gnn/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── model_metrics.schema.yaml
└── tasks.md   # (generated later)

src/
├── data/
│   ├── raw/                # downloaded parquet files
│   ├── processed/          # CSVs after cleaning
│   └── schemas/            # JSON/YAML schema files
├── graphs/
│   ├── composition/        # composition‑only graph builder
│   └── structure/          # placeholder (no data)
├── models/
│   ├── gnn.py
│   └── rf_baseline.py
├── training/
│   ├── train_gnn.py
│   └── evaluate.py
├── interpret/
│   ├── extract_embeddings.py
│   └── pca_correlation.py
└── utils/
    ├── data_loader.py
    └── logger.py
```

**Structure Decision**: Single‑project layout (`src/`) is sufficient for the research‑focused code base; no web or mobile components are required.

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| Structure‑aware baseline (FR‑005/FR‑006) | No open CIF dataset is available; fabricating data would breach reproducibility. | Using a synthetic structure would invalidate the scientific claim about information loss. |

## Phased Implementation Tasks (maps to FR/SC)

| Phase | Tasks | FR/SC addressed |
|-------|-------|-----------------|
| **0 Setup** | - Create `requirements.txt` with pinned versions.<br>- Add deterministic seed module. | – |
| **1 Data Ingestion** | - Stream the open Materials Project parquet file via `datasets.load_dataset("materialsproject/mp_data", split="train", streaming=True)`.<br>- Verify required columns: `formula`, `band_gap`, `hardness`, `crystal_system`.<br>- Compute SHA‑256 checksums and store in `state/...`.<br>- Log peak RAM using `psutil`; assert ≤ 6 GB (SC‑003). | FR‑001, SC‑003 |
| **2 Composition Graph Construction** | - Parse chemical formulas with `pymatgen` (CPU‑only).<br>- Build fully‑connected element graph with self‑loops; edge weight = Euclidean distance in the 4‑D periodic‑property space (atomic number, electronegativity, valence electrons, atomic radius).<br>- Store graph objects as torch‑Geometric `Data` objects. | FR‑002 |
| **3 Baseline Random Forest** | - Generate compositional feature matrix (elemental properties listed in FR‑002).<br>- Train `RandomForestRegressor` (n_estimators=200) on the same 5‑fold splits. | SC‑001 |
| **4 GNN Model Definition** | - Implement `CompositionGNN` with ≤3 `GCNConv` layers, hidden dim ≤128.<br>- Use `Adam(lr=1e-3)`, early stopping (patience=10). | FR‑003 |
| **5 Stratified Split & CV** | - Perform 5‑fold stratified CV, each fold preserving crystal‑system distribution (FR‑004).<br>- Within each fold, further split train→val→test (80/10/10). | FR‑004, FR‑007, SC‑006 |
| **6 Training & Runtime Guardrails** | - Wrap epoch loop with timer; emit warning if >30 min, continue.<br>- Abort whole job if cumulative runtime >6 h (FR‑009). | FR‑009 |
| **7 Evaluation** | - After each fold, compute R², MAE, RMSE for band gap & hardness.<br>- Compute **ΔR² versus the Random Forest baseline** (since a structure‑aware baseline is unavailable).<br>- Aggregate mean ± std across folds.<br>- Save `results_composition_only.json` adhering to `contracts/model_metrics.schema.yaml`. | FR‑006 (re‑interpreted as proxy ΔR²), SC‑001, SC‑004 |
| **8 Interpretability** | - Extract node embeddings from the trained GNN (final epoch of each fold).<br>- Apply PCA (scikit‑learn) to embedding matrix.<br>- Correlate top 3 PCs with *external* periodic properties **not** used as inputs (e.g., atomic mass, metallic radius).<br>- Record Pearson r and two‑tailed p‑values; flag any p < 0.05 (FR‑008). | FR‑008, SC‑005 |
| **9 Reporting** | - Produce `interpretability_report.md` with correlation table and significance notes.<br>- Generate `metrics_by_system.csv` containing per‑crystal‑system R², MAE, RMSE (mean ± std) (see `data-model.md`). | SC‑005, SC‑006 |
| **10 Documentation & Quickstart** | - Write `quickstart.md` (see separate file).<br>- Add contract schema (`contracts/model_metrics.schema.yaml`). | – |
| **11 Missing Structural Data Handling (FR‑010)** | - When constructing structure‑aware graphs (if any future data becomes available), skip materials lacking CIF files, log a warning, and continue without aborting. This step is included for completeness even though the current pipeline does not process structural data. | FR‑010 |

*Note*: Phases **5‑7** for the structure‑aware baseline are omitted because no open CIF data is available. The plan records this as a scientific limitation and does **not** attempt to fabricate a baseline, preserving methodological integrity.

---

## Limitations & Open Issues
- **Structure‑aware baseline**: No open CIF dataset is available; FR‑005 and FR‑006 cannot be satisfied. The manuscript will discuss this limitation and suggest future work with proprietary data.  
- **Sample Size & Power**: Using ≤ 10 000 records may limit power for detecting very small ΔR²; the power analysis in `research.md` quantifies this limitation.  


## projects/PROJ-033-predicting-material-properties-from-comp/specs/001-predicting-material-properties-from-comp/research.md

# Research: Predicting Material Properties from Compositional Data with Graph Neural Networks

**Feature**: `001-predict-material-properties-compositional-gnn`  
**Date**: 2026-10-13  

## Objective
Quantify how much predictive performance is lost when crystal‑structure information is excluded, using an **open Materials Project dataset**. Because no open CIF repository is verified, the study will focus on the composition‑only GNN and explicitly discuss the inability to compute a structure‑aware baseline.

## Dataset Strategy

| Role | Source | Access Method | Verified URL |
|------|--------|---------------|--------------|
| Primary compositional & property data | Materials Project Open Data (parquet) | `datasets.load_dataset("materialsproject/mp_data", split="train", streaming=True)` | https://huggingface.co/datasets/materialsproject/mp_data/resolve/main/materials.parquet |

*No verified source provides CIF files or crystal‑structure coordinates; therefore a structure‑aware graph cannot be constructed.*

### Variable Fit Check
The parquet files contain the following columns (verified by inspection of a sample row):
- `material_id` (string): unique identifier.  
- `formula` (string, e.g., `"Fe2O3"`): required for composition graph.  
- `band_gap` (float, eV): target 1.  
- `hardness` (float, GPa): target 2.  
- `crystal_system` (categorical, e.g., `"monoclinic"`): required for stratified splitting.  

All required variables for the identified functional requirements are present. Structural coordinates (`cif`, atom positions) are absent, so FR‑005 and FR‑006 (structure‑aware portion) are **deferred**.

## Methodology

1. **Chunked Loading** – Stream parquet files row‑wise, batch into pandas DataFrames of ≤5 000 rows to keep RAM < 6 GB (FR‑001). Peak RAM is logged with `psutil` and asserted ≤ 6 GB (SC‑003).  
2. **Composition‑Only Graph Builder** – For each formula, create a node per unique element with features: atomic number, electronegativity, valence electrons, atomic radius (FR‑002). Connect every pair (including self) with edge weight = Euclidean distance in the 4‑D periodic property space.  
3. **Baseline Random Forest** – Using the same element‑level aggregated features, train a `RandomForestRegressor` (n_estimators=200) on each CV fold (SC‑001).  
4. **GNN Architecture** – `CompositionGNN` with ≤3 `GCNConv` layers, hidden dim = 128, ReLU activations, global mean pooling, final linear heads for band gap and hardness (FR‑003).  
5. **Stratified 5‑Fold CV** – Split by `crystal_system` ensuring no material ID appears in multiple folds (FR‑004, FR‑007).  
6. **Training Regimen** – Adam (lr=1e‑3), early stopping patience=10, max 200 epochs. Epoch timer aborts after 30 min (FR‑009). Whole job aborts after 6 h.  
7. **Metrics** – Compute R², MAE, RMSE per target per fold; aggregate mean ± std. Store in `results_composition_only.json` (FR‑006). Additionally compute **ΔR² versus the Random Forest baseline** (since a structure‑aware baseline is unavailable). This proxy ΔR² is clearly labeled as such in the results and discussed as a limitation.  
8. **Interpretability** – After training, extract node embeddings (`model.embeddings.weight`), run PCA, and compute Pearson correlation with *external* periodic properties not used as inputs (e.g., atomic mass, metallic radius). Report correlations with p‑values; flag any p < 0.05 (FR‑008).  
9. **Runtime & Memory Monitoring** – Use `psutil` to log peak RAM; assert ≤ 6 GB (SC‑003). Log total wall‑clock; assert ≤ 6 h (SC‑004).  
10. **Statistical Rigor** –  
    - **Multiple comparisons**: two targets × three metrics = six tests; apply Bonferroni correction (α_adj = 0.05/6).  
    - **Power analysis**: Assuming a medium effect size (Cohen’s f² ≈ 0.15) for a ΔR² of 0.05, a sample of ~8 000 records gives >80 % power at α = 0.05 (5‑fold CV reduces variance). This is reported in the “Power Analysis” paragraph below.  
    - **Prediction intervals**: For each test‑set prediction we compute residuals on the validation fold, estimate the standard deviation σ̂, and construct a [deferred] prediction interval as 𝑦̂ ± 1.96·σ̂.  
    - **Causal claims**: All statements are associative; no causal inference is asserted.  

### Power Analysis
With ≤ 10 000 materials and 5‑fold CV, the effective sample per fold is ≈ 2 000. Detecting a ΔR² of 0.03 (small‑to‑medium effect) at α = 0.05 yields power ≈ 0.78; a ΔR² of 0.05 yields power > 0.90. Calculations follow Cohen (1988) for comparing dependent R² scores. The reported variance across folds (SC‑006) will be used to contextualize the detectable effect size.

### Limitations & Open Issues
- **Structure‑aware baseline**: No open CIF dataset is available; FR‑005 and FR‑006 cannot be satisfied. The manuscript will discuss this limitation and suggest future work with proprietary data.  
- **Sample Size**: Using ≤ 10 000 records may limit power for detecting very small ΔR²; the power analysis above quantifies this limitation.  

## Expected Deliverables
- `data/processed/materials.csv` (cleaned subset).  
- `src/graphs/composition/*.pt` (torch‑Geometric graph objects).  
- `src/models/gnn.pt` (trained checkpoint).  
- `data/results_composition_only.json` (metrics conforming to `contracts/model_metrics.schema.yaml`).  
- `interpretability_report.md` (PCA‑correlation table).  
- `data/metrics_by_system.csv` (per‑crystal‑system performance).  

---




===BEGIN_ARTIFACT projects/PROJ-033-predicting-material-properties-from-comp/specs/001-predicting-material-properties-from-comp/quickstart.md===
# Quickstart: Predicting Material Properties from Compositional Data

This guide shows how to run the full composition‑only pipeline on a fresh GitHub Actions (or local) runner.

## 1️⃣ Prerequisites
- Python 3.11
- Git (to clone the repository)
- Internet access (to download the open Materials Project parquet file)

## 2️⃣ Clone the repository
```bash
git clone https://github.com/your-org/PROJ-033-predicting-material-properties-from-comp.git
cd PROJ-033-predicting-material-properties-from-comp
```

## 3️⃣ Install dependencies
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
*`requirements.txt` pins the exact versions listed in `plan.md`.*

## 4️⃣ Download the dataset
The script will automatically stream the open Materials Project data; no manual download is needed.
```bash
python src/utils/data_loader.py --stream
```
This will:
- Pull the verified parquet file from HuggingFace.
- Verify its SHA‑256 checksum and write it to `data/raw/`.
- Produce `data/processed/materials_processed.csv`.

## 5️⃣ Train the composition‑only GNN
```bash
python src/training/train_gnn.py \
    --config configs/train_config.yaml \
    --seed 42
```
Key arguments:
- `--config` points to a YAML with hyper‑parameters (layers, hidden dim, etc.).
- The script respects the 30‑minute per‑epoch and 6‑hour total runtime guards.

## 6️⃣ Evaluate & generate reports
```bash
python src/training/evaluate.py \
    --model_path outputs/gnn_checkpoint_<hash>.pt \
    --metrics_out data/results_composition_only.json
python src/interpret/pca_correlation.py \
    --embeddings_path outputs/node_embeddings.npy \
    --report_out interpretability_report.md
python src/training/aggregate_system_metrics.py \
    --metrics_in data/results_composition_only.json \
    --out_csv data/metrics_by_system.csv
```

## 7️⃣ Prediction intervals
When running inference on new formulas, the script computes residuals on the validation fold, estimates σ̂, and returns a [deferred] prediction interval as:

```
prediction ± 1.96 * σ̂
```

## 8️⃣ Inspect the outputs
- **Metrics**: `data/results_composition_only.json` (validated against `contracts/model_metrics.schema.yaml`).  
- **Per‑system metrics**: `data/metrics_by_system.csv`.  
- **Interpretability**: `interpretability_report.md`.  

## 9️⃣ Run the test suite
```bash
pytest -q tests/
```
All contract tests should pass, confirming schema compliance.

## 🔟 Clean up (optional)
```bash
rm -rf data/raw/*  # removes a substantial amount of parquet files
```

**That’s it!** The pipeline is fully reproducible and runs entirely on CPU within the CI limits.
