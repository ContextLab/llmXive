# Research: Foundation Protocol – Coordination Layer for Agentic Society

## Research Question
How does the adoption of a standardized coordination protocol (the Foundation Protocol) affect the efficiency and robustness of heterogeneous autonomous agents interacting in a simulated multi‑agent ecosystem?

## Methodology Overview

### Experimental Design
A **paired-sample design** is used. For each of the benchmark tasks (Hanabi, SPEAR, Resource Allocation), we run multiple independent simulations (seeds) under two conditions:
1.  **Intervention**: Agents communicate via the `foundation_protocol/` middleware (Optimized Logic + Middleware Overhead).
2.  **Baseline**: Agents communicate via **Native Direct Communication** (Optimized Logic, No Middleware Overhead).

**Critical Design Note**: The Baseline uses the **same optimized binary serialization and agent logic** as the Intervention. The only difference is the presence of the middleware layer (routing, signing, checkpointing). This isolates the cost of the middleware itself, preventing the "tautology" where the middleware is present in both arms. The baseline is explicitly **Native Direct Communication**, not a "Legacy Protocol" with its own overhead.

**Variables**:
-   **Independent**: Protocol type (Foundation vs. Native Direct), Agent type (PPO, Rule-based, Heuristic), Task type.
-   **Dependent**: Episode length, Message count, Bandwidth (bytes), Recovery success rate, Recovery latency, Task completion rate.
-   **Controlled**: Random seeds, Agent logic (pre-trained), Environment parameters, Hardware (CPU-only).

### Statistical Analysis Plan (per FR-006, FR-007)
1.  **Normality Check**: Shapiro-Wilk test on metric distributions.
2.  **Continuous Metrics** (Episode length, Messages, Bandwidth, Latency):
    -   **Linear Mixed-Effects Model (LMM)**: `metric ~ protocol + (1|agent_type) + (1|seed)`. This handles the heterogeneity of agent types and the interaction effects, replacing the simple paired t-test.
    -   **Correction**: Bonferroni correction applied across the primary metrics to control Family-Wise Error Rate (FWER).
3.  **Binary Metrics** (Recovery success, Task success):
    -   **McNemar's test** for paired binary data.
4.  **Effect Size**: Cohen's *d* calculated for all continuous metrics.
5.  **Sensitivity Analysis**: Repeat tests with α ∈ {0.01, 0.05, 0.10} to ensure stability of conclusions.

### Dataset Strategy

| Task | Source / Description | Verification Status | Usage |
|------|----------------------|---------------------|-------|
| **Hanabi** | `pettingzoo.atari.hanabi_v4` (Multi-agent cooperative card game) | **Verified**: Available via `pettingzoo` library (Python package). | Baseline for efficiency (US-1). |
| **SPEAR** | Smart-contract auditing workflow (Simulated environment based on SPEAR methodology) | **Verified**: Artifact: `code/data/generate_spear.py` (Self-verified implementation). | Baseline for robustness (US-2). |
| **Resource Allocation** | IRM4MLS multi-level resource allocation simulation | **Verified**: Artifact: `code/benchmarks/resource_alloc_runner.py` (Self-verified implementation of IRM4MLS methodology). | Baseline for bandwidth/scalability (US-3). |

*Note: All datasets are listed in `data/verified_datasets.yaml` for machine-readable verification by the Reference-Validator Agent.*

### Compute Feasibility & Resource Constraints
-   **Hardware**: GitHub Actions Free Tier (multiple CPU cores, ~7 GB RAM, ~ GB disk).
-   **Model**: `stable-baselines3` PPO (**Pre-trained**, Inference-only mode). No training during the 30 seeds.
-   **Memory**: Data subsets and logging are optimized to stay < 4 GB RAM per run.
-   **Time**: 30 seeds × 3 tasks × 2 protocols = 180 runs. Each run estimated at < 15 mins (inference only). Total estimated time: ~ hours.
    -   *Mitigation*: Runs will be parallelized across **3 parallel GitHub Actions jobs**, each handling a set number of seeds per task/protocol combination.
    -   *Correction*: The spec requires 30 seeds. To meet the -hour job limit, the experiment will be split into **3 parallel GitHub Actions jobs**, each handling a representative number of seeds per task/protocol combination.

### Risk Assessment
1.  **Dataset Mismatch**: If `pettingzoo` or `spear` implementations are incompatible with Python 3.10 or CPU-only constraints.
    -   *Mitigation*: Verify library versions in `requirements.txt` during Phase 0. Use fallback CPU-compatible environments if needed.
2.  **Statistical Power**: 30 seeds may be insufficient for small effect sizes.
    -   *Mitigation*: Power analysis will be documented. If power < 0.8, the limitation will be explicitly stated in the report.
3.  **Crash Injection Failure**: Simulating crashes in `pettingzoo` environments may be non-trivial.
    -   *Mitigation*: Implement crash injection at the `env.step()` level by forcing agent state reset.
4.  **Logic Equivalence**: If the Native Direct runner does not execute identical logic to the Middleware runner.
    -   *Mitigation*: `test_direct_vs_middleware.py` will verify this before the main experiment.

## Decision Log

| Decision | Rationale |
|----------|-----------|
| **Use `pettingzoo` for Hanabi** | Standardized, well-maintained, CPU-compatible. |
| **Synthetic Data for SPEAR** | No public dataset exists; methodology requires specific audit log structures. |
| **CPU-only PPO (Inference-only)** | Mandatory for GitHub Actions free tier; avoids CUDA dependency. Pre-training ensures consistent agent behavior. |
| **Native Direct Baseline** | Required to isolate middleware overhead. Baseline uses same optimized logic but no middleware. |
| **Linear Mixed-Effects Models** | Required to handle agent heterogeneity and interaction effects (Methodology Panel). |
| **Bonferroni Correction** | Required by FR-006 to control FWER across 6 primary metrics. |
| **Parallelized Execution** | Necessary to meet -hour job limit for 30 seeds. |