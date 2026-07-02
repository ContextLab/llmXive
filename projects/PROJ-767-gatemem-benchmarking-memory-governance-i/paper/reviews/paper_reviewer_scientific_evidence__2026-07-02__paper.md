---
action_items:
- id: 48f338ec1f7e
  severity: science
  text: Table 1 reports results for 'GPT-5.4', 'Deepseek-V4-Pro', and 'Llama-4-Maverick'.
    These model names appear hypothetical or future-dated. Without access to these
    specific artifacts or clarification that they are aliases for existing models,
    the core empirical claims regarding backbone performance cannot be independently
    verified or replicated.
- id: 90811fe620fb
  severity: science
  text: The study relies on an LLM-as-a-judge for all primary metrics. The human validation
    sample (Appendix A4) covers only ~13% of the 2,218 checkpoints. Given the high
    stakes of leakage detection, a larger stratified human audit or a sensitivity
    analysis showing how judge variance impacts baseline rankings is required to rule
    out systematic bias.
- id: 615c91d70145
  severity: science
  text: The 'Active Forgetting' metric depends heavily on the specific phrasing of
    recovery queries. The paper does not report variance in failure rates across different
    attack phrasings for the same deleted fact. Without this, it is unclear if reported
    rates reflect true model robustness or sensitivity to specific prompt templates.
artifact_hash: 4f01dcbb1424147633a4eb29c69325a37730d0263065af71df4aeeea6414618e
artifact_path: projects/PROJ-767-gatemem-benchmarking-memory-governance-i/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T02:08:11.040849Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a comprehensive benchmark for memory governance, but the scientific evidence supporting the central claims regarding model performance requires clarification on reproducibility and statistical robustness.

First, the experimental results in Table 1 rely on backbone models such as "GPT-5.4", "Deepseek-V4-Pro", and "Llama-4-Maverick". These identifiers do not correspond to currently public or stable model releases. If these are hypothetical or future-dated names, the empirical claims regarding the superiority of specific backbones (e.g., Deepseek-V4-Pro vs. GPT-5.4) are currently unverifiable. For the evidence to be robust, the authors must either provide the specific model weights/API keys used, or clarify if these are aliases for existing models (e.g., GPT-4o, Llama-3). Without this, the comparative analysis of backbone capabilities remains speculative.

Second, the primary evaluation metric (MGS) is entirely dependent on an LLM-as-a-judge (GPT-4o). While the authors provide a human validation study in Appendix A4, the sample size is approximately 290 cases (roughly 13% of the total 2,218 checkpoints). In security and governance tasks, false negatives in leakage detection are critical. A 13% sample may not be sufficient to detect systematic biases in the judge's evaluation of "soft" leaks or indirect inferences. The authors should expand the human validation to a larger, stratified random sample (e.g., 10-20% of the full dataset) or provide a sensitivity analysis demonstrating how potential judge errors would alter the ranking of the baselines.

Finally, the "Active Forgetting" metric is sensitive to the specific phrasing of the recovery query. The paper reports aggregate failure rates but does not break down the variance of these rates across different attack types (e.g., direct confirmation vs. social engineering) for the same deleted fact. If a model fails only on specific prompt templates but succeeds on others, the aggregate score may misrepresent its true robustness. A more granular analysis of failure modes per attack type would strengthen the evidence that current agents are fundamentally brittle in this domain.
