# Implementation Plan: Reproduce & validate: TUA-Bench

**Branch**: `805-reproduce-tua-bench` | **Date**: 2024-05-21 | **Spec**: [link]  
**Input**: Feature specification from `/specs/805-reproduce-tua-bench/spec.md`

## Summary

The goal is to **reproduce** the TUA‑Bench pipeline on a free‑tier GitHub Actions runner (CPU‑only, ~7 GB RAM, 6 h total runtime). The plan focuses on two scientifically rigorous validation objectives:

1. **Pipeline Feasibility** – can the containerised environment be built and each task executed without error?
2. **Scoring‑Protocol Correctness** – does the original `verify.py` correctly distinguish pass vs. fail cases when evaluated against an *independent* oracle?

A **stratified subset** (one task per reported family, plus two edge‑case tasks) is used to keep runtime within CI limits. The subset is **not** used to infer the paper’s overall success‑rate; the report will explicitly state that the calculated success‑rate applies **only to the offline subset** (see Phase 2).

## Constitution Check

The project constitution (`constitution.md`) was not supplied in the input. Consequently, a formal constitution audit is **deferred** until the document is provided. When available, the plan will be revisited to ensure compliance with all constitutional principles (e.g., FR‑030).

## Requirement Traceability Matrix

| Requirement ID | Description | Plan Phase / Step | Evidence |
|----------------|-------------|-------------------|----------|
| FR-001 | Execute `repo_env/setup_env.py` for each task | Phase 1 – Step 1.1 (FR‑001) | Container build |
| FR-002 | Run verification script and capture exit code | Phase 1 – Step 1.3 (FR‑002) | `verify.py` invocation |
| FR-003 | Compare outputs using exact vendored logic | Phase 1 – Step 1.3 (FR‑003) | No modification of verifier |
| FR-004 | Produce structured JSON per task | Phase 1 – Step 1.5 (FR‑004) | `results/<task_id>.json` |
| FR-005 | Aggregate results into summary report | Phase 2 – Step 2.1 (FR‑005) | `results/summary.json` |
| FR-006 | Enforce 30 min hard timeout per task | Phase 1 – Step 1.2 (FR‑006) | Timeout wrapper |
| FR-007 | Log specific failure reasons to stderr | Phase 1 – Step 1.4 (FR‑007) | Regex mapping |
| SC-001 | % tasks completing without init errors | Phase 0a – Step 0a.1 (SC‑001) | Count of successful setups |
| SC-002 | Scoring protocol accuracy ≥ 95 % on control cases | Phase 0b – Step 0b.5 (SC‑002) | Accuracy calculation |
| SC-003 | Verify existence of five task families | Phase 0a – Step 0a.2 (SC‑003) | Family count |
| SC-004 | Total execution time ≤ 6 h CI limit | Phase 2 – Step 2.3 (SC‑004) | Summed runtimes |
| SC-005 | Verify ≥ 110 tasks present | Phase 0a – Step 0a.3 (SC‑005) | Directory count |

*Each step is annotated with the FR/SC it satisfies (e.g., “Step 1.1 (FR‑001)”).*

## Phases & Detailed Steps

### Phase 0a – Metadata Verification & Task Count (SC‑005, SC‑003, SC‑001)

1. **Locate Tasks** (Step 0a.1 – SC‑001): Traverse `external/TUA-Bench/tasks/` to enumerate all task directories.
2. **Count Tasks & Families** (Step 0a.2 – SC‑003): Compute total task count and distinct families.
3. **Enforce Minimum Task Count** (Step 0a.3 – SC‑005):  
   - If total tasks `< 110`, abort with exit code 1 and record failure in the summary report.  
   - If `≥ 110`, continue.
4. **Select Representative Subset** (Step 0a.4): Choose **one task per family** (5 tasks) plus two edge‑case tasks (memory‑intensive, timeout‑prone). Store IDs in `subset_tasks.txt`.

### Phase 0b – Independent Oracle & Control‑Test (SC‑002, FR‑002, FR‑003)

1. **Create Oracle Files** (Step 0b.1): For each selected task, author an oracle JSON (`oracle/<task_id>.json`) containing the exact expected terminal output.  
2. **Generate Corrupted Variations** (Step 0b.2): For each task, produce four altered outputs (numeric drift >5 %, missing file, extra line, wrong order) → total 20 control cases. Store under `control_cases/<task_id>_case<N>.out`.
3. **Prepare Reference Swaps** (Step 0b.3): For each control case, copy the corresponding oracle file to the task’s `tests/reference/` location **without modifying `verify.py`**. This lets the original verifier compare the agent output against an independent ground truth.
4. **Run Verification** (Step 0b.4 – FR‑002, FR‑003): Execute the unmodified `verify.py` on each control case, capturing exit code, stdout, and stderr.
5. **Assess Accuracy** (Step 0b.5 – SC‑002): Compute `accuracy = correct_classifications / total_samples`. The pipeline aborts if `accuracy < 0.95`, logging the shortfall.

