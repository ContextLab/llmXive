# Implementation Plan: llmXive Follow-up: Extending "Mega-ASR" for Semantic Collapse Thresholds

**Branch**: `001-semantic-collapse-threshold` | **Date**: 2026-07-12 | **Spec**: [link]
**Input**: Feature specification from `/specs/001-semantic-collapse-threshold/spec.md`

## Summary

This feature implements a CPU-tractable pipeline to investigate non-linear interactions between acoustic distortions (reverberation and noise) and their effect on ASR semantic integrity. The system will generate stress curves by applying multiple compound distortion scenarios to a stratified subset of audio data, identify "semantic collapse points" where Semantic Similarity Scores (SSS) drop below 0.5 (normalized) and Word Error Rate (WER) spikes, and train a lightweight regression model to predict these collapse intensities. 

**Critical Methodological Update**: To address circularity concerns, the regression target is redefined as the **Human-Validated Collapse Margin (HVCM)**, derived from a separate human-annotation task on a held-out subset of distorted clips. The SSS metric is used for descriptive stress curves, but the predictive model targets human-judged intelligibility collapse, breaking the tautology of predicting input parameters from the same input parameters.

The plan explicitly addresses the "Critical Interaction Vector" hypothesis, ensuring all statistical claims are associational and corrected for multiple comparisons, while strictly adhering to the constrained RAM and runtime limits of the GitHub Actions free tier.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn`, `transformers` (CPU-only), `torch` (CPU), `librosa`, `pandas`, `numpy`, `datasets`, `sentence-transformers`, `jiwer`  
**Storage**: Local file system (`data/`), Parquet/CSV formats  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest`)  
**Project Type**: Data Analysis / Research Pipeline  
**Performance Goals**: Complete stress testing and regression analysis on a sampled subset within 6 hours; peak RSS < 7GB.  
**Constraints**: No GPU; no deep-learning fine-tuning; no 8-bit/4-bit quantization requiring CUDA; strict memory management via chunked processing.  
**Scale/Scope**: Subset of audio clips (target: [deferred] clips, determined by SC-004 runtime constraints); distortion scenarios per clip; A small set of ASR models (e.g., Whisper-tiny).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: The plan mandates pinned random seeds in `code/`, deterministic data fetching from canonical sources, and a `requirements.txt` to ensure re-runs on fresh runners produce identical results.
- **II. Verified Accuracy**: **Note on Deviation**: The spec (FR-001) mandates "Voices-in-the-Wild-2M". This dataset has no verified URL. The plan explicitly deviates from the spec's dataset source to satisfy Principle II, substituting with verified **LibriSpeech** and **CORAA-MUPE-ASR** subsets. All dataset citations in `research.md` are restricted to these verified URLs.
- **III. Data Hygiene**: The pipeline will download raw data to `data/raw/`, compute checksums, and write derived artifacts (stress curves, collapse points) to `data/derived/` without modifying originals.
- **IV. Single Source of Truth**: All figures and statistics in the final report will be generated programmatically from the `data/derived/` artifacts, preventing manual transcription errors.
- **V. Versioning Discipline**: **Explicit Step**: A `hash-updater.py` script is included in the pipeline. Post-pipeline, it computes content hashes for all `data/derived/` artifacts and updates `state/projects/PROJ-844-llmxive-follow-up-extending-mega-asr-tow.yaml` with these hashes.
- **VI. Non-Linear Interaction Characterization**: The plan explicitly includes engineered interaction terms (SNR × RT60, etc.) in the regression model (FR-05) AND mandates a **Sensitivity Analysis** (FR-06) to verify the "critical interaction vector" is not an artifact of the threshold choice.
- **VII. CPU-Tractability**: The plan restricts ASR models to small variants (e.g., `whisper-tiny`) and the embedding model to `all-MiniLM-L6-v2`. It explicitly forbids GPU-only libraries and mandates memory-efficient data loading strategies (chunking, sampling) to fit the 7GB RAM constraint.

## Project Structure

### Documentation (this feature)

```text
specs/001-semantic-collapse-threshold/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-844-llmxive-follow-up-extending-mega-asr-tow/
├── code/
│   ├── __init__.py
│   ├── config.py              # Paths, seeds, hyperparameters
│   ├── data_loader.py         # Dataset fetching and stratification
│   ├── distortion_engine.py   # Apply compound distortions
│   ├── metrics.py             # SSS, WER, Collapse detection
│   ├── models.py              # Regression model training
│   ├── statistics.py          # Multiple comparison correction (FR-008)
│   ├── analysis.py            # Sensitivity analysis, plotting, HVCM validation
│   ├── monitor_resources.py   # SC-004: Memory/Runtime monitoring
│   ├── hash_updater.py        # Principle V: State file hash update
│   └── main.py                # Orchestration script
├── data/
│   ├── raw/                   # Downloaded datasets
│   ├── derived/               # Stress curves, collapse points
│   └── validation/            # Human-annotated subset
├── tests/
│   ├── contract/
│   ├── integration/
│   └── unit/
├── docs/
└── requirements.txt
```

**Structure Decision**: A single-project structure (`code/`) is selected to maintain simplicity for a research pipeline. The separation of `data/raw` and `data/derived` ensures data hygiene. The modular design allows independent testing of distortion generation, metric calculation, and model training.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Distortion Scenarios

The research question, method, and references remain as stated, with the specific count of scenarios generalized to a qualitative description of multiple distortion scenarios. | Required by spec to capture non-linear interactions across the full space of reverberation and noise combinations. | A smaller subset would fail to detect the "critical interaction vector" and invalidate the core hypothesis (VI). |
| Multiple ASR Models | Required to test the "universal" nature of the collapse threshold across architectures. | Testing a single model would only yield model-specific results, not a universal phenomenon. |
| Sensitivity Analysis (Threshold Sweep) | Required by FR-06 to ensure findings are not artifacts of the arbitrary 0.5 cutoff. | A single-point analysis would be fragile and scientifically weak. |
| Human-Validated Target (HVCM) | Required to break circularity in regression (predicting input from input). | Using SSS-derived targets creates a tautology. Human validation is the only valid ground truth for "semantic collapse". |