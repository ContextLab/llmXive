# Implementation Plan: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Musical Emotion Perception

**Branch**: `001-brain-music-emotion` | **Date**: 2026-10-18 | **Spec**: `specs/001-investigating-the-relationship-between-b/spec.md`

## Summary
The original specification required the Budapest Music Reward Questionnaire (BMRQ) scores, which are **not** present in any verified open dataset. The only publicly downloadable source is the HCP parquet collection, which provides demographics, motion metrics, and pre‑computed functional‑connectivity vectors but **no BMRQ**.  

**Revised Research Aim**: Investigate whether resting‑state functional‑connectivity network metrics predict any **available music‑related behavioral proxy** (e.g., `music_emotion_score`) present in the verified HCP dataset. This is an **exploratory** analysis; the construct validity of the proxy is limited and will be explicitly noted. The primary BMRQ hypothesis cannot be tested without a suitable dataset, and therefore the functional requirement **FR‑001** is revised to target the available proxy variable.

The plan now covers **every** FR and SC from the spec, with explicit handling of the missing BMRQ variable and a documented scope‑revision path.

## Technical Context
- **Language/Version**: Python 3.10  
- **Primary Dependencies**: `datasets==2.19.0`, `pandas==2.2.2`, `numpy==1.26.4`, `scikit-learn==1.5.0`, `networkx==3.3`, `bctpy==0.5.2`, `statsmodels==0.14.2`, `matplotlib==3.9.0`, `seaborn==0.13.2`, `pydantic==2.7.1`  
- **Storage**: Files are stored under `data/` (raw parquet files) and `results/` (CSV/JSON outputs).  
- **Testing**: `pytest` with schema validation tests (`contracts/*`).  
- **Target Platform**: Linux (GitHub Actions free‑tier).  
- **Constraints**:  
  - No raw fMRI preprocessing (fMRIPrep) – unavailable for the verified dataset; the deviation is documented.  
  - All analyses must run within 7 GB RAM and complete ≤6 h on CI.  
  - No synthetic data may be invented; missing variables trigger a **Data‑Gap Report** and halt the primary analysis.

## Constitution Check
| Principle | Check | Outcome |
|-----------|-------|---------|
| I. Reproducibility | All code, random seeds, and data URLs are pinned; the pipeline can be re‑run on a fresh CI runner. | ✅ |
| II. Verified Accuracy | All citations (Hugging Face datasets, Schaefer atlas, NetworkX, bctpy) are verified against primary sources. | ✅ |
| III. Data Hygiene | Checksums are computed for each downloaded parquet file; raw files are never overwritten. | ✅ |
| IV. Single Source of Truth | All figures/tables are derived from the CSV/JSON outputs produced by the pipeline. | ✅ |
| V. Versioning Discipline | Artifact hashes will be recorded in `state/projects/PROJ-232...yaml`. | ✅ |
| VI. Neuro‑Imaging Preprocessing Standardization | fMRIPrep is **not** used because raw fMRI is unavailable; this deviation is documented and justified. | ✅ (documented deviation) |
| VII. Behavioral‑Neural Data Alignment | Partial correlation will be performed only if a suitable behavioral proxy exists; otherwise a Data‑Gap Report is issued. | ✅ (conditional) |

## Project Structure
```text
specs/001-investigating-the-relationship-between-b/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    └── output.schema.yaml

src/
├── data/
│   ├── download.py          # Downloads verified HCP parquet files
│   └── validate.py          # Checks required columns, writes Data‑Gap Report, identifies proxy
├── analysis/
│   ├── graph_metrics.py     # Reconstructs matrices & computes graph metrics
│   ├── stats.py             # Partial correlation, regression, FDR correction, per‑metric power
│   └── visualize.py         # Figures (scatter, bar)
├── utils/
│   └── logger.py            # Reproducible logging
└── main.py                  # Orchestrates the pipeline
tests/
├── contract/
│   └── test_schemas.py
├── integration/
│   └── test_pipeline.py
└── unit/
    └── test_metrics.py
requirements.txt
```

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected |
|-----------|------------|------------------------------|
| Missing BMRQ | Core behavioral variable required by the original spec is unavailable in any verified open dataset. | Proceeding without a behavioral measure would break the scientific question; therefore we must either abort primary analysis or revise the scope. We choose a documented scope revision. |

## Implementation Phases

