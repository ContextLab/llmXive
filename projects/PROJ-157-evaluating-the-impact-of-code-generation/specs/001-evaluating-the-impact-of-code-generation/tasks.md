# Tasks: Evaluating the Impact of Code Generation Models on Code Security

**Inputs**: `spec.md`, `plan.md`, original research idea, reviewer feedback.  

All tasks are unchecked; each includes the artifact paths it creates or modifies and the verification steps required to satisfy the corresponding functional and success‑criteria requirements.

---

- [ ] T000 [P1] [US1] Set up deterministic environment and pin random seeds. <!-- FAILED-IN-EXECUTION: code/setup_env.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/setup_env.py exit=1 -->
  *Implementation*: `code/setup_env.py` → writes `data/env_config.json` and configures the Docker environment.
  *Verification*:
   · Confirm that all random seeds are pinned in `code/` and recorded in `data/env_config.json`.
   · Verify the Docker image digest matches the pinned version in `plan.md`.

- [ ] T001 [P1] [US1] Acquire human reference C++ solutions from the Codeforces benchmark.  
  *Implementation*: `code/download_human.py` → writes `data/raw/codeforces_cpp.jsonl`.  
  *Verification*:  
  · Run the script and confirm ≥ 50 distinct `problem_id`s are present.  
  · Verify the SHA‑256 checksum of the downloaded archive matches the value recorded in `plan.md`.  
  · Ensure each entry contains a compilable C++ source string (`human_code`).

- [ ] T002 [P1] [US1] Generate LLM variants for each problem using CodeLlama‑7B‑Instruct and StarCoder‑15B via the HuggingFace inference API.  
  *Implementation*: `code/generate_llm_variants.py` → writes `data/generated/codellama/variants.jsonl` and `data/generated/starcoder/variants.jsonl`.  
  *Verification*:  
  · For every `problem_id` that succeeded, the entry contains a non‑empty source string under `llm_code["codellama"]` / `llm_code["starcoder"]`.  
  · Log all failed generations to `log/llm_generation_fail.log`; ensure failed IDs are excluded from the final paired dataset.

- [ ] T003 [P1] [US1] Consolidate human and LLM sources into a validated `ProblemPair` collection.  
  *Implementation*: `code/create_problem_pairs.py` → produces `data/raw/problem_pairs_v{hash}.jsonl` conforming to `contracts/problem_pair.schema.yaml`.  
  *Verification*:  
  · Run schema validation (`pytest tests/test_problem_pair_schema.py`).  
  · Count that each retained `ProblemPair` has a `human_code` field and LLM fields for both models (or records a `generation_failed` flag).  
  · Ensure the pair‑integrity rate ≥ 95 % (SC‑005).

- [ ] T004 [P2] [US2] Deterministically compile every source (human and LLM) with flags `-O0 -g` and ASan + UBSan inside a pinned Docker container and record compilation status.  
  *Implementation*: `code/compile_and_fuzz.py` → writes compilation metadata to `data/compiled/compile_status_v{hash}.jsonl` and successful binaries to `data/compiled/binaries/`.  
  *Verification*:  
  · All entries have `execution_status` either `"success"` or `"compile_fail"` (FR‑002, FR‑003).  
  · Verify that binaries are compiled using exactly the `-O0 -g` flags mandated by FR-002 and Constitution VI.
  · Overall compile‑failure rate ≤ 5 % (SC‑005).

- [ ] T005 [P2] [US2] Auto‑generate a libFuzzer harness (`LLVMFuzzerTestOneInput`) for each compiled binary, compile with coverage instrumentation (`-fsanitize-coverage`), and rebuild the instrumented binary.  
  *Implementation*: `code/generate_fuzz_harness.py` → stores harness source files in `code/harness_templates/` and final fuzzable binaries in `data/compiled/fuzz_binaries/`.  
  *Verification*:  
  · Confirm binaries are built with `-fsanitize-coverage` as required by FR-010 and Constitution VII.
  · Each binary runs `./binary -runs=0` without immediate crash (sanity check).  
  · Harness source files are present and correctly referenced.

- [ ] T006 [P2] [US2] Execute the fuzzing harness on each binary for a hard‑capped 30‑minute budget, capturing crash logs and timeout events.  
  *Implementation*: `code/run_fuzzing.py` → writes one `FuzzResult` line per run to `data/results/fuzz_results_v{hash}.jsonl`.  
  *Verification*:  
  · Every `FuzzResult` conforms to `contracts/fuzz_result.schema.yaml`.  
  · `execution_status` is one of `"success"`, `"timeout"`, or `"compile_fail"` (FR‑003, FR‑011).

