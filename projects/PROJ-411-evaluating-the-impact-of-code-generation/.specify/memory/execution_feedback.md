# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/prs-v2-sample.parquet) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/raw/prs-v2-sample.parquet) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 7 run-book script(s) missing (plan/impl path mismatch): python code/classify_provenance.py  --input data/raw/prs-v2-sample.parquet  --output data/processed/classified_prs.csv; python code/compute_metrics.py  --input data/processed/classified_prs.csv  --output data/processed/processed_prs.csv; python code/outlier_filter.py --iqr 1.5; 1 command(s) failed: python code/download_data.py (rc=1)

## Failing / missing run-book commands

- python code/download_data.py -> rc=1
8 INFO __main__: Required fields from schema: ['pr_id', 'repo_name', 'created_at', 'merged_at', 'additions', 'deletions', 'comment_count', 'commit_message']
2026-10-21 14:18:53,848 INFO __main__: Listing files for repo loubnabnl/prs-v2-sample
2026-10-21 14:18:53,979 INFO __main__: Downloading data/train-00000-of-00001-a3494cf8c0712e34.parquet from loubnabnl/prs-v2-sample
2026-10-21 14:18:54,603 INFO __main__: Combined parquet written to /home/runner/work/llmXive/llmXive/projects/PROJ-411-evaluating-the-impact-of-code-generation/data/raw/prs-v2-sample.parquet
2026-10-21 14:18:54,647 INFO __main__: Checksum for prs-v2-sample.parquet: b585da537a022e37c51fff0289df4d4e69bec972b8ec3c5b6d860f26bd6188e7
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-411-evaluating-the-impact-of-code-generation/code/download_data.py", line 241, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-411-evaluating-the-impact-of-code-generation/code/download_data.py", line 218, in main
    raise RuntimeError(
RuntimeError: Primary dataset 'loubnabnl/prs-v2-sample' is missing mandatory fields required for scope: ['comment_count', 'merged_at']

- python code/classify_provenance.py  --input data/raw/prs-v2-sample.parquet  --output data/processed/classified_prs.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-411-evaluating-the-impact-of-code-generation/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-411-evaluating-the-impact-of-code-generation/code/classify_provenance.py': [Errno 2] No such file or directory

- python code/compute_metrics.py  --input data/processed/classified_prs.csv  --output data/processed/processed_prs.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-411-evaluating-the-impact-of-code-generation/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-411-evaluating-the-impact-of-code-generation/code/compute_metrics.py': [Errno 2] No such file or directory

- python code/outlier_filter.py --iqr 1.5 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-411-evaluating-the-impact-of-code-generation/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-411-evaluating-the-impact-of-code-generation/code/outlier_filter.py': [Errno 2] No such file or directory

- python code/statistical_analysis.py  --input data/processed/filtered_prs.csv  --results data/results/stats_summary.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-411-evaluating-the-impact-of-code-generation/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-411-evaluating-the-impact-of-code-generation/code/statistical_analysis.py': [Errno 2] No such file or directory

- python code/validation.py  --input data/processed/filtered_prs.csv  --report data/results/validation_report.md -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-411-evaluating-the-impact-of-code-generation/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-411-evaluating-the-impact-of-code-generation/code/validation.py': [Errno 2] No such file or directory

- python code/sensitivity.py --mode full -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-411-evaluating-the-impact-of-code-generation/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-411-evaluating-the-impact-of-code-generation/code/sensitivity.py': [Errno 2] No such file or directory

- python code/report.py  --stats data/results/stats_summary.csv  --validation data/results/validation_report.md  --output report.md -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-411-evaluating-the-impact-of-code-generation/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-411-evaluating-the-impact-of-code-generation/code/report.py': [Errno 2] No such file or directory


## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Download / stream** this exact data URL directly (do NOT `pip install` it — it is a data file, not a package): `https://raw.githubusercontent.com/soroushj/ghpr-dataset/main/ghpr-sample.csv`
- **Verified**: streaming a sample yielded **100** real records with fields: repo_id, issue_number, issue_title, issue_body_md, issue_body_plain, issue_created_at, issue_author_id, issue_author_association, issue_label_ids, pull_number, pull_created_at, pull_merged_at, pull_comments, pull_review_comments, pull_commits, pull_additions, pull_deletions, pull_changed_files.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import pandas as pd
url = "https://raw.githubusercontent.com/soroushj/ghpr-dataset/main/ghpr-sample.csv"
# Load CSV directly from GitHub raw URL
df = pd.read_csv(url)
print(f"RECORDS={len(df)}")
desired = ["pr_id","repository_name","pr_number","created_at","merged_at","comment_count","additions","deletions","changed_files","review_timestamps","provenance_label"]
present = [col for col in desired if col in df.columns]
print("FIELDS=" + ",".join(present))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.