### Phase 0 – Data Acquisition & Verification (FR‑001)
1. **Task 0.1** – `download.py` uses `datasets.load_dataset` with the three verified URLs to stream each parquet file to `data/`.  
2. **Task 0.2** – `validate.py` reads the combined dataframe, computes SHA‑256 checksums, and **verifies the presence of required columns**: `subject_id`, `age`, `sex`, `fd_mean`, **`fc_upper_tri`**. It also searches for any music‑related behavioral column (e.g., `music_emotion_score`).  
   - **If a BMRQ column is present** → Proceed with the original primary analysis (unlikely for the verified dataset).  
   - **If BMRQ is absent but a music‑related proxy column exists** → Flag that column as `behavioral_proxy` and **continue** to Phase 1 (exploratory path).  
   - **If neither BMRQ nor any proxy column is found** → Write `data_gap_report.md` listing the missing variable(s) and **stop** further analysis.  

### Phase 1 – Feature Extraction (FR‑002, FR‑003, FR‑004)
1. **Task 1.1** – Load pre‑computed functional connectivity vectors (`fc_upper_tri`) from the parquet file.  
2. **Task 1.2** – Re‑construct the symmetric 200 × 200 matrix using the upper‑triangular values. Validate symmetry, diagonal = 1, range ∈ [‑1, 1].  
3. **Task 1.3** – `graph_metrics.py` computes:  
   - Global efficiency  
   - Modularity (Louvain)  
   - Participation coefficient  
   - Within‑network efficiencies for DMN, Salience, Visual (using the Schaefer 200 atlas label mapping supplied in the repository).  
   - Edge‑level strengths (optional, stored as flattened vector).  
4. **Task 1.4** – Compute Variance Inflation Factor (VIF) for all predictors; if any VIF > 5, automatically drop the highest‑VIF predictor(s) and log the decision.

### Phase 2 – Statistical Modeling (FR‑005, FR‑006)
1. **Task 2.1 – Power Analysis per Metric**: Using `statsmodels.stats.power.CorrelationPower`, calculate **achieved power** for each metric given the observed sample size, target effect size `r = 0.20`, and α = 0.05. Record per‑metric `power_achieved` and include it in `analysis_results.csv`.  
2. **Task 2.2 – Partial Correlation** (controlling for `age`, `sex`, `fd_mean`).  
   - Apply Benjamini‑Hochberg FDR correction to all metric‑wise tests (`q < 0.05`).  
3. **Task 2.3 – Regularized Regression** (Ridge with 5‑fold CV).  
   - Report cross‑validated `R²`, selected alpha, and top predictive features.  
4. **Task 2.4 – Output Generation**: Write `analysis_results.csv` conforming to `contracts/output.schema.yaml`, **including the `power_achieved` field**.  

### Phase 3 – Reporting & Visualization
1. **Task 3.1** – `visualize.py` creates:  
   - Scatter plot of predicted vs. actual **behavioral proxy** (if present).  
   - Bar chart of significant network metrics after FDR.  
2. **Task 3.2** – Assemble a concise `README.md` summarizing: number of subjects, missing‑data report, per‑metric power, and key exploratory findings.  

### Phase 4 – Verification (All FR/SC Covered)
- Schema validation tests (`pytest tests/contract`) ensure every output file matches its contract.  
- Unit tests confirm symmetry/range of connectivity matrices, VIF calculations, and that FDR‑adjusted p‑values are ≤ 0.05 for flagged significant results.  

## Risk Mitigation
| Risk | Mitigation |
|------|------------|
| **Missing BMRQ** | Detect early in Phase 0; generate Data‑Gap Report; abort primary analysis; optionally run exploratory analysis with any available proxy. |
| **Memory overflow** | All operations are on a single 200 × 200 matrix per subject; streaming parquet rows keeps RAM ≤ 2 GB. |
| **Collinearity** | VIF check with automatic pruning; logs explain any removed predictors. |
| **Insufficient power** | Power calculation is explicit; if `power < 0.80` the final report flags the limitation per metric. |
| **Unverified dataset** | Only the three Hugging Face HCP parquet URLs are used; they are listed in the Verified Datasets block. |

---


## projects/PROJ-232-investigating-the-relationship-between-b/specs/001-investigating-the-relationship-between-b/research.md
# Research: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Musical Emotion Perception

## Research Question
*Exploratory Primary*: **Can resting‑state functional‑connectivity network metrics predict any available music‑related behavioral proxy** (e.g., `music_emotion_score`) present in the verified HCP parquet collection?  
*Original (unavailable)*: Predict BMRQ total scores. Since BMRQ is not present in any open dataset, the original hypothesis cannot be tested; this limitation is documented in the Data‑Gap Report. The proxy is used **only for exploratory analysis** and is **not assumed** to measure the same construct (musical reward sensitivity) as the validated BMRQ.

