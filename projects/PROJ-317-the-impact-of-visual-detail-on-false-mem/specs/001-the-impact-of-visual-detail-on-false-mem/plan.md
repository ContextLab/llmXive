# Implementation Plan: Visual Detail and False Memory Susceptibility

**Branch**: `001-visual-detail-false-memory` | **Date**: 2026-06-30 | **Spec**: `specs/001-the-impact-of-visual-detail-on-false-mem/spec.md`
**Input**: Feature specification from `specs/001-the-impact-of-visual-detail-on-false-mem/spec.md`

## Summary

This project implements a computational pipeline to test the hypothesis that visual detail complexity modulates false memory susceptibility. The system uses a **Between-Subjects design**: participants are assigned to one condition (Enhanced, Reduced, or Baseline) and view a single image. The pipeline downloads a pre-bundled subset of Visual Genome images (to ensure CI reproducibility), manipulates them via a "Semantic Compositor" to create variants, and orchestrates a participant recognition test. Statistical analysis (One-Way ANOVA) will compare false memory rates across conditions. The implementation strictly adheres to CPU-first execution on GitHub Actions free-tier runners.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `Pillow` (image manipulation), `scipy` (statistics), `matplotlib` (visualization), `datasets` (HuggingFace data loading), `pandas` (data handling), `pytest` (testing).
**Storage**: Local filesystem (`data/stimuli/`, `data/responses/`, `data/analysis/`).
**Testing**: `pytest` with unit tests for image manipulation logic and integration tests for the data flow.
**Target Platform**: Linux (GitHub Actions free-tier: CPU, sufficient RAM).
**Project Type**: Research pipeline / CLI tool.
**Performance Goals**: Image manipulation < 5s/image; Analysis < 30m for 60 participants; Total runtime < 6h.
**Constraints**: No GPU dependencies; No external API calls during execution (except dataset download); Memory usage < 7GB; Disk usage < 14GB.
**Scale/Scope**: A set of baseline images (pre-bundled); A sufficient number of simulated participant sessions for validation; Real data collection deferred to post-IRB approval phase.

> **Data Strategy Note**: The "Verified datasets" block provided in the prompt context contains only a math dataset, which is unsuitable for this visual study. To satisfy the **Data Availability** constraint for CI runs (which cannot fetch external gated data) and the **Verified Accuracy** principle, the plan uses a **Pre-bundled Subset** of Visual Genome images (shipped in `data/stimuli/raw_subset/`). This subset is verified by content hash. The final study will use the standard HuggingFace `visual_genome` loader once a new verification step is completed.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Evidence/Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/`. `requirements.txt` created. Data fetching uses `datasets` library with explicit versioning. Pre-bundled subset ensures CI reproducibility. |
| **II. Verified Accuracy** | **PASS** | All citations in `research.md` will be validated against primary sources. No fabricated URLs. Pre-bundled subset is verified by content hash. |
| **III. Data Hygiene** | **PASS** | Checksums for generated stimuli. No in-place modification. PII anonymization in `data/responses/`. |
| **IV. Single Source of Truth** | **PASS** | Figures/stats generated directly from `data/` via scripts. No manual typing. |
| **V. Versioning Discipline** | **PASS** | Content hashes for artifacts. `updated_at` timestamps managed by agent. |
| **VI. Human Subjects Ethics** | **PASS** | `data/ethics/` directory created. `informed_consent.md` template generated. **Gate**: No *real* participant recruitment until IRB approval is manually confirmed (T012.1). CI validation uses mock data (no IRB required). |
| **VII. Stimulus Standardization** | **PASS** | `data/stimuli/` stores images + `metadata.json` with manipulation params. Script version archived. |

## Project Structure

### Documentation (this feature)

```text
specs/001-the-impact-of-visual-detail-on-false-mem/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-317-the-impact-of-visual-detail-on-false-mem/
├── code/
│   ├── __init__.py
│   ├── config.py             # Constants, seeds, paths
│   ├── stimuli/
│   │   ├── generator.py      # PIL-based semantic compositing (T015)
│   │   └── metadata.py       # Stimulus metadata logging (T017)
│   ├── participants/
│   │   ├── interface.py      # Simulated participant session (T027)
│   │   └── response.py       # Response capture & validation
│   ├── analysis/
│   │   ├── power.py          # Power analysis & gate (T012)
│   │   ├── anova.py          # One-Way ANOVA (T035)
│   │   └── viz.py            # Visualization generation (T037)
│   └── utils/
│       ├── data_loader.py    # Dataset fetching (T006) - Handles Pre-bundled & HF
│       └── ethics.py         # Consent & anonymization (T010)
├── data/
│   ├── stimuli/              # Generated images + metadata
│   ├── responses/            # Participant data (anonymized)
│   ├── analysis/             # Power reports, ANOVA results
│   └── ethics/               # Consent forms, IRB docs
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
└── requirements.txt
```

**Structure Decision**: Single project structure with modular `code/` subdirectories. Chosen to minimize overhead for a research pipeline and ensure all artifacts are co-located for reproducibility.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **None** | The project is a linear pipeline: Stimuli -> Data Collection -> Analysis. No complex architecture needed. | N/A |