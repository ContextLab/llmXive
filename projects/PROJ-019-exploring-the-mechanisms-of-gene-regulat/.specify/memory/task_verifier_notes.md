# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The repository contains a `requirements.txt` with all listed packages, but the provided test (`tests/test_requirements_install.py`) fails because it looks for the file in the wrong location and never demonstrates a successful `pip install -r requirements.txt` in a fresh virtualenv. Without evidence that the install command runs and exits with code 0, the task’s verification condition is not met.
