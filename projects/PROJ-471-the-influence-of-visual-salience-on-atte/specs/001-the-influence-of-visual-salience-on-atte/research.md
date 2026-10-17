# Research: The Influence of Visual Salience on Attentional Bias on Moral Judgements

## 1. Research Question & Hypotheses
- **Primary Question**: Does computational visual salience (derived from low‑level image properties) predict the allocation of visual attention (dwell time, first‑fixation probability, fixation latency) to morally relevant regions (faces, weapons) in moral‑judgment images?
- **Hypothesis**: Higher mean salience within an ROI will be associated with (a) longer dwell time, (b) higher first‑fixation probability, and (c) shorter fixation latency.  
- **Null**: No systematic relationship; attention driven primarily by top‑down processes.

## 2. Dataset Strategy
| Dataset | Role | Verified Source | Access |
|---|---|---|---|
| **OpenNeuro ds003123 (Moral Foundations Eye‑Tracking)** | Raw eye‑tracking logs + stimulus images | *Not in verified list* → **Manual prerequisite**: place the extracted dataset in `data/raw/ds003123/` before running the pipeline. | Manual placement; no automated download. |
| **GBVS (pySaliencyMap)** | Primary salience algorithm (CPU) | Open‑source pip package (no external URL required). | Auto‑installed via `requirements.txt`. |
| **DeepGaze II weights** | Optional GPU fallback for failed GBVS images | ` (verified) | Loaded with `datasets.load_dataset(...)` if CUDA present AND fallback needed. |
| **YOLOv8 face weights** | Face segmentation | ` (verified) | Auto‑downloaded by `ultralytics`. |
| **Detectron2 weapon weights** | Weapon segmentation | ` (verified) | Auto‑downloaded via `detectron2`. |

**Variable Fit Verification**  
- **Predictor**: Mean salience (GBVS or DeepGaze II fallback) within each ROI.  
- **Outcomes**: Dwell time (ms), first‑fixation probability (0‑1), fixation latency (ms).  
- **Covariates**: 
  - Low‑level visual: Luminance, contrast, edge density (computed from the same stimulus image).  
  - Semantic: Moral valence (extracted via VADER sentiment on image captions if available in ds003123, else coded as binary moral/neutral), scene complexity (number of detected objects via YOLOv8/Detectron2).  
- **ROIs**: Faces, weapons – generated via YOLOv8/Detectron2 masks.  

If `ds003123` is absent, the pipeline aborts with `DATA_MISSING_001`; no open substitute exists.

## 3. Methodological Rigor
### 3.1 Construct Validity & Operationalization

The study operationalizes "visual salience" as **low‑level computational salience** derived from pixel-wise image properties (contrast, color, edges) using GBVS or DeepGaze II. This operationalization captures the **perceptual salience** construct as specified in FR‑001, not semantic or emotional salience (e.g., moral valence of the scene, emotional intensity of a face).

**Scope & Limitations**:
- GBVS/DeepGaze II are designed to model human gaze allocation driven by low‑level visual features.
- They do NOT capture semantic salience (e.g., a weapon is "salient" because it is morally relevant, not because it has high contrast).
- If the true mechanism by which moral judgment drives attention is semantic (top‑down moral relevance) rather than perceptual (bottom‑up contrast/edges), a null result in this study would support the hypothesis that moral reasoning overrides low‑level perceptual capture (Principle VII: Bidirectional Result Interpretation).
- The study explicitly tests the perceptual pathway; semantic salience is addressed as a covariate (moral valence) to control for confounding.

### 3.2 Statistical Analysis Plan
1. **Model Specification** (using `statsmodels` MixedLM):  
   - **Model A (baseline)**: `dwell_time_ms ~ salience_score + luminance + contrast + edge_density + moral_valence + scene_complexity + (1|ParticipantID) + (1|StimulusID)`.  
   - **Model B (sensitivity)**: Same fixed effects, plus random slopes for `salience_score` per participant: `(salience_score|ParticipantID)`.  
   - **Orthogonalization**: If any predictor (luminance, contrast, edge_density) has VIF > 5, apply PCA to these three features to create orthogonal components and re-fit both models with the orthogonalized features. Report pre-orthogonalization and post-orthogonalization VIF values.
2. **Distribution Checks**: Shapiro‑Wilk test on residuals; if violated, log‑transform `dwell_time_ms` or switch to a Gamma GLMM (recorded in `diagnostics.log`).  
3. **Multiple Comparisons**: Benjamini‑Hochberg FDR correction applied to all fixed‑effect p‑values (FR‑006).  
4. **Power Analysis** (`SC‑003`):  
 - Simulate 500 datasets with n_participants=50, trials_per_participant=100 ([deferred] total trials), ICC ≈ 0.1 for both random effects, and effect size f = 0.15.
   - Use `pingouin.power_analysis` to estimate power at α = 0.05.  
   - Abort with `POWER_INSUFFICIENT` if estimated power < 0.8.  
   - **Conditional Statement**: This power analysis assumes the specified sample size. If the actual study collects fewer participants or trials, power will be lower.
5. **Sensitivity Analysis** (`FR‑005`):  
   - Compute `stability_metric = |β_A – β_B|` (absolute change in salience coefficient between Model A and Model B).  
   - Store both estimates and the metric in `results.json`.  
6. **Collinearity Diagnostics**: 
   - Compute VIF for `salience_score`, `luminance`, `contrast`, `edge_density`, `moral_valence`, `scene_complexity` before orthogonalization.  
   - If any VIF > 5 (indicating collinearity among the low‑level visual features), apply PCA to orthogonalize luminance, contrast, edge_density into uncorrelated components.  
   - Report both pre-orthogonalization and post-orthogonalization VIF in `diagnostics.log`.  
   - Use the orthogonalized features in the final model to ensure the salience_score coefficient is not confounded by correlated visual covariates.  
7. **Disclaimer Enforcement** (`FR‑007`): Every JSON result file includes `"disclaimer": "correlational only"` irrespective of significance.

### 3.3 Robustness & Edge Cases
| Edge Case | Handling |
|---|---|
| Missing fixation data for a trial | Exclude trial, set `excluded=True` in `aligned_data.csv`, log warning. |
| Empty or invalid ROI mask | Skip salience aggregation for that ROI, flag image in `mask_issues.log`. |
| GBVS failure on a high‑contrast image | Log as `fallback_needed=True`; if GPU available, attempt DeepGaze II on Kaggle; otherwise exclude image and log reason. |
| Low confidence (< 0.85) in YOLOv8/Detectron2 masks | Discard mask, flag for manual review; the trial remains in the dataset with `excluded=True` for that ROI. |
| Missing moral valence data (no captions in ds003123) | Use scene complexity alone; document limitation in `diagnostics.log`. |

## 4. Compute Feasibility
- **CPU‑first**: GBVS processes a single 1024×768 image in ≈ 0.8 s on 2 CPU cores; A substantial set of images spanning several hours, < 4 GB RAM.  
- **GPU Escape Hatch**: DeepGaze II runs only when `torch.cuda.is_available()` AND images marked fallback_needed exist. A small subset (≤ 20 images) is processed on the Kaggle free GPU (~16 GB VRAM, one kernel of several hours duration), staying well within the 9 h kernel limit.  
- **Resource Validator** (`resource_validator.py`) aborts if RAM > 7 GB or total CPU time > 6 h.  

## 5. Decision Rationale
- **GBVS** chosen for its CPU efficiency and open‑source availability, guaranteeing the pipeline fits the free‑tier compute budget.  
- **Manual dataset placement** respects the verified‑datasets rule; no automated download of a gated OpenNeuro collection is attempted.  
- **Simulation‑based power analysis** (500 reps, explicit sample-size parameters) provides a rigorous, verifiable justification for adequate power in a mixed‑effects context.  
- **Fallback to DeepGaze II** only on a genuine GPU (Kaggle) and only for images where GBVS fails avoids fabricating a CPU approximation of a GPU‑only model.  
- **PCA orthogonalization** of visual covariates ensures the salience coefficient is not confounded by collinear low‑level features, improving the interpretability of the main effect.  
- **Semantic covariates** (moral valence, scene complexity) control for confounds that could plausibly explain attention allocation independent of low‑level salience.
