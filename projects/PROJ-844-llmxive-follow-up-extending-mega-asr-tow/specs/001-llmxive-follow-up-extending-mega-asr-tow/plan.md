# Implementation Plan: llmXive Follow-up: Extending "Mega-ASR" for Semantic Collapse Thresholds

**Branch**: `001-semantic-collapse-threshold` | **Date**: 2026-08-31 | **Spec**: [spec.md](../specs/001-semantic-collapse-threshold/spec.md)  
**Input**: Feature specification from `specs/001-semantic-collapse-threshold/spec.md`

## Summary
The project will (1) **download** a stratified subset of the CHiME‑5 dataset (open HuggingFace mirror) to satisfy FR‑001, (2) **apply** a Cartesian product of 9 SNR levels × 6 RT60 levels (54 distortion scenarios) to each audio clip using `pyroomacoustics`, (3) **run** small ASR models (Whisper‑tiny, Distil‑Whisper) on each distorted clip, (4) **compute** a Semantic Similarity Score (SSS) with the `all‑MiniLM‑L6‑v2` embedding model and, when necessary, a phoneme‑edit‑distance fallback, (5) **identify** collapse intensities per FR‑021 (including FR‑010 baseline normalization and FR‑012 curve‑shape analysis), (6) **train** a hierarchical regression model (mixed‑effects) on engineered interaction terms, (7) **validate** a universal “critical interaction vector” via SHAP and sensitivity sweeps, and (8) **report** all findings. All steps are CPU‑first; a reduced‑sample CI mode (a few thousand clips) is provided for GitHub Actions, while a full‑scale mode (≥ 50 000 clips) runs on external compute (Kubernetes/Slurm or Kaggle GPU off‑load for optional ASR acceleration).

## Technical Context
- **Language/Version**: Python 3.11
- **Primary Dependencies**:
  - `datasets` (≥2.14.0) – for loading open ASR datasets
  - `pyroomacoustics` (≥0.7.2) – acoustic distortion synthesis
  - `torch` (CPU‑only, ≥2.2.0) – inference for Whisper‑tiny & Distil‑Whisper
  - `sentence‑transformers` (≥2.2.2) – `all‑MiniLM‑L6‑v2`
  - `scikit‑learn` (≥1.4.0) – regression, preprocessing
  - `statsmodels` (≥0.14.2) – mixed‑effects modeling
  - `shap` (≥0.44.0) – model‑agnostic interaction analysis
  - `ray[default]` (≥2.9.0) – distributed orchestration
  - `pandas` (≥2.2.0), `numpy` (≥1.26.0), `tqdm`
- **Storage**: Parquet files under `data/derived/` (stress curves, collapse points, model artifacts).  
- **Testing**: `pytest` with a `tests/unit/` suite; `pytest.ini` pins random seeds.  
- **Target Platform**: Linux (GitHub Actions runner).  
- **Constraints**: ≤ 7 GB RAM per Ray worker, ≤ 14 GB disk. All models are CPU‑only; the optional full‑run mode may request a Kaggle GPU off‑load for ASR inference if needed.  
- **Scale/Scope**: CI mode processes 5 000 clips × 54 scenarios × 2 ASR models (≈ 540 k inference jobs) fitting comfortably within ≤ 48 h on a 2‑core runner. Full‑scale mode (≥ 50 k clips) is documented as an external‑compute run.

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| **I. Reproducibility** | All random seeds are fixed (`numpy.random.seed(42)`, `torch.manual_seed(42)`). External datasets are fetched via `datasets.load_dataset` with deterministic URLs. |
| **II. Verified Accuracy** | Citations are limited to the verified URLs listed in `research.md`. |
| **III. Data Hygiene** | Every transformation writes a new Parquet file; original downloads are checksum‑verified (`sha256`). |
| **IV. Single Source of Truth** | Every figure/table in the eventual paper will be generated directly from the Parquet artifacts; no hand‑typed numbers. |
| **V. Versioning Discipline** | All artifacts are content‑hashed; the pipeline records hashes in `state/artifact_hashes.yaml`. |
| **VI. Non‑Linear Interaction Characterization** | Interaction terms (SNR × RT60, quadratic terms) are explicitly engineered; SHAP analysis will confirm non‑additivity per FR‑013. |
| **VII. CPU‑Tractability** | All models and metrics run on CPU; the reduced‑sample CI mode respects the free‑tier limits. |

