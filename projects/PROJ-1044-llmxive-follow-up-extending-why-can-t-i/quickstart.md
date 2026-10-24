# Quickstart: Counterfactual Consistency Research Pipeline

> **One‑command end‑to‑end** — runs the pipeline driver, which
> pre‑computes optical‑flow features for the original videos, writes the
> SHA‑256 checksum manifest, and prints a summary of the generated
> artifacts before exiting with status 0.

## Prerequisites

- Python 3.11 with the project environment (numpy, pandas, scipy,
 matplotlib, scikit‑learn, opencv, PyYAML are already available).
- CPU‑only machine; no GPU required.

## Run

The simplest, fully reproducible invocation uses the default configuration
file:

```bash
python -m src.pipeline.run_all --config configs/run.yaml
```

This command reads default paths and hyper‑parameters from
`configs/run.yaml` (subset size, λ sweep values, seeds, thresholds,
output directory), executes the pipeline stages in order, prints a
`=== Pipeline Summary ===` block listing the generated artifacts, and
exits with status 0 on success.

### Alternative: explicit legacy flags

For compatibility with historic examples you can also pass the individual
flags directly. **Use a concrete integer for `--num_videos`;** the placeholder
`<sufficient number of videos>` that appeared in earlier documentation is
replaced here with the default of `200` videos:

```bash
python -m src.pipeline.run_all \
 --num_videos 200 \
 --lambda_values 0.1 0.5 1.0 \
 --seeds 1 2 3 4 5 \
 --flow_divergence_thresh 0.15 \
 --feature_sim_thresh 0.9 \
 --output_dir./output
```

Both forms are equivalent – the flag‑based form overrides the values in
`configs/run.yaml` where supplied.

## Re‑running or extending

- **Change the number of synthetic videos**: edit `--num_videos` (or the
 `subset_size` entry in `configs/run.yaml`).
- **Add λ values**: extend `--lambda_values` or the corresponding list in the
 config.
- **Use a different seed list**: modify `--seeds` or the `seeds` entry in the
 config.

All changes preserve reproducibility because seeds and hyper‑parameters are
recorded in `output/config.yaml`.

## Notes on Required Resources

- The `data/patches/` directory containing simple coloured‑shape patches is
 shipped with the repository. If it is missing (e.g., a fresh clone), the
 pipeline will automatically generate a minimal set of placeholder patches
 before counterfactual generation, ensuring no script failure.
- Optical flow for counterfactual videos is **computed after generation**
 (still CPU‑only) and cached for downstream steps, satisfying FR‑006 while
 validating motion preservation.
