# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/preprocessing.py --input data/processed/merged_clean.parquet --output data/processed/diversity_metrics.parquet`
  - script usage: `preprocessing.py [-h] --input INPUT --output OUTPUT --median-depth`
  - argparse error: `preprocessing.py: error: the following arguments are required: --median-depth, --loss`
- run-book command: `python code/analysis.py --input data/processed/diversity_metrics.parquet --output data/results/associations.csv`
  - script usage: `analysis.py [-h] --bray-curtis BRAY_CURTIS --metadata METADATA --output`
  - argparse error: `analysis.py: error: the following arguments are required: --bray-curtis, --metadata`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python code/data_ingestion.py --check-only (rc=1); python code/data_ingestion.py --output data/processed/merged_clean.parquet (rc=1); python code/preprocessing.py --input data/processed/merged_clean.parquet --output data/processed/diversity_metrics.parquet (rc=2); 10 declared deliverable(s) absent: data/interim/adjusted_pvals.csv; data/interior/estimated_loss.json; data/interior/median_depth.json

## Failing / missing run-book commands

- python code/data_ingestion.py --check-only -> rc=1

2026-10-13 08:32:19,153 INFO pipeline: Starting data ingestion pipeline...
2026-10-13 08:32:19,153 INFO pipeline: Checking data feasibility...
2026-10-13 08:32:19,153 INFO pipeline: Attempting to load AGP data from verified mirror...
2026-10-13 08:32:19,175 WARNING pipeline: HuggingFace dataset load failed: pyarrow requires NumPy 2.0 or newer, found 1.26.4
/home/runner/work/llmXive/llmXive/projects/PROJ-215-investigating-the-relationship-between-g/code/data_ingestion.py:130: ParserWarning: Falling back to the 'python' engine because the 'c' engine does not support regex separators (separators > 1 char and different from '\s+' are interpreted as regex); you can avoid this warning by specifying engine='python'.
  otu_df = pd.read_csv(OTU_TABLE_URL, sep='\\t', index_col=0)
2026-10-13 08:32:19,276 ERROR pipeline: Failed to load data from direct URLs: HTTP Error 404: Not Found
2026-10-13 08:32:19,276 ERROR pipeline: Could not load data from verified sources.
2026-10-13 08:32:19,277 CRITICAL pipeline: Data Gap Report generated: /home/runner/work/llmXive/llmXive/projects/PROJ-215-investigating-the-relationship-between-g/results/data_gap_report.md

- python code/data_ingestion.py --output data/processed/merged_clean.parquet -> rc=1

2026-10-13 08:32:19,693 INFO pipeline: Starting data ingestion pipeline...
2026-10-13 08:32:19,694 INFO pipeline: Checking data feasibility...
2026-10-13 08:32:19,694 INFO pipeline: Attempting to load AGP data from verified mirror...
2026-10-13 08:32:19,715 WARNING pipeline: HuggingFace dataset load failed: pyarrow requires NumPy 2.0 or newer, found 1.26.4
/home/runner/work/llmXive/llmXive/projects/PROJ-215-investigating-the-relationship-between-g/code/data_ingestion.py:130: ParserWarning: Falling back to the 'python' engine because the 'c' engine does not support regex separators (separators > 1 char and different from '\s+' are interpreted as regex); you can avoid this warning by specifying engine='python'.
  otu_df = pd.read_csv(OTU_TABLE_URL, sep='\\t', index_col=0)
2026-10-13 08:32:19,763 ERROR pipeline: Failed to load data from direct URLs: HTTP Error 404: Not Found
2026-10-13 08:32:19,763 ERROR pipeline: Could not load data from verified sources.
2026-10-13 08:32:19,764 CRITICAL pipeline: Data Gap Report generated: /home/runner/work/llmXive/llmXive/projects/PROJ-215-investigating-the-relationship-between-g/results/data_gap_report.md

- python code/preprocessing.py --input data/processed/merged_clean.parquet --output data/processed/diversity_metrics.parquet -> rc=2

usage: preprocessing.py [-h] --input INPUT --output OUTPUT --median-depth
                        MEDIAN_DEPTH --loss LOSS
                        [--loss-threshold LOSS_THRESHOLD]
preprocessing.py: error: the following arguments are required: --median-depth, --loss

- python code/analysis.py --input data/processed/diversity_metrics.parquet --output data/results/associations.csv -> rc=2

usage: analysis.py [-h] --bray-curtis BRAY_CURTIS --metadata METADATA --output
                   OUTPUT [--alpha-metrics ALPHA_METRICS]
                   [--taxa-data TAXA_DATA]
