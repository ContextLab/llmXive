# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No `spec_amendments.patch` file or modified `spec.md` is present in the provided evidence, and the task description lists the required changes as “<!-- FAILED: unspecified -->”, indicating that the implementer did not supply the concrete diff or apply it. Consequently, the required artifact is missing.
- **T009** — declared artifact(s) missing/empty/invalid: state/projects/PROJ-527-evaluating-the-impact-of-prompt-complexi.yaml
- **T024** — No `runner.py` file or diff showing added exception handling was provided, and there is no evidence of samples being marked as failed or error types being logged. The required code changes are missing, so the task is not satisfied.
- **T025** — No evidence of a modified `runner.py` implementing timeout handling is provided; the artifact is missing, empty, or not shown, so the requirement to mark problems as failed after exceeding a time threshold is not satisfied.
- **T027** — I looked for the required documentation artifacts – comments in `static_analysis.py` citing McCabe and other literature, and corresponding entries in `research.md`. No such files or content were presented, so the claimed documentation does not exist or cannot be verified. The task remains unfinished.
- **T029** — No `static_analysis.py` file or diff showing added vulnerability flagging (hardcoded credentials, eval usage) is provided; without any code artifact we cannot confirm the feature was implemented or that samples are marked for manual review instead of causing test failures. The required implementation is missing.
- **T030** — declared artifact(s) missing/empty/invalid: data/results/execution_outcomes.csv
- **T034** — No `stats.py` file or code showing a Bonferroni or Holm‑Bonferroni correction was provided; without the actual implementation we cannot confirm that the adjusted significance threshold (α ≤ 0.05 / number of tests) was added. The required artifact is missing.
