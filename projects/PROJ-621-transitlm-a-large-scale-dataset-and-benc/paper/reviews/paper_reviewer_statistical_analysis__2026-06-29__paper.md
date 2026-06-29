---
action_items:
- id: 9f2209ed21f1
  severity: science
  text: The statistical analysis in this paper contains critical flaws undermining
    the validity of claims regarding "map-free" generation and "implicit spatial grounding."
    First, the evaluation of numeric field accuracy (Estimation Accuracy and MAPE)
    suffers from severe selection bias. As defined in Section 4.2, these metrics are
    computed *only* on samples achieving Route Exact Match (REM=1). Since REM is approximately
    71% for the best model, the reported MAPE of 1.33% reflects performance on a curated
artifact_hash: edae6ae2d895f06d190c806d301a85f463bbdd062907b9af82e2ca86a0aa3cf7
artifact_path: projects/PROJ-621-transitlm-a-large-scale-dataset-and-benc/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T22:47:22.542855Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: full_revision
---

The statistical analysis in this paper contains critical flaws undermining the validity of claims regarding "map-free" generation and "implicit spatial grounding."

First, the evaluation of numeric field accuracy (Estimation Accuracy and MAPE) suffers from severe selection bias. As defined in Section 4.2, these metrics are computed *only* on samples achieving Route Exact Match (REM=1). Since REM is approximately 71% for the best model, the reported MAPE of 1.33% reflects performance on a curated subset of "perfectly structured" cases. It fails to capture numeric errors in the ~29% of cases where the route structure is hallucinated. A rigorous analysis must report these metrics on the entire test set to provide an unbiased estimate of model performance.

Second, the "GPS-only ablation" study lacks statistical rigor. The authors claim that minimal performance degradation (e.g., -0.5% in REM) proves robust spatial grounding. However, no confidence intervals, standard errors, or hypothesis tests (such as McNemar's test for paired proportions) are provided. Without these, it is impossible to distinguish between a genuine effect of the training method and random variance, rendering the claim of "minimal degradation" statistically unsupported.

Third, the comparison with general-purpose LLMs in Table 1 is methodologically unsound. The baselines are evaluated on a simplified task (predicting only boarding/alighting stations), whereas the proposed model is evaluated on full station sequences. This difference in output space constitutes a confounding variable. The authors argue the simplified setting is "more lenient," but this does not account for the exponentially larger error space of full sequence generation. To support the claim that "domain-specific data is the critical enabler," baselines must be evaluated on the identical full-sequence task.

Finally, the ablation study on single-city vs. multi-city training (Table 5) attributes performance drops to "token-level sparsity" without controlling for potential distribution shifts in route complexity. The authors must demonstrate that the distribution of route lengths, transfer counts, and geographic densities is statistically identical between the Beijing-only and four-city datasets before attributing the delta to vocabulary sparsity.

To proceed, the authors must re-run numeric error analysis on the full test set, perform statistical significance testing on all ablation results, and ensure baseline comparisons use identical task definitions.
