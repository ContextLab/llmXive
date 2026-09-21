# Mode Labeling Guide: CI vs Research

This document explains the operational modes supported by the llmXive-Moebius pipeline and how to correctly label artifacts, logs, and reports.

## Overview

The system operates in two distinct modes to ensure scientific rigor and CI compatibility:

1. **CI Mode**: A simulation environment for automated testing and continuous integration.
2. **Research Mode**: The full scientific workflow using real human-annotated data.

## Configuration

Modes are controlled via the `config.py` module:
- `set_mode('CI')` or `set_mode('RESEARCH')`
- `is_ci_mode()` and `is_research_mode()` helpers are available throughout the codebase.

## Artifact Labeling Requirements

To prevent ambiguity and ensure reproducibility, all generated artifacts MUST explicitly state the mode used.

### 1. Data Files
- **CSVs**: Must include a `mode` column (e.g., `data/annotations/decoupled_scores.csv`).
 - Example: `image_id,score,mode` -> `img_001,4.2,CI_MODE`
- **JSONs**: Must include a top-level `mode` key.
 - Example: `{"mode": "RESEARCH", "alpha": 0.65,...}`

### 2. Logs
- Every log entry generated during execution MUST include a timestamp and mode indicator.
- Format: `[TIMESTAMP] [MODE] Message`
- Example: `[2023-10-27 10:00:00] [CI_MODE] Ground truth decoupled from metrics.`

### 3. Reports
- The final `paper/draft.md` and `data/results/evaluation_report.json` must clearly state the mode.
- CI Mode reports must explicitly note that results are "Simulation Only" and "Decoupled from Model Metrics".

## Mode-Specific Behaviors

### CI Mode
- **Data Generation**: Synthetic scores generated via `np.random` with fixed seeds.
- **Validation**: Correlation checks expect low values ($r < 0.1$) and do not block execution.
- **Gate Logic**: Proxy validation gates are bypassed or marked as `EXPECTED_LOW_CORRELATION`.
- **Goal**: Verify pipeline integrity without requiring external human data.

### Research Mode
- **Data Generation**: Loads real human annotations from `data/annotations/human_scores.csv`.
- **Validation**: Requires Inter-Rater Reliability (Krippendorff's $\alpha \ge 0.5$) and Proxy Correlation ($r \ge 0.7$).
- **Gate Logic**: Fails execution if validation gates are not met.
- **Goal**: Produce scientifically valid results for publication.

## Implementation Checklist

- [ ] `code/config.py` exposes mode flags.
- [ ] `code/data/annotator.py` writes `mode` to CSVs.
- [ ] `code/eval/stats.py` logs mode in validation results.
- [ ] `paper/draft.md` contains mode-specific sections.
- [ ] All log files include `[CI_MODE]` or `[RESEARCH_MODE]` tags.