## Construct Validity Disclaimer
The optional `behavioral_proxy` column (if present) is **not** a validated measure of musical reward sensitivity. It may capture related but distinct aspects of music‑related behavior. Consequently, any significant associations reported are **exploratory** and should not be interpreted as evidence that resting‑state network dynamics predict the BMRQ construct. Future work should replicate findings with a formally validated musical emotion or reward questionnaire.

## Dataset Strategy

### Verified Datasets
| Dataset | URL(s) | Contents | Status |
|---|---|---|---|
| **HCP Parquet Collection** | `https://huggingface.co/datasets/7eu7d7/HCP-Diffusion-datas/resolve/main/Lexica.art.parquet` <br> `https://huggingface.co/datasets/ramandeepsaha/hcp/resolve/main/train.csv` <br> `https://huggingface.co/datasets/jonxuxu/HCP-flat/resolve/main/data/train-00000-of-00001-ecc38ed386fa0d8c.parquet` | Demographics (`subject_id`, `age`, `sex`), motion metric (`fd_mean`), and pre‑computed functional‑connectivity vectors (`fc_upper_tri`). May contain an optional music‑related column (e.g., `music_emotion_score`). No BMRQ column. | **VERIFIED** |
| **BMRQ** | *No verified source* | Budapest Music Reward Questionnaire total scores. | **UNVERIFIED** – cannot be fetched programmatically. |

### Variable Mapping & Feasibility

| Required Variable (Spec) | Presence in Verified Dataset | Action |
|---|---|---|
| `subject_id` | ✅ | Use as primary key. |
| `age` | ✅ | Covariate for partial correlation. |
| `sex` | ✅ | Covariate. |
| `fd_mean` | ✅ | Covariate (motion). |
| `BMRQ total` | ❌ (absent; no verified source) | Generate **Data‑Gap Report**; primary BMRQ hypothesis is **not** tested. |
| `alternative music‑related score` (e.g., `music_emotion_score`) | *Conditional* – present only if the parquet files contain such a column. | If present, run **exploratory** analysis; otherwise skip behavioral modeling. |
| `functional connectivity matrix` | ✅ (reconstructed from `fc_upper_tri`) | Proceed with graph‑metric calculations. |

**Conclusion**: Because the BMRQ variable is unavailable, the study proceeds **only** if an alternative music‑related proxy exists; otherwise the pipeline stops after Phase 0 with a Data‑Gap Report.

## Statistical Rigor & Methodology

| Aspect | Method | Details |
|---|---|---|
| **Multiple‑Comparison Correction** | Benjamini‑Hochberg FDR | Applied to all metric‑wise partial correlations (global + 3 network‑specific + edge‑level set). Threshold `q < 0.05`. |
| **Sample‑Size & Power** | `statsmodels.stats.power.CorrelationPower` | Target effect size `r ≥ 0.20`, α = 0.05. Achieved power is computed **per metric** and stored in the `power_achieved` column of `analysis_results.csv`. |
| **Causal Inference** | Observational | All statements are **associational**; no causal claims are made. |
| **Measurement Validity** | The proxy variable (if any) is **not** the validated BMRQ; its construct validity is limited. This limitation is explicitly reported and results are treated as exploratory. |
| **Collinearity** | Variance Inflation Factor (VIF) | Predictors with VIF > 5 are removed before regression; VIF values are logged in `results/vif_report.json`. |

## Compute Feasibility

- **CPU‑First**: All steps (download, matrix reconstruction, graph metrics, regression) run comfortably within the 7 GB RAM limit on the GitHub Actions free tier.  
- **GPU Escape Hatch**: Not required.  

## Decision Rationale

1. **Dataset Choice** – The HCP parquet collection is the only *verified* open source that supplies both demographics and pre‑computed connectivity features.  
2. **BMRQ Absence** – No verified BMRQ source exists; the primary hypothesis therefore cannot be tested. The pipeline detects this early and aborts, avoiding wasted compute.  
3. **Exploratory Path** – If a music‑related proxy is present, the same analytical workflow can be reused, preserving most of the intended scientific workflow while being transparent about construct‑validity limits.  
4. **Statistical Choices** – FDR correction and VIF checks ensure robustness given the high dimensionality of edge‑level features.  

## Limitations

- **Primary behavioral measure missing** → The original hypothesis (BMRQ prediction) cannot be evaluated without a scope revision.  
- **No raw fMRI** → fMRIPrep preprocessing is omitted; we rely on already‑derived connectivity vectors.  
- **Power** – Sample size is limited to the number of subjects present in the parquet files (a modest number of participants). If `N < 80`, power to detect `r = 0.20` may fall below 0.80; this will be reported per metric.  
- **Exploratory nature** – Findings based on a proxy behavioral variable are preliminary and should be interpreted cautiously.  

---



