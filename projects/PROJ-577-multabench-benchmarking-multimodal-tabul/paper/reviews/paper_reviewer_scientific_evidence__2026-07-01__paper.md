---
action_items:
- id: a0dcddf3a30c
  severity: science
  text: The curation pipeline uses a fixed threshold (delta=0.001) for acceptance.
    The paper must report the distribution of gains (Delta_Joint and Delta_Awareness)
    across the 56 text and 16 image candidates to demonstrate that the 0.001 threshold
    is not arbitrary and that the selected datasets are not just marginally passing.
    Without this distribution, the robustness of the benchmark selection is unclear.
- id: 516e4c117e8a
  severity: science
  text: The regression target discretization (20 bins) for TAR finetuning is a significant
    methodological choice that alters the learning objective. The paper must provide
    evidence (e.g., a sensitivity analysis or ablation) showing that this discretization
    does not artificially inflate the TAR gains compared to a direct regression finetuning
    baseline, or explain why the discretization is necessary for stability without
    introducing bias.
- id: 6a426139a703
  severity: science
  text: The claim that TAR gains generalize across 'several tabular learners' relies
    on 5 curation models and 7 additional models. However, the additional models (e.g.,
    TabICLv2, ConTextTab) show significantly lower win rates (55-73%) compared to
    GBDTs (80-93%). The paper should explicitly discuss this variance and whether
    the 'generalization' claim holds for all model families or is primarily driven
    by GBDTs and specific TFMs.
- id: a79216962f6b
  severity: science
  text: The curation process involves subsampling up to 10,000 examples. For datasets
    with N < 10,000 (e.g., CS:GO Skins, N=956), the full set is used, but for larger
    ones, a subset is used. The paper must clarify if the 5 random seeds account for
    the subsampling variance and if the performance gains are consistent across different
    random subsamples, or if the results are sensitive to the specific 10k subset
    chosen.
artifact_hash: 28e097e31933ecce294eb34fd92a9e53c4dcbbab117fcc0a77af75a314777084
artifact_path: projects/PROJ-577-multabench-benchmarking-multimodal-tabul/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T20:50:07.997116Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The scientific evidence supporting the necessity of Target-Aware Representations (TAR) and the validity of the MulTaBench curation is generally strong but lacks critical statistical depth in the selection process and robustness analysis.

First, the curation pipeline's acceptance criteria rely on a fixed threshold $\delta=0.001$ (Appendix \ref{app:curation_formal}). While this ensures a minimum gain, the paper does not present the distribution of $\Delta_{\text{Joint}}$ and $\Delta_{\text{Awareness}}$ across the 56 text and 16 image candidates. Without visualizing or tabulating the full distribution of gains, it is impossible to determine if the 41% acceptance rate for text and 31% for image datasets reflects a natural bimodal distribution of task properties or if the threshold is arbitrarily placed to include marginally significant cases. The authors should include a histogram or cumulative distribution plot of the gains for all candidates to demonstrate that the selected datasets are distinct from the rejected ones in terms of effect size magnitude, not just binary pass/fail status.

Second, the handling of regression tasks introduces a potential confound. For regression, the continuous target is discretized into 20 bins to enable cross-entropy loss during the TAR finetuning step (Appendix \ref{app:curation_tar_training}). This fundamentally changes the learning objective from regression to classification. The paper claims this is for stability but does not provide evidence that this discretization does not artificially inflate the TAR gains. A robustness check comparing the TAR gains under this discretized setup versus a direct regression finetuning (e.g., MSE loss) on a subset of datasets is necessary to ensure the observed benefits are not artifacts of the classification proxy.

Third, the claim of generalization across "several tabular learners" (Section \ref{sec:results}) is partially undermined by the variance in win rates. While GBDTs show 80-93% win rates, models like TabICLv2 and ConTextTab show significantly lower rates (55-73% and 73% respectively, Table \ref{tab:win_rate}). The paper treats the "generalization" as a uniform finding, but the data suggests the benefit of TAR is highly model-dependent. The authors should explicitly discuss this heterogeneity and clarify whether the benchmark is specifically optimized for GBDTs and certain TFMs, or if the lower performance of other models indicates a limitation in the TAR approach for those architectures.

Finally, the subsampling strategy (up to 10,000 examples) for large datasets introduces variance. The paper mentions 5 random seeds, but it is unclear if these seeds account for the subsampling of the dataset itself or just the model initialization. If the 10k subset is fixed per dataset and only the model training is randomized, the results may be sensitive to the specific subset chosen. The authors should clarify the randomization protocol and, if possible, report the variance of the TAR gain across different random subsamples to ensure the findings are not dependent on a specific 10k slice of the data.