analysis.py: error: the following arguments are required: --bray-curtis, --metadata

- python code/visualization.py --input data/results/associations.csv --output docs/figures/ -> rc=1
ng taxa heatmap visualization (T028)
2026-10-13 08:32:22,207 INFO __main__: Starting taxa heatmap visualization (T028)
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-215-investigating-the-relationship-between-g/code/visualization.py", line 178, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-215-investigating-the-relationship-between-g/code/visualization.py", line 175, in main
    run_heatmap_visualization()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-215-investigating-the-relationship-between-g/code/visualization.py", line 157, in run_heatmap_visualization
    df_assoc = load_association_results()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-215-investigating-the-relationship-between-g/code/visualization.py", line 22, in load_association_results
    raise FileNotFoundError(f"Association results not found at {path}. "
FileNotFoundError: Association results not found at /home/runner/work/llmXive/llmXive/projects/PROJ-215-investigating-the-relationship-between-g/data/processed/association_results.csv. Ensure T025 has been completed successfully.

- python code/report.py --input data/results/associations.csv --output docs/report.md -> rc=1
 found: /home/runner/work/llmXive/llmXive/projects/PROJ-215-investigating-the-relationship-between-g/data/processed/association_results.csv
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-215-investigating-the-relationship-between-g/code/report.py", line 200, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-215-investigating-the-relationship-between-g/code/report.py", line 193, in main
    output_path = run_report_generation()
                  ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-215-investigating-the-relationship-between-g/code/report.py", line 163, in run_report_generation
    assoc_df = load_association_results()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-215-investigating-the-relationship-between-g/code/report.py", line 21, in load_association_results
    raise FileNotFoundError(f"Association results file not found: {path}")
FileNotFoundError: Association results file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-215-investigating-the-relationship-between-g/data/processed/association_results.csv


## Declared deliverables still missing

- data/interim/adjusted_pvals.csv
- data/interior/estimated_loss.json
- data/interior/median_depth.json
- data/processed/alpha_metrics.csv
- data/processed/association_results.csv
- data/processed/bray_curtis.npz
- data/processed/cleaned_dataset.csv
- data/processed/ks_test_results.json
- data/processed/metrics.json
- data/processed/validation_results.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/interim/adjusted_pvals.csv` is declared but was NOT written. Scripts referencing it:
    - `code/check_covariate_adjustment.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/adjusted_pvals.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/interior/estimated_loss.json` is declared but was NOT written. Scripts referencing it:
    - `code/preprocessing.py` — IS a run-book command
  Make ONE of these WRITE `data/interior/estimated_loss.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/interior/median_depth.json` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/preprocessing.py` — IS a run-book command
  Make ONE of these WRITE `data/interior/median_depth.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/alpha_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — IS a run-book command
    - `code/output_cleaned_dataset.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/alpha_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/association_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/check_ks_pvalue.py` — NOT invoked by the run-book
    - `code/generate_final_report.py` — NOT invoked by the run-book
    - `code/output_association_results.py` — NOT invoked by the run-book
    - `code/report.py` — IS a run-book command
    - `code/run_visualization_and_report.py` — NOT invoked by the run-book
    - `code/validation.py` — NOT invoked by the run-book
    - `code/visualization.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/association_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/bray_curtis.npz` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — IS a run-book command
    - `code/preprocessing.py` — IS a run-book command
    - `code/run_visualization_and_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/bray_curtis.npz` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/cleaned_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/output_cleaned_dataset.py` — NOT invoked by the run-book
    - `code/run_visualization_and_report.py` — NOT invoked by the run-book
    - `code/visualization.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/cleaned_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/ks_test_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/check_ks_pvalue.py` — NOT invoked by the run-book
    - `code/generate_final_report.py` — NOT invoked by the run-book
    - `code/report.py` — IS a run-book command
    - `code/run_visualization_and_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/ks_test_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — IS a run-book command
    - `code/check_pipeline_runtime.py` — NOT invoked by the run-book
    - `code/generate_final_report.py` — NOT invoked by the run-book
    - `code/output_cleaned_dataset.py` — NOT invoked by the run-book
    - `code/output_validation_results.py` — NOT invoked by the run-book
    - `code/preprocessing.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/validation_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_final_report.py` — NOT invoked by the run-book
    - `code/output_validation_results.py` — NOT invoked by the run-book
    - `code/reference_validator.py` — NOT invoked by the run-book
    - `code/run_reference_validator.py` — NOT invoked by the run-book
    - `code/validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/validation_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
