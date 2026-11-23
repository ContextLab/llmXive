# Failure Modes Documentation

## Overview

This document records the error handling and failure strategies employed by the data generation pipeline, specifically for **Task T013** in `code/generate_text.py`.

## Failure Strategy for T013

- **Goal**: Ensure that the generated dataset of AI‑generated texts exhibits sufficient variance in the **Flesch‑Kincaid** readability scores, spanning at least the range **5.0 – 12.0** (SC‑001). This variance is required for downstream regression analyses.

- **Validation Logic** (`validate_fk_range`):
 1. After generating the initial batch of text samples, the script computes the minimum and maximum Flesch‑Kincaid scores across all samples.
 2. If the observed range **does not** cover the required interval (i.e., `max_fk - min_fk < 7.0` or the bounds fall outside 5.0–12.0), the script attempts to broaden the distribution by re‑sampling prompts.
 3. The re‑sampling process is limited to **three retry attempts** (`max_retries = 3`). Each retry reloads a new stratified sample of Wikipedia articles and re‑generates the texts using alternative prompt variations designed to push the readability scores toward the extremes.

- **Failure Outcome**:
 - If, after three retries, the Flesch‑Kincaid range still fails to meet the 5.0–12.0 criterion, the script **exits with status code 1**.
 - An error message is logged to the standard logger:
 ```
 ERROR: Could not achieve FK variance 5.0-12.0 after 3 retries.
 ```
 - No `generated_text.csv` file is written, preventing downstream tasks from operating on an insufficiently varied dataset.

## Rationale

- **Statistical Power**: A narrow readability range would limit the explanatory power of the regression models (see SC‑001) and could produce misleading or non‑significant results.
- **Reproducibility**: By capping retries and providing a clear exit condition, the pipeline remains deterministic and avoids indefinite loops that could stall CI runs.

## Interaction with the Pipeline

- **Upstream**: The failure occurs within `code/generate_text.py` after the Wikipedia sample is loaded and the LLM (Gemma‑2B) generates texts.
- **Downstream**: Subsequent tasks (e.g., `T014` checksum generation, `T024` analysis) depend on the existence of `data/raw/generated_text.csv`. A failure at T013 therefore halts the entire pipeline, which is the intended behavior to enforce data quality.

## Logging

All messages related to this failure strategy are emitted via the project‑wide logger obtained from `llmxive_toolkit.get_logger`. The log entry includes a timestamp and the module name (`generate_text`), facilitating debugging in CI logs.

## Future Extensions

- **Adaptive Prompt Generation**: Replace the static retry prompt list with a heuristic that selects prompts based on the current FK distribution.
- **Dynamic Retry Count**: Allow the maximum number of retries to be configured via a CLI argument for flexibility in experimental settings.