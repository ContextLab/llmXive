# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required directory tree `projects/PROJ-normalized-gaps-between-consecutive-squa/...` is provided; the “Actual artifacts / evidence on disk” section is empty, so we cannot confirm that the directories were created. The implementer must supply a listing or screenshot showing the full path hierarchy.
- **T002** — declared artifact(s) missing/empty/invalid: projects/PROJ-722-normalized-gaps-between-consecutive-squa/requirements.txt
- **T003** — declared artifact(s) missing/empty/invalid: projects/PROJ-722-normalized-gaps-between-consecutive-squa/pyproject.toml
- **T006** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T010** — The test file `tests/contract/test_squarefree_sequence.py` is present, but it references `contracts/SquarefreeSequence.schema.yaml`, which does not exist in the repository, causing the test to fail with a FileNotFoundError. The required schema file must be added for the test to genuinely validate JSON against it.
- **T018** — The `tests/contract/test_test_result.py` file is present and contains a test that attempts to load `contracts/TestResult.schema.yaml`, but the required schema file does not exist in the repository, causing the test to fail (FileNotFoundError). The missing schema means the test cannot actually validate any JSON against the contract.