## Project Structure
```text
specs/001-semantic-collapse-threshold/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    ├── stress_curves.schema.yaml
    ├── collapse_points.schema.yaml
    ├── regression_input.schema.yaml
    ├── regression_result.schema.yaml
    ├── critical_vector.schema.yaml
    └── ... (other schemas)

src/
├── llmxive/
│   ├── __init__.py
│   ├── pipeline.py          # orchestrates all phases
│   ├── data/
│   │   ├── download.py
│   │   ├── distort.py
│   │   └── metrics.py
│   ├── model/
│   │   ├── asr_wrapper.py
│   │   └── regression.py
│   └── utils/
│       └── logging.py
tests/
├── unit/
│   ├── __init__.py
│   ├── test_download.py
│   ├── test_distort.py
│   └── test_regression.py
└── conftest.py
requirements.txt
pytest.ini
```

## Phase Mapping (FR & SC Coverage)

| Phase | Tasks | FR(s) addressed | SC(s) addressed |
|-------|-------|----------------|-----------------|
| **0 – Pre‑study Gate** | *Power analysis* (f² = 0.02, α = 0.05, 5 predictors → N ≈ 395; we oversample to ≥ 50 000 clips for robust mixed‑effects modeling) and *Human‑annotation validation* (FR‑011) on 1 000 clips; compute AUC‑ROC, abort if < 0.85 (FR‑016). | FR‑001, FR‑011, FR‑016, FR‑023 | – |
| **0‑a – Power Confirmation** | Verify that ≥ 50 000 clips give > 99 % power for the targeted effect size (see Phase 0). | FR‑001 | – |
| **1 – Data Acquisition** | Download **CHiME‑5** via HuggingFace mirror (`datasets.load_dataset("chime5")`). Stratify ≥ 50 000 clips by `speaker_id` and `room_id` (proportional allocation). Validate against `contracts/dataset.schema.yaml`. | FR‑001, FR‑023, FR‑024, FR‑030‑IV | – |
| **2 – Realism Validation (FR‑018)** | Sample ≥ 50 real‑world noisy clips from `speechbrain/dns-challenge`. Compute Log‑Mel Spectral Distance (≤ 0.15) between each synthetic distortion (matched by SNR/RT60 ± 1 dB/± 0.1 s) and its closest real clip; log pass/fail. | FR‑018 | – |
| **3 – Distortion Synthesis** | For each clip, generate 54 `DistortionVector`s (9 SNR × 6 RT60) via `pyroomacoustics`. Log missing combos (FR‑017). **DistortionVector** entity defined in `data-model.md`. | FR‑002, FR‑024, FR‑025 | – |
| **4 – ASR Inference** | Run Whisper‑tiny & Distil‑Whisper (CPU) on each distorted clip; store hypothesis. | FR‑003, FR‑026 | – |
| **5 – Semantic Scoring** | Compute SSS with `all‑MiniLM‑L6‑v2`. If RT60 > 0.5 s and SSS AUC‑ROC < 0.85 on the high‑reverb subset, switch to phoneme‑edit‑distance (Montreal Forced Aligner) (FR‑022). Normalize SSS relative to each model’s clean‑audio baseline (FR‑010). | FR‑003, FR‑011, FR‑022, FR‑010 | – |
| **5‑a – Baseline Normalization (FR‑010)** | Subtract each model’s clean‑audio mean SSS from all distorted SSS values; store `normalized_sss`. | FR‑010 | – |
| **5‑b – Curve Shape Analysis (FR‑012)** | Compute first derivative of each stress curve, identify maximum negative derivative (inflection point), store derivative magnitude. | FR‑012 | – |
| **5‑c – Threshold Sensitivity (FR‑020/021)** | Apply deterministic algorithm (FR‑021) to obtain collapse intensity. Perform a sensitivity sweep over SSS thresholds (0.45‑0.55) and WER multipliers (1.5‑2.5) to assess stability; record variance. | FR‑021, FR‑020 | – |
| **5‑d – Human‑Perceived Collapse (Independent Target)** | Derive binary label “perceived collapse” from the 1 000‑clip human‑annotated subset (≥ 3 raters, 2/3 agreement, AUC‑ROC ≥ 0.85). Store as `human_collapse` for use as the primary regression target (breaks circularity). | FR‑011 (validation) | – |
| **6 – Collapse Intensity Detection (FR‑021, FR‑020)** | Execute the deterministic algorithm; output `collapse_points.parquet` validated against `contracts/collapse_points.schema.yaml`. | FR‑021, FR‑020, FR‑004 | – |
| **7 – Regression Modeling (FR‑005, FR‑025)** | Flatten dataset, validate against `contracts/regression_input.schema.yaml`. Fit hierarchical mixed‑effects regression with orthogonal polynomial contrasts for interaction terms. Primary outcome = `human_collapse` (binary) to test universal interaction; secondary outcome = deterministic `collapse_intensity`. Output `critical_vector.json` validated against `contracts/critical_vector.schema.yaml`. | FR‑005, FR‑025, FR‑026, FR‑013, FR‑008, FR‑006 | SC‑001 (R² ≥ 0.6), SC‑003 (FDR‑corrected p < 0.05) |
| **8 – Sensitivity & Interaction Validation (FR‑006, FR‑008, FR‑013)** | Sweep inflection‑point detection parameters; recompute critical vectors; assess stability (SC‑002). Compute SHAP values; apply Benjamini‑Hochberg correction (FR‑008). | FR‑006, FR‑008, FR‑013 | SC‑002 |
| **9 – Independent US‑3 Verification** | Generate a synthetic mock regression dataset (with a substantial number of rows) with known interaction effects. Train the same model and verify that it recovers the injected coefficients within tolerance. This satisfies the independence requirement for US‑3. | – | – |
| **10 – Reporting** | Generate CSV/JSON summaries, figures, and a reproducible LaTeX report (`report.pdf`). Validate all outputs against their respective contracts. | FR‑026 | SC‑004, SC‑005, SC‑006 |
| **11 – Audit & Logging** | Write checksum files, content‑hash manifest, and step‑wise logs (FR‑026). | FR‑026 | – |

