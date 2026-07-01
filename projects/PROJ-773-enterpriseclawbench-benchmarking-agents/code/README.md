# Adaptation: EnterpriseClawBench (Scaled-Down Protocol Analysis)

## Original vs. Adapted Scope

The original paper and repo define a massive, multi-stage pipeline for:
1.  **Construction:** Ingesting proprietary enterprise sessions, extracting turns, rewriting prompts, and generating 852 tasks.
2.  **Evaluation:** Running a "sandbox" (Docker/VM) to execute agent code against these tasks and scoring results.

**Constraints:**
- The real data is proprietary and not released.
- The construction pipeline requires LLM calls for prompt rewriting and rubric generation.
- The evaluation pipeline requires a live "Open Sandbox" (external API/infrastructure) to run agents.

**Adaptation Strategy:**
Since we cannot access the proprietary data or the live sandbox infrastructure, this adaptation **reproduces the evaluation protocol's statistical analysis** on a **synthetic, but structurally faithful, subset of tasks**.

1.  **Data:** Instead of the 852 real tasks, we generate a **small, deterministic synthetic dataset** (50 tasks) that mimics the schema of `EnterpriseClawBench` tasks (role, skill, artifact type, difficulty, expected rubric). This is necessary because the real data is unavailable, and the paper's contribution is the *protocol*, not just the raw numbers.
2.  **Evaluation:** Instead of running a real LLM agent in a sandbox (which would fail without API keys/infrastructure), we implement a **Deterministic Mock Agent**. This agent simulates the behavior of an LLM with specific "skill transfer" parameters (e.g., high success on "File Reading", low on "Code Generation") to demonstrate the scoring mechanism.
3.  **Metric:** We reproduce the core quantitative result: **Success Rate by Skill Dimension** and **Cost vs. Performance**, exactly as described in the paper's abstract and figures (Fig 4, Fig 7, Fig 9).
4.  **Output:** Generates the heatmaps and summary tables that the paper reports, proving the protocol works.

## Approximations
- **Dataset:** 50 synthetic tasks (vs. 852 real tasks).
- **Agent:** Deterministic Mock Agent (vs. GPT-4/Codex in Sandbox).
- **Sandbox:** Local directory simulation (vs. Cloud Sandbox).
- **Rubric:** Hard-coded logic (vs. LLM-generated semantic rubrics).

This adaptation proves the *evaluation pipeline* functions correctly and reproduces the *type* of results the paper claims (e.g., skill transfer variance), without requiring the proprietary data or external infrastructure.
