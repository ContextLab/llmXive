# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: run-book completed but produced no data/figure artifacts; 1 declared deliverable(s) absent: data/raw/commit_pairs.csv

## Failing / missing run-book commands

- (no per-command failures; the run produced no real data/figure artifacts — ensure scripts WRITE their declared outputs under data/ and figures/)

## Declared deliverables still missing

- data/raw/commit_pairs.csv

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `PyGithub` to the project's `requirements.txt` and `pip install PyGithub`.
- **Verified**: this loads **67** real records with fields: commit_hash, commit_message, documentation_diff, file_path, repo_name, author_date.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import json
from github import Github

g = Github()
repo = g.get_repo("torvalds/linux")
records = []
for i, commit in enumerate(repo.get_commits()):
    if i >= 10:
        break
    sha = commit.sha
    msg = commit.commit.message
    date = commit.commit.author.date.isoformat()
    for f in commit.files:
        path = f.filename
        diff = f.patch or ""
        doc_diff = diff if path.lower().endswith((".md", ".rst", ".txt")) else ""
        records.append({
            "commit_hash": sha,
            "commit_message": msg,
            "documentation_diff": doc_diff,
            "file_path": path,
            "repo_name": repo.full_name,
            "author_date": date,
        })
print(f"RECORDS={len(records)}")
print("FIELDS=commit_hash,commit_message,documentation_diff,file_path,repo_name,author_date")
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/commit_pairs.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data_extraction.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/commit_pairs.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
