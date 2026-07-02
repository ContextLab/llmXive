# Automated-review action items — GateMem: Benchmarking Memory Governance in Multi-Principal Shared-Memory Agents

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The bibliography entry 'c-001' links to a JSON file of GGUF stats, which is unrelated to the cited claim about LLM backbones. Verify and replace with the correct official model documentation URLs for GPT-5.4, Deepseek-V4-Pro, Llama-4-Maverick, and Gemini-2.5-Flash-Lite.
- **[science]** The paper cites 'GPT-5.4', 'Deepseek-V4-Pro', and 'Llama-4-Maverick' as evaluated backbones. These model versions do not currently exist in public release. If these are hypothetical or future-dated models, the claims regarding their specific performance metrics (Table 4) are factually unsupported by real-world evidence. Clarify the provenance of these models or correct the model names to existing versions.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript exhibits a tendency to overuse specialized terminology that, while precise for the authors, creates unnecessary friction for a broader audience. The term "principals" is used repeatedly (Abstract, Introduction, Section 3) to denote users or entities. In the context of LLM agents, "users" or "requesters" is more accessible; "principals" is a security-specific term that should be defined immediately if retained. The word "governance" is applied liberally (Abstract, Introduction, Sec

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The paper presents a logically sound framework for evaluating memory governance, with clear definitions for Utility (U), Access Control (A), and Active Forgetting (F). The multiplicative Memory Governance Score (MGS) is a coherent mechanism to enforce the requirement that a system must perform well on all three dimensions to be considered successful. The experimental results in Table 4.1 consistently support the conclusion that no single method dominates across all dimensions, and the trade-offs

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim that "no method simultaneously achieves strong utility, robust access control, and reliable forgetting" (Abstract) is contradicted by Long-Context (GPT-5.4) achieving 91.4% Utility and 80.1% MGS in Medical. Define "strong" or qualify the claim to "across all domains" to avoid overgeneralization.
- **[writing]** The conclusion that "current memory agents remain far from reliable shared institutional deployment" (Abstract) overreaches. The benchmark tests synthetic episodes; generalizing to all institutional deployments ignores potential human-in-the-loop safeguards or hybrid architectures not evaluated here.
- **[writing]** Describing Long-Context as the "best governance trade-off" (Abstract) ignores its high token cost (Table 2). The claim overreaches by prioritizing MGS without explicitly weighing the prohibitive economic cost for large-scale deployment in the trade-off definition.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The dataset contains sensitive simulated PII (medical diagnoses, household codes). Explicitly detail the IRB/ethics approval status or the specific de-identification/synthetic generation protocols used to ensure no real individuals are represented, as required for human-subject-adjacent benchmarks.
- **[writing]** The 'Active Forgetting' evaluation relies on LLM judges to detect 'leaks' of deleted data. Add a specific safety warning in the appendix regarding the risk of the judge model itself hallucinating or inadvertently reproducing the 'leak_targets' it is supposed to audit, potentially creating a feedback loop of exposure.
- **[writing]** The benchmark includes 'social engineering' and 'authority pressure' attack vectors (Appendix A1). Clarify that these are strictly simulated within the dataset generation pipeline and that the evaluation protocol does not involve real-world adversarial testing against live agents to prevent accidental deployment of harmful prompts.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** Table 1 reports results for 'GPT-5.4', 'Deepseek-V4-Pro', and 'Llama-4-Maverick'. These model names appear hypothetical or future-dated. Without access to these specific artifacts or clarification that they are aliases for existing models, the core empirical claims regarding backbone performance cannot be independently verified or replicated.
- **[science]** The study relies on an LLM-as-a-judge for all primary metrics. The human validation sample (Appendix A4) covers only ~13% of the 2,218 checkpoints. Given the high stakes of leakage detection, a larger stratified human audit or a sensitivity analysis showing how judge variance impacts baseline rankings is required to rule out systematic bias.
- **[science]** The 'Active Forgetting' metric depends heavily on the specific phrasing of recovery queries. The paper does not report variance in failure rates across different attack phrasings for the same deleted fact. Without this, it is unclear if reported rates reflect true model robustness or sensitivity to specific prompt templates.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Report confidence intervals or standard errors for the main metrics (U, A, F, MGS) in Table 1. The current point estimates do not convey the variance across the 2,218 checkpoints or the stability of the LLM-as-a-judge evaluation.
- **[science]** Clarify the statistical basis for the 'maximum absolute difference of 1.04 percentage points' in the judge-human validation (Table A4). Specify if this is a mean absolute error, a max deviation, or a bound derived from a specific statistical test, and provide the sample size (N) for each metric in the validation set.
- **[science]** The multiplicative MGS formula (U * (1-A) * (1-F)) creates a non-linear scale. When comparing methods, consider reporting statistical significance (e.g., bootstrap confidence intervals or paired tests) for MGS differences, as small changes in A or F can disproportionately affect the final score.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 1 (Introduction), the phrase 'a critical deployment regime remains insufficiently studied, namely the multi-principal shared environment' is slightly clunky. Consider rephrasing to 'a critical deployment regime, namely the multi-principal shared environment, remains insufficiently studied' for better flow.
- **[writing]** In Section 3 (Task Formulation), Equation 4 defines the turn tuple as (p_t, r_t, z_t, u_t) where r_t is the timestamp. However, the text immediately following states 'r_t is the timestamp' but the variable name 'r' typically suggests 'role' or 'requester' in this context, potentially causing confusion with p_t (speaker). Consider renaming r_t to t_t or timestamp_t for clarity.
- **[writing]** In Section 4 (Experiments), the footnote listing model URLs contains a broken link or mismatched citation for 'c-001' (url: .../gguf-public-stats/...). While this is a bibliography issue, it disrupts the reading flow if the PDF renders a broken link. Ensure all URLs in the bibliography are valid and point to the correct model documentation.
