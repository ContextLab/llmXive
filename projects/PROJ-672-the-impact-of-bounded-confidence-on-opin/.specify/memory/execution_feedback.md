# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/generate_networks.py --output data/raw/networks/ --seeds 50`
  - script usage: `generate_networks.py [-h] --topology {ER,BA,WS} [--instances INSTANCES]`
  - argparse error: `generate_networks.py: error: the following arguments are required: --topology`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python code/simulate_hk.py  --networks data/raw/networks/  --epsilon-start 0.05  --epsilon-end 0.50  --epsilon-step 0.05  --seeds 50  --output data/raw/simulations/; python code/analyze_scaling.py  --simulations data/raw/simulations/  --networks data/raw/networks/  --output data/processed/; 3 command(s) failed: python code/generate_networks.py --output data/raw/networks/ --seeds 50 (rc=2); python -m pytest tests/unit/test_hk_update.py -v (rc=4); python -m pytest tests/integration/test_full_pipeline.py -v (rc=4)

## Failing / missing run-book commands

- python code/generate_networks.py --output data/raw/networks/ --seeds 50 -> rc=2

usage: generate_networks.py [-h] --topology {ER,BA,WS} [--instances INSTANCES]
                            [--seed SEED]
generate_networks.py: error: the following arguments are required: --topology

- python code/simulate_hk.py  --networks data/raw/networks/  --epsilon-start 0.05  --epsilon-end 0.50  --epsilon-step 0.05  --seeds 50  --output data/raw/simulations/ -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-672-the-impact-of-bounded-confidence-on-opin/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-672-the-impact-of-bounded-confidence-on-opin/code/simulate_hk.py': [Errno 2] No such file or directory

- python code/analyze_scaling.py  --simulations data/raw/simulations/  --networks data/raw/networks/  --output data/processed/ -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-672-the-impact-of-bounded-confidence-on-opin/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-672-the-impact-of-bounded-confidence-on-opin/code/analyze_scaling.py': [Errno 2] No such file or directory

- python -m pytest tests/unit/test_hk_update.py -v -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.6.0 -- /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-672-the-impact-of-bounded-confidence-on-opin/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-672-the-impact-of-bounded-confidence-on-opin
configfile: pytest.ini
collecting ... collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/unit/test_hk_update.py


- python -m pytest tests/integration/test_full_pipeline.py -v -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.6.0 -- /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-672-the-impact-of-bounded-confidence-on-opin/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-672-the-impact-of-bounded-confidence-on-opin
configfile: pytest.ini
collecting ... collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/integration/test_full_pipeline.py


## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
