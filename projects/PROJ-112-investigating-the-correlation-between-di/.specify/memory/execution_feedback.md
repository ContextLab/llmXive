# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m src.preprocessing.clr_transform --input data/cleaned_data.csv --method bayesian`
  - script usage: `clr_transform.py [-h] [--input INPUT] [--output OUTPUT]`
  - argparse error: `clr_transform.py: error: unrecognized arguments: --method bayesian`

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python -m src.ingestion.agp_loader`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 14 command(s) failed: python -m src.ingestion.agp_loader (rc=1); python -m src.ingestion.user_loader (rc=1); python -m src.preprocessing.harmonize --input-dir data/raw/ (rc=1); 1 declared deliverable(s) absent: data/state/agp_checksums.json

## Failing / missing run-book commands

- python -m src.ingestion.agp_loader -> rc=1
-23 05:27:13 - agp_loader - ERROR - Failed to download AGP dataset: 401 Client Error. (Request ID: Root=1-6adaf031-42a3880673ee4ca12a93090d;35e5bf1e-124c-4bc9-b6ac-bdb47dfd13d7)

Repository Not Found for url: https://huggingface.co/american_gut/agp_diet/resolve/main/agp_counts.tsv.
Please make sure you specified the correct `repo_id` and `repo_type`.
If you are trying to access a private or gated repo, make sure you are authenticated and your token has the required permissions.
For more details, see https://huggingface.co/docs/huggingface_hub/authentication
Invalid username or password.
2026-10-23 05:27:13,282 - agp_loader - ERROR - Failed to download AGP dataset: 401 Client Error. (Request ID: Root=1-6adaf031-42a3880673ee4ca12a93090d;35e5bf1e-124c-4bc9-b6ac-bdb47dfd13d7)

Repository Not Found for url: https://huggingface.co/american_gut/agp_diet/resolve/main/agp_counts.tsv.
Please make sure you specified the correct `repo_id` and `repo_type`.
If you are trying to access a private or gated repo, make sure you are authenticated and your token has the required permissions.
For more details, see https://huggingface.co/docs/huggingface_hub/authentication
Invalid username or password.


- python -m src.ingestion.user_loader -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-112-investigating-the-correlation-between-di/bin/python: No module named src.ingestion.user_loader

- python -m src.preprocessing.harmonize --input-dir data/raw/ -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-112-investigating-the-correlation-between-di/bin/python: No module named src.preprocessing.harmonize

- python -m src.preprocessing.covariate_handler --input data/harmonized_data.csv -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-112-investigating-the-correlation-between-di/code/src/preprocessing/covariate_handler.py", line 3, in <module>
    import miceforest as mf
ModuleNotFoundError: No module named 'miceforest'

- python -m src.preprocessing.clr_transform --input data/cleaned_data.csv --method bayesian -> rc=2

usage: clr_transform.py [-h] [--input INPUT] [--output OUTPUT]
                        [--validation-log VALIDATION_LOG]
                        [--pseudocount PSEUDOCOUNT]
clr_transform.py: error: unrecognized arguments: --method bayesian

- python -m src.analysis.association --matrix data/analysis_matrix_clr.csv --mode spearman_partial -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-112-investigating-the-correlation-between-di/bin/python: No module named src.analysis.association

- python -m src.analysis.association --matrix data/analysis_matrix_clr.csv  --mode maaslin2 --covariates age,bmi,sex,antibiotic_use,read_depth -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-112-investigating-the-correlation-between-di/bin/python: No module named src.analysis.association

- python -m src.analysis.association --merge-results -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-112-investigating-the-correlation-between-di/bin/python: No module named src.analysis.association

- python -m src.analysis.differential --matrix data/analysis_matrix_clr.csv  --group-method quartile --methods ANCOM-II DESeq2 -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-112-investigating-the-correlation-between-di/bin/python: No module named src.analysis.differential

- python -m src.analysis.measurement_error --synthetic --beta 0.1 --error-sd 0.10 -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-112-investigating-the-correlation-between-di/bin/python: No module named src.analysis.measurement_error

- python -m src.preprocessing.power_analysis --mode spearman  --target-beta 0.1 --alpha 0.05 --power 0.80 --method correlation_power -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-112-investigating-the-correlation-between-di/bin/python: No module named src.preprocessing.power_analysis

- python -m src.preprocessing.power_analysis --mode linear  --target-beta 0.1 --alpha 0.05 --power 0.80 --method ftest_power -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-112-investigating-the-correlation-between-di/bin/python: No module named src.preprocessing.power_analysis

- python -m src.reporting.summary  --assoc results/association_combined.tsv  --diff-ancom results/diff_ancom.tsv  --diff-deseq2 results/diff_deseq2.tsv  --me-bias results/measurement_error_bias.tsv -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-112-investigating-the-correlation-between-di/bin/python: Error while finding module specification for 'src.reporting.summary' (ModuleNotFoundError: No module named 'src.reporting')

- python -m pytest tests/contract/ -> rc=1
ile or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-112-investigating-the-correlation-between-di/data/processed/results/association_results.tsv'
=========================== short test summary info ============================
FAILED tests/contract/test_maaslin2_schema.py::TestMaaslin2OutputSchema::test_output_file_exists
FAILED tests/contract/test_maaslin2_schema.py::TestMaaslin2OutputSchema::test_required_columns_present
FAILED tests/contract/test_maaslin2_schema.py::TestMaaslin2OutputSchema::test_column_order
FAILED tests/contract/test_maaslin2_schema.py::TestMaaslin2OutputSchema::test_no_null_values_in_required_columns
FAILED tests/contract/test_maaslin2_schema.py::TestMaaslin2OutputSchema::test_taxon_column_is_non_empty
FAILED tests/contract/test_maaslin2_schema.py::TestMaaslin2OutputSchema::test_p_value_range
FAILED tests/contract/test_maaslin2_schema.py::TestMaaslin2OutputSchema::test_spearman_rho_range
FAILED tests/contract/test_maaslin2_schema.py::TestMaaslin2OutputSchema::test_se_positive
FAILED tests/contract/test_maaslin2_schema.py::TestMaaslin2OutputSchema::test_file_is_tsv
========================= 9 failed, 7 passed in 0.36s ==========================



## Declared deliverables still missing

- data/state/agp_checksums.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/state/agp_checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/ingestion/agp_loader.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/state/agp_checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
