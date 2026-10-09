# Adaptive Sampling in Workflow Generation

## Overview

The original synthetic workflow generator (`SyntheticWorkflowGenerator`) creates a **uniform** distribution of workflow depths: each depth level from 1 to 20 receives roughly the same number of workflows. While this uniformity is useful for exploratory analyses, the *policy‑compression trade‑off* study (Section 3 of the specification) identified a **critical reduction percentage** at which the policy‑violation error rate first exceeds the 1 % bound.

To obtain higher resolution around this *safe operating zone* we introduce **adaptive sampling**:

* **Goal** – Densify the depth distribution near the depth that corresponds to the identified reduction threshold.
* **Source of the threshold** – The analysis step `code/analysis/threshold_detection.py` writes the result to `data/results/threshold_ci.json`. The JSON contains a key `threshold` (the reduction percentage where the error rate crosses 1 %).

## How Adaptive Sampling Works

1. **Load the threshold**
 The generator reads `data/results/threshold_ci.json`. If the file is missing or malformed it gracefully falls back to the original uniform strategy.

2. **Map reduction → depth**
 The relationship between reduction percentage and depth is not analytically defined in the current prototype. As a pragmatic heuristic we assume a **linear scaling**:
 ```
 target_depth = round(threshold_pct * MAX_DEPTH / 100)
 ```
 where `MAX_DEPTH = 20`. This gives an approximate depth that yields a reduction close to the threshold.

3. **Define a target window**
 Depths within **±2** of `target_depth` are considered *near the threshold*.

4. **Adjust the per‑depth count**
 For depths inside the target window we **double** the nominal count (adaptive factor = 2). All other depths keep the uniform count. The total number of generated *valid* workflows is kept close to the user‑specified `--count` by truncating excess entries in a deterministic order (lowest depth first).

5. **Invalid workflows**
 As before, ~10 % of the total count are generated as deliberately invalid workflows (conflicting constraints). [UNRESOLVED-CLAIM: c_674c55e0 — status=not_enough_info] They are placed after the valid set and use a distinct ID range (`9000+`) to keep them identifiable.

## Usage

The adaptive generator is available as a module and as a CLI entry point:

```bash
# Uniform generation (default)
python -m services.generator --count 500 --seed 42 --output data/raw/workflows.json

# Adaptive generation – densify depths near the 1 % error threshold
python -m services.generator --count 500 --seed 42 --output data/raw/workflows.json --adaptive
```

The `--adaptive` flag toggles the behaviour; omitting it reproduces the original uniform distribution, ensuring backward compatibility with existing pipelines.

## Implementation Details

* **Module** – `services/generator.py`
* **Key classes / functions**
 * `AdaptiveWorkflowGenerator` – subclass of `SyntheticWorkflowGenerator` that overrides `generate_all`.
 * `_load_threshold` – helper that reads `data/results/threshold_ci.json` and returns the numeric threshold.
 * `_determine_depth_weights` – computes a mapping `depth → workflow count` applying the adaptive factor.
* **Determinism** – The random seed supplied via `--seed` (or the class constructor) is used for all stochastic choices (complexity, invalid workflow depth, etc.).
* **Error handling** – If the threshold file cannot be read, a warning is printed and the generator falls back to the uniform strategy rather than aborting the pipeline.

## Rationale

By concentrating more synthetic workflows around the depth that corresponds to the critical reduction percentage, downstream analyses (GLMM, bootstrapping, etc.) obtain finer granularity where the trade‑off curve changes most rapidly. This improves the statistical power for estimating the exact location of the safe operating zone without increasing the overall computational budget.

## Future Extensions

* Replace the linear heuristic with an empirical mapping derived from the full trade‑off curve (e.g., by interpolating the `tradeoff_curve.csv`).
* Allow the adaptive factor and target window to be configurable via CLI arguments.
* Integrate directly with the orchestrator (`code/main.py`) so that the adaptive mode can be selected through a top‑level flag.