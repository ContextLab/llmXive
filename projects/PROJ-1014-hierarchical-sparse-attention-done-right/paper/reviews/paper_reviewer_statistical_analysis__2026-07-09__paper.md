---
action_items:
- id: 72605a4abee4
  severity: writing
  text: "Section 4.1 and Tables 345M_main_ppl/ruler report single-point perplexity\
    \ and RULER scores without any measure of variance (e.g., standard deviation or\
    \ confidence intervals) across training seeds or runs. Given the stochastic nature\
    \ of LLM training, reporting a single number implies false precision. Report mean\
    \ \xB1 SD over at least 3 seeds for all main results, or explicitly state that\
    \ results are from a single run and treat them as such."
- id: b5c0a63a721d
  severity: writing
  text: Section 4.3 (Ablation Study) and Tables 345M_ablation_ppl/ruler present comparisons
    of multiple variants (e.g., Q-Cal ranks, positional encodings) without correcting
    for multiple comparisons. With ~10+ pairwise comparisons per metric, the risk
    of false positives is high. Apply a Holm-Bonferroni or Benjamini-Hochberg correction
    to the reported p-values (if tests were run) or explicitly acknowledge the multiplicity
    issue when claiming 'significant' improvements.
- id: b333dc20c945
  severity: writing
  text: "Figure 4 (efficiency_speedup_bars.pdf) and Section 4.4 report specific speedup\
    \ factors (e.g., '13.5x', '15.7x') and latency values (e.g., '5.0s vs 67.0s')\
    \ with high precision (one decimal place) but provide no error bars or standard\
    \ deviation across multiple inference runs. Inference latency is subject to system\
    \ noise; report mean \xB1 SD over at least 5 runs to validate the stability of\
    \ these speedup claims."
artifact_hash: c95e527feac1da55ce3c1a4f78a6e7762db38d741afaaaef5a9558e2491c1f16
artifact_path: projects/PROJ-1014-hierarchical-sparse-attention-done-right/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-09T02:55:39.699525Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical treatment of the results in this paper is generally consistent with common practices in the LLM systems literature (reporting point estimates), but it lacks the rigorous uncertainty quantification required to distinguish robust improvements from stochastic noise or system variance.

**1. Missing Uncertainty in Main Results (Section 4.1, Tables 345M_main_ppl/ruler):**
The paper reports single-point values for perplexity (e.g., "4.94") and RULER accuracy (e.g., "100", "95") for the proposed HiLS-Attention and baselines. In deep learning, training dynamics are stochastic; a single run does not represent the expected performance of the method. The absence of standard deviation (SD), standard error (SE), or confidence intervals (CI) makes it impossible to determine if the reported differences (e.g., HiLS at 4.94 vs. Full-Attn at 4.96) are statistically significant or merely within the noise floor of training. The authors should report results as mean ± SD over at least 3 independent training seeds. If only one seed was used, this must be explicitly stated, and claims of "better" or "comparable" performance should be softened to reflect the lack of statistical power.

**2. Multiple Comparisons in Ablation Studies (Section 4.3, Tables 345M_ablation_ppl/ruler):**
The ablation study evaluates numerous variants (different ranks for Q-Cal, different positional encodings, presence/absence of landmark tokens, etc.). The text highlights specific variants as "best" or "significantly better" based on point estimates. With the number of comparisons made, the probability of finding a "best" variant by chance alone is non-negligible. While formal hypothesis testing is not always standard in ML ablations, the authors should either apply a correction for multiple comparisons (e.g., Bonferroni) if p-values are implied, or at minimum, avoid using the term "significant" without a statistical test and acknowledge the exploratory nature of these comparisons.

**3. Precision of Inference Benchmarks (Section 4.4, Figure 4):**
The inference efficiency section reports latency and speedup with high precision (e.g., "13.5x", "5.0s"). Inference latency on GPUs is subject to significant variance due to system noise, memory bandwidth fluctuations, and kernel launch overheads. Reporting a single measurement or a mean without error bars (e.g., ± SD) gives a false sense of precision. The authors should report the mean and standard deviation of latency over multiple runs (e.g., 5-10 runs) to demonstrate that the observed speedups are stable and not artifacts of a single lucky run.

**4. General Reporting Standards:**
Throughout the paper, numbers are reported to two or three decimal places (e.g., perplexity 3.234). While this is common, without accompanying variance metrics, this precision is misleading. The statistical machinery is sound in its arithmetic, but the inferential claims (that one method is "better" than another) are not supported by the reported uncertainty measures. Addressing these reporting gaps is essential for the numbers to mean what the paper claims they mean.