### Phase 1 – Execution Pipeline for Selected Tasks

For each task in `subset_tasks.txt`:

1. **Environment Setup** (Step 1.1 – FR‑001, FR‑006)  
   ```bash
   python external/TUA-Bench/repo_env/setup_env.py --task <task_id>
   ```  
   - Pull/build Docker/Podman image.  
   - Enforce a **30 min hard timeout** via `timeout` wrapper.  
   - Log missing Docker/Podman as `"Container runtime not available"` (error_message).

2. **Task Execution** (Step 1.2)  
   - Run the task’s agent script inside the container.  
   - Record wall‑clock time (`execution_time_seconds`).  
   - Enforce the same 30 min timeout at process level.

3. **Verification** (Step 1.3 – FR‑002, FR‑003)  
   - Invoke `verify.py` with the generated output and the original `tests/reference/` file.  
   - Capture exit code and both stdout & stderr.

4. **Error Reason Parsing** (Step 1.4 – FR‑007)  
   - Parse `stderr` using the following regex‑to‑reason map:  
     - `FileNotFoundError` → `"File Missing"`  
     - `ValueError|expected.*got` → `"Value Mismatch"`  
     - `TimeoutError|Timed out` → `"Timeout"`  
     - `MemoryError|OOM` → `"OOM"`  
     - `NetworkError|Connection refused|Network timeout` → `"Network Timeout"`  
   - If none match, use `"Unknown Error"`.

5. **JSON Result Generation** (Step 1.5 – FR‑004)  
   - Write `results/<task_id>.json` conforming to `execution_result.schema.yaml`.  
   - Include `status` (`pass`/`fail`/`timeout`/`oom`/`error`), `execution_time_seconds`, `error_message`, `verification_score` (0.0 or 1.0), and ISO‑8601 `timestamp`.

### Phase 2 – Aggregation, Reporting & Scope‑Limitation (FR‑005, SC‑004)

1. **Aggregate Results** (Step 2.1 – FR‑005)  
   - Combine all `results/*.json` into `results/summary.json` validated against `reproduction_report.schema.yaml`.
2. **Compute Subset Success Rate** (Step 2.2)  
   - `success_rate = passed / attempted` (offline subset only).  
   - Add explicit field `success_rate_scope: "offline_subset_only"` in the report.
3. **Validate Runtime Budget** (Step 2.3 – SC‑004)  
   - Sum `execution_time_seconds` across tasks; ensure total ≤ 6 h. Abort with clear message if exceeded.
4. **Generate Markdown Report** (Step 2.4)  
   - Produce `docs/reproduction_report.md` containing:  
     - Task‑level table (ID, family, execution time, status, error).  
     - **Scope‑Limitation Notice** (offline subset only).  
     - Comparison of observed task count & family count to paper claims (SC‑003, SC‑005).  
     - Control‑test accuracy result (SC‑002).  
     - Family‑level pass rates.  
     - Any deviations with severity tags.

### Edge‑Case Handling (All Phases)

| Condition | Detection | Action |
|-----------|-----------|--------|
| Docker/Podman missing | `which docker`/`which podman` fails | Abort with `"Container runtime not available"` |
| Network call fails (live‑web tasks) | Exception containing `NetworkError` | Log `Network Timeout` and continue |
| OOM inside container | Container exit code 137 | Record status `oom` and `error_message: "OOM"` |
| Timeout exceeded | `timeout` wrapper exits non‑zero | Record status `timeout` and `error_message: "Timeout"` |
| Numerical drift | Verifier uses tolerance ≥ 1e‑5 (rel) or ≥ 1e‑3 (abs) | No failure; tolerance is built‑in to `verify.py` |

## Compute Feasibility

- All Docker images are CPU‑only; no GPU or large‑model libraries are required.  
- Subset size (≈5 tasks) + 20 control cases ensures total runtime < 2 h and disk usage < 5 GB.  
- The plan prunes images after each task (`docker system prune -f`) to stay within the disk quota.

## Timeline (estimated)

| Phase | Duration |
|-------|----------|
| 0a – Metadata Verification | 10 min |
| 0b – Oracle & Control Test | 30 min |
| 1 – Execution (5 tasks) | ≤ 90 min |
| 2 – Aggregation & Reporting | 15 min |
| Buffer & Cleanup | 15 min |
**Total ≤ 2.5 h**, well within CI limits.
