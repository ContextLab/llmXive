# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T008** — No `utils/logging.py` file (or any non‑empty implementation) was presented in the evidence. Without the required module containing the standardized error handling and progress‑logging code, the task is not satisfied. The next implementer must add a functional `utils/logging.py` with the specified logging utilities.
- **T009** — declared artifact(s) missing/empty/invalid: data/ingestion.py
- **T014** — declared artifact(s) missing/empty/invalid: data/ingestion.py
- **T015** — declared artifact(s) missing/empty/invalid: data/ingestion.py
- **T016** — declared artifact(s) missing/empty/invalid: data/preprocessing.py
- **T017** — declared artifact(s) missing/empty/invalid: data/preprocessing.py
- **T018** — No code, configuration, or documentation showing that 403 HTTP errors are caught and handled, nor any logic that detects and warns when a dataset contains fewer than 500 points, was provided. The required error‑handling implementation and associated tests or logs are missing.
- **T019** — declared artifact(s) missing/empty/invalid: data/processed/cleaned_slr_data.csv, data/processed/.checksums.json
- **T023** — declared artifact(s) missing/empty/invalid: models/dynamics.py
- **T024** — declared artifact(s) missing/empty/invalid: models/estimator.py
- **T025** — No code defining `extract_joint_parameters` or any related file was provided; the required function, its return dictionary, and the extraction of `ac`, `g`, and covariance from an `OrbitSolution` are absent. The task therefore lacks the necessary artifact.
- **T026** — No `analysis/eotvos.py` file was presented, and there is no evidence that such a module exists or contains the required logic to compute η = |a_c| / g and its 95 % confidence interval from the joint covariance matrix. The task therefore remains unfulfilled.
- **T027** — No code, script, or documentation implementing the required fallback logic (relax tolerance, log warning, output best‑fit) was provided; the evidence consists only of the task description and specifications, with no tangible artifact to verify that the feature was actually built. The implementer must supply the implementation (e.g., source file, unit tests, and example run logs) for review.
- **T028** — declared artifact(s) missing/empty/invalid: data/results/orbit_solutions.json, data/results/eotvos_metrics.json
- **T032** — No `analysis/validation.py` file or its contents were presented, and there is no evidence that the required F‑test and BIC model‑comparison functionality has been implemented. The task’s deliverable is missing, so the requirement is not satisfied.
