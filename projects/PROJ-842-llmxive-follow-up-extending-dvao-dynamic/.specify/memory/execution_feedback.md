# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python run_experiment.py --full-sweep; python run_experiment.py --N 10 --k 0.05 --runs 5; 1 command(s) failed: python code/src/derivation/sample_complexity.py --output docs/theoretical_derivation.md (rc=1); 2 declared deliverable(s) absent: data/processed/empirical_results.json; data/processed/statistical_report.json

## Failing / missing run-book commands

- python run_experiment.py --full-sweep -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-842-llmxive-follow-up-extending-dvao-dynamic/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-842-llmxive-follow-up-extending-dvao-dynamic/run_experiment.py': [Errno 2] No such file or directory
- python run_experiment.py --N 10 --k 0.05 --runs 5 -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-842-llmxive-follow-up-extending-dvao-dynamic/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-842-llmxive-follow-up-extending-dvao-dynamic/run_experiment.py': [Errno 2] No such file or directory
- python code/src/derivation/sample_complexity.py --output docs/theoretical_derivation.md -> rc=1
    Starting Sample Complexity Derivation...

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-842-llmxive-follow-up-extending-dvao-dynamic/code/src/derivation/sample_complexity.py", line 260, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-842-llmxive-follow-up-extending-dvao-dynamic/code/src/derivation/sample_complexity.py", line 231, in main
    result = derive_sample_complexity_bound()
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-842-llmxive-follow-up-extending-dvao-dynamic/code/src/derivation/sample_complexity.py", line 118, in derive_sample_complexity_bound
    variance_data = derive_variance_accumulation()
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: derive_variance_accumulation() missing 1 required positional argument: 'N'

## Declared deliverables still missing

- data/processed/empirical_results.json
- data/processed/statistical_report.json

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `mo-gymnasium` to the project's `requirements.txt` and `pip install mo-gymnasium`.
- **Verified**: this loads **118** real records with fields: state, action, reward, episode_id, next_state, done.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import mo_gymnasium as mg

# Use a valid environment name that exists in the package
env = mg.make("CartPole-v1")

records = []
for episode_id in range(2):
    obs, info = env.reset()
    done = False
    while not done:
        action = env.action_space.sample()
        next_obs, reward, terminated, truncated, info = env.step(action)
        done = terminated or truncated
        records.append({
            "state": obs,
            "action": action,
            "reward": reward,
            "episode_id": episode_id,
            "next_state": next_obs,
            "done": done,
        })
        obs = next_obs

print(f"RECORDS={len(records)}")
print("FIELDS=state,action,reward,episode_id,next_state,done")
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `derive_variance_accumulation` — defined in `code/src/derivation/variance_scaling.py`; called 4 way(s):

- code/src/derivation/variance_scaling.py: result = derive_variance_accumulation(N)
- code/src/derivation/variance_scaling.py: result = derive_variance_accumulation(N_test)
- code/src/derivation/sample_complexity.py: variance_data = derive_variance_accumulation()
- code/src/derivation/symbolic_verification.py: derived_expr = derive_variance_accumulation()

Make `derive_variance_accumulation` in `code/src/derivation/variance_scaling.py` accept ALL of the above.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/empirical_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/main.py` — NOT invoked by the run-book
    - `code/src/analysis/stats.py` — NOT invoked by the run-book
    - `code/src/environment/runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/empirical_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/statistical_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/main.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/statistical_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
