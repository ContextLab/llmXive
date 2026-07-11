# Implementation Plan: llmXive follow-up: extending "EVA-Bench: A New End-to-end Framework for Evaluating Voice Agents"

**Branch**: `001-llmxive-latency-study` | **Date**: 2026-07-12 | **Spec**: `specs/001-llmxive-latency-study/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-latency-study/spec.md`

## Summary

This project extends the EVA-Bench framework to investigate the impact of **temporal disruption** (network latency/jitter) on voice agent performance. The technical approach involves:
1.  **Data Ingestion**: Downloading the EVA-Bench dataset (audio + metadata). *Verification*: We will confirm the presence of audio files; if only transcripts exist, we will fail fast or use a TTS fallback (Research Constraint).
2.  **Latency Injection**: Programmatically inserting silence gaps (200ms–2000ms in 200ms steps) **strictly at turn boundaries** defined in the JSONL metadata to avoid disrupting speech content (FR-001, SC-001).
3.  **Re-evaluation**: Re-running the original EVA-Bench scoring pipeline (or a lightweight surrogate if LLM-based) on the modified audio to generate metric scores (FR-002).
4.  **Statistical Analysis**: Performing repeated-measures ANOVA and piecewise regression to identify non-linear failure thresholds (FR-003, FR-004, SC-002).
5.  **Sensitivity Analysis**: Sweeping the identified breakpoint ±50ms to verify stability (SC-005).
6.  **Comparative Reporting**: Contrasting latency degradation curves against an acoustic-noise baseline re-run on the *same* scenario subset (FR-005, FR-008, SC-003).
7.  **Behavioral Metrics**: Utilizing 'Task Completion Rate', 'Semantic Coherence', and 'Interruption Count' to ensure metrics are not tautologically derived from silence (FR-009).

All processing is constrained to CPU-only execution on GitHub Actions free-tier runners (2 CPU, 7GB RAM) to ensure reproducibility and feasibility (FR-006, FR-007, SC-004).

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pydub` (audio manipulation), `scipy` (signal processing), `pandas` (data handling), `statsmodels` (ANOVA/Regression), `matplotlib`/`seaborn` (visualization), `requests` (dataset fetch).
**Storage**: Local filesystem (`data/`, `results/`). No external DB.
**Testing**: `pytest` (unit tests for injection logic, integration tests for pipeline).
**Target Platform**: Linux (GitHub Actions Ubuntu runner).
**Project Type**: Computational Research Pipeline.
**Performance Goals**: Full dataset analysis (213 scenarios [Source: EVA-Bench Paper, Table 1] × 10 latency steps) < 6 hours.
**Constraints**:
-   **No GPU/CUDA**: All libraries must have CPU wheels; no `torch` GPU ops.
-   **Memory**: Peak RAM usage < 7 GB (requires streaming audio processing or batched loading).
-   **Data Integrity**: Raw audio must remain bit-identical except for injected silence (SC-001). *See Data Hygiene rules in `data-model.md` Section 4.*

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/`. EVA-Bench dataset fetched from canonical HuggingFace URL every run. `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **PASS** | EVA-Bench dataset URL verified in `research.md`. Citations to the original paper will be validated by the Reference-Validator Agent. **Blocking Gate**: The project cannot proceed to `research_complete` without a successful Reference-Validator run. |
| **III. Data Hygiene** | **PASS** | Raw data downloaded to `data/raw/` with checksums. Modified audio written to `data/processed/` with new filenames. No in-place edits. |
| **IV. Single Source of Truth** | **PASS** | All figures/statistics in `paper/` generated from `results/` CSVs derived from `code/`. No hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Artifacts under `data/` and `code/` will carry content hashes in `state/`. *Workflow*: A CI script `scripts/update-hashes.sh` will generate SHA-256 hashes for all `data/` and `code/` files and update `state/projects/PROJ-824-llmxive-follow-up-extending-eva-bench-a.yaml` on every commit. |
| **VI. Temporal Robustness** | **PASS** | Latency injection explicitly varies 200ms–2000ms in 200ms increments (FR-001, Const-VI). |
| **VII. Statistical Validation** | **PASS** | Plan includes Repeated-Measures ANOVA and Piecewise Regression (FR-003, FR-004, Const-VII). |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-latency-study/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    ├── injection.schema.yaml
    └── results.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-824-llmxive-follow-up-extending-eva-bench-a/code/
├── requirements.txt
├── config.py            # Paths, seeds, constants (200ms-2000ms steps)
├── data/
│   ├── download.py      # Fetches EVA-Bench from HuggingFace
│   ├── checksums.json   # Recorded hashes
│   └── raw/             # Downloaded JSONL
├── processing/
│   ├── __init__.py
│   ├── latency_injector.py # pydub/scipy logic for silence insertion
│   └── pipeline_runner.py  # Wraps EVA-Bench scoring logic
├── analysis/
│   ├── __init__.py
│   ├── stats_models.py     # ANOVA, Piecewise Regression
│   └── comparison.py       # AUC, Acoustic vs. Latency
├── visualization/
│   └── plots.py
└── tests/
    ├── test_injection.py
    └── test_pipeline.py
```

**Structure Decision**: Single project structure selected to minimize overhead. The `processing` module isolates the audio manipulation, `analysis` handles the statistical rigor, and `data` separates raw vs. processed artifacts to satisfy Data Hygiene (Const-III).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **None** | The scope is contained within a single research pipeline. | N/A |

### Schema Validation
The pipeline will enforce the contracts defined in `contracts/` at runtime. The `data/download.py` and `processing/pipeline_runner.py` will validate input/output against `dataset.schema.yaml` and `results.schema.yaml` respectively.