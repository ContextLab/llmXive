# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T014** — declared artifact(s) missing/empty/invalid: tests/unit/test_synthetic_data.py
- **T021** — The required artifact `tests/unit/test_edge_density.py` does not exist in the repository, so no unit test for edge density calculation is present. The task cannot be considered completed until this file is added with appropriate tests verifying that edge density values are normalized to the [0, 1] range.
- **T022** — The required artifact `tests/unit/test_color_entropy.py` does not exist in the repository, so no unit test for the color entropy calculation is present. The task’s deliverable is missing entirely.
- **T023** — The required artifact `tests/unit/test_object_count.py` does not exist in the repository, so the unit test for object count handling cannot be verified. The task remains unfinished until the file is added with the appropriate test code.
- **T046** — No `quickstart.md` file or excerpt was provided, and there is no evidence that it has been updated to explain the synthetic data fallback or the associational framing. The required documentation change is missing.
- **T047** — No code files, diff, lint reports, or any documentation showing that the repository was cleaned up or refactored to meet PEP8 standards were provided. The evidence only contains the unrelated feature specification for visual distraction research, with no artifacts demonstrating the claimed code cleanup. The required deliverable—a PEP8‑compliant codebase or proof thereof—is missing.
- **T048** — No profiling logs, timing reports, or benchmark results for `01_data_acquisition.py` and `02_visual_metrics.py` are present, so there is no evidence that the combined runtime is ≤ 6 hours on CPU cores. The required artifact (runtime verification) is missing.
