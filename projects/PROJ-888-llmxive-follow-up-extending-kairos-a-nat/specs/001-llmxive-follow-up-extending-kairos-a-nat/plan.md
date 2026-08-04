# Implementation Plan: llmXive follow-up: extending "Kairos: A Native World Model Stack for Physical AI"

**Branch**: `001-llmxive-kairos-discrete-scaling` | **Date**: 2026-07-14 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-llmxive-follow-up-extending-kairos-a-nat/spec.md`

## Summary

This project investigates how the minimum information density required for stable long-horizon forecasting in embodied agents scales as input modality shifts from continuous visual streams to sparse, discrete sensor streams. The technical approach involves converting the continuous LIBERO benchmark dataset into discrete, JSON-serialized state vectors with configurable quantization (4, 8, 16-bit), feeding these into a CPU-only execution of the Kairos Hybrid Linear Temporal Attention module (with a *pre-trained, frozen* discrete projection layer, initialized via a small pre-training step to ensure valid input mapping), and statistically analyzing the **Model-Adjusted Error** (MSE_normalized - QuantizationNoiseFloor) growth rates to identify stability thresholds. The baseline comparison uses the *same* frozen projection layer configuration for both modalities to isolate the modality shift effect from projection failure.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-only), `datasets` (Hugging Face), `numpy`, `pandas`, `scipy`, `pytest`, `pyyaml`  
**Storage**: Local file system (JSON/Parquet), Hugging Face cache  
**Testing**: `pytest` (unit, integration, contract)  
**Target Platform**: GitHub Actions Free Tier (2 vCPU, ~7GB RAM, ~14GB Disk, CPU-only, **6h runtime limit**)  
**Project Type**: Research / Data Pipeline / Model Evaluation  
**Performance Goals**: Training loop completes ≤ 4 hours on sampled data; Inference ≤ 2s/step; RAM < 6GB  
**Constraints**: No CUDA; No external API calls during CI; Strict reproducibility via pinned seeds.  
**Scale/Scope**: LIBERO subset (streamed/sampled); 3 quantization levels; 500-step horizon predictions.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*Gates determined based on `constitution.md`*

1.  **Reproducibility (Principle I)**: The plan mandates pinned random seeds in `code/config.py` and uses the `datasets` library with `streaming=True` to fetch the *same* canonical HuggingFace source on every run. Checksums will be recorded for all derived data in `data/`.
2.  **Verified Accuracy (Principle II)**: All dataset URLs cited in `research.md` are restricted to the verified list provided in the prompt (HuggingFace LIBERO variants). No external citations will be introduced without validation.
3.  **Data Hygiene (Principle III)**: The pipeline will not modify raw data. Raw parquet files will be downloaded to `data/raw/` with checksums. Quantized outputs will be written to `data/derived/` with new filenames and documented derivation scripts.
4.  **Single Source of Truth (Principle IV)**: All figures in the final paper will be generated programmatically from `data/derived/` files. No hand-typed statistics.
5.  **Versioning Discipline (Principle V)**: The plan explicitly tracks artifact hashes in the specific file `state/projects/PROJ-888-llmxive-follow-up-extending-kairos-a-nat.yaml` as required by the Constitution.
6.  **Resource-Constrained Stability Verification (Principle VI)**: The entire pipeline is designed for the 2-core/7GB RAM/6h constraint. The plan explicitly defines the "CPU-only" execution path and includes logic to checkpoint and exit gracefully if time limits are approached.
7.  **Discrete Modality Error Characterization (Principle VII)**: The analysis script will calculate MSE normalized by state space dimensionality, subtract the quantization noise floor, and perform paired t-tests/Wilcoxon tests as required.

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-kairos-discrete-scaling/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Design Artifacts)
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-888-llmxive-follow-up-extending-kairos-a-nat/
├── code/
│   ├── __init__.py
│   ├── config.py              # Seeds, paths, hyperparameters
│   ├── data/
│   │   ├── __init__.py
│   │   ├── downloader.py      # HF dataset fetcher
│   │   ├── quantizer.py       # Continuous -> Discrete conversion (includes degeneracy check)
│   │   └── noise_injector.py  # Gaussian noise simulation
│   ├── model/
│   │   ├── __init__.py
│   │   ├── kairos_adapter.py  # Discrete projection layer (Pre-trained, frozen)
│   │   └── trainer.py         # CPU training loop (generates ResourceConstraintReport.json)
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── metrics.py         # MSE, growth rate, normalization, noise floor
│   │   └── stats.py           # T-tests, Wilcoxon, threshold detection (generates StabilityFramingReport.md)
│   └── main.py                # Orchestration script
├── data/
│   ├── raw/                   # Downloaded parquet (symlinked or cached)
│   ├── derived/               # Quantized JSON/Parquet
│   └── .checksums             # SHA256 hashes
├── tests/
│   ├── __init__.py
│   ├── contract/              # Schema validation tests
│   ├── integration/           # End-to-end pipeline tests
│   └── unit/                  # Quantization logic tests
├── state/
│   └── projects/PROJ-888-llmxive-follow-up-extending-kairos-a-nat.yaml # Versioning artifact
└── README.md                  # Project overview and quickstart
```

**Structure Decision**: Selected the "Single Project" structure (`code/`, `data/`, `tests/`) as this is a research pipeline rather than a production service. The separation of `data/`, `model/`, and `analysis` modules ensures modularity for the specific phases of quantization, training, and statistical validation. **Note**: `contracts/` are design artifacts located in `specs/`, not source code.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The project scope is tightly constrained by the CPU/6h limits. | N/A - The design is intentionally minimal to ensure feasibility. |

## Functional Requirements Mapping

- **FR-001**: Implemented in `code/data/quantizer.py` (Phase 1). Includes degeneracy check for 1-bit collapse.
- **FR-002**: Implemented in `code/model/kairos_adapter.py` (Phase 2). The discrete projection layer is **pre-trained, frozen** (after initialization via a small pre-training step) to isolate modality shift.
- **FR-003**: Implemented in `code/model/trainer.py` (Phase 3).
- **FR-004**: Implemented in `code/analysis/metrics.py` (Phase 3).
- **FR-005**: Implemented in `code/analysis/stats.py` (Phase 3).
- **FR-006**: Implemented in `code/analysis/stats.py` (Phase 3).
- **FR-007**: Implemented in `code/model/trainer.py` which MUST write `ResourceConstraintReport.json` at every epoch, containing CPU utilization, peak RAM, and latency per step.
- **FR-008**: Implemented in `code/analysis/stats.py` which MUST generate `StabilityFramingReport.md` explicitly framing claims as "relative degradation" against the continuous baseline.
- **FR-009**: Implemented in `code/analysis/metrics.py` (Phase 3) to calculate and subtract the Quantization Noise Floor.
- **SC-001**: Implemented in `code/analysis/stats.py` which identifies the threshold where Model-Adjusted MSE exceeds the continuous baseline by a specific percentage (e.g., [deferred] or [deferred]).

## projects/PROJ-888-llmxive-follow-up-extending-kairos-a-nat/specs/001-llmxive-follow-up-extending-kairos-a-nat/research.md