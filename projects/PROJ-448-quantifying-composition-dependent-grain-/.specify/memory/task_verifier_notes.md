# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T013** — The required file `data/raw/dft_energies.json` does not exist, yet `SurrogateService._load_data` falls back to a placeholder instead of raising a hard error as the task mandates. Consequently the service does not strictly enforce the “raise error if missing” constraint and cannot guarantee loading real DFT energies. The implementation therefore does not satisfy the task’s core requirement.
- **T018** — declared artifact(s) missing/empty/invalid: data/processed/segregation_profiles.json
- **T021a** — No code, data, or result files were provided that show interaction terms were generated, a regression model was built, or statistical metrics (p‑values, MSE reduction) were computed. Consequently the required evidence for User Story 2 is missing.
- **T022** — No code, script, or log file was provided that implements the MSE comparison, prints the required “MSE reduction: X% (Threshold: 10%)” message, or raises a warning when the reduction is ≤10 %. Without these artifacts the task’s requirement cannot be verified.
- **T023** — No code, script, notebook, test results, or any other artifact demonstrating that significance testing (p‑value < 0.05) for interaction coefficients has been implemented is present. The claim lacks the required implementation and verification output, so the task requirement is not satisfied.
- **T024b** — declared artifact(s) missing/empty/invalid: data/figures/segregation_heatmap.png
- **T025** — declared artifact(s) missing/empty/invalid: data/processed/cooperative_effects_analysis.json
- **T026** — No code, script, module, or test output was provided that implements the required “flag systems where no significant cooperative effects are detected” logic, nor any evidence that it runs after T025. The artifact is missing entirely, so the task is not satisfied.
