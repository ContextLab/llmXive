---
action_items:
- id: dbbcbca99e25
  severity: science
  text: The claim that 'Each setting is repeated three times' (Experiment Settings)
    lacks statistical rigor. For a benchmark of 1,000 instances, reporting only the
    mean of three runs without standard deviation, confidence intervals, or significance
    testing (e.g., paired t-tests or Wilcoxon signed-rank) makes it impossible to
    assess if the reported ~30% F1 gains are robust or due to random variance in the
    LLM's stochastic sampling.
- id: aa0993a9280a
  severity: science
  text: The annotation pipeline relies on 'two independent LLM annotators' followed
    by 'two expert annotators' (Dataset section). The paper does not report inter-annotator
    agreement (e.g., Cohen's Kappa or Fleiss' Kappa) for either the LLM stage or the
    human expert stage. Without these metrics, the reliability of the ground truth
    labels in TELBench is unverifiable, and the benchmark's validity is questionable.
- id: bb300fa15c14
  severity: science
  text: The ablation study (Figure 1c, Appendix) claims performance gains from specific
    modules (Claim Keeper, Support Seeker). However, the text does not specify if
    these ablation results are statistically significant or if the improvements are
    consistent across the three random seeds. A statistical test comparing the full
    DRIFT against the ablated variants is required to support the claim that the gains
    arise from the proposed modules rather than noise.
artifact_hash: 35ded812a75ceef1f48d0fbc3a809a8b976c23d29d82ed40e43751cfcaadee3e
artifact_path: projects/PROJ-664-https-arxiv-org-abs-2606-02060/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T03:03:29.215292Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling shift from outcome-based to process-based evaluation for deep-research agents, but the scientific evidence supporting the robustness of the proposed benchmark (TELBench) and the framework (DRIFT) is currently insufficient due to a lack of statistical rigor and reliability metrics.

First, the experimental protocol described in `sections/experiment.tex` states that "Each setting is repeated three times." However, the results in `tab/main_exp.tex` and `fig:performance` report only single-point estimates (means). For LLM-based evaluations, which are inherently stochastic, reporting only the mean without standard deviation, confidence intervals, or statistical significance testing (e.g., paired t-tests or bootstrap resampling) is a critical weakness. A 30 percentage point gain is substantial, but without variance estimates, it is impossible to determine if this improvement is consistent or an artifact of specific random seeds. The authors must provide error bars or statistical significance tests to validate the claim that DRIFT robustly outperforms baselines.

Second, the construction of the ground truth for TELBench relies heavily on an LLM-assisted pipeline (`sections/traj_collection.tex`). While the authors mention "two independent LLM annotators" and "two expert annotators," they fail to report any inter-annotator agreement metrics (e.g., Cohen's Kappa or Fleiss' Kappa). In annotation tasks involving complex semantic judgments like "unsupported commitment" or "premature finalization," human agreement is rarely perfect. Without reporting these agreement scores, the reliability of the gold labels is unknown. If the ground truth is noisy or inconsistent, the evaluation of DRIFT becomes unreliable, and the reported performance metrics may reflect the model's ability to match noisy labels rather than true error localization.

Finally, the ablation study in `sections/further_analysis` and `figure/appendix_ablation_prf_four_models_pastel_20260526.pdf` attributes performance gains to specific modules (Claim Keeper, Support Seeker). The text asserts these gains are "not merely caused by over-predicting," but lacks statistical evidence. The authors should include significance tests comparing the full DRIFT pipeline against its ablated variants to confirm that the modular design is the actual driver of performance, rather than random fluctuation.

To strengthen the scientific evidence, the authors must: (1) report standard deviations and statistical significance for all main results and ablation studies; (2) provide inter-annotator agreement scores for the TELBench annotation process; and (3) clarify the statistical power of the three-run experimental design.
