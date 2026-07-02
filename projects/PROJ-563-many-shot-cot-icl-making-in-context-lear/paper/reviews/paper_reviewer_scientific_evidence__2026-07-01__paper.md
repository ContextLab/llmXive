---
action_items:
- id: 2d8e2c4ac2e9
  severity: science
  text: The claim of a 5.42 percentage-point gain on geometry (Abstract) lacks explicit
    statistical significance testing (e.g., p-values or confidence intervals) in the
    main text. While Appendix Table 3 shows means and standard deviations, the main
    text should explicitly state whether the observed gains are statistically significant
    to rule out random variance, especially given the reported order-scaling variance.
- id: 45405aa75297
  severity: science
  text: The 'Procedural-corruption ablation' (Table 1, section/factor.tex) shows a
    performance drop at n=128 but not at n=16. The sample size (number of test instances)
    for these specific ablation experiments is not explicitly stated in the text or
    table captions. Please report the number of test samples (N) used to calculate
    these accuracy percentages to allow for proper assessment of the effect size and
    statistical power.
- id: b573d9f0e2a3
  severity: science
  text: The correlation analysis between curvature and performance (Section 4.3.2)
    reports Pearson r values (e.g., -0.547) but does not provide the number of permutations
    (k) sampled to generate these correlations. Since the correlation is computed
    over random orderings, the robustness of this finding depends on the sampling
    size. Please specify the number of random orderings used for the correlation analysis.
artifact_hash: da80d19d18126d829231e022c90784234c941daee73db4750a219950884e0e6f
artifact_path: projects/PROJ-563-many-shot-cot-icl-making-in-context-lear/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T23:25:56.557421Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling empirical investigation into the scaling behavior of Many-Shot Chain-of-Thought In-Context Learning (CoT-ICL), challenging the assumption that established many-shot ICL rules (e.g., order insensitivity, similarity-based retrieval) transfer to reasoning tasks. The experimental design is generally sound, utilizing a diverse set of models (reasoning vs. non-reasoning) and tasks (math, narrative, classification) to isolate the effects of demonstration scaling and ordering.

However, the strength of the scientific evidence is slightly undermined by a lack of explicit statistical rigor in reporting key quantitative claims. Specifically:

1.  **Statistical Significance of Gains:** The abstract and Section 5 highlight a "5.42 percentage-point gain" on geometry using the proposed CDS method. While Table 2 (section/curvature.tex) provides mean accuracies, it does not report p-values or confidence intervals for the comparison between the "origin" and "CDS" baselines. Given the paper's own finding that performance variance increases with the number of demonstrations (Section 4.1), it is critical to demonstrate that the observed improvements are statistically significant and not artifacts of random ordering variance. The Appendix provides some mean/std data (Table 3), but the main text should explicitly confirm the statistical significance of the primary claims.

2.  **Sample Sizes for Ablations:** In the "Procedural-corruption ablation" (Table 1, section/factor.tex), the authors compare valid vs. corrupted rationales. The table reports accuracy percentages but omits the number of test instances (N) used to derive these figures. Without knowing the sample size, it is difficult to assess the reliability of the observed drop at n=128 versus the stability at n=16. Similarly, the correlation analysis in Section 4.3.2 reports Pearson correlation coefficients between curvature and accuracy but does not state the number of random permutations (k) sampled to compute these correlations. A small k would make the correlation estimate unstable.

3.  **Effect Size Context:** The paper reports absolute accuracy gains (e.g., ~5-6 points). While these are practically relevant, providing effect sizes (e.g., Cohen's d) relative to the baseline variance would strengthen the argument that the ordering method provides a robust improvement over the noise introduced by random ordering.

The core findings—that similarity-based retrieval fails for reasoning and that ordering matters more at scale—are supported by the data trends shown in the figures and tables. However, the manuscript requires minor revisions to explicitly report sample sizes, statistical significance tests, and the number of permutations used in correlation analyses to fully substantiate the robustness of these claims.
