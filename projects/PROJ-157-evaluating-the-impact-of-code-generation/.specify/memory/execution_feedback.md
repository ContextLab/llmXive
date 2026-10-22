# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 8 run-book script(s) missing (plan/impl path mismatch): python code/download_humaneval.py  --output data/raw/codeforces_cpp.jsonl  --min-problems 50  --seed 20231027; python code/generate_llm_variants.py  --model codellama-7b-instruct  --input data/raw/codeforces_cpp.jsonl  --output data/generated/codellama/; python code/generate_llm_variants.py  --model starcoder-15b  --input data/raw/codeforces_cpp.jsonl  --output data/generated/starcoder/; 2 command(s) failed: python code/setup_env.py (rc=1); python -m pytest -m contract (rc=5); 1 declared deliverable(s) absent: data/env_config.json

## Failing / missing run-book commands

- python code/setup_env.py -> rc=1
-157-evaluating-the-impact-of-code-generation/code/setup_env.py", line 89, in _fetch_docker_digest
    response.raise_for_status()
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/requests/models.py", line 1024, in raise_for_status
    raise HTTPError(http_error_msg, response=self)
requests.exceptions.HTTPError: 401 Client Error: Unauthorized for url: https://registry-1.docker.io/v2/library/gcc/manifests/13.2-bullseye

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-157-evaluating-the-impact-of-code-generation/code/setup_env.py", line 101, in <module>
    docker_digest = _fetch_docker_digest(DOCKER_IMAGE)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-157-evaluating-the-impact-of-code-generation/code/setup_env.py", line 91, in _fetch_docker_digest
    raise RuntimeError(f"Failed to fetch manifest for {image}: {exc}") from exc
RuntimeError: Failed to fetch manifest for gcc:13.2-bullseye: 401 Client Error: Unauthorized for url: https://registry-1.docker.io/v2/library/gcc/manifests/13.2-bullseye

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

============================ no tests ran in 0.07s =============================



## Declared deliverables still missing

- data/env_config.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/env_config.json` is declared but was NOT written. Scripts referencing it:
    - `code/setup_env.py` — IS a run-book command
  Make ONE of these WRITE `data/env_config.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
