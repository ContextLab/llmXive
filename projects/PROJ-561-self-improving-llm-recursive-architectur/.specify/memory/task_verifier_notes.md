# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T005c** — No `pipeline/loader.py` file with a fail‑fast wrapper raising `FileNotFoundError` is present, and no unit test asserting that the exception is raised for missing files was provided. The required code change and corresponding test are missing.
- **T008** — No `config.py` file was presented in the evidence, and therefore there is nothing to load or check for the required hyperparameters, parameter‑increase constraint, or path definitions. The implementer must supply a non‑empty `config.py` that defines `lr=5e-5`, `bs=4`, a seed, enforces the ≤30 % parameter‑increase limit, and includes the specified path variables, and it must load without error and assert the default values.
- **T009** — No `utils/logging.py` file or any generated log file is provided for inspection, so we cannot confirm that a structured JSON log is created after a mock cycle. The required artifact and its functional verification are missing.
- **T010** — No `pipeline/evaluator.py` file is present, nor any unit test that mocks datasets and checks accuracy/ECE calculations. The required benchmark runner implementation and its verification test are missing, so the task is not satisfied.
- **T059a** — declared artifact(s) missing/empty/invalid: tests/unit/test_validator.py
- **T017c** — declared artifact(s) missing/empty/invalid: tests/unit/test_metrics.py
