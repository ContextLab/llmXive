---
action_items:
- id: eaa0fa7f14ff
  severity: science
  text: The user study (Tab. 1, App. D) reports percentages (e.g., 62.23%) from 48
    prompts and 8 annotators but lacks confidence intervals or significance tests
    (e.g., binomial test) to confirm the improvements over FIFO-Diffusion are statistically
    significant rather than random variation.
- id: 804f00d137d0
  severity: science
  text: Ablation tables (Tab. 2, Tab. 3) present single-point performance metrics
    without standard deviations or error bars, making it impossible to assess the
    stability of the reported gains (e.g., the 0.01% memory increase) or the robustness
    of hyperparameter choices.
- id: d26cd6280bdd
  severity: science
  text: The claim of 'state-of-the-art' performance relies on point estimates from
    VBench and NarrLV; the manuscript should clarify if these benchmarks provide variance
    estimates or if the authors performed multiple runs to ensure the observed differences
    are not due to stochasticity in the generation process.
artifact_hash: 2fc45fd89cfd8c3cc27102ad20713af6a66d4f721af1c258a0cd318f7ea682b3
artifact_path: projects/PROJ-614-enhancing-train-free-infinite-frame-gene/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T14:35:22.099785Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript presents a compelling method (MIGA) for train-free long video generation, but the statistical rigor of the experimental evaluation requires strengthening to fully support the claims of superiority and stability.

First, the human evaluation results presented in Table 1 (Appendix D) are reported as precise percentages (e.g., 62.23% preference for MIGA) derived from a sample of 48 prompts and 8 annotators. While the point estimates favor the proposed method, the manuscript lacks any measure of statistical significance. Given the sample size, it is unclear if these differences are statistically distinguishable from chance. The authors should perform a binomial test or report 95% confidence intervals for these preference rates to validate that the observed improvements are robust.

Second, the ablation studies (Tables 2 and 3 in the main text and Appendix) report single-point performance metrics for various hyperparameters (e.g., $L_{\mathrm{zig}}$, $\delta_{\mathrm{adju}}$). In stochastic generative models, a single run per configuration is often insufficient to distinguish true performance gains from random noise. The absence of standard deviations, error bars, or results from multiple random seeds makes it difficult to assess the stability of the method. For instance, the reported memory increase of 0.10% (Table 4) is extremely small and likely within the margin of error for a single measurement; reporting variance would clarify if this is a consistent overhead or a measurement artifact.

Finally, while the VBench and NarrLV scores are presented as definitive improvements, the manuscript does not discuss the variance inherent in these automated benchmarks. Video generation is inherently stochastic; without reporting results over multiple seeds or providing confidence intervals for the benchmark scores, the claim of "state-of-the-art" performance rests on point estimates that may not be reproducible. The authors should either report mean and standard deviation over multiple runs or explicitly state the limitations of single-run reporting in the context of their conclusions.
