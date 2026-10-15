# Quickstart: 001-static-dynamic-gap-analysis

This guide documents the minimal runnable command for the project.
The full pipeline (ingestion, graph extraction, feature engineering,
model training, error mining) is orchestrated by the same CLI and is
documented in later tasks; the command below is the single verified
entry point for a fresh clone.

## Run the dry-run

```bash
python -m src.cli.run_pipeline --dry-run
```

The command:

1. Creates the project directory skeleton (`data/`, `data/results/`,
 `interim/`, `features/`, `models/`, `reports/`, `src/pipeline/`,
 `src/cli/`).
2. Pins the global random seed (42) for `random` and `numpy`.
3. Writes a tiny result file `data/results/sample_run.csv`
 (4 rows, well under the 10-row limit) with columns
 `patch_id,true_label,predicted_label,predicted_prob`.
4. Prints the path of the sample result file and exits with code 0. [UNRESOLVED-CLAIM: c_9198ce03 — status=not_enough_info]

Expected console output ends with a line of the form:

```
Dry-run completed. Sample result at: <project>/data/results/sample_run.csv
```

## Reproducibility notes

- Seed: 42 (pinned at module import and re-applied from `--seed`).
- All output paths are created via the `llmxive_toolkit.paths`
 helpers, so the command works from any working directory.
- Later phases extend the same CLI with `--swe_gym_url`,
 `--multi_swe_rl_url`, `--output_dir`, and `--seed` flags; the
 dry-run above requires no arguments.
