# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- data/processed/style_scores_threshold_0.25_0.75.csv: header only, ZERO data rows — the analysis produced no rows
- every produced artifact is gitignored (data/processed/style_scores_threshold_0.25_0.75.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 hollow-result signal(s) — the analysis ran but computed nothing: data/processed/style_scores_threshold_0.25_0.75.csv: header only, ZERO data rows — the analysis produced no rows; every produced artifact is gitignored (data/processed/style_scores_threshold_0.25_0.75.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 1 run-book script(s) missing (plan/impl path mismatch): python projects/PROJ-108-assessing-the-impact-of-code-style-consi/code/00_download_data.py; 5 command(s) failed: python code/00_validate_urls.py (rc=1); python code/01_style_scoring.py (rc=1); python code/04_evaluation.py (rc=1); 4 declared deliverable(s) absent: data/metadata/file_metadata.csv; data/processed/sensitivity_report.json; data/processed/statistical_report.json

## Failing / missing run-book commands

- python code/00_validate_urls.py -> rc=1
Starting URL validation for dataset sources...
------------------------------------------------------------
Checking CodeSearchNet...
  URL: https://github.com/code-search-net/CodeSearchNet/archive/master.zip
  Status: FAIL (HTTP Error: 404 Not Found) [0.15s]
------------------------------------------------------------
Checking Defects4J...
  URL: https://github.com/rjust/defects4j/releases/download/v2.0.0/defects4j-2.0.0.tar.gz
  Status: FAIL (HTTP Error: 404 Not Found) [0.21s]
------------------------------------------------------------

Summary:
  One or more dataset URLs are unreachable.
  Please check your network connection or the URL configuration.

Failed checks:
  - CodeSearchNet: HTTP Error: 404 Not Found
  - Defects4J: HTTP Error: 404 Not Found


- python projects/PROJ-108-assessing-the-impact-of-code-style-consi/code/00_download_data.py -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-108-assessing-the-impact-of-code-style-consi/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-108-assessing-the-impact-of-code-style-consi/projects/PROJ-108-assessing-the-impact-of-code-style-consi/code/00_download_data.py': [Errno 2] No such file or directory

- python code/01_style_scoring.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-108-assessing-the-impact-of-code-style-consi/code/01_style_scoring.py", line 23, in <module>
    from code.utils import metrics  # Importing to ensure utils exists, though not used for scores directly here
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-108-assessing-the-impact-of-code-style-consi/code/utils/__init__.py", line 5, in <module>
    from .metrics import bleu_score, f1_score, compute_cohen_d, pearson_correlation
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-108-assessing-the-impact-of-code-style-consi/code/utils/metrics.py", line 236, in <module>
    ) -> Dict[str, Union[float, str]]:
         ^^^^
NameError: name 'Dict' is not defined. Did you mean: 'dict'?

- python code/04_evaluation.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-108-assessing-the-impact-of-code-style-consi/code/04_evaluation.py", line 22, in <module>
    from metrics import bleu_score, f1_score
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-108-assessing-the-impact-of-code-style-consi/code/utils/metrics.py", line 236, in <module>
    ) -> Dict[str, Union[float, str]]:
         ^^^^
NameError: name 'Dict' is not defined. Did you mean: 'dict'?

- python code/05_statistical_analysis.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-108-assessing-the-impact-of-code-style-consi/code/05_statistical_analysis.py", line 11, in <module>
    from utils.metrics import compute_cohen_d, t_test_independent, ancova
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-108-assessing-the-impact-of-code-style-consi/code/utils/__init__.py", line 5, in <module>
    from .metrics import bleu_score, f1_score, compute_cohen_d, pearson_correlation
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-108-assessing-the-impact-of-code-style-consi/code/utils/metrics.py", line 236, in <module>
    ) -> Dict[str, Union[float, str]]:
         ^^^^
NameError: name 'Dict' is not defined. Did you mean: 'dict'?

- python code/06_robustness_check.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-108-assessing-the-impact-of-code-style-consi/code/06_robustness_check.py", line 23, in <module>
    from utils.model_loader import load_model_and_tokenizer, TimeoutStoppingCriteria
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-108-assessing-the-impact-of-code-style-consi/code/utils/__init__.py", line 5, in <module>
    from .metrics import bleu_score, f1_score, compute_cohen_d, pearson_correlation
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-108-assessing-the-impact-of-code-style-consi/code/utils/metrics.py", line 236, in <module>
    ) -> Dict[str, Union[float, str]]:
         ^^^^
NameError: name 'Dict' is not defined. Did you mean: 'dict'?


## Declared deliverables still missing

- data/metadata/file_metadata.csv
- data/processed/sensitivity_report.json
- data/processed/statistical_report.json
- data/processed/style_scores.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/metadata/file_metadata.csv` is declared but was NOT written. Scripts referencing it:
    - `code/00_extract_metadata.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/metadata/file_metadata.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/03_sensitivity_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/statistical_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/07_generate_statistical_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/statistical_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/style_scores.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_style_scoring.py` — IS a run-book command
    - `code/02_stratification.py` — IS a run-book command
    - `code/03_inference.py` — NOT invoked by the run-book
    - `code/03_sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/06_ablation_analysis.py` — NOT invoked by the run-book
    - `code/06_robustness_check.py` — IS a run-book command
    - `code/07_generate_statistical_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/style_scores.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
