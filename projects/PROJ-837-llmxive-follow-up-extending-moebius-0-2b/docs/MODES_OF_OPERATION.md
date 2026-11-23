# Modes of Operation: CI vs Research

## Overview

The LlmXive pipeline supports two distinct modes of operation to balance rapid development
with scientific rigor. Understanding the differences is critical for interpreting results
and ensuring reproducibility.

## CI Mode (Continuous Integration / Simulation)

**Purpose**: Automated testing, pipeline validation, and CI/CD integration.

**Characteristics**:
- **Ground Truth**: Generated via a decoupled random process (`np.random.seed(config.seed)`).
 Scores are strictly independent of synthetic mask metrics (gradient variance, texture entropy).
- **Proxy Validation**: Low correlation between synthetic metrics and ground truth is **expected**.
 The pipeline logs `gate_status: EXPECTED_LOW_CORRELATION` and continues execution.
- **Inter-Rater Reliability**: Not applicable. Single-rater simulation is used.
- **Data Integrity**: Ensures the pipeline logic functions correctly without requiring external
 human annotation data.

**Configuration**:
```python
from config import set_mode
set_mode('CI')
```

**Output Artifacts**:
- `data/annotations/decoupled_scores.csv`: Contains a `mode` column set to `CI_MODE`.
- `data/results/proxy_validation.json`: Records expected low correlation behavior.

## Research Mode (Scientific Validation)

**Purpose**: Rigorous scientific validation against human complexity annotations.

**Characteristics**:
- **Ground Truth**: Ingested from external human-annotated CSV (`data/annotations/human_scores.csv`).
 Schema: `[image_id, score, rater_id]`.
- **Proxy Validation**: Requires Pearson correlation $r \ge 0.7$ between synthetic metrics and
 human scores. If $r < 0.7$, the pipeline raises `SystemExit(1)` with `gate_status: BLOCKED`.
- **Inter-Rater Reliability**: Calculates Krippendorff's alpha. If $\alpha < 0.5$, logs warnings
 to `data/results/validation_log.txt`.
- **Data Integrity**: Validates sample size ($\ge 50$) and label independence.

**Configuration**:
```python
from config import set_mode
set_mode('RESEARCH')
```

**Output Artifacts**:
- `data/results/inter_rater_reliability.json`: Contains calculated alpha value.
- `data/results/proxy_validation.json`: Records gate status (PASSED/BLOCKED) and correlation $r$.

## Comparison Matrix

| Feature | CI Mode | Research Mode |
|:--- |:--- |:--- |
| **Ground Truth Source** | Decoupled Synthetic | Human Annotations |
| **Correlation Requirement** | None (Expected Low) | $r \ge 0.7$ |
| **IR Reliability Check** | Skipped | Required ($\alpha \ge 0.5$) |
| **Pipeline Exit on Low Correlation** | No (Logs warning) | Yes (Blocks execution) |
| **Primary Goal** | Pipeline Stability | Scientific Validity |

## Implementation Details

The mode is managed centrally in `code/config.py`:
- `is_ci_mode()`: Returns `True` if mode is 'CI'.
- `is_research_mode()`: Returns `True` if mode is 'RESEARCH'.
- `set_mode(mode_str)`: Updates the global mode configuration.

Scripts check the mode at runtime to determine execution flow:
- `code/data/annotator.py`: Branches between `generate_ci_scores` and `load_research_annotations`.
- `code/eval/stats.py`: Branches validation logic in `run_correlation_analysis`.
- `code/training/save_model.py`: Enforces gate status before saving weights.

## Artifact Manifest

Ensure the following files exist for verification:
- `data/annotations/decoupled_scores.csv` (CI Mode only)
- `data/annotations/human_scores.csv` (Research Mode only)
- `data/results/proxy_validation.json` (Both modes, different content)
- `data/results/inter_rater_reliability.json` (Research Mode only)
- `data/results/validation_log.txt` (Both modes)
