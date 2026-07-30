# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T009** — No configuration files, scripts, or code were provided that set up environment management, load random seeds, or define config paths. The claim lacks any tangible artifact demonstrating that these requirements have been implemented.
- **T010** — The provided evidence only describes a Monte Carlo simulation feature for confidence‑interval coverage; there is no code, configuration, or documentation showing deterministic random‑seed handling across the project’s modules. The required seed‑management implementation is missing.
- **T011** — No code, script, or documentation for generating checksums on raw data creation was provided; the only artifacts described relate to Monte Carlo simulation of confidence intervals, which do not address the checksum requirement. The task T011 remains unimplemented.
- **T012** — No schema files were presented for `data-models/schemas/`, and there is no evidence that definitions for SimulationRun, CoverageRecord, or AggregateReport exist or contain any fields. The required artifacts are missing, so the task is not satisfied.
- **T016** — No evidence of a downloader script, nor any files in `data/raw/` for the five required UCI datasets, is provided. The implementer has not supplied the code that fetches the real numeric datasets or the resulting saved files, so the task is not satisfied.
- **T017** — No code, script, or documentation for a data‑loader that parses downloaded UCI datasets and detects continuous numeric variables was supplied. The artifact required by task T017 is missing, so the requirement is not satisfied.
- **T033** — declared artifact(s) missing/empty/invalid: outputs/aggregate_report.md
