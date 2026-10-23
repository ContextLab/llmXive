# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T000** — The provided `setup_env.py` creates a virtual environment, validates `requirements.txt` against its schema, and the test suite checks that `pandas` can be imported, but the script never runs `pip install -r requirements.txt`; it only verifies that `pip` is available. Consequently the requirement “install pinned dependencies from `requirements.txt`” is not fulfilled. Implement a real installation step (e.g., `subprocess.run([pip_path, "install", "-r", str(requirements_path)])`) and adjust the test to confirm that the packages were installed.
- **T001** — Requested task execution failed; rerun successfully: code/data/fetch_heas.py exit=1
