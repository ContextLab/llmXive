# Research: The Influence of Visual Salience on Attentional Bias in Moral Judgements

## 1. Research Question & Hypotheses

- **Primary Question**: Does computational low-level visual salience predict attentional allocation (dwell time, first-fixation probability, fixation latency) to morally relevant regions (faces, weapons) in moral-judgment stimuli?
- **Hypothesis**: Higher mean ROI salience ↔ (a) longer dwell time, (b) higher first-fixation probability, (c) shorter fixation latency.
- **Null**: no systematic relationship — attention driven by top-down moral-relevance processes. Both outcomes are interpreted with equal rigor (Constitution Principle VII).

## 2. Dataset Strategy

| Dataset / Resource | Role | Verified Source | Access |
|---|---|---|---|
| OpenNeuro ds003123 "Moral Foundations Eye-Tracking" | Raw eye-tracking logs + stimulus images | **No verified source.** None of the URLs in the verified-datasets block corresponds to this dataset (the listed OpenNeuro parquet is fMRI derivative data; the DeepGaze parquet is an unrelated image collection). No URL is fabricated. | **Manual placement** into `data/raw/ds003123/` before running; `verify_data.py` enforces structure and aborts with `DATA_MISSING_001` otherwise. No open substitute supporting the same question was identified. |
| OpenCV `cv2.saliency` (spectral residual) | Salience computation | Ships inside `opencv-contrib-python` (pip) | Auto-installed; no download at runtime |
| YOLOv8 (ultralytics) | Face + weapon ROI detection | Standard ultralytics weight release channel (auto-download by the library) | Auto-installed |

**Variable fit verification**: predictor = mean salience within ROI (image stream); outcomes = dwell time, first-fixation probability, fixation latency (gaze stream); covariates = luminance, contrast, edge density (image stream) + scene complexity (object count). This fit is **conditional on ds003123 containing the stimulus images and per-trial fixation logs**; `verify_data.py` checks this before any analysis and the pipeline refuses to run otherwise (no synthetic stand-in, per the fabrication gate).

## 3. Methodological Rigor

### 3.1 Construct validity
Salience is operationalized as **low-level perceptual salience** (spectral-residual / center-surround statistics), not semantic salience. A null result is therefore informative: it would indicate attention is driven by top-down moral relevance rather than bottom-up feature capture. Semantic confounds are controlled via scene complexity (and moral valence if captions exist in the dataset; otherwise the limitation is logged).

### 3.2 Statistical analysis plan
1. **Models** (`statsmodels MixedLM`):
   - Model A: `dwell_time_ms ~ salience_score + luminance + contrast + edge_density + scene_complexity + (1|ParticipantID) + (1|StimulusID)`
   - Model B: Model A + random slope for `salience_score` by participant.
2. **Multiple comparisons**: Benjamini-Hochberg FDR across all fixed-effect p-values (FR-006).
3. **Power**: simulation-based (500 reps; f=0.15, ICC≈0.1, α=0.05, N taken from the actual aligned dataset). Power < 0.8 ⇒ `power_status: "invalid"` (SC-003); limitation acknowledged explicitly.
4. **Sensitivity**: `stability_metric = |β_A − β_B|` reported (FR-005, SC-004).
5. **Collinearity**: VIF for all predictors; PCA orthogonalization of {luminance, contrast, edge_density} if any VIF > 5; pre/post VIF reported (SC-006). No claim of independent effects among definitionally related low-level features without this check.
6. **Distribution checks**: residual diagnostics; log-transform of dwell time (or Gamma GLMM) if violated, recorded in `logs/diagnostics.log`.
7. **Causal framing**: observational design — all results reported as **associations**; `"correlational only"` disclaimer enforced on every p-value-bearing artifact (FR-007).

### 3.3 Edge cases (spec-mandated)
| Edge case | Handling |
|---|---|
| Missing fixation data for a trial | exclude (`excluded=True`), log warning |
| Empty/invalid ROI mask | skip salience aggregation for that ROI, flag image in `mask_issues.log` |
| Salience failure on an image | center-surround fallback; if that also fails, exclude image with reason in metadata (pipeline never crashes) |
| Low-confidence detection (<0.85) | discard mask, flag for review; trial kept with ROI excluded |
| YOLOv8/weights unavailable at runtime | graceful degradation: ROIs marked `undetected`, images flagged; no crash (fixes T004) |

## 4. Compute Feasibility

- **All CPU, no GPU steps.** Spectral-residual saliency: ~0.1 s per image on 2 cores, <1 GB RAM — two orders of magnitude inside the 7 GB / 6 h budget (SC-002). YOLOv8 CPU inference on ~200 images: minutes. MixedLM on ~10k trials: minutes.
- **v1 removals and why**: DeepGaze II required GPU weights and produced unverifiable CPU failures (T003); GBVS/pySaliencyMap also failed. OpenCV spectral residual is a standard, published, deterministic CPU saliency method (Hou & Zhang, 2007) with no downloads. Detectron2 could not be imported on the runner (T004); YOLOv8 alone now covers both ROI classes.
- `resource_validator.py` records peak RAM and CPU time against the free-tier limits.

## 5. Decision Rationale

- **OpenCV spectral residual** chosen as primary salience method: faithful, deterministic, CPU-only, zero external dependencies — guarantees T003-class failures cannot recur. Center-surround fallback covers the spec's "simpler heuristic salience calculation" edge case.
- **YOLOv8 for both faces and weapons**: single pip-installable library; lazy import + graceful degradation makes the module testable even when weights are unavailable.
- **Manual dataset placement with strict verification**: ds003123 has no verified open download; the pipeline never fabricates or substitutes data — it aborts loudly with `DATA_MISSING_001` and empty-checksum guard (fixes T002).
- **Bootstrap with explicit `--root`**: removes the fragile monkeypatching that failed T001.
- **Simulation-based power with realized N** and **VIF/PCA collinearity handling** satisfy SC-003 and SC-006 rigor requirements.
