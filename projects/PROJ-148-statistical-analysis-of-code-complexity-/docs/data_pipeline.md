# Data Pipeline Documentation

This document describes each stage of the **data acquisition and preprocessing pipeline** implemented in the `code/data/` package.
The pipeline is orchestrated by `code/data/pipeline.py` via the `run_pipeline` function, which sequentially calls the following public functions:

1. **`download_gh.py` – `download_projects` / `main`**
 - Downloads archives of ≥10 Java projects from the GHTorrent dataset.
 - Verifies SHA‑256 checksums (via `utils.checksum`) before extraction.
 - Stores raw archives under `data/raw/` and creates a manifest `data/projects_manifest.csv`.

2. **`extract_commits.py` – `extract_commits` / `main`**
 - Unpacks each archive, walks the repository tree, and extracts every Java source file together with its Git commit metadata (author, timestamp, commit SHA).
 - Outputs a CSV `data/commits.csv` with columns `project_id, file_path, commit_sha, author_date, author_name`.

3. **`extract_metrics.py` – `extract_metrics` / `main`**
 - Uses **lizard** to compute static code complexity metrics for every source file:
 - **Cyclomatic Complexity** (`cyclomatic_complexity`)
 - **Lines of Code** (`loc`)
 - **Token Count** (`token_count`)
 - **Nesting Depth** (`nesting_depth`)
 - **Halstead Volume** (`halstead_volume`)
 - Handles parse failures gracefully (fallback from T050) and processes files in memory‑aware chunks (T051).
 - Writes `data/metrics.csv`.

4. **`label_bug_fixes.py` – `label_bug_fixes` / `main`**
 - Inspects commit messages and linked issue IDs to decide whether a commit is a *bug‑fix*.
 - Implements the `is_bug_fix` predicate (keyword‑based + issue‑type heuristics).
 - Adds a binary column `bug_label` (1 = bug‑fix, 0 = non‑bug‑fix) to the metrics table, producing `data/labeled_metrics.csv`.

5. **`validate_bug_labels.py` – `validate_bug_labels` / `main`**
 - Performs the reliability validation required by T014/T049.
 - Computes precision/recall against a manually curated sample and aborts the pipeline if precision < 85 %.
 - Logs the validation summary.

6. **`preprocess.py` – `preprocess` / `main`**
 - Handles missing data: imputes values when < 5 % missing per column, drops rows with > 5 % missing.
 - Detects highly skewed metrics (skewness > 2) and applies a log‑transform.
 - Saves the cleaned dataset to `data/preprocessed_metrics.csv`.

7. **`split_dataset.py` – `get_split_proportions`, `document_split_proportions`, `main`**
 - Determines the train/test split proportions (30 % test, stratified by `project_id`).
 - Documents the split in `data/split_proportions.json`.
 - Performs the split, ensuring each project appears **only in one** split (assertion from T017).
 - Writes `data/train.csv` and `data/test.csv`.

8. **`pipeline.py` – `run_pipeline`**
 - High‑level wrapper that calls the above stages in order, propagating the `Config` seed and logger.
 - Returns a tuple of paths to the final train and test CSV files.

## Reproducibility notes

- All random operations (e.g., train/test split) are seeded via `utils.config.set_random_seed`.
- Logging is handled by `utils.logging.get_logger`, with logs written to `logs/pipeline.log`.
- The pipeline can be executed from the command line:
 ```bash\npython -m code.data.pipeline\n```

## Expected outputs

| File | Description |
|------|-------------|
| `data/raw/<project>.zip` | Original downloaded archives |
| `data/commits.csv` | Commit‑level metadata |
| `data/metrics.csv` | Raw lizard metrics |
| `data/labeled_metrics.csv` | Metrics with `bug_label` |
| `data/preprocessed_metrics.csv` | Cleaned and transformed data |
| `data/train.csv` | Training split (project‑level stratified) |
| `data/test.csv` | Hold‑out test split |
| `data/split_proportions.json` | Documented split ratios |

---
