# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T035** — The `reporting.py` file only defines loading helpers and a partial table generator, but it never assembles a full markdown report or writes it to `final_report.md`. It also contains a placeholder comment for partial‑dependence plots and the code is truncated, so the required final‑report generation functionality is missing.
- **T036** — No CI configuration, timing logs, or rendered PDF/Markdown artifacts are provided to demonstrate that the final report can be generated within 30 seconds on the CI system. The required evidence to validate the rendering performance is missing.
- **T037** — No `research.md` file or its contents were provided; without the updated document containing the final findings and limitations, the task requirement cannot be verified as satisfied.
- **T038** — No execution logs, timing measurements, or output from `main.py` are provided; without a recorded run showing the full pipeline completing in ≤ 600 seconds, the claim cannot be verified. The implementer must supply evidence of the integration test (e.g., console output, a benchmark report, or a CI log) demonstrating the end‑to‑end run time.
- **T039** — No artifact (e.g., validation log, report, or updated quickstart.md) is provided to demonstrate that the quickstart.md validation was actually executed; the claim lacks any concrete evidence. The required output is missing.
