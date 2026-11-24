# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/simulation_runner.py --icc 0.1 --alpha 0.05 --iterations 100`
  - script usage: `simulation_runner.py [-h] [--icc-range ICC_RANGE] [--icc-step ICC_STEP]`
  - argparse error: `simulation_runner.py: error: ambiguous option: --icc could match --icc-range, --icc-step`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python code/simulation_runner.py (rc=-1); python code/simulation_runner.py --icc 0.1 --alpha 0.05 --iterations 100 (rc=2); python -m pytest tests/ -v (rc=2)

## Failing / missing run-book commands

- python code/simulation_runner.py -> rc=-1
c[pos]`
  p_value = results.pvalues[1]
/home/runner/work/llmXive/llmXive/projects/PROJ-239-evaluating-the-statistical-significance-/code/estimators.py:123: FutureWarning: Series.__getitem__ treating keys as positions is deprecated. In a future version, integer keys will always be treated as labels (consistent with DataFrame behavior). To access a value by position, use `ser.iloc[pos]`
  p_value = results.pvalues[1]
/home/runner/work/llmXive/llmXive/projects/PROJ-239-evaluating-the-statistical-significance-/code/estimators.py:123: FutureWarning: Series.__getitem__ treating keys as positions is deprecated. In a future version, integer keys will always be treated as labels (consistent with DataFrame behavior). To access a value by position, use `ser.iloc[pos]`
  p_value = results.pvalues[1]
/home/runner/work/llmXive/llmXive/projects/PROJ-239-evaluating-the-statistical-significance-/code/estimators.py:123: FutureWarning: Series.__getitem__ treating keys as positions is deprecated. In a future version, integer keys will always be treated as labels (consistent with DataFrame behavior). To access a value by position, use `ser.iloc[pos]`
  p_value = results.pvalues[1]

[TIMEOUT after 120s]
- python code/simulation_runner.py --icc 0.1 --alpha 0.05 --iterations 100 -> rc=2
llmXive/projects/PROJ-239-evaluating-the-statistical-significance-/code/simulation_runner.py:30: DeprecationWarning: 
Pyarrow will become a required dependency of pandas in the next major release of pandas (pandas 3.0),
(to allow more performant data types, such as the Arrow string type, and better interoperability with other libraries)
but was not found to be installed on your system.
If this would cause problems for you,
please provide us feedback at https://github.com/pandas-dev/pandas/issues/54466
        
  import pandas as pd
usage: simulation_runner.py [-h] [--icc-range ICC_RANGE] [--icc-step ICC_STEP]
                            [--alpha-list ALPHA_LIST] [--alpha ALPHA]
                            [--cluster-mean CLUSTER_MEAN]
                            [--cluster-std CLUSTER_STD]
                            [--n-clusters N_CLUSTERS]
                            [--n-obs-per-cluster N_OBS_PER_CLUSTER]
                            [--seed SEED] [--iterations ITERATIONS]
                            [--n-permutations N_PERMUTATIONS]
                            [--output OUTPUT] [--verbose]
simulation_runner.py: error: ambiguous option: --icc could match --icc-range, --icc-step

- python -m pytest tests/ -v -> rc=2
/../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92
../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92
../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92
../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92
  /home/runner/.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92: PyparsingDeprecationWarning: 'resetCache' deprecated - use 'reset_cache'
    parser.resetCache()

../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_mathtext.py:45
  /home/runner/.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_mathtext.py:45: PyparsingDeprecationWarning: 'enablePackrat' deprecated - use 'enable_packrat'
    ParserElement.enablePackrat()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/unit/test_uci_ingest.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
======================== 15 warnings, 1 error in 1.08s =========================


## Platform-owned paths written inside the project

A script in this project created `.github/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
