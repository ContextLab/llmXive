# Research: Reproduce & Validate Code as Agent Harness

## 1. Problem Definition & Methodological Rigor

The goal is to verify the **reproducibility feasibility** of the "Code as Agent Harness" (arXiv 2605.18747) by executing its reference implementation in a constrained environment (CPU-only, 7GB RAM) and validating its output against the paper's abstract claims. 

**Scope Limitation**: This study validates the *specific implementation* on the *specific code commit* provided. It does not claim to validate the general theoretical capabilities of the "Harness" across all possible agents, as N=1 (one run) is insufficient for generalizable statistical claims. The focus is on **deterministic execution success** and **functional consistency** with the paper's description.

### Coverage of Requirements

- **FR-001 (Submodule Init)**: Method: Use `git submodule update --init --recursive`. Verification: Check commit hash against expected state if available, or simply verify directory existence and `README.md` presence.
- **FR-002 (CPU Execution)**: Method: Wrap execution in `subprocess` with environment variable `CUDA_VISIBLE_DEVICES=""` and explicit `torch.set_device('cpu')` injection if possible. Fallback: Catch `ImportError` for CUDA libraries and attempt CPU-only import.
- **FR-003 (Artifact Generation)**: Method: Monitor `output/` directory for file creation > 0 bytes.
- **FR-004 (Claim Mapping - Functional Verification)**: 
    - **Old Method**: Static analysis of abstract + keyword scan. (Rejected: Correlational, not causal).
    - **New Method**: **Functional Verification Protocol**. The script will execute specific harness entry points (e.g., `run_interface_test.py`) and assert the **structural and semantic content** of the output against the abstract's definition of "Unified Interface" (e.g., checking if the output JSON contains specific keys like `interface_config` and `agent_list`, and verifying `agent_list` is not empty).
- **FR-005 (Execution Verification - Content Assertion)**:
    - **Old Method**: Keyword matching ("success", "pass"). (Rejected: Tautological).
    - **New Method**: **Structured Log Parsing**. The script will parse the execution logs (JSON/structured data) to verify specific return codes or result states (e.g., `assert result['status'] == 'verified'`). If the log contains "success" but the `status` field is `error`, the claim is **unsupported**.
- **FR-006 (Sensitivity Analysis - Simulation)**:
    - **Old Method**: Regex scan for patterns. (Rejected: Insufficient).
    - **New Method**: **Sensitivity Simulation Protocol**. The script will detect hardcoded parameters (e.g., `temperature=0.7`). If the code allows, it will **re-run** the execution with varied parameters (e.g., `0.1`, `0.5`, `0.9`) and measure the impact on output metrics (e.g., success rate, log content). If re-running is not feasible (e.g., due to time limits), the `limitations.md` will explicitly flag this as "Sensitivity Analysis Not Executed: Resource Constraints".
- **FR-007 (Limitations)**: Method: Scan for `import requests`, `os.environ.get('API_KEY')`, or hardcoded URLs.

### Statistical & Methodological Notes

- **Observational Nature**: This is a *reproducibility study*, not a statistical hypothesis test. The "sample size" is N=1 (the specific code commit). Power analysis is N/A; the focus is on *deterministic* execution success.
- **Validity**: Internal validity is threatened by environmental differences (OS, library versions). Mitigation: Use Docker or pinned `requirements.txt` from the submodule.
- **Collinearity**: Not applicable (no regression models).
- **Multiple Comparisons**: Not applicable (no hypothesis testing).

## 2. Dataset Strategy

**Constraint**: The project relies on a *vendored codebase* (submodule), not an external dataset for training. The "data" is the code itself and its execution logs.

**Verified Datasets**:
- **None required for the harness execution**. The harness executes code; it does not train on external datasets like `mustc` or `US-3`.
- *Note*: If the submodule *internally* requires a dataset (e.g., for a demo run), the plan must identify it. Based on the spec, the assumption is the code runs a "quickstart" or "demo" that does not require external downloads, or the dataset is bundled. If a dataset is needed and not bundled, it will be flagged in `limitations.md` (FR-007).
- **Action**: The research phase will inspect the submodule's `README.md` and `requirements.txt` to confirm if any external data download is triggered. If so, and if no verified URL exists in the project's `# Verified datasets` block, the plan will flag this as a reproducibility gap (US-3).

**Decision**: No external dataset citation is needed for the *harness* logic. If the submodule fails due to missing data, the error is logged as a limitation.

## 3. Compute Feasibility & Constraints

- **Hardware**: GitHub Actions Free Tier (2 CPU, 7 GB RAM, No GPU).
- **Strategy**:
    1.  **Pre-Execution Resource Check**: Before running the submodule, the script will estimate memory/CPU load based on the `requirements.txt` and code size. If the estimated load exceeds 7GB RAM, the execution will be skipped, and a "Resource Constraint" flag will be set in `limitations.md`.
    2.  **Library Pinning**: If the submodule uses `transformers` or `torch`, ensure `requirements.txt` (if present) does not force GPU-only wheels. If the code uses `bitsandbytes` or `load_in_8bit`, the plan must include a patch to remove these flags for CPU execution.
    3.  **Memory Management**: If the code attempts to load a large model, the runner will OOM. The plan must include a "Sensitivity Analysis" recommendation to use a smaller model (e.g., `distilbert` instead of `llama-7b`) if the default is too large.
    4.  **Timeout**: Set a reasonable timeout for the execution step.

## 4. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Submodule contains CUDA-only code | Execution fails | Catch error, log as "Compute Constraint Violation" (US-1 Edge Case), generate `limitations.md`. |
| Hardcoded API keys | Execution fails | Detect via scan, flag in `limitations.md` (FR-007). |
| Vague Paper Claims | Validation fails | Map "Scaling" to any multi-agent log found; if only single-agent, explicitly state "Claim Not Fully Reproduced" (Edge Case). |
| Missing Dependencies | Execution fails | Detect `ModuleNotFoundError`, list in `limitations.md`. |
| Resource Exhaustion (False Negative) | Execution fails due to OOM | Pre-flight check and explicit "Resource Constraint" flag in `limitations.md` to distinguish from code errors. |

## 5. Validation Strategy

- **Success Metric 1 (SC-001)**: Exit code 0 + Artifact > 0 bytes.
- **Success Metric 2 (SC-002)**: `validation_report.md` contains 3 sections (Interface, Mechanisms, Scaling) with **evidence of functional execution** (e.g., "Found `agent_list` with 3 items" not just "Found `agent_list`").
- **Success Metric 3 (SC-003)**: `limitations.md` contains ≥ 1 gap or recommendation.
- **Success Metric 4 (SC-004)**: Total runtime < 6 hours.

**Decision**: The validation script will use **structured log parsing** and **semantic content verification** to map *actual* code output to *specific* paper claims. It will explicitly distinguish between "Execution Success" (code ran) and "Claim Support" (output matches abstract). If the code runs but the output doesn't match the claim (e.g., single agent vs. scaling), the report will explicitly state "Claim Not Supported".

**Schema Dependency**: The validation script will load and validate all output artifacts against the schemas defined in `contracts/artifact.schema.yaml` and `contracts/validation_report.schema.yaml` to ensure data integrity.