- [ ] T007 [P2] [US2] Parse ASan/UBSan crash logs, map stack traces to vulnerability categories, and assign severity scores (1‑4) per the rubric; separate security-relevant crashes from input-assumption failures.  
  *Implementation*: `code/parse_crashes.py` → reads raw fuzzer logs, enriches each `FuzzResult` with `unique_stack_traces` and `severity_scores`, writes `data/results/fuzz_results_parsed_v{hash}.jsonl`.  
  *Verification*:  
  · Each security‑relevant crash has a severity integer between 1 and 4.  
  · Confirm that security-relevant crashes AND input-assumption failures are captured and reported as separate counts (FR-011).

- [ ] T008 [P3] [US3] Perform paired and unpaired statistical analyses: Wilcoxon signed‑rank (primary), Mann‑Whitney U, and Kolmogorov‑Smirnov (secondary) on crash‑count and severity‑score differences; compute Cliff’s Δ effect sizes and apply Holm‑Bonferroni correction.  
  *Implementation*: `code/statistical_analysis.py` → reads `fuzz_results_parsed_v{hash}.jsonl`, outputs `data/analysis/stat_summary_v{hash}.jsonl`.  
  *Verification*:  
  · Summary file contains, for each model, `p_value`, `effect_size`, and `corrected_alpha` for Wilcoxon, Mann-Whitney U, and KS tests (FR-005, SC-002).
  · All adjusted α values are reported as 0.05 (FR‑008).

- [ ] T009 [P3] [US3] Generate the final Markdown report with visualizations (box‑plots of crash counts, severity distributions, compile‑failure statistics) and a discussion that frames findings as associational.  
  *Implementation*: `code/generate_report.py` → creates `paper/report.md` and writes figures to `figures/`.  
  *Verification*:  
  · Report includes a reproducibility section citing content‑hashed artifact IDs.  
  · All figures render without errors (`pytest tests/test_report_render.py`).

- [ ] T010 [P3] [US3] Conduct a reproducibility audit: verify that all random seeds, Docker image digests, and file hashes are recorded in `manifest.json`; re‑run the entire pipeline from `quickstart.md` on a fresh runner and confirm identical hashes.  
  *Implementation*: `code/audit_reproducibility.py` → writes `data/manifest.json`.  
  *Verification*:  
  · A fresh CI run produces a bit‑wise identical `manifest.json`.  
  · Script exits with status 0 only if all checks pass.

- [ ] T011 [P3] [US3] Document the full experimental protocol (data acquisition, LLM generation parameters, compilation flags, fuzzing budget, statistical methods) in `docs/methodology.md` and link it from the report.  
  *Implementation*: Write `docs/methodology.md` referencing exact script versions and parameter values.  
  *Verification*:  
  · The methodology file is cross‑referenced from `paper/report.md`.  
  · Reviewers can locate every script and configuration via the provided hyperlinks.

- [ ] T012 [P3] [US3] Create a CI test suite that validates schema compliance, ensures the minimum dataset size (≥ 50 problem pairs per model), and checks that the statistical summary meets the success criteria (p‑value reporting, effect‑size calculation).  
  *Implementation*: Add tests under `code/tests/` (e.g., `test_schema.py`, `test_dataset_size.py`, `test_statistics.py`).  
  *Verification*:  
  · All tests pass on the CI runner (`pytest -q`).  
  · Failures surface as pipeline errors, preventing progression to the paper hand‑off.

---

### Dependencies and Requirement Coverage

| Requirement | Satisfied by Task(s) |
|-------------|----------------------|
| **FR‑001** | T001, T002, T003 |
| **FR‑002** | T004 |
| **FR‑003** | T004, T006 |
| **FR‑004** | T007 |
| **FR‑005** | T008 |
| **FR‑006** | T009 |
| **FR‑007** | T009 |
| **FR‑008** | T008 |
| **FR‑009** | T007 |
| **FR‑010** | T005 |
| **FR‑011** | T006, T007 |
| **SC‑001** – **SC‑006** | T000–T010 (as indicated in verification steps) |

All tasks respect the data‑flow ordering: setup → acquisition → generation → pair creation → compilation → harness generation → fuzzing → parsing → analysis → reporting → audit. No task writes outside the `data/`, `code/`, `figures/`, `paper/`, or `docs/` directories.