# Research: EvoArena: Tracking Memory Evolution for Robust LLM Agents in Dynamic Environments

## Problem Statement

The goal is to reproduce and validate the claims of the "EvoArena" paper (arXiv:2606.13681), which posits that an EvoMem agent (tracking memory evolution via patches) outperforms a baseline agent in dynamic environments (TerminalBench-Evo and PersonaMem-Evo). The validation must be achieved on a CPU-only CI environment with strict resource constraints (limited RAM, 2 CPU cores).

**Critical Scope Note**: Due to resource constraints, this run is a **Feasibility & Pipeline Integrity Probe**. It is **not** a statistically powered validation of the paper's causal claims. Results will be reported as **Descriptive Statistics** only. No inferential statistics (t-tests, etc.) will be performed.

## Dataset Strategy

The following datasets are verified and will be used. The plan explicitly avoids inventing URLs.

| Dataset Name | Domain | Verified Source URL | Usage in Plan |
|:--- |:--- |:--- |:--- |
| **TerminalBench-Evo** | Terminal Tasks | ` (and related parquet files) | Used for `EvoMem-TerminalBench-Evo` evaluation (FR-001). Subset of 5 chains selected via **Deterministic Head Sampling**. |
| **PersonaMem-Evo** | Social/Preference | ` | Used for `EvoMem-PersonaMem-Evo` evaluation (FR-002). Subset of 5 chains selected via **Deterministic Head Sampling**. |
| **EvoMem Code/Data** | Vendored | **NO verified source found** (as per user input) | The code and specific dataset files (e.g., `chat_history_32k`) are assumed to be present in `external/EvoArena` via submodule. **Pre-flight Check Required**: Verify presence of 'Evo' specific logic and data. |

**Dataset Variable Fit Analysis**:
- **TerminalBench**: The verified URLs point to `users.parquet` and `train-00000-of-00001.parquet`. The spec assumes the vendored code contains the specific "Evo" chains and task definitions. If the vendored code expects a specific directory structure not present in the verified HuggingFace parquet files, the plan must handle this by checking the `external/EvoArena` directory for the necessary files. *Critical Risk*: If the verified HuggingFace links do not contain the "Evo" specific modifications (e.g., dynamic environment states), the reproduction may fail. The plan includes a **Dynamic State Synthesis** step: if the base data is static, the vendored code's internal logic (if present) will be used to synthesize 'Evo' dynamics. If the code lacks this logic, the run aborts with a clear error.
- **PersonaMem**: The verified URLs provide `benchmark_text_32k.parquet` and `train.parquet`. The plan assumes the vendored code maps these to the "Evo" format. If the "Evo" version requires specific dynamic updates not in the base PersonaMem dataset, the plan will rely on the vendored code's internal logic to generate these, or fail if the data is missing.

## Methodological Approach

### 1. Environment Configuration
- **Compute**: CPU-only. The plan will enforce `torch.device("cpu")` in the configuration.
- **Model**: Use a small, CPU-tractable model (e.g., `Llama-3.2-1B` or similar if available, or a distilled model) or rely on the API if the vendored code supports it. *Constraint*: If the vendored code attempts to load a large model (e.g., 7B+), the plan will trigger a fallback to a smaller model or a mocked response for the CI run to ensure completion within 6 hours.
- **Data Subset**: Limit to 5 chains for TerminalBench and 5 for PersonaMem to ensure runtime < 6 hours.

### 2. Execution Flow
- **Phase 0.5: Code & Data Integrity Check**:
 - Verify `external/EvoArena` submodule is populated.
 - Verify presence of 'Evo' specific logic (e.g., `evo_mem.py`, dynamic state generators).
 - Verify presence of 'Evo' specific data files or synthesis logic.
 - **Abort** if critical files/logic are missing.
- **Phase 1: Baseline Execution**: Run `launch_terminus_baseline.sh` (or Python equivalent) on the 5 Terminal chains.
- **Phase 2: EvoMem Execution**: Run `launch_terminus_evomem.sh` on the same 5 Terminal chains. Capture memory patches.
- **Phase 3: Persona Execution**: Run `evaluate_persona_chain_acc.py` for multiple Persona chains for both Baseline and EvoMem.
- **Phase 4: Artifact Validation**: Check that all JSON logs are valid and non-empty (FR-005) against `contracts/execution_log.schema.yaml` and `contracts/memory_patch.schema.yaml`.
- **Phase 5: Aggregation**: Compute average accuracy and chain-level accuracy. **Descriptive Statistics Only**.

### 3. Statistical Rigor & Limitations
- **Sample Size**: The subset (a limited number of chains per domain) is small. The plan explicitly acknowledges this as a **power limitation**. The results will be treated as a *proof-of-concept* for the reproduction pipeline, not a definitive statistical validation of the paper's claims.
- **Causal Inference**: Since this is a reproduction of an existing study, the causal claims are inherited from the paper. The plan will not make new causal claims but will verify if the *observed* difference in accuracy matches the paper's reported direction.
- **Multiple Comparisons**: With only two conditions (Baseline vs. EvoMem) and two domains, standard t-tests or Wilcoxon signed-rank tests (if sample size permits) can be used, but the small N (5) makes statistical significance unlikely. The focus is on **effect size** and **direction of improvement**. **Decision**: No inferential statistics will be performed. Results will be reported as descriptive statistics (mean, median, range) only, with a clear disclaimer that no statistical significance can be claimed.
- **Sampling Strategy**: **Deterministic Head Sampling**. A subset of chains from the verified dataset will be selected to ensure reproducibility and avoid selection bias. This acknowledges that the subset may not be fully representative of the population.

## Decision Log

| Decision | Rationale |
|:--- |:--- |
| **Subset to 5 chains** | To fit within 6-hour CI limit and 7GB RAM. Full dataset is too large for CPU-only execution. |
| **CPU-only enforcement** | The CI environment lacks GPU. Using CPU-tractable models or API calls is the only viable path. |
| **Vendored code reliance** | The spec assumes `external/EvoArena` is functional. No code modifications are planned; only configuration changes. |
| **No new dataset URLs** | Adherence to the "Verified datasets" block. If the vendored code requires data not in the verified list, the plan will flag this as a "Missing Data" error rather than inventing a URL. |
| **Descriptive Statistics Only** | N=5 is insufficient for inferential statistics. Results are reported as observed metrics with a disclaimer. |
| **Real API Calls Required** | To satisfy the "Reproduction" goal, real API calls are required for the main validation path. Mocks are only for unit testing. |

## Risk Assessment

- **Risk 1: Dataset Mismatch**. The verified HuggingFace datasets may not match the specific "Evo" format required by the vendored code.
 - *Mitigation*: The plan includes a pre-flight check to verify the presence of expected files in `external/EvoArena/data`. If missing, the run aborts with a clear error. Dynamic state synthesis logic is checked.
- **Risk 2: OOM (Out of Memory)**. Large context windows or memory patch histories could exceed 7GB RAM.
 - *Mitigation*: Enforce a hard limit on `max_patch_history` and `max_context_tokens` in the configuration.
- **Risk 3: API Rate Limits**. If the evaluation relies on external APIs, the 6-hour window might be exceeded.
 - *Mitigation*: Implement exponential backoff in the runner script. If limits are hit, skip the remaining chains and report partial results.
- **Risk 4: Missing Evo Logic**. The vendored code may lack the logic to synthesize 'Evo' dynamics from static base data.
 - *Mitigation*: Phase 0.5 Code Integrity Check will abort the run if this logic is missing, preventing silent failure.
