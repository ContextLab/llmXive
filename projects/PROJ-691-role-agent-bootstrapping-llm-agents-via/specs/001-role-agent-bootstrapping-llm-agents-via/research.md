# Research: Reproduce & validate: Role-Agent: Bootstrapping LLM Agents via Dual-Role Evolution

## Overview
This research phase validates the feasibility of reproducing the "Role-Agent" paper's core mechanisms (WIA/AIW) on a CPU-only CI runner. It identifies the necessary dependencies, confirms dataset availability for ALFWorld, and defines the strategy for handling the "dual-role" evolution on a limited sample.

## Dataset Strategy

The reproduction relies on the **ALFWorld** environment. The paper describes a framework where the agent interacts with a simulated environment. Unlike static datasets, ALFWorld is a text-based simulation environment where the "data" consists of task templates and environment configurations that generate dynamic episodes.

| Dataset/Resource | Verified URL | Usage in Plan | Notes |
|:--- |:--- |:--- |:--- |
| **ALFWorld Environment** | ` | **Primary Source** | The environment is generated dynamically via the `alfworld` Python library installed from this repository. The plan does **not** use a static Parquet file. Episodes are generated on-the-fly from task templates (e.g., "put something on something") during execution. |
| **Role-Agent Code** | `external/roleagent` (Git Submodule) | **Code Source** | The implementation is vendored. No external download URL is needed for the code itself. |
| **Model Weights (Primary)** | `https://huggingface.co/facebook/opt-125m` | **Inference** | The primary model for CPU execution. It is small enough to run on 7GB RAM and provides non-deterministic reasoning for the WIA component. |
| **Agent Logic (Fallback)** | N/A (Local Implementation) | **Mechanism Isolation** | A **Rule-Based Agent** (local implementation) will be used if `opt-125m` fails or to strictly isolate the mechanism. It uses hard-coded logic to simulate the dual-role behavior, ensuring meaningful failure pattern analysis. |

**Dataset Fit Analysis**:
- **Required Variables**: The WIA component needs `state`, `action`, `observation` from the ALFWorld environment. The `alfworld` library generates these dynamically based on task templates.
- **Coverage**: The `train` split of task templates within the ALFWorld environment is sufficient to sample 5 distinct tasks.
- **Gap Handling**: If the vendored code expects a specific large model that cannot run on CPU, the plan will inject a "Rule-Based Agent" class that returns deterministic valid states based on simple logic (e.g., "if action is 'go to table', state is 'at table'"). This satisfies the *mechanism* check (WIA/AIW flow) and allows for meaningful AIW analysis (e.g., "Agent failed to predict state X given action Y") without the *inference* cost of a large LLM.

**Correction on Static Data**: Previous references to static Parquet files for ALFWorld were incorrect. The environment requires the dynamic simulation loop provided by the official library to generate the `predicted_state` vs `actual_state` pairs required for the WIA log.

## Technical Feasibility & Constraints

### 1. Compute Constraints (CPU-Only)
- **Constraint**: The runner has multiple CPUs and sufficient RAM.
- **Risk**: Loading a standard LLM (e.g., LLaMA-7B) will cause OOM.
- **Mitigation**:
 - **Primary**: Use `facebook/opt-125m` with `torch_dtype=torch.float32`.
 - **Fallback**: Use a **Rule-Based Agent** (local implementation) if memory pressure is detected or if the mechanism logic needs to be isolated from model reasoning.
 - **No CUDA**: Explicit checks in `sanity_check.py` to ensure `torch.cuda.is_available()` is False or ignored.

### 2. Memory Management
- **Strategy**: Generate only 5 episodes dynamically. Do not load the full dataset or environment history.
- **Library**: Use `pandas` with `dtype` optimization for log storage.

### 3. Ray Cluster
- **Strategy**: Run Ray in "local mode" (`ray.init(num_cpus=2, ignore_reinit_error=True)`) to avoid cluster startup overhead and network issues on CI.

## Statistical & Methodological Rigor

**Scope**: This is a **Mechanism Plumbing Verification**, not a statistical reproduction.
- **Sample Size**: n=5.
- **Power Analysis**: Not applicable. A sample of 5 cannot support statistical inference regarding the paper's claim of ">4% gain" or the cognitive efficacy of the dual-role mechanism.
- **Success Metric**: The pipeline runs without error, produces `wia_results.json` with valid state transitions, and `aiw_analysis_report.md` identifies *at least one* failure pattern (or confirms success) based on the logs.
- **Limitation**: The results **do not** validate the scientific claims of the paper. They only confirm that the *code executes* and the *loop functions*. This limitation is explicitly documented in the final report to prevent overclaiming.
- **Construct Validity**: By using a **Rule-Based Agent** (fallback) or `opt-125m` (primary), we ensure that the "Agent" role has defined behavior. Failures in the AIW analysis will be due to logic gaps in the environment or the agent's rules, not the hallucinations of a large model, allowing for interpretable "failure pattern" analysis.

## Decision Log

| Decision | Rationale |
|:--- |:--- |
| **Sample Size = 5 episodes** | Fits within 30 mins runtime and 7GB RAM. Allows testing the full WIA->AIW loop. |
| **Primary Model: facebook/opt-125m** | Small enough for CPU, provides non-deterministic reasoning for a realistic test. Cited from HuggingFace. |
| **Fallback: Rule-Based Agent** | Ensures mechanism isolation. If the LLM fails, the Rule-Based Agent guarantees the WIA/AIW loop runs and produces interpretable logs. |
| **Dynamic ALFWorld Generation** | ALFWorld is an interactive environment, not a static dataset. We use the official library to generate episodes dynamically. |
| **Local Ray Mode** | Avoids overhead of cluster management on CI. |
| **No GPU Check** | Explicitly fail if CUDA is detected but not usable, or if code attempts GPU allocation. |
| **SC-003 Interpretation** | "Confirm presence" is interpreted as confirming the *operational instantiation* of the dual-role loop, not its scientific efficacy. The report will reflect this distinction. |