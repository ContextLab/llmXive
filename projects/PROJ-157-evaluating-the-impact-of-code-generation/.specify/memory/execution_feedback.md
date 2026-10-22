# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 8 run-book script(s) missing (plan/impl path mismatch): python code/download_humaneval.py  --output data/raw/codeforces_cpp.jsonl  --min-problems 50  --seed 20231027; python code/generate_llm_variants.py  --model codellama-7b-instruct  --input data/raw/codeforces_cpp.jsonl  --output data/generated/codellama/; python code/generate_llm_variants.py  --model starcoder-15b  --input data/raw/codeforces_cpp.jsonl  --output data/generated/starcoder/; 2 command(s) failed: python code/setup_env.py (rc=1); python -m pytest -m contract (rc=5); 1 declared deliverable(s) absent: data/env_config.json

## Failing / missing run-book commands

- python code/setup_env.py -> rc=1
, line 220, in _retrieve_server_version
    raise DockerException(
docker.errors.DockerException: Error while fetching server API version: Not supported URL scheme http+docker

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-157-evaluating-the-impact-of-code-generation/code/setup_env.py", line 159, in <module>
    docker_digest = _fetch_docker_digest_via_registry(DOCKER_IMAGE)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-157-evaluating-the-impact-of-code-generation/code/setup_env.py", line 139, in _fetch_docker_digest_via_registry
    raise RuntimeError(
RuntimeError: Failed to fetch manifest for gcc:13.2-bullseye from Docker Hub: 401 Unauthorized

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-157-evaluating-the-impact-of-code-generation/code/setup_env.py", line 165, in <module>
    raise RuntimeError(
RuntimeError: Cannot determine Docker image digest; aborting environment setup.

- python code/download_humaneval.py  --output data/raw/codeforces_cpp.jsonl  --min-problems 50  --seed 20231027 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-157-evaluating-the-impact-of-code-generation/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-157-evaluating-the-impact-of-code-generation/code/download_humaneval.py': [Errno 2] No such file or directory

- python code/generate_llm_variants.py  --model codellama-7b-instruct  --input data/raw/codeforces_cpp.jsonl  --output data/generated/codellama/ -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-157-evaluating-the-impact-of-code-generation/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-157-evaluating-the-impact-of-code-generation/code/generate_llm_variants.py': [Errno 2] No such file or directory

- python code/generate_llm_variants.py  --model starcoder-15b  --input data/raw/codeforces_cpp.jsonl  --output data/generated/starcoder/ -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-157-evaluating-the-impact-of-code-generation/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-157-evaluating-the-impact-of-code-generation/code/generate_llm_variants.py': [Errno 2] No such file or directory

- python code/create_problem_pairs.py  --human data/raw/codeforces_cpp.jsonl  --llm-dir data/generated/  --output data/raw/problem_pairs_v${HASH}.jsonl -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-157-evaluating-the-impact-of-code-generation/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-157-evaluating-the-impact-of-code-generation/code/create_problem_pairs.py': [Errno 2] No such file or directory

- python code/compile_and_fuzz.py  --pairs data/raw/problem_pairs_v*.jsonl  --output data/results/fuzz_results_v${HASH}.jsonl  --timeout 1800   # 30 min per binary -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-157-evaluating-the-impact-of-code-generation/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-157-evaluating-the-impact-of-code-generation/code/compile_and_fuzz.py': [Errno 2] No such file or directory

- python code/parse_crashes.py  --fuzz-results data/results/fuzz_results_v${HASH}.jsonl  --output data/results/scored_fuzz_results_v${HASH}.jsonl -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-157-evaluating-the-impact-of-code-generation/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-157-evaluating-the-impact-of-code-generation/code/parse_crashes.py': [Errno 2] No such file or directory

- python code/statistical_analysis.py  --results data/results/scored_fuzz_results_v${HASH}.jsonl  --output data/analysis/stat_summary_v${HASH}.jsonl -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-157-evaluating-the-impact-of-code-generation/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-157-evaluating-the-impact-of-code-generation/code/statistical_analysis.py': [Errno 2] No such file or directory

- python code/generate_report.py  --summary data/analysis/stat_summary_v${HASH}.jsonl  --output report.md -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-157-evaluating-the-impact-of-code-generation/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-157-evaluating-the-impact-of-code-generation/code/generate_report.py': [Errno 2] No such file or directory

- python -m pytest -m contract -> rc=5
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.7.0
rootdir: /home/runner/work/llmXive/llmXive
configfile: pyproject.toml
collected 0 items

============================ no tests ran in 0.12s =============================



## Declared deliverables still missing

- data/env_config.json

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `datasets` to the project's `requirements.txt` and `pip install datasets`.
- **Verified**: this loads **9556** real records with fields: contest_id, title, tags, rating, time_limit, memory_limit.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import datasets, sys
# Load the Codeforces dataset from Hugging Face Hub
ds = datasets.load_dataset('open-r1/codeforces', split='train')
records = len(ds)
if records == 0:
    raise ValueError('No records loaded')
print(f'RECORDS={records}')
# Determine which of the required fields are present
required = ['problem_id','contest_id','title','tags','rating','language','source_code','time_limit','memory_limit','url']
available = [f for f in required if f in ds.column_names]
print('FIELDS=' + ','.join(available))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/env_config.json` is declared but was NOT written. Scripts referencing it:
    - `code/setup_env.py` — IS a run-book command
  Make ONE of these WRITE `data/env_config.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
