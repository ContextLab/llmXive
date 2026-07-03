---
action_items:
- id: 7365bc348feb
  severity: science
  text: The cluster bootstrap analysis (Sec. 5.4, Tab. 10-11) resamples benchmarks
    to assess robustness to benchmark selection but does not account for run-to-run
    training variance. Given the stochastic nature of RL training (rollouts, advantage
    estimation), the reported 95% CIs may underestimate total uncertainty. Please
    clarify if single-run results are sufficient or if multiple seeds were averaged.
- id: 64848a70d9de
  severity: science
  text: The BCQ audit (Tab. 8) reports accuracy of 36-69%, yet the method relies on
    the student correctly identifying the teacher's trace. The paper does not explicitly
    quantify the false-positive rate (student selecting the wrong candidate) or analyze
    if the 'correct' teacher trace is actually optimal for the student's current capability,
    which could introduce noise into the gradient.
- id: ce136c721906
  severity: science
  text: The claim of 'super-additive' gains from combining BCQ/NCQ with the replay
    buffer (Sec. 5.3) is supported by ablation tables, but the interaction effect
    size is not statistically tested (e.g., via ANOVA or interaction terms). The current
    evidence relies on point-estimate differences which may not be robust to the variance
    inherent in RL training.
artifact_hash: 0fd8fa2b8ede4e304df4503c08bd0823fb3038495b7a89b759c4ee4216df60db
artifact_path: projects/PROJ-731-zone-of-proximal-policy-optimization-tea/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T03:39:35.493424Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a novel method (ZPPO) for improving small VLMs by keeping the teacher in the prompt rather than the gradient, addressing the zero-advantage problem in standard RL. The experimental design is generally robust, utilizing a large suite of 31 benchmarks across VLM, LLM, and Video domains, and comparing against strong baselines including distillation and standard GRPO variants. The inclusion of a cluster bootstrap to assess benchmark-selection robustness is a strong methodological choice.

However, the scientific evidence regarding the statistical significance of the reported gains requires clarification. The cluster bootstrap (Sec. 5.4) effectively addresses the variance introduced by the specific choice of benchmarks but does not account for the inherent stochasticity of the RL training process itself (e.g., random rollouts, initialization noise). The paper reports results from single training runs (implied by the lack of "mean ± std" notation in the main tables). For RL methods, where performance can vary significantly between seeds, a single run is often insufficient to claim a definitive improvement, especially for smaller effect sizes (e.g., the +0.3 to +0.4 pp gains on Video benchmarks). The confidence intervals provided are conditional on the benchmark set, not the training run.

Furthermore, the mechanism of BCQ relies on the student correctly discriminating between a teacher trace and a student trace. The audit in Table 8 shows BCQ accuracy is only 36-69%, meaning the student frequently fails to identify the correct candidate. While the authors argue this is evidence against trivial matching, the paper does not explicitly analyze the impact of these failures on the gradient update. If the student consistently picks the wrong candidate, does the method introduce a negative bias? The current evidence supports the *existence* of a signal but lacks a rigorous analysis of the *noise* introduced by the imperfect discrimination, which is critical for validating the "Zone of Proximal Development" claim.

Finally, the claim of "super-additive" effects (ZPPO > GRPO + BCQ + NCQ + Buffer) is supported by point estimates in the ablation tables (e.g., Tab. 9), but the interaction terms are not statistically tested. Given the variance in RL, the observed super-additivity could potentially be an artifact of a single lucky run. Replication with multiple seeds or a more rigorous statistical test for interaction effects would strengthen the central claim.
