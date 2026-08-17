# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory listings, `ls` output, or other evidence were provided to show that the required folders under `projects/PROJ-236-exploring-the-influence-of-network-topol/` (e.g., `code/utils`, `code/tests/unit`, `data/raw`, etc.) actually exist. Without such proof the verification condition cannot be satisfied.
- **T003** — No linting/formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`) or command‑line output logs are provided, and there is no evidence that `ruff --quiet` and `black --check` were run successfully on the `code/` directory. The required artifacts and verification results are missing.
- **T009** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T010** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T011** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T017** — No CI script or related code was provided; the claim that a verification script exists that reads connectivity metrics and aborts the build when the overall success rate falls below 95% after retries cannot be confirmed. The required artifact is missing.
- **T018** — The implementer supplied only a unrelated feature specification about network topology and heat transport, with no CI configuration, test results, or any evidence of a “Physical Stability Filter” pass‑rate check. Consequently, the required artifact (CI check ensuring >5 % seed rejection causes failure) is missing.
- **T019** — The implementer provided only a textual description of the intended verification and did not supply any actual artifact (e.g., CI configuration, unit‑test code, or test output) demonstrating that a CI assertion fails when the distance‑cutoff scaling is incorrect. Without concrete code or results, the requirement for a verifiable CI‑based check is not met.
- **T020** — The claim provides no actual artifact—no test script, checksum‑recomputation code, or `data/` directory contents are presented. Without concrete files or code that loops over saved artifacts and validates their checksums, the verification task is not satisfied. The implementer must supply the automated test implementation and the relevant data files.
- **T025** — The repository lacks the required `simulation_config.yaml` file, and the provided `code/generate_networks.py` does not show an ensemble‑generation loop, a cutoff‑sweep implementation, or any code that writes per‑realization `meta.json` logs. Consequently the task’s core requirements are not satisfied.
- **T025c** — declared artifact(s) missing/empty/invalid: data/analysis/sensitivity_results.csv
- **T026** — No code, configuration, or CI test artifacts were presented that enforce a ≥95 % connectivity success rate, abort generation when the threshold is missed, or log failing IDs. The required implementation and verification steps are missing.
- **T027** — declared artifact(s) missing/empty/invalid: state/projects/PROJ-236-exploring-the-influence-of-network-topol.yaml
- **T028** — declared artifact(s) missing/empty/invalid: data/processed/pilot_data/pilot_metrics.csv
- **T059** — declared artifact(s) missing/empty/invalid: tests/unit/test_network_gen.py
