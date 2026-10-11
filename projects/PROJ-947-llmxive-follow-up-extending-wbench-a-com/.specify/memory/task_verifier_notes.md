# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — The only execution evidence (`tests/unit/test_requirements.py` log) shows `pip install -r code/requirements.txt` FAILED (exit 1, opencv-python-headless==4.8.0 not found); the current file pins 4.7.0.72 instead, but there is no re-run or fresh evidence that the install now succeeds. Additionally, the current pins are internally suspect: pandas==2.0.0 predates numpy 2.x support (numpy==2.0.0 will break it), so the verification criterion "pip install succeeds in a clean venv" is not demonstrated. Fix the pins (e.g., numpy<2 or pandas≥2.2.2) and provide a passing install/test run.
- **T006** — Requested task execution failed; rerun successfully: code/utils/dummy_logger_test.py exit=5
