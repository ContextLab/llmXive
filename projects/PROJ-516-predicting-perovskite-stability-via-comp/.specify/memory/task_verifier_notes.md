# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — the task writes platform-owned path(s) inside the project: `state/` (shadows `state/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T002** — The `code/requirements.txt` file exists and contains the required pinned versions, but the recorded test (`tests/test_requirements_install.py`) shows that `pip install -r code/requirements.txt` fails (exit code 1) because the specified `mp-api==0.38.5` cannot be installed in the Python 3.11 environment. The installation must succeed in a fresh virtual environment for the task to be considered complete.
- **T038** — Requested task execution failed; rerun successfully: code/state_manager.py exit=1
