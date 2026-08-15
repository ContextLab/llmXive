# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T013** — declared artifact(s) missing/empty/invalid: tests/unit/test_schema.py
- **T008** — No `config.py` file was presented in the evidence, and therefore there is nothing to load or check for the required hyperparameters, parameter‑increase constraint, or path definitions. The implementer must supply a non‑empty `config.py` that defines `lr=5e-5`, `bs=4`, a seed, enforces the ≤30 % parameter‑increase limit, and includes the specified path variables, and it must load without error and assert the default values.
- **T009** — No `utils/logging.py` file or any generated log file is provided for inspection, so we cannot confirm that a structured JSON log is created after a mock cycle. The required artifact and its functional verification are missing.
- **T010** — No `pipeline/evaluator.py` file or corresponding unit test is present in the provided evidence; therefore the required benchmark runner and evaluation logic, as well as the mocked‑dataset test asserting accuracy/ECE, are missing. The implementer must add the module and its test to satisfy T010.
