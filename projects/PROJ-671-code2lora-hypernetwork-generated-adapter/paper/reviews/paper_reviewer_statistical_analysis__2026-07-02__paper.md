---
action_items:
- id: 94549c92847c
  severity: science
  text: Report statistical significance (e.g., p-values, confidence intervals, or
    effect sizes) for the reported performance gains (e.g., the +1.8pp OOD lead and
    +4.8pp CR lead). Without variance estimates or significance testing, it is unclear
    if these improvements are robust or due to random seed variance.
- id: 06b851ea195a
  severity: science
  text: Clarify the experimental protocol for hyperparameter selection. The paper
    reports best checkpoint selection by 'CR-val loss' but does not specify if the
    test set was used for any tuning or if a strict hold-out validation set was maintained
    throughout. Ensure the test set was never used for model selection to prevent
    data leakage.
- id: 3b0ded195ced
  severity: science
  text: The OOD evaluation section explicitly notes that target lengths are shorter
    in the OOD set, inflating Exact Match (EM) scores. However, the primary claim
    of superiority relies on EM. Provide a re-analysis of the OOD results using length-normalized
    metrics (e.g., EditSim or CodeBLEU) as the primary comparison to ensure the conclusion
    is not an artifact of the target length distribution shift.
artifact_hash: fad4da344b5e72bb204a08d5e9a960cbc3b14e42d22c2e81bf4f3bf3224fac8e
artifact_path: projects/PROJ-671-code2lora-hypernetwork-generated-adapter/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T23:42:21.811053Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical rigor of the evaluation requires strengthening to fully support the claims of superiority, particularly regarding the Out-of-Distribution (OOD) results and the magnitude of performance gains.

First, the paper reports point estimates for performance metrics (e.g., Exact Match percentages) without accompanying measures of uncertainty. In Table~\ref{tab:ood_results}, \codeloraevo{} leads \codelorastatic{} by 1.9 percentage points (74.1% vs 72.2%) and \texttt{sLoRA} by 1.8 points. Similarly, in the static track (Table~\ref{tab:main_results}), the gain over the best baseline is substantial. However, the manuscript does not report standard deviations, confidence intervals, or results from statistical significance tests (e.g., paired t-tests or Wilcoxon signed-rank tests) across multiple random seeds or data splits. Given the high variance observed in per-repo LoRA performance (median 62.5%, $\sigma=20.9$ as noted in Appendix~\ref{app:per_repo_variance}), it is critical to demonstrate that the observed improvements are statistically significant and not artifacts of random initialization or specific data splits.

Second, the OOD evaluation presents a known confound: the OOD targets are significantly shorter (median 7 chars vs 12--13 chars), which the authors admit inflates Exact Match scores. While the authors note that \codeloraevo{} still leads by a narrower margin, the primary claim of "superior generalization" relies heavily on the EM metric. To robustly support the conclusion that the model generalizes better rather than simply exploiting the shorter target length, the authors should re-evaluate the OOD results using length-agnostic metrics (EditSim, CodeBLEU) as the primary evidence, or explicitly normalize the EM scores. Currently, the reliance on EM in the presence of a known distribution shift weakens the statistical validity of the OOD claim.

Finally, the experimental protocol for model selection needs clarification. The text states that the "best checkpoint [is selected] by CR-val loss." It is essential to confirm that the test sets (CR Test, IR Test, OOD Test) were strictly held out and never used for hyperparameter tuning or early stopping decisions. If the test set influenced any part of the training loop or model selection, the reported performance metrics would be optimistically biased. The manuscript should explicitly state the separation of train/validation/test splits to ensure reproducibility and validity.

While the dataset statistics (Table~\ref{tab:dataset_actual}) and error analysis (Appendix~\ref{app:errors}) are descriptive and well-presented, the inferential statistics required to validate the comparative claims are missing.
