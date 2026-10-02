# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T000** — The required `research.md` file is not present in the provided evidence, and therefore none of the mandated sections (e.g., Project requirements, Feature Specification, User Scenarios & Testing) can be verified. The implementer must create a non‑empty `research.md` containing all specified sections and details.
- **T001c** — No `utils/data_loader.py` file containing a `verify_urls(urls: List[str])` implementation is provided, nor is a unit test for this function shown. The required code and its test are missing, so the task is not satisfied.
- **T001d** — No code defining `download_and_checksum(dataset_name, dest_path)` or the accompanying unit test was provided; the required SHA‑256 file generation artifact is missing, so the task’s deliverable cannot be confirmed.
- **T131** — declared artifact(s) missing/empty/invalid: results/trajectory.json
- **T124** — No evidence of a modified `utils/logging.py` was provided, nor any sample log output showing the required “Authority Trace” entries with benchmark scores, oracle results, and human constraints. The artifact is missing, so the task’s logging requirement has not been demonstrated.
- **T125** — No code changes to `pipeline/evaluator.py` or accompanying unit test are provided; thus we cannot confirm that a read‑only, immutable benchmark loading mechanism was added or that a test asserting failure on modification exists. The required artifact is missing.
- **T126** — No code changes to `pipeline/attempt_tracker.py` implementing the rollback state machine are provided, nor is an integration test that simulates a degradation event and checks the cycle counter and new modification. The required artifact and verification are missing.
