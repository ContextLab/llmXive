# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/model_verification_log.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/raw/model_verification_log.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 1 run-book script(s) missing (plan/impl path mismatch): python src/analysis/statistical_tests.py --input data/derived/baseline_scores.jsonl,data/derived/degraded_scores.jsonl,data/derived/intervention_scores.jsonl --output data/derived/stats.csv; 6 command(s) failed: python code/src/sim/trajectory_generator.py --n 500 --condition baseline --output data/raw/baseline_trajectories.jsonl (rc=1); python code/src/sim/trajectory_generator.py --n 500 --condition degraded --output data/raw/degraded_trajectories.jsonl (rc=1); python code/src/sim/trajectory_generator.py --n 500 --condition intervention --output data/raw/intervention_trajectories.jsonl (rc=1); 1 declared deliverable(s) absent: data/raw/baseline_failures.json

## Failing / missing run-book commands

- python code/src/sim/trajectory_generator.py --n 500 --condition baseline --output data/raw/baseline_trajectories.jsonl -> rc=1
    Starting model verification for meta-llama/Llama-3-8B-Instruct...
Attempting to load model: meta-llama/Llama-3-8B-Instruct on cpu...
CRITICAL: Model verification failed: Failed to load model meta-llama/Llama-3-8B-Instruct: meta-llama/Llama-3-8B-Instruct is not a local folder and is not a valid model identifier listed on 'https://huggingface.co/models'
If this is a private repository, make sure to pass a token having permission to this repo either by logging in with `huggingface-cli login` or by passing `token=<your_token>`
- python code/src/sim/trajectory_generator.py --n 500 --condition degraded --output data/raw/degraded_trajectories.jsonl -> rc=1
    Starting model verification for meta-llama/Llama-3-8B-Instruct...
Attempting to load model: meta-llama/Llama-3-8B-Instruct on cpu...
CRITICAL: Model verification failed: Failed to load model meta-llama/Llama-3-8B-Instruct: meta-llama/Llama-3-8B-Instruct is not a local folder and is not a valid model identifier listed on 'https://huggingface.co/models'
If this is a private repository, make sure to pass a token having permission to this repo either by logging in with `huggingface-cli login` or by passing `token=<your_token>`
- python code/src/sim/trajectory_generator.py --n 500 --condition intervention --output data/raw/intervention_trajectories.jsonl -> rc=1
    Starting model verification for meta-llama/Llama-3-8B-Instruct...
Attempting to load model: meta-llama/Llama-3-8B-Instruct on cpu...
CRITICAL: Model verification failed: Failed to load model meta-llama/Llama-3-8B-Instruct: meta-llama/Llama-3-8B-Instruct is not a local folder and is not a valid model identifier listed on 'https://huggingface.co/models'
If this is a private repository, make sure to pass a token having permission to this repo either by logging in with `huggingface-cli login` or by passing `token=<your_token>`
- python src/sim/validation.py --input data/raw/baseline_trajectories.jsonl --output data/derived/baseline_validated.jsonl -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-926-llmxive-follow-up-extending-role-agent-b/src/sim/validation.py", line 12, in <module>
    from src.sim.alfworld_runner import run_episode
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-926-llmxive-follow-up-extending-role-agent-b/src/sim/alfworld_runner.py", line 14, in <module>
    import alfworld
ModuleNotFoundError: No module named 'alfworld'
- python src/sim/validation.py --input data/raw/degraded_trajectories.jsonl --output data/derived/degraded_validated.jsonl -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-926-llmxive-follow-up-extending-role-agent-b/src/sim/validation.py", line 12, in <module>
    from src.sim.alfworld_runner import run_episode
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-926-llmxive-follow-up-extending-role-agent-b/src/sim/alfworld_runner.py", line 14, in <module>
    import alfworld
ModuleNotFoundError: No module named 'alfworld'
- python src/sim/validation.py --input data/raw/intervention_trajectories.jsonl --output data/derived/intervention_validated.jsonl -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-926-llmxive-follow-up-extending-role-agent-b/src/sim/validation.py", line 12, in <module>
    from src.sim.alfworld_runner import run_episode
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-926-llmxive-follow-up-extending-role-agent-b/src/sim/alfworld_runner.py", line 14, in <module>
    import alfworld
ModuleNotFoundError: No module named 'alfworld'
- python src/analysis/statistical_tests.py --input data/derived/baseline_scores.jsonl,data/derived/degraded_scores.jsonl,data/derived/intervention_scores.jsonl --output data/derived/stats.csv -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-926-llmxive-follow-up-extending-role-agent-b/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-926-llmxive-follow-up-extending-role-agent-b/src/analysis/statistical_tests.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/raw/baseline_failures.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/baseline_failures.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/conditions/run_degraded.py` — NOT invoked by the run-book
    - `code/tests/integration/test_baseline_generation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/baseline_failures.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
