# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007s** — No logs, command output, or any other artifact showing that `libfftw3-dev` was installed or that `fftw3-config --version` was run successfully are present. Without such evidence the requirement to install and verify the system dependency cannot be confirmed.
- **T006a** — No evidence of the required directory structure (`code/{data_generation,training,evaluation,utils}`, `data/{raw,processed}`, `tests/{unit,contract,integration}`, `specs/001-predict-stiffness-cnn/contracts`) or a `tree` command output is provided, so we cannot confirm the directories were created as specified. The implementer must supply the actual directory listing or command output showing the tree and a successful exit code.
- **T012** — declared artifact(s) missing/empty/invalid: schema.yaml
