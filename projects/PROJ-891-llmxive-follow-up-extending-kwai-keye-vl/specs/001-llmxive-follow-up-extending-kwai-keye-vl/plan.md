# Implementation Plan: llmXive follow-up: extending "Kwai Keye-VL-2.0 Technical Report"

**Branch**: `001-extreme-aspect-ratio-robustness` | **Date**: 2026-08-12 | **Spec**: `spec.md`
**Input**: Feature specification for extending Kwai Keye-VL-2.0 Technical Report with extreme aspect ratio robustness testing.

## Summary

This feature implements a rigorous empirical study to validate the "native-resolution" claims of the Kwai Keye-VL-2.0 architecture. The primary requirement is to programmatically generate a synthetic video benchmark dataset from ActivityNet Captions by applying extreme geometric distortions across a wide range of aspect ratios while preserving temporal ground truth. The technical approach involves a three-phase pipeline: (1) Synthetic Data Generation using `ffmpeg` for precise aspect ratio manipulation (Extreme Ratios only); (2) CPU-Constrained Inference using INT4-quantized model weights via `llama.cpp` or `optimum-intel` (with LLaVA-NeXT fallback) to operate within 7GB RAM limits; and (3) Statistical Analysis calculating mean Intersection-over-Union (mIoU) using Independent Samples tests (Welch's t-test / Mann-Whitney U) to compare distorted clips against ORIGINAL unmodified source videos (Control).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `opencv-python`, `ffmpeg-python`, `transformers`, `optimum-intel`, `llama-cpp-python`, `pandas`, `scipy`, `numpy`, `requests`, `huggingface_hub`  
**Storage**: Local filesystem (`data/raw`, `data/distorted`, `data/outputs`); Parquet/CSV for metadata; JSON for predictions.  
**Testing**: `pytest` for unit tests (data generation logic, mIoU math, stats); integration tests for pipeline execution.
- `tests/unit/test_distort.py`: Covers **FR-001** (Data Generation).
- `tests/integration/test_inference.py`: Covers **FR-002**, **FR-003** (Inference).
- `tests/unit/test_stats.py`: Covers **FR-004**, **FR-005** (Metrics & Stats).
**Target Platform**: Linux (GitHub Actions Free Tier: Multiple CPU, 7GB RAM, 14GB Disk).  
**Project Type**: Data Science / Research Pipeline  
**Performance Goals**: Complete inference batch within 6 hours; peak memory < 7GB; mIoU calculation < 1 minute.  
**Constraints**: No GPU available for primary inference; strict adherence to 7GB RAM limit; must handle OOM via fallback or exclusion.  
**Scale/Scope**: synthetic clips (a representative sample per ratio); A set of original control clips

The research question, method, and references remain unchanged as required.; A model evaluation run will be conducted to address the research question using the established method, as supported by the relevant literature [Citation].; A statistical report will be generated to address the research question using the specified method, as supported by the referenced literature..

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*Gates determined based on constitution file*

| Principle | Compliance Status | Evidence / Plan Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Compliant** | Plan mandates pinned seeds, `requirements.txt`, and CI-driven re-runs. Data generation scripts will be deterministic. |
| **II. Verified Accuracy** | **Compliant** | **Validation Step**: A `validate_citations.py` script (or Reference-Validator Agent) will run pre-execution to verify citations against the provided verified dataset URLs before any data download or model load. |
| **III. Data Hygiene** | **Compliant** | Raw data (ActivityNet) will be checksummed. Derived data (distorted clips) will be new files with documented derivation scripts. |
| **IV. Single Source of Truth** | **Compliant** | Final mIoU and p-values will be generated directly from `data/outputs` JSON/CSV, not hand-typed. |
| **V. Versioning Discipline** | **Compliant** | All artifacts (scripts, data, results) will be tracked with content hashes in the specific project state file: `state/projects/PROJ-891-llmxive-follow-up-extending-kwai-keye-vl.yaml`. |
| **VI. Geometric Stress-Testing Integrity** | **Compliant** | Plan explicitly includes extreme ratios representing varying degrees of class imbalance. The control group is defined as the **Original Unmodified ActivityNet Captions** videos, ensuring no generation artifacts confound the comparison. |
| **VII. Resource-Constrained Inference Fidelity** | **Compliant** | Inference will strictly use `llama.cpp`/`optimum-intel` on CPU with INT4 quantization. Fallback to LLaVA-NeXT if architecture unsupported. |

## Project Structure

### Documentation (this feature)

```text
specs/001-extreme-aspect-ratio-robustness/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml      # Used by data generation (FR-001)
│   ├── prediction.schema.yaml   # Used by inference (FR-003)
│   └── metric.schema.yaml       # Used by analysis (FR-004)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-891-llmxive-follow-up-extending-kwai-keye-vl/code/
├── data/
│   ├── raw/                 # Downloaded ActivityNet clips (streamed) + Metadata JSON
│   ├── distorted/           # Generated extreme aspect ratio clips
│   └── metadata/            # CSV/JSON mapping IDs to timestamps
├── models/
│   └── [kwai_keye_vl2_int4 | llava_next_int4]/  # Local cache of quantized weights
├── src/
│   ├── generators/
│   │   └── distort_video.py # FR-001: Aspect ratio generation (See contracts/dataset.schema.yaml)
│   ├── inference/
│   │   └── run_inference.py # FR-002, FR-003: CPU inference (See contracts/prediction.schema.yaml)
│   └── analysis/
│       ├── mIoU.py          # FR-004: Metric calculation (See contracts/metric.schema.yaml)
│       └── stats.py         # FR-005: Statistical testing (Independent Samples)
├── tests/
│   ├── unit/
│   │   ├── test_distort.py  # Covers FR-001
│   │   └── test_stats.py    # Covers FR-005
│   └── integration/
│       └── test_pipeline.py # Covers FR-002, FR-003
├── scripts/
│   └── validate_citations.py # Implements Constitution Principle II
└── requirements.txt
```

**Structure Decision**: Selected a linear pipeline structure (`generators` -> `inference` -> `analysis`) to match the sequential data flow required by the spec. This minimizes interdependency complexity and aligns with the "Data Hygiene" principle by separating raw, derived, and result data. Explicit contract references ensure data integrity.

## Complexity Tracking

No complexity violations found. The plan adheres strictly to the spec's constraints and the project constitution, with specific adjustments for statistical validity (Independent Samples) and data source accuracy (ActivityNet Captions).
