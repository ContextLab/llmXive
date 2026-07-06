# Implementation Plan: Investigating the Relationship Between Neural Synchrony and Attention Switching Costs

**Branch**: `001-neural-synchrony-switching-costs` | **Date**: 2023-10-27 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-neural-synchrony-switching-costs/spec.md`

## Summary

This project implements a computational pipeline to test the hypothesis that pre-stimulus neural synchrony (Instantaneous Phase Difference or wPLI) in theta and gamma bands *modulates* attention switching costs (the difference in reaction time between switch and stay conditions). The approach involves downloading EEG data (OpenNeuro dataset), preprocessing (filtering, ICA), extracting trial-level behavioral metrics, computing pre-stimulus synchrony metrics, and fitting Linear Mixed-Effects Models (LMM) with interaction terms and multiple-comparison corrections. The entire pipeline is constrained to run on a CPU-only GitHub Actions runner (≤7 GB RAM, ≤6 hours).

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: `mne`, `numpy`, `pandas`, `statsmodels`, `scipy`, `pyyaml`, `requests`  
**Storage**: Local file system (`data/raw`, `data/processed`, `data/interim`)  
**Testing**: `pytest` (contract tests against YAML schemas, unit tests for signal processing logic)  
**Target Platform**: Linux (GitHub Actions Free Tier)  
**Project Type**: Computational Neuroscience Research Pipeline  
**Performance Goals**: Process all subjects sequentially within 6 hours; peak RAM < 7 GB.  
**Constraints**: No GPU; no CUDA; strict memory management (batched processing); no deep learning libraries.  
**Scale/Scope**: Single dataset (OpenNeuro ds004173), ~15-20 subjects, trial-level analysis.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **CONDITIONAL** | All random seeds pinned in `code/`; `requirements.txt` used; data fetched from canonical OpenNeuro source via `mne.datasets.fetch_openneuro_dataset`. Checksums recorded in `state/` *only if* fetch succeeds. If fetch fails or data is missing required labels, the pipeline halts, preserving reproducibility by failing explicitly. |
| **II. Verified Accuracy** | **CONDITIONAL** | Citations restricted to verified dataset URLs. Since the provided verified URLs are invalid for the specific task, the plan relies on the canonical OpenNeuro fetch. If the canonical fetch fails or data is missing labels, the pipeline halts with a 'Data Unavailable' error, failing the accuracy gate at runtime. No invalid data is used. |
| **III. Data Hygiene** | **PASS** | Raw data stored immutable; checksums recorded in `state/` (SHA256) via `code/download_data.py`; derived data written to new files; PII scan passed (OpenNeuro is anonymized). |
| **IV. Single Source of Truth** | **PASS** | All stats in `paper/` trace to `data/interim/` CSVs and `code/` output logs; no hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Artifacts tracked via content hash; `updated_at` timestamps managed by Advancement-Evaluator. |
| **VI. Neural Signal Processing** | **PASS** | Preprocessing (1-45Hz, ICA) and Synchrony (Theta/Gamma, -500ms window) strictly adhere to spec. Deviations trigger auto-generation of `sensitivity_analysis.md` in Phase 4. |
| **VII. Computational Resources** | **PASS** | Pipeline designed for sequential, **batched** processing (batch size scaled to fit 7GB RAM); no GPU/CUDA. |

## Project Structure

### Documentation (this feature)

```text
specs/001-neural-synchrony-switching-costs/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-498-investigating-the-relationship-between-n/
├── code/
│   ├── __init__.py
│   ├── download_data.py       # Downloads, verifies checksums, and records to state/
│   ├── preprocess_eeg.py      # Filtering, ICA, Epoching (batched)
│   ├── compute_synchrony.py   # Morlet wavelets, Phase Difference, wPLI (batched)
│   ├── analyze_lmm.py         # LMM fitting (interaction terms), permutation tests, correction
│   └── main.py                # Orchestrator (sequential subject loop, batched trials)
├── data/
│   ├── raw/                   # OpenNeuro raw files (downloaded)
│   ├── interim/               # Preprocessed epochs, behavioral CSVs, synchrony features
│   └── processed/             # LMM results
├── tests/
│   ├── contract/              # Validates output against YAML schemas
│   └── unit/                  # Tests for signal processing logic
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure selected. The workflow is linear (Download -> Preprocess -> Compute -> Analyze) and does not require a microservices or frontend/backend split. All logic resides in `code/` to ensure reproducibility and ease of execution on a single runner.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Batched Processing** | Required by GitHub Actions RAM limits (7GB) when handling large EEG epochs and wavelet transforms. | Loading all epochs at once risks memory overflow. Batch size of 100 trials is profiled to fit within 7GB. |
| **Linear Mixed-Effects Models** | Required by FR-004 to account for within-subject correlations and to test the interaction effect (Synchrony * Condition). | Simple correlation or ANOVA would violate statistical assumptions for repeated measures and fail to test the 'cost' hypothesis. |
| **Morlet Wavelets** | Required by FR-003 for precise time-frequency decomposition with side-lobe attenuation. | Standard FFT lacks the time resolution needed for the specific pre-stimulus window. |
| **Circular-Linear Regression** | Required for IPD metric (circular) to avoid category errors in linear models. | Using raw phase in LMM is mathematically invalid; sine/cosine transformation is the standard solution. |

## Implementation Phases

### Phase 0: Data Acquisition & Validation
1.  **Fetch Data**: Attempt to download `ds004173` from the canonical OpenNeuro source using `mne.datasets.fetch_openneuro_dataset`. **No HuggingFace URLs are used** as they are invalid for this task.
2.  **Verify Labels**: Check for `switch` and `stay` event labels.
    *   If missing, check for alternative task labels (e.g., `Go/No-Go`).
    *   **Contingency**: If alternative labels exist but do not map to 'switch/stay' (as per spec), **halt execution** with "Hypothesis Untestable: Missing Condition Labels". Do not substitute analysis.
    *   If no condition labels exist, **halt execution**.
3.  **Checksum**: Compute SHA256 hash of the downloaded file and record in `state/artifact_hashes.yaml`. This step is skipped if the fetch fails.

### Phase 1: Preprocessing (Batched)
1.  **Filter**: Apply a low-frequency bandpass filter (low-frequency to a clinically relevant upper threshold).
2.  **ICA**: Perform ICA for artifact removal.
3.  **Epoch**: Create epochs from a pre-stimulus baseline period to a post-stimulus interval.
4.  **Batch**: Process subjects sequentially. Within each subject, process trials in batches of 100 to manage memory.
5.  **Exclude**: Flag subjects with >20% artifact trials or <20 switch trials.

### Phase 2: Synchrony Feature Extraction
1.  **IPD**: Compute Instantaneous Phase Difference using Morlet wavelets (≥7 cycles) in Theta (low-frequency) and Gamma (high-frequency) bands for the -500ms to 0ms window.
    *   **Transformation**: Calculate `sin_phase = sin(IPD)` and `cos_phase = cos(IPD)`.
2.  **wPLI**: Compute weighted Phase-Lag Index over a sliding window of trials. (as per FR-003 alternative).
    *   **Nature**: wPLI is a linear scalar bounded within a normalized range.
3.  **Merge**: Join with behavioral data (RT, Condition).

### Phase 3: Statistical Analysis
1.  **Model**: Fit LMM:
    *   **For IPD**: `log(RT) ~ sin_phase + cos_phase + Condition + sin_phase:Condition + cos_phase:Condition + (1 | subject_id)`
    *   **For wPLI**: `log(RT) ~ wPLI + Condition + wPLI:Condition + (1 | subject_id)`
    *   **Hypothesis Test**: The interaction term(s) (`sin_phase:Condition`, `cos_phase:Condition`, or `wPLI:Condition`) test if synchrony modulates the *switching cost*.
2.  **Likelihood Ratio Test (LRT)**:
    *   **Full Model**: Includes main effects and interactions.
    *   **Reduced Model**: Includes main effects and condition but **excludes** the interaction terms.
    *   **Test**: Compare Full vs. Reduced. If LRT p-value < 0.05 (corrected), the interaction is significant.
3.  **Correction**: Apply Bonferroni or FDR correction across bands and electrode pairs.
4.  **Success Logic**:
    *   **IPD**: If LRT is significant, check the directionality of the interaction vector (see Success Determination Logic).
    *   **wPLI**: Check if the `wPLI:Condition` coefficient is significant (corrected p < 0.05) and negative (if hypothesis predicts negative correlation).
5.  **Permutation**: Run a permutation test on the interaction term(s) with a sufficient number of iterations.

### Phase 4: Reporting
1.  **Output**: Save results to `data/processed/lmm_results.csv`.
2.  **Sensitivity**: If any parameter deviates from spec, generate `sensitivity_analysis.md` as required by Constitution Principle VI.
3.  **Validation**: Run contract tests against `contracts/lmm_results.schema.yaml`.

## Success Determination Logic

1.  **Retrieve** the model results for each electrode pair and frequency band.
2.  **For IPD Metrics**:
    *   Check if the joint test (LRT) for `sin_phase:Condition` and `cos_phase:Condition` is significant (corrected p < 0.05).
    *   **Directionality Check**: If significant, calculate the interaction vector `V = (beta_sin, beta_cos)`. The 'negative correlation with cost' is supported if the vector `V` points in the direction that reduces RT for the 'switch' condition relative to 'stay'. This is operationalized by checking the sign of the dot product of `V` and the expected direction vector (derived from the hypothesis).
3.  **For wPLI Metrics**:
    *   Check if the `wPLI:Condition` coefficient is significant (corrected p < 0.05).
    *   Check if the coefficient sign matches the predicted direction (negative).
4.  **Pass Condition**: If *any* metric (IPD or wPLI) in *any* band/pair meets the significance and directionality criteria, the project passes SC-001. If all are null, the project passes by explicitly reporting a null result.