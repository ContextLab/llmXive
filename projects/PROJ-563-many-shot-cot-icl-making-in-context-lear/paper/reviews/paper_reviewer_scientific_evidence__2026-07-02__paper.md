---
action_items:
- id: 310e674c8cdc
  severity: science
  text: The claim that CDS yields 'up to a 5.42 percentage-point gain' (Abstract)
    lacks statistical significance testing. Table 1 shows point estimates, but without
    p-values or confidence intervals for the differences between 'origin' and 'CDS',
    it is unclear if these gains exceed random variance, especially given the observed
    order-scaling variance in Section 4.4.
- id: f2f6f71dcfeb
  severity: science
  text: The correlation analysis in Section 4.3.2 (r=-0.547) relies on only 5 random
    permutations per task to establish the curvature-performance relationship. This
    sample size is insufficient to robustly claim a strong negative correlation or
    to rule out spurious associations driven by the specific dataset splits used.
- id: db6a3e75eb0b
  severity: science
  text: The 'procedural-corruption' ablation (Table 2) uses a static CoT from the
    first demonstration for all examples. This conflates 'procedural mismatch' with
    'repetition bias' or 'loss of diversity'. A stronger control would involve shuffling
    the original CoTs or using CoTs from a different task to isolate the effect of
    procedural alignment specifically.
artifact_hash: da80d19d18126d829231e022c90784234c941daee73db4750a219950884e0e6f
artifact_path: projects/PROJ-563-many-shot-cot-icl-making-in-context-lear/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:15:13.120237Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling empirical investigation into the scaling behavior of Many-Shot CoT-ICL, challenging the assumption that more demonstrations always yield stable improvements. The distinction drawn between reasoning and non-reasoning tasks, and between reasoning-oriented and standard LLMs, is well-supported by the scaling curves in Figures 1 and 2. The evidence that similarity-based retrieval fails on reasoning tasks (Section 4.2) is particularly strong, supported by both aggregate trends and the qualitative example in Appendix Table 1.

However, the statistical robustness of the central claims regarding the proposed CDS method and the curvature correlation requires strengthening. First, the reported performance gains of CDS (e.g., the 5.42% gain mentioned in the abstract and Table 1) are presented as point estimates. Given the paper's own finding that performance variance increases with the number of demonstrations (Section 4.4), the absence of statistical significance tests (e.g., paired t-tests or bootstrap confidence intervals) for the CDS vs. Origin comparisons is a critical gap. Without this, it is difficult to distinguish genuine methodological improvement from random fluctuation in the prompt ordering.

Second, the correlation analysis in Section 4.3.2, which links embedding-space curvature to accuracy, is based on only five random permutations per task. While the reported correlation coefficients (e.g., r=-0.628) appear strong, a sample size of N=5 is statistically fragile and highly susceptible to outliers. A more robust validation would involve sampling a larger number of random orderings (e.g., 20-50) to establish the stability of this correlation.

Finally, the "procedural-corruption" ablation in Table 2, while conceptually sound, uses a static CoT from the first demonstration for all subsequent examples. This design introduces a confound: the model is not just receiving "mismatched" procedures, but also a highly repetitive, non-diverse context. It is unclear if the performance drop is due to the procedural mismatch or the lack of demonstration diversity. A control condition using shuffled original CoTs or CoTs from a semantically distinct but structurally similar task would better isolate the specific contribution of procedural alignment.
