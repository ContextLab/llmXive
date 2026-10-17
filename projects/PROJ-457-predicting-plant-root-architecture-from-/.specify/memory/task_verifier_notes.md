# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The `directory_structure.txt` file exists, but it is placed inside the project subdirectory (`projects/PROJ-457‑.../directory_structure.txt`) while the CI test `tests/test_directory_structure.py` looks for the file two levels up (`projects/directory_structure.txt`). Consequently both test assertions fail, so the required verification artifact is not in the expected location. Relocate or duplicate `directory_structure.txt` to the path the test checks (or adjust the test) to satisfy the task.
- **T002** — The `code/requirements.txt` file exists and contains pinned versions, but there is no provided evidence that `pip install -r code/requirements.txt` was executed and exited with code 0 as required. The implementer must supply execution logs or test results confirming a successful installation.
- **T003** — Requested task execution failed; rerun successfully: code/run_lint.py exit=1
