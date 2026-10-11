# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — The `requirements.txt` file exists, but the recorded unit‑test shows that `pip install -r code/requirements.txt` fails in a clean environment because the pinned version `opencv-python-headless==4.8.0` has no compatible wheel for Python 3.11, causing the installation to abort. The task’s verification condition (successful install) is therefore not met.
- **T005** — The provided `code/config.py` defines the required constants, but it imports `utils.logging` and `utils.errors` using a top‑level `utils` package that does not exist (the utilities live in `code/utils`). Consequently, `import code.config` would raise a `ModuleNotFoundError`, so the verification step “importing `code.config` yields the expected attributes” cannot succeed. The import paths must be corrected (e.g., `from code.utils.logging import …`) for the module to be importable and satisfy the task.
- **T006** — Requested task execution failed; rerun successfully: code/utils/dummy_logger_test.py exit=5
