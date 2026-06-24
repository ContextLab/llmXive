# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 35 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- No task in tasks.md is explicitly linked to Functional Requirement FR-001 (download GEO count matrices).
- Functional Requirement FR-002 (normalization via TPM or VST) lacks a corresponding task tag or description.
- Functional Requirement FR-003 (CPM filtering) is not covered by any task in tasks.md.
- Functional Requirement FR-004 (Pearson correlation with threshold ≥ 0.8) has no dedicated task entry.
- Functional Requirement FR-005 (gene‑to‑STRING identifier mapping) is not represented by any task.
- Functional Requirement FR-006 (evaluation against STRING high‑confidence set) is missing from the task list.
- Functional Requirement FR-007 (degree‑preserving random‑graph baseline) is not mapped to any task.
- Functional Requirement FR-008 (GO enrichment) lacks a corresponding task.
- Functional Requirement FR-009 (Makefile orchestration and ≤ 6 h runtime) is not explicitly covered by any task.
- Functional Requirement FR-010 (central logging) is not linked to any task.
- Functional Requirement FR-011 (per‑species edge‑list output) is missing from the task list.
- Functional Requirement FR-012 (global `--seed` flag for reproducibility) has no dedicated task.
- Success Criterion SC-001 (AUROC ≥ 0.70 and AUPRC ≥ 0.65) is not referenced by any task or test.
- Success Criterion SC-002 (at least one GO term with adjusted p < 0.05) lacks a task or test mapping.
- Success Criterion SC-003 (pipeline runtime ≤ 6 h) is not covered by any explicit performance‑benchmark task.
- Success Criterion SC-004 (reproducibility with fixed seed) has no task ensuring deterministic output verification.
- Success Criterion SC-005 (presence and parsability of all required output files) is not tied to any validation task.
- Task T038 (CI reproducibility step) is still marked `[P]` but consumes all pipeline output files produced by earlier Makefile targets. It must run after those targets; the `[P]` annotation is therefore inaccurate.
- Task T056 (validation script extension) asserts presence of all required output files and therefore depends on those files. It cannot be safely parallelised; the `[P]` flag should be removed.
- Task T064 (documentation build verification) runs `mkdocs build` and must occur after all documentation‑generation tasks. Marking it `[P]` is incorrect; remove the flag or enforce proper ordering.
- Duplicate task identifiers detected: T064 is used for both the GEO downloader (US1) and the documentation‑build verification step, and T031 appears in both Phase 3 and Phase 6. Task IDs must be unique to preserve a deterministic execution order.
- Task T001 creates repository skeleton directories but does not specify a verification step (e.g., a test that asserts the directories exist). Without a concrete verification artifact the task is not deterministically executable.
- Task T002 initializes a Python project (pyproject.toml, requirements.txt) but lacks a verification artifact (e.g., a test that checks both files are present and contain the expected pinned dependencies).
- Task T003 sets up an R environment with renv.lock and installs Bioconductor packages, yet no verification is defined to confirm the lockfile was created and the packages are installed.
- Task T004 adds linting/formatting configuration (ruff, black, styler) but does not include a test or CI step that runs the linters to prove the configuration works.
- Task T005 adds a CI workflow file `.github/workflows/ci.yml` but provides no verification that the workflow triggers correctly (e.g., a CI smoke‑test or a test that checks the file exists and contains the expected `make validate` command).
- Task T006 creates a central logger module but does not define a test that confirms the module writes ISO‑8601 timestamps to `pipeline.log` as specified.
- Task T007 implements the CLI entry point but lacks a verification artifact (e.g., a unit test that checks argument parsing for `--norm-method`, `--threshold`, `--seed`, `--species`).
- Task T008 writes a Makefile with several targets but does not include a test that confirms each target (`all`, `evaluate`, `enrich`, `clean`, `validate`, `sensitivity`, `reproducibility-check`) executes without error.
- Task T009 creates configuration files (`species.yaml`, `parameters.yaml`) without a verification step that checks the files are syntactically valid YAML and contain required default keys.
- Task T010 implements schema files in `contracts/` but provides no test that validates a sample result file against these schemas.
- Task T012 adds a CLI argument validator enforcing `--threshold` ≥ 0.8, yet no unit test is defined to verify that values below 0.8 are rejected and values ≥ 0.8 are accepted.
- Task T013 implements a citation verification step invoking the Reference‑Validator Agent, but there is no CI test that confirms the agent runs and fails the pipeline on mismatched citations.
- The newly added verification task T072 (documentation lint test) only checks for the existence of `docs/false_positives.md` and required sections, but does not verify that the Poisson derivation content is *accurate* (e.g., matches a reference implementation). This leaves the original concern about content correctness only partially addressed.
- The specification (SC-001) permits AUROC ≥ 0.70, whereas the constitution (VII) mandates AUROC > 0.70. This creates a mismatch that weakens the required performance threshold.
