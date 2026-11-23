# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007A** — The required artifact `data/validation/log_age_column.json` does not exist, so the pipeline cannot have logged the missing‑age error nor halted as specified. Without this file (or any evidence of the halt), the task’s core requirement is unmet.
- **T007B** — declared artifact(s) missing/empty/invalid: data/validation/source_verification.log
- **T001A** — The repository does not contain the required directories (`data/raw`, `data/processed`, `logs`, `paper/figures`) – only the `plan.md` file is present, and no evidence of those folders being created is provided. The implementer must add the missing directories at the repository root.
- **T001B** — No evidence was provided showing that the required directories `code/analysis` and `code/tests` actually exist (or contain any files). The implementer’s claim cannot be verified without such artifacts.
- **T002** — The provided `requirements.txt` lists the required packages but does not pin their versions, and there is no evidence that `pip check` was run or that the environment integrity was verified. Both version pinning and verification are required by the task.
- **T006A** — declared artifact(s) missing/empty/invalid: code/contracts/dataset.schema.yaml
- **T006B** — declared artifact(s) missing/empty/invalid: code/contracts/output.schema.yaml
- **T009** — declared artifact(s) missing/empty/invalid: code/config.yaml, code/logs/url_verification.log
- **T019A** — declared artifact(s) missing/empty/invalid: code/logs/haplogroup_success_rate.txt
- **T052** — declared artifact(s) missing/empty/invalid: code/logs/memory_profile.log