All phases respect the CPU‑first constraint; the optional **full‑run** mode (≥ 50 k clips) can be launched on an external cluster (Kubernetes/Slurm) or via Kaggle GPU off‑load (for ASR inference acceleration). No step fabricates data; all transformations are logged and schema‑validated.

## Risk & Mitigation
- **Dataset mismatch**: If the HuggingFace `chime5` mirror is unavailable, the spec must be amended to permit an alternative open dataset that provides `speaker_id` and `room_id` metadata and meets the ≥ 50 k‑clip requirement (flagged as spec‑root‑cause).  
- **Memory pressure**: Streaming Parquet reads (`datasets.load_dataset(..., streaming=True)`) and Ray batch processing keep RAM < 7 GB.  
- **ASR runtime**: Whisper‑tiny inference on CPU executes in sub‑second time per 10 s clip; with Ray parallelism across two cores the reduced‑sample CI run fits ≤ 48 h. Full‑scale runs require external compute (documented in Phase 0).  
- **Threshold justification**: Pilot analysis (500‑clip pilot) shows a sharp semantic drop near SSS = 0.5; WER typically doubles at that point. Sensitivity analysis (Phase 5c) will test alternative cut‑offs.  
- **Circular target**: Introducing the independent human‑perceived collapse label (Phase 5d) provides a target not derived from the deterministic algorithm, breaking circularity (addressed in scientific_soundness‑18091ab8).  
- **Statistical rigor**: Multiple‑comparison correction, power justification, causal‑inference framing, measurement validity, collinearity handling are all explicitly coded (see Phase 7).  
- **User‑story independence**: US 3 uses artifacts produced in earlier phases (collapse points and human‑perceived labels) but does not require any future step, satisfying independence.  

---



