# Research: Reproduce & validate: TUA-Bench

## Executive Summary

We evaluate the feasibility of reproducing the TUA‑Bench benchmark on a free‑tier GitHub Actions runner (CPU‑only, 7 GB RAM, 6 h job limit). The validation focuses on **pipeline feasibility** (can the containerised environment be built and tasks run) and **scoring‑protocol correctness** (does the original `verify.py` correctly separate pass/fail cases). 

**Scope Limitation**: The success‑rate metric reported is **restricted to the offline subset** (tasks that do not require live network access). It is **not** extrapolated to the paper’s overall success‑rate claim for the full 120‑task suite. This limitation is explicitly noted in the final report.

## Verified Datasets

- **TUA‑Bench Source**: `external/TUA-Bench` (local submodule).  
  - Contains the full benchmark code, task definitions, and reference solutions.  
  - Verified locally after `git submodule update --init`.

## Dataset Strategy

| Dataset | Source/URL | Loading Method | Variables Needed | Fit Assessment |
|---------|------------|----------------|------------------|----------------|
| TUA‑Bench Tasks | `external/TUA-Bench` (local) | Filesystem traversal (`os.walk`), TOML parsing | `task_id`, `family`, `instruction.md`, `solution/`, `tests/reference/` | **High** – Direct mapping to required entities. |
| Paper Claims | Embedded in repository metadata (`dataset.toml` or `README`) | Simple file read | `total_tasks`, `family_count` | **High** – Claims are explicitly stated in the codebase. |
| Independent Oracle | Hand‑crafted JSON files under `oracle/` | Direct file read | Expected terminal output per task | **High** – Provides an external ground truth for control testing. |

## Methodological Rigor

1. **Stratified Subset Selection** – One task per reported family (five families) plus two edge‑case tasks, ensuring coverage while staying within CI limits.
2. **Independent Oracle & Control Test (N=20)** – For each selected task, an oracle JSON is authored. Four corrupted variations are generated per task, yielding a set of control cases. The **original** `verify.py` is run unchanged, with the oracle temporarily copied to the expected `tests/reference/` location. This breaks circularity and tests the verifier against an external ground truth.
3. **Control Test Accuracy** – The verifier’s classification accuracy on the 20 control cases must be **≥ 95 %** (SC‑002). Accuracy is computed as the ratio of correct classifications to the total number of instances.
4. **Metadata Verification** – Before any execution, the pipeline counts all tasks and families, asserting ≥ 110 tasks (SC‑005) and at least five families (SC‑003). Failure aborts with a clear error.
5. **Error Reason Parsing** – `stderr` from `verify.py` is parsed using predefined regex patterns to produce standardized error messages (`File Missing`, `Value Mismatch`, `Timeout`, `OOM`, `Network Timeout`), satisfying FR‑007.
6. **Selection Bias Disclosure** – Live‑web tasks are excluded because network access is unreliable in CI. The report explicitly states this exclusion and its impact on the success‑rate metric.
7. **Statistical Reporting** – Success‑rate is reported **only for the offline subset**; the paper’s overall success‑rate claim is not claimed to be reproduced.

## Decision Log

| Decision | Rationale | Alternative Rejected |
|----------|-----------|----------------------|
| Use stratified subset | Guarantees family coverage while fitting CI runtime and resource limits. | Random full‑suite execution – exceeds time/memory limits. |
| Create independent oracle (N=20) | Breaks circular validation of the benchmark’s own verifier; enables statistical accuracy check. | Rely solely on reference solutions – tautological. |
| Run original `verify.py` unchanged, swapping reference files | Tests the verifier’s logic against an external ground truth without modifying its code. | Modify verifier to accept oracles – would test the wrapper, not the verifier. |
| Exclude live‑web tasks | Network access is unreliable in CI; inclusion would cause nondeterministic failures. | Simulate network calls – adds complexity and hidden failure modes. |
| Restrict success‑rate to offline subset | Prevents invalid extrapolation from a biased sample to the full benchmark. | Compare subset rate to paper’s overall rate – methodologically unsound. |

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Large container images exceed disk quota | Run `docker system prune -f` after each task; select tasks with smaller images. |
| Oracle creation errors | Oracle files are manually verified; a sanity‑check script confirms JSON validity before use. |
| Timeout or OOM inside containers | Enforce a hard timeout of a reasonable duration; monitor container memory and kill on OOM, logging status. |
| Selection bias affecting success‑rate comparison | Explicitly state in the report that the success‑rate applies only to the offline subset and cannot validate the paper’s overall claim. |

## Success Metrics Alignment

- **SC‑001** – Percentage of tasks completing without init errors is measured during Phase 0a.  
- **SC‑002** – Control‑test accuracy (≥ 95 % on 20 cases) is computed in Phase 0b.  
- **SC‑003** – Family count verification occurs in Phase 0a.  
- **SC‑004** – Total execution time summed across tasks is compared to the CI time limit in Phase 2.  
- **SC‑005** – Task count verification (≥ 110 tasks) is a hard gate in Phase 0a.

## Limitations

- The subset excludes live‑web tasks; therefore the reproduced success‑rate does **not** reflect the paper’s reported overall success‑rate.  
- The oracle creation is manual; any mistake in the oracle will affect control‑test results, but a sanity‑check script mitigates this risk.
