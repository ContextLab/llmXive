# Implementation Plan: llmXive follow-up: extending "AnyFlow: Any-Step Video Diffusion Model with On-Policy Flow Map Distil"

**Branch**: `001-llmxive-follow-up-extending-anyflow-any` | **Date**: 2026-08-26 | **Spec**: `spec.md`
**Input**: Feature specification for CPU‑tractable flow‑map divergence analysis.

## Summary
This plan implements a rigorous, reproducible pipeline that (1) curates a balanced video dataset using verified sources (UCF101 for continuous motion, MovieNet for scene cuts), (2) collects independent human continuity scores via an external annotation workflow, (3) computes a CPU‑only "flow‑map divergence" metric using a frozen AnyFlow model in ONNX Runtime, (4) performs statistically sound correlation and classification analyses (including Fisher's r‑to‑z test and IPW weighting), (5) validates the analysis logic on a synthetic subset (FR-012), and (6) produces a final report. All steps respect the CI runtime and 7 GB RAM limits. The plan strictly separates the *pipeline integrity test* (using synthetic data) from the *scientific validation* (using human scores) to avoid circularity.

## Technical Context

- **Language/Version**: Python 3.11  
- **Core Libraries**: `torch` (CPU wheel), `onnxruntime`, `datasets` (streaming), `pandas`, `scikit‑learn`, `scipy`, `statsmodels`, `numpy`, `matplotlib`, `seaborn`, `hypothesis` (for synthetic generation)
- **Storage**: `data/` (raw, processed, checksums), `results/` (final report)  
- **Compute**: CPU‑first; only ONNX Runtime on CPU; no GPU required.  
- **Testing**: `pytest` with contract validation (`tests/test_contracts.py`) against YAML schemas in `contracts/` and unit tests for each module.  

## Project Structure

```text
projects/PROJ-812-llmxive-follow-up-extending-anyflow-any/
├─ code/
│  ├─ __init__.py
│  ├─ requirements.txt
│  ├─ data/
│  │  ├─ download_and_stratify.py          # FR‑001
│  │  ├─ annotation/
│  │  │   ├─ collect_annotations.py        # FR‑002 (human ingestion)
│  │  │   ├─ validate_annotations.py        # FR‑010 (Kappa, variance, bimodality)
│  │  │   └─ adjudicate.py                  # FR‑002 (third‑expert resolution)
│  │  ├─ model/
│  │  │   ├─ load_onnx.py                  # FR‑003
│  │  │   └─ compute_divergence.py          # FR‑004
│  │  ├─ analysis/
│  │  │   ├─ correlation.py                # FR‑005 (Pearson, Spearman, IPW)
│  │  │   ├─ fisher_r_to_z.py              # FR‑004 null‑hypothesis test
│  │  │   ├─ control_analysis.py           # FR‑004 control distribution
│  │  │   ├─ sensitivity.py                # FR‑006
│  │  │   ├─ power_analysis.py             # FR‑011
│  │  │   └─ synthetic_validation_subset.py # FR‑012 (synthetic subset generation & verification)
│  │  ├─ utils/
│  │  │   ├─ checksums.py                  # Versioning Discipline (Principle V)
│  │  │   ├─ logging.py
│  │  │   └─ reference_validator.py        # Constitution II verification
│  │  └─ main.py                            # Orchestrator (phase ordering)
├─ data/
│  ├─ raw/
│  │   ├─ video_clips/                      # 16‑frame clips (streamed)
│  │   └─ ground_truth.csv                  # immutable human annotations
│  ├─ processed/
│  │   ├─ divergence_scores.csv
│  │   ├─ sensitivity_report.csv
│  │   └─ variance_report.csv
│  └─ checksums.json                        # SHA‑256 hashes for raw files
├─ results/
│   └─ final_report.md
├─ tests/
│   ├─ test_contracts.py
│   └─ test_units.py
└─ contracts/
   ├─ analysis.schema.yaml
   ├─ annotation.schema.yaml
   ├─ clip.schema.yaml
   ├─ clip_feature_schema.schema.yaml
   ├─ clip_metadata.schema.yaml
   ├─ continuity_scores.schema.yaml
   ├─ correlation_results.schema.yaml
   ├─ dataset.schema.yaml
   ├─ divergence.schema.yaml
   ├─ divergence_metric_schema.schema.yaml
   ├─ divergence_metrics.schema.yaml
   ├─ divergence_schema.schema.yaml
   ├─ ground_truth_schema.schema.yaml
   ├─ metric.schema.yaml
   ├─ result.schema.yaml
   ├─ results.schema.yaml
   ├─ sensitivity.schema.yaml
   ├─ sensitivity_report.schema.yaml
   ├─ sensitivity_schema.schema.yaml
   ├─ threshold_result_schema.schema.yaml
   └─ variance_report.schema.yaml
```

### Phase Mapping (FR → Script)

| Functional Requirement | Phase | Script(s) |
|------------------------|-------|-----------|
| **FR‑001**: Download & stratify clips (balanced continuous/cut) | Data Curation | `download_and_stratify.py` (uses `datasets.load_dataset(..., streaming=True)` on UCF101 and MovieNet) |
| **FR‑002**: Human annotation (5‑point Likert, blinded) | Ground Truth | `annotation/collect_annotations.py` (ingests external CSV) → produces `ground_truth.csv` |
| **FR‑002**: Third-expert adjudication | Validation | `annotation/adjudicate.py` |
| **FR‑010**: Inter‑annotator agreement & variance check | Validation | `annotation/validate_annotations.py` (Cohen's κ, variance, Hartigan's Dip) |
| **FR‑003**: Load frozen AnyFlow in ONNX (CPU) | Model Loading | `model/load_onnx.py` |
| **FR‑004**: Compute flow‑map divergence, baseline Euler, control analysis, Fisher r‑to‑z | Metric Computation | `model/compute_divergence.py`, `analysis/control_analysis.py`, `analysis/fisher_r_to_z.py` |
| **FR‑005**: Correlation, logistic regression, IPW | Statistical Analysis | `analysis/correlation.py` |
| **FR‑006**: Sensitivity sweep (thresholds & N) | Sensitivity | `analysis/sensitivity.py` |
| **FR‑009**: Pre‑flight runtime estimate, adapt N | Complexity | `analysis/power_analysis.py` (also used for FR‑011) |
| **FR‑012**: Synthetic subset validation | Synthetic Validation | `analysis/synthetic_validation_subset.py` |
| **Constitution II**: Verify URLs | Reference Validation | `utils/reference_validator.py` |
| **Constitution V**: Checksums & versioning | Versioning | `utils/checksums.py` |
| **Constitution VI**: Stability check after quantization | Fidelity | `analysis/fidelity_check.py` (re‑run correlation after adding 0.01 noise) |

### Detailed Tasks (ordered)

1. **Reference Validation** – `utils/reference_validator.py` runs before any download to ensure all URLs in `research.md` are reachable and match the verified list.
2. **Dataset Download & Stratified Sampling** – `download_and_stratify.py` streams clips, extracts a representative subset of frames at 30 fps, and enforces a balanced cut-continuous split using verified labels from UCF101 (continuous) and MovieNet (cuts).
3. **Checksum Generation** – `utils/checksums.py` creates `data/checksums.json` for every raw file (clips and `ground_truth.csv`). This satisfies Principle V.
4. **Human Annotation Collection** – `annotation/collect_annotations.py` ingests a pre-collected CSV of human scores (generated via external tool like Label Studio) and stores them in `data/raw/ground_truth.csv`.
5. **Inter‑Annotator Agreement & Adjudication** – `annotation/validate_annotations.py` computes Cohen's κ; if κ < 0.81, the pipeline aborts. Disagreements are resolved by `annotation/adjudicate.py` (third expert), producing a final immutable CSV.
6. **Model Loading** – `model/load_onnx.py` converts the frozen AnyFlow checkpoint to ONNX (CPU) on‑the‑fly and caches the model hash.
7. **Divergence Computation** – `model/compute_divergence.py` runs on each clip, computes the high‑resolution Euler baseline (default N=500), checks convergence, falls back to N=200 if FR‑009 demands, and records additional temporal features (kurtosis, clustering). Errors are logged and the clip is marked "skipped".
8. **Control Distribution Analysis** – `analysis/control_analysis.py` compares divergence score distributions between the verified smooth (UCF101) and cut (MovieNet) groups (Kolmogorov‑Smirnov test) and outputs a small report.
9. **Fisher r‑to‑z Null‑Hypothesis Test** – `analysis/fisher_r_to_z.py` performs Fisher's transformation on the Pearson r and reports the z‑score and p‑value for H₀: r = 0.
10. **Correlation & IPW** – `analysis/correlation.py` calculates Pearson, Spearman, applies inverse‑probability weighting to correct the artificial 50/50 sampling, and fits a multivariate logistic regression (features: divergence, kurtosis, clustering). Outputs `analysis_results.json` validated against `contracts/analysis.schema.yaml`.
11. **Sensitivity Sweep** – `analysis/sensitivity.py` iterates over thresholds spanning low to moderate significance levels and Euler steps {[deferred]} (or restricted set if N < 500) and writes `sensitivity_report.csv`.
12. **Synthetic Validation Subset** – `analysis/synthetic_validation_subset.py` builds a synthetic dataset with known binary labels (using `hypothesis`), runs the full metric pipeline, and verifies false‑positive/negative rates against hand‑computed expectations (≤ 0.01 error). Results are stored in `synthetic_validation_report.json`.
13. **Power Analysis** – `analysis/power_analysis.py` confirms that N=500 achieves 80 % power to detect r≈0.12 (α = 0.05). If the pre‑flight estimate exceeds a critical threshold, N is reduced to 200. and the pilot re‑run to ensure r > 0.7 before full execution (FR‑009).
14. **Fidelity Check (Constitution VI)** – `analysis/fidelity_check.py` adds small Gaussian noise (σ=0.01) to latent vectors, recomputes Pearson r, and verifies that |Δr| ≤ 0.05.
15. **Report Generation** – `results/final_report.md` aggregates all metrics, includes explicit associational framing, documents all steps, and links each figure/table to its source CSV (Principle IV).

## Constitution Check

| Principle | Status | Action/Note |
|-----------|--------|-------------|
| **I. Reproducibility** | PASS | Seeds pinned; all external data fetched via verified URLs; `main.py` enforces strict phase ordering. |
| **II. Verified Accuracy** | PASS | `utils/reference_validator.py` runs before any download; citations limited to verified URLs listed in `research.md`. |
| **III. Data Hygiene** | PASS | Checksums recorded; no in‑place mutation; raw files immutable. |
| **IV. Single Source of Truth** | PASS | Every figure/table references a single row in a CSV; contracts enforce schema compliance. |
| **V. Versioning Discipline** | PASS | `utils/checksums.py` generates `data/checksums.json`; artifact hashes tracked in `state/`. |
| **VI. Latent Trajectory Fidelity** | PASS | Fidelity check (`analysis/fidelity_check.py`) ensures Pearson r stability within ±0.05 after quantization/noise. |
| **VII. Temporal Continuity Ground Truth** | PASS | Human annotations collected **outside** CI (ingested as immutable CSV); adjudication ensures high agreement. |

### Two-Phase Validation Strategy
- **Pipeline Integrity Test**: Uses a synthetic subset (FR-012) with known labels to verify code correctness and error rates. This does *not* validate the scientific hypothesis.
- **Scientific Validation**: Uses independent human annotations (FR-002) to test the hypothesis. This is the only data used for the final correlation and regression results.