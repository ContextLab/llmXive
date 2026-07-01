# Research: Reproduce & Validate OpenComputer

## 1. Problem Statement & Hypothesis

**Problem**: The "OpenComputer" paper claims that its hard-coded verifiers align more closely with human adjudication than LLM-as-judge baselines. To validate this, we must reproduce the execution loop and compare the verifier's output against a manually adjudicated ground truth.

**Hypothesis**: On a representative sample of 5 tasks from the OpenComputer corpus, the hard-coded verifier's pass/fail judgment will show **consistent alignment** with the manual human adjudication, confirming the *feasibility* of the validation loop.

**Null Hypothesis**: The hard-coded verifier's judgment is inconsistent with manual adjudication, indicating a fundamental flaw in the verification logic or the task definitions.

**Decision Rule**: Success is defined as **consistent alignment** across the majority of the sample (e.g., 4 out of 5 tasks match). We do not set a specific percentage threshold (e.g., 90%) as N=5 is insufficient for statistical generalization. The study assesses the *mechanism* of verification, not the statistical superiority of the paper's claims.

## 2. Dataset Strategy

The study utilizes tasks defined within the `external/OpenComputer` submodule. These tasks are not a separate dataset but are embedded in the repository's `task_generator` and `evaluation/apps/specs` directories.

| Dataset Source | Description | Access Method | Verified URL |
|:--- |:--- |:--- |:--- |
| OpenComputer Submodule | Contains task definitions (`task.json`), environment manifests, and hard-coded verifiers. | Git Submodule (`git submodule update --init --recursive`) | N/A (Local Repository) |
| OpenComputer Paper | The primary reference for claims being reproduced (e.g., "33 applications"). | arXiv | ` |

**Variable Fit**: The study requires:
1. **Task Definition**: Provided by `task.json` (outcome criteria).
2. **Verifier Logic**: Provided by `evaluation/apps/specs/` (hard-coded checks).
3. **Ground Truth**: Generated manually via `collect_artifacts.py` and `prepare_ground_truth.py` using dual inspection.

**Constraint**: The free-tier CI environment (limited disk space) cannot host the full OpenComputer corpus.. The study is restricted to a **sample of 5 tasks** selected from the `task_generator` directory, ensuring they are lightweight enough to run within the time and memory limits.

## 3. Methodology

### 3.1. Execution Pipeline (Phases)

The pipeline is strictly ordered to ensure data availability:
1. **Provisioning**: Build/Run Docker container (if image missing).
2. **Smoke Test**: Execute 1 task to validate the loop.
3. **Batch Execution**: Run 5 tasks via `run_eval.py`.
4. **Artifact Collection**: Extract generated files (e.g., `.wav`, `.docx`) to host.
5. **Blinding**: Anonymize artifacts and generate `blinded_ground_truth.json` (human inspection).
6. **Comparison**: Merge verifier results with manual ground truth.
7. **Reporting**: Generate `reproduction_report.md`.

### 3.2. Manual Adjudication Protocol (Blinding & Dual-Inspection)

To avoid bias and ensure construct validity, the manual inspection step follows a **Dual-Inspection Protocol**:

1. **Collection**: `collect_artifacts.py` copies the output files from the Docker container to a local `results/blinded_artifacts/` folder.
2. **Preparation**: `prepare_ground_truth.py` renames files to random IDs and generates a `blinded_ground_truth.json` with fields: `task_id`, `inspector_1_verdict`, `inspector_2_verdict`, `arbitration_verdict`, `manual_judgment_notes`.
3. **Independence**: Two independent researchers (human_01 and human_02), who are **distinct from the pipeline designer**, inspect the artifacts.
4. **Tool-Assisted Verification**: Inspectors must use **distinct, independent validation instruments** to verify semantic correctness, not just visual inspection.
 * *Audio Tasks*: Use `ffprobe` to check frequency spectra and duration (distinct from verifier's file-existence check).
 * *Document Tasks*: Use `pandoc` or `diff` tools to compare semantic content (distinct from verifier's byte-exact check).
5. **Arbitration**: If `inspector_1_verdict` and `inspector_2_verdict` disagree, a third-party senior researcher (human_03) arbitrates to determine the `arbitration_verdict`.
6. **Comparison**: `compare_verdicts.py` merges the verifier's `verification_report.json` with the `arbitration_verdict` to calculate alignment.

### 3.3. Statistical Considerations

**Sample Size Limitation**: With N=5, statistical tests (e.g., McNemar's test, Chi-square) are invalid due to insufficient degrees of freedom. The study **does not** calculate p-values or confidence intervals. Instead, it relies on a **qualitative narrative** and a simple alignment consistency (matches / total) to assess fidelity.

**Collinearity**: Not applicable (no predictors/covariates in this validation loop).

**Multiple Comparisons**: Not applicable (single hypothesis: verifier alignment feasibility).

## 4. Feasibility & Risks

### 4.1. Compute Feasibility
- **CPU/GPU**: All tasks are CPU-bound (Docker container execution). No GPU required.
- **Memory**: Adequate RAM is sufficient for a single Docker container running lightweight apps (e.g., Audacity, LibreOffice) and the Python orchestration scripts.
- **Disk**: 14 GB is tight. The plan ensures:
 - Base Docker images are pulled once and cached.
 - Artifacts are deleted from the container after extraction.
 - Only 5 task artifacts are stored on the host.

### 4.2. Risk Mitigation

| Risk | Mitigation Strategy |
|:--- |:--- |
| **Docker Build Failure** | `run_smoke_test.sh` checks for image existence; if missing, attempts build. If build fails, logs error and marks task "failed" without crashing. |
| **Disk Quota Exceeded** | Scripts check disk usage before build. If >12 GB, aborts with "disk_quota_exceeded" error. |
| **Missing API Keys** | Agent scripts catch `KeyError` for env vars (e.g., `ANTHROPIC_API_KEY`), log "missing_credentials", and skip the agent/task gracefully. |
| **Verifier Mismatch** | If a task requires an app not in the Docker image, the verifier records "dependency_missing" and the task is marked "skipped". |
| **Inspection Bias** | Mitigated by Dual-Inspection Protocol and mandatory tool-assisted verification. |

## 5. Decision Rationale

**Why N=5?**
The free-tier CI limit and disk quota make a large-scale reproduction impossible.. A sample of 5 tasks allows for a deep-dive validation of the *mechanism* (verifier vs. human) without exhausting resources. This aligns with the "smoke test" philosophy: proving the loop works, not proving the paper's entire corpus is valid.

**Why Qualitative Narrative?**
Recent reviewer feedback (T024, T031) explicitly rejected statistical significance testing for N=5. The plan adopts a qualitative narrative to describe the alignment, focusing on specific examples of matches and mismatches rather than a single p-value.

**Why Hard-Coded Verifiers?**
The paper claims hard-coded verifiers are superior to LLM-as-judge. Validating this requires comparing the hard-coded verifier against *human* judgment, not another LLM. The **Dual-Inspection Protocol** ensures this comparison is fair and independent of the pipeline designer's bias.

**Why Feasibility Over Superiority?**
The study is reframed as a feasibility assessment of the validation loop. A qualitative narrative on N=5 cannot validate a comparative claim about "better alignment" (which implies statistical superiority). The hypothesis is thus narrowed to "assess feasibility of the validation loop" rather than "validate the paper's claim".