# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T036** — No code, benchmark results, or profiling data were provided to demonstrate that the perturbation‑sweep loop was rewritten with vectorized operations or that its runtime improved. The claim lacks any concrete artifact (e.g., updated source file, performance comparison table, or timing logs), so the requirement is not satisfied.
- **T037** — No evidence of new unit test files in `tests/unit/` was provided, and there are no visible tests covering the specified edge cases (normality violation, no valid sigma). The required artifact—a set of additional unit tests for those scenarios—is missing.
- **T038** — The provided artifacts relate to a latent‑vector noise‑injection experiment and contain no code, configuration, or test results showing that logs or output files have been audited or stripped of PII. There is no evidence of security‑hardening changes, log‑scrubbing mechanisms, or verification that no personal data can be leaked, so the task requirement is unmet.
