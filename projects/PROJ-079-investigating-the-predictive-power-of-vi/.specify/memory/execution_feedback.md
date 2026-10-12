# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python code/src/main.py --step download (rc=1); python code/src/main.py --step preprocess (rc=1); python code/src/main.py --step features (rc=1); 15 declared deliverable(s) absent: data/artifacts/fdr_pvalues_exploratory.json; data/artifacts/metrics.json; data/artifacts/permutation_pvalue.json

## Failing / missing run-book commands

- python code/src/main.py --step download -> rc=1
2026-10-12 09:55:34,343 - __main__ - INFO - Pipeline started.
2026-10-12 09:55:34,343 - __main__ - CRITICAL - Data not found: Expected ISG scores at data/processed/isg_scores.csv. Has T016 run?


- python code/src/main.py --step preprocess -> rc=1
2026-10-12 09:55:34,716 - __main__ - INFO - Pipeline started.
2026-10-12 09:55:34,716 - __main__ - CRITICAL - Data not found: Expected ISG scores at data/processed/isg_scores.csv. Has T016 run?


- python code/src/main.py --step features -> rc=1
2026-10-12 09:55:35,086 - __main__ - INFO - Pipeline started.
2026-10-12 09:55:35,086 - __main__ - CRITICAL - Data not found: Expected ISG scores at data/processed/isg_scores.csv. Has T016 run?


- python code/src/main.py --step train -> rc=1
2026-10-12 09:55:35,448 - __main__ - INFO - Pipeline started.
2026-10-12 09:55:35,448 - __main__ - CRITICAL - Data not found: Expected ISG scores at data/processed/isg_scores.csv. Has T016 run?


- python code/src/main.py --step viz -> rc=1
2026-10-12 09:55:35,811 - __main__ - INFO - Pipeline started.
2026-10-12 09:55:35,812 - __main__ - CRITICAL - Data not found: Expected ISG scores at data/processed/isg_scores.csv. Has T016 run?


- python code/src/main.py --step all -> rc=1
2026-10-12 09:55:36,181 - __main__ - INFO - Pipeline started.
2026-10-12 09:55:36,181 - __main__ - CRITICAL - Data not found: Expected ISG scores at data/processed/isg_scores.csv. Has T016 run?



## Declared deliverables still missing

- data/artifacts/fdr_pvalues_exploratory.json
- data/artifacts/metrics.json
- data/artifacts/permutation_pvalue.json
- data/artifacts/plots/coefficients.png
- data/artifacts/plots/pdp_top5.png
- data/artifacts/pvalues_exploratory.json
- data/manifest.json
- data/manifest_template.json
- data/processed/aggregated_dataset.csv
- data/processed/isg_scores.csv
- data/processed/merged_dataset.csv
- data/processed/normalized_counts.csv
- data/processed/ortholog_map.csv
- data/processed/test.csv
- data/processed/train.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/artifacts/fdr_pvalues_exploratory.json` is declared but was NOT written. Scripts referencing it:
    - `code/tests/integration/test_quickstart_e2e.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/artifacts/fdr_pvalues_exploratory.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/artifacts/metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/features.py` — NOT invoked by the run-book
    - `code/src/main.py` — IS a run-book command
    - `code/src/model.py` — NOT invoked by the run-book
    - `code/tests/integration/test_quickstart_e2e.py` — NOT invoked by the run-book
    - `code/tests/unit/test_model_eval.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/artifacts/metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/artifacts/permutation_pvalue.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/main.py` — IS a run-book command
    - `code/src/model.py` — NOT invoked by the run-book
    - `code/tests/integration/test_quickstart_e2e.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/artifacts/permutation_pvalue.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/artifacts/plots/coefficients.png` is declared but was NOT written. Scripts referencing it:
    - `code/src/viz.py` — NOT invoked by the run-book
    - `code/tests/integration/test_quickstart_e2e.py` — NOT invoked by the run-book
    - `code/tests/unit/test_viz_labels.py` — NOT invoked by the run-book
    - `code/tests/unit/test_viz_pdp.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/artifacts/plots/coefficients.png` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/artifacts/plots/pdp_top5.png` is declared but was NOT written. Scripts referencing it:
    - `code/src/viz.py` — NOT invoked by the run-book
    - `code/tests/integration/test_quickstart_e2e.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/artifacts/plots/pdp_top5.png` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/artifacts/pvalues_exploratory.json` is declared but was NOT written. Scripts referencing it:
    - `code/tests/integration/test_quickstart_e2e.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/artifacts/pvalues_exploratory.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/manifest.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/download.py` — NOT invoked by the run-book
    - `code/tests/unit/test_download_manifest.py` — NOT invoked by the run-book
    - `src/download.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/manifest.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/manifest_template.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/download.py` — NOT invoked by the run-book
    - `src/download.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/manifest_template.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/aggregated_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/features.py` — NOT invoked by the run-book
    - `code/src/main.py` — IS a run-book command
    - `code/src/model.py` — NOT invoked by the run-book
    - `code/tests/integration/test_quickstart_e2e.py` — NOT invoked by the run-book
    - `code/tests/unit/test_main.py` — NOT invoked by the run-book
    - `code/tests/unit/test_model.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/aggregated_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/isg_scores.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/main.py` — IS a run-book command
    - `code/src/preprocess.py` — NOT invoked by the run-book
    - `code/tests/unit/test_preprocess.py` — NOT invoked by the run-book
    - `code/tests/unit/test_preprocess_isg.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/isg_scores.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/merged_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/main.py` — IS a run-book command
    - `code/tests/integration/test_merge_schema.py` — NOT invoked by the run-book
    - `code/tests/integration/test_quickstart_e2e.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/merged_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/normalized_counts.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/preprocess.py` — NOT invoked by the run-book
    - `code/tests/integration/test_preprocess_e2e.py` — NOT invoked by the run-book
    - `code/tests/unit/test_preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/normalized_counts.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/ortholog_map.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/preprocess.py` — NOT invoked by the run-book
    - `code/tests/unit/test_download_manifest.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/ortholog_map.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/test.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/features.py` — NOT invoked by the run-book
    - `code/src/model.py` — NOT invoked by the run-book
    - `code/src/viz.py` — NOT invoked by the run-book
    - `code/tests/integration/test_merge_schema.py` — NOT invoked by the run-book
    - `code/tests/integration/test_preprocess_e2e.py` — NOT invoked by the run-book
    - `code/tests/integration/test_quickstart_e2e.py` — NOT invoked by the run-book
    - `code/tests/run_coverage.py` — NOT invoked by the run-book
    - `code/tests/unit/test_download.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/test.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/train.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/download.py` — NOT invoked by the run-book
    - `code/src/features.py` — NOT invoked by the run-book
    - `code/src/main.py` — IS a run-book command
    - `code/src/model.py` — NOT invoked by the run-book
    - `code/src/preprocess.py` — NOT invoked by the run-book
    - `code/src/viz.py` — NOT invoked by the run-book
    - `code/tests/integration/test_merge_schema.py` — NOT invoked by the run-book
    - `code/tests/integration/test_quickstart_e2e.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/train.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
