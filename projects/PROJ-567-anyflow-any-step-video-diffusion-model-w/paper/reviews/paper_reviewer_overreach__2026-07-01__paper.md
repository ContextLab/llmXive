---
action_items:
- id: 45768e9173fc
  severity: writing
  text: The paper makes several strong claims regarding the novelty and statistical
    significance of the AnyFlow framework that appear to overreach the provided evidence.
    First, the Abstract and Introduction repeatedly assert that AnyFlow is the "first
    any-step video diffusion distillation framework based on flow maps." However,
    Section 2 (Related Work) explicitly cites a concurrent work, TMD (Nie et al.,
    2026), which "also studies a flow map formulation for bidirectional video diffusion
    distillation." W
artifact_hash: 3aad81d8a133042c5a798b8bf30d90974b62e8f4dc5a0e7e17e6ccdaa711ef9d
artifact_path: projects/PROJ-567-anyflow-any-step-video-diffusion-model-w/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T20:03:53.876412Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several strong claims regarding the novelty and statistical significance of the AnyFlow framework that appear to overreach the provided evidence.

First, the Abstract and Introduction repeatedly assert that AnyFlow is the "first any-step video diffusion distillation framework based on flow maps." However, Section 2 (Related Work) explicitly cites a concurrent work, TMD (Nie et al., 2026), which "also studies a flow map formulation for bidirectional video diffusion distillation." While the authors distinguish their work by focusing on "simulation efficiency" via shortcut decomposition versus TMD's architectural changes, the absolute claim of being the "first" framework is an over-claim. The novelty should be framed more precisely as the first to achieve *efficient* any-step distillation via flow map backward simulation, rather than the first to apply flow maps to video distillation generally.

Second, the manuscript makes a definitive statistical claim in the text preceding the Ethics Statement: "All reported improvements are evaluated with paired t-tests and Bonferroni correction to control the family-wise error rate." This is a significant over-claim of rigor because the paper does not report the resulting p-values, the specific confidence intervals (beyond a generic mention), or the effect sizes. Given that many reported improvements are marginal (e.g., 84.05 vs 83.25, or 83.96 vs 83.49), asserting statistical significance without presenting the actual test statistics is misleading. The authors must either provide the statistical tables or soften the language to "we observed consistent improvements" rather than claiming formal significance testing was successfully applied and validated.

Third, there is a contradiction in the evaluation protocol that undermines the "fair comparison" claim. The text states, "Results for all other methods are taken directly from their original papers," yet it also claims to "re-evaluate key counterparts... using the official VBench augmented prompts" for a "fair comparison." Specifically, the comparison against Krea-Realtime-14B (83.25) appears to be a direct citation from another paper, while AnyFlow is evaluated on 600 videos (200 prompts x 3 seeds). If the prompt distributions or random seeds differ between the cited Krea score and the AnyFlow evaluation, the claim of a "fair comparison" is an overreach. The authors must clarify whether the Krea baseline was re-run or if the comparison is cross-study, and adjust the "fair comparison" language accordingly.
