---
action_items:
- id: 962ee8b409c0
  severity: science
  text: Replace all citations with years 2025-2026 (e.g., GPT-5.4, Deepseek-V4-Pro,
    Mem0 2025) with verified, existing models and benchmarks. The current bibliography
    contains non-existent future artifacts that invalidate the experimental results.
- id: 12d56c6a9669
  severity: science
  text: Re-run the entire experimental pipeline (Table 1, Table 2) using only verified,
    publicly available LLM backbones (e.g., GPT-4o, Llama-3, Claude-3.5) and existing
    memory frameworks. The current results are based on hypothetical models.
- id: 49c3a96034e9
  severity: science
  text: Clarify the 'Active Forgetting' metric definition. The current definition
    conflates 'refusal' with 'no_memory' in a way that penalizes safe refusal behaviors
    (see Table 3 case study). The metric must distinguish between 'I don't know' (safe)
    and 'I remember but won't say' (unsafe) more rigorously.
artifact_hash: 4f01dcbb1424147633a4eb29c69325a37730d0263065af71df4aeeea6414618e
artifact_path: projects/PROJ-767-gatemem-benchmarking-memory-governance-i/paper/metadata.json
backend: dartmouth
feedback: Benchmark relies on unverified future-dated citations and hypothetical model
  backbones, invalidating the empirical claims.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T16:11:37.631487Z'
reviewer_kind: llm
reviewer_name: paper_reviewer
score: 0.0
verdict: major_revision_science
---

# Free-form review body

## Strengths
- **Novel Problem Formulation:** The paper correctly identifies a critical gap in current LLM agent benchmarks: the lack of evaluation for *shared-memory governance* in multi-principal environments. The distinction between single-user recall and multi-user access control/forgetting is timely and significant.
- **Comprehensive Benchmark Design:** The construction of 91 long-form episodes across four distinct domains (Medical, Office, Education, Household) with 2,218 hidden checkpoints is ambitious and well-structured. The inclusion of "soft-overreach" attacks and "closed active-forgetting chains" adds necessary realism.
- **Clear Metrics:** The proposed Memory Governance Score (MGS) using a multiplicative formula ($U \cdot (1-A) \cdot (1-F)$) effectively captures the trade-off between utility and safety, preventing high utility from masking security failures.
- **Strong Baseline Analysis:** The comparison across full-context, RAG, and external memory systems provides valuable insights into the current limitations of agent memory architectures, particularly the tension between retrieval depth and policy adherence.

## Concerns
- **Non-Existent Citations and Models (Critical):** The bibliography and experimental setup rely heavily on citations and model names that do not exist as of the current date.
    - **Models:** The paper evaluates against `GPT-5.4`, `Deepseek-V4-Pro`, `Llama-4-Maverick`, and `Gemini-2.5-Flash-Lite`. These models are not publicly available, and their specific versions (e.g., "5.4") appear fabricated or speculative.
    - **Benchmarks/Papers:** Several citations are dated 2025 or 2026 (e.g., `hu2025evaluating`, `zheng2025lifelongagentbench`, `shu2026remem`). While arXiv preprints can be future-dated in a hypothetical scenario, the specific combination of these "future" papers and "future" models suggests the entire experimental section is a simulation or hallucination rather than a report of actual empirical work.
    - **Impact:** Without verified, reproducible experiments on real models, the claims about "Long-Context prompting is strong but not governance-complete" are unsubstantiated. The results in Table 1 are effectively fictional.

- **Metric Ambiguity in Active Forgetting:**
    - In the case study (Table 3, Active Forgetting), `Long-Context` receives a `\warnmark` (mismatch) for responding with `refuse` ("I cannot confirm...") when the expected action was `no_memory`.
    - However, the definition of `no_memory` is "information is deleted or not available." If the model *remembers* the deleted info but refuses to say it (due to safety alignment), is that a failure of *forgetting* or a success of *safety*?
    - The current metric penalizes the model for *knowing* the info but refusing to say it, which might be the desired behavior for a safety-aligned model. The benchmark needs to distinguish between "reconstructing the fact" (failure) and "refusing to answer" (potentially safe, but not "forgetting"). The current setup conflates "behavioral non-recoverability" with "refusal," which may lead to misleading conclusions about the efficacy of forgetting mechanisms.

- **Judge Reliability:**
    - While the paper reports high human-judge agreement (97.7%), the judge itself is an LLM (`GPT-4o`). Given that the models being evaluated are also LLMs, there is a risk of "judge bias" where the judge favors the reasoning style of the models it is similar to. The validation sample size (approx. 50% of 579 checkpoints from *one* run) is relatively small for such a complex benchmark.

## Recommendation
The paper presents a compelling *concept* for a benchmark but fails as a scientific report because the core empirical evidence (experiments on GPT-5.4, etc.) is based on non-existent models and future-dated citations. The results cannot be verified or reproduced.

The verdict is **major_revision_science**. The authors must:
1.  **Replace all hypothetical models** with currently available, verifiable LLM backbones (e.g., GPT-4o, Llama-3.1, Claude-3.5 Sonnet).
2.  **Re-run the entire experimental pipeline** and update all tables and figures with real data.
3.  **Update the bibliography** to cite only existing, verifiable works. If the paper is intended as a "vision" or "proposal" for a future benchmark, it should be reframed as such, removing the specific experimental results and presenting them as "simulated" or "expected" outcomes with clear disclaimers.
4.  **Refine the Active Forgetting metric** to clearly distinguish between "successful refusal" (safe) and "successful forgetting" (no memory of the fact), ensuring the benchmark does not penalize safe refusal behaviors that are indistinguishable from forgetting in a black-box evaluation.

Until these fundamental scientific issues are resolved, the paper cannot be accepted.
