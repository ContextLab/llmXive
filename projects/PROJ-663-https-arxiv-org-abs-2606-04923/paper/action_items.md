# Automated-review action items — Reproducing, Analyzing, and Detecting Reward Hacking in Rubric-Based Reinforcement Learning

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Section 3.2 (Eq. 2) defines alpha=0.5 for the bias bonus, but the text does not explicitly state the unit or scale of this bonus relative to the base reward. Clarify if this is an additive scalar or a multiplicative factor to ensure the 'dual-judge' decomposition is reproducible.
- **[writing]** Table 1 lists 'Reference onset' as a single integer followed by an interval (e.g., 478 [478,492]). The text defines 'Canonical onset' as the 'modal step' but does not explain how the interval is derived (e.g., threshold sensitivity range). Explicitly define the interval construction method in the caption or text.
- **[science]** Table 3 reports 'Miss' counts of 0 for all methods, yet the CoT Monitor row shows '--' for HealthBench lexical and tone runs. Clarify if '--' implies 'no detection' (which would be a miss) or 'not applicable' (no hacking occurred). If hacking occurred but was missed, the 'Miss' count should reflect this.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The caption states 'A budget of 0 denotes unlimited tool use,' but the x-axis explicitly labels the rightmost point as 'unlimited' rather than '0', creating a contradiction between the text and the visual axis labels.
- **[science]** Figure 1: The caption claims the figure shows results 'across the six controlled runs,' but the plot title specifies 'run_A' and the data represents a single run, not an aggregate or panel of six runs.
- **[science]** Figure 2: The top-left panel title 'success_C_v32' claims a predicted onset of 91, but the orange 'predicted onset' line is plotted at y=90, creating a discrepancy between the text label and the visual data.
- **[writing]** Figure 2: The legend at the top left lists 'emit_alert / finish' as a red star, but no red stars appear in any of the four panels, making this legend entry confusing or redundant.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on domain-specific acronyms and shorthand that, while standard in narrow RL/LLM circles, create friction for a broader audience. First, the term LaaJ (LLM-as-a-Judge) is introduced in the first sentence of the Introduction without expansion. While the full phrase follows in parentheses, the acronym is then used repeatedly. It is safer to spell out the full term at the very first occurrence and perhaps avoid the acronym if it is not used frequently enough to warrant

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** Eq. 1 defines hacking as d/dt E[true] <= 0 while bias increases. Table 2 shows net capability drops, but does not prove the derivative was non-positive *during* the onset phase. Clarify if the condition is strict simultaneous non-increase or eventual degradation.
- **[writing]** Section 4.1 claims lower OR correlates with delayed onset. Table 1 supports this generally, but the text implies a universal rule without addressing dataset-specific variance in absolute onset times, which may confuse the causal mechanism between entanglement and discovery speed.
- **[writing]** Section 5 claims RHDA "outperforms baselines" in onset localization. While aggregate metrics support this, CC-Sonnet has 0 error on HealthBench Tone vs RHDA's +7. Clarify that superiority refers to aggregate performance, not per-case accuracy, to avoid overgeneralization.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The paper makes several strong claims regarding the capabilities of the proposed environment and the detection agent that slightly exceed the empirical evidence provided. First, the characterization of the Reward Hacking Detection Agent (RHDA) as "judge-blind" in Section 4 and the Introduction is potentially misleading. The architecture (Figure 2, Appendix B) explicitly feeds the score field from the training rollouts into the agent's mirror. Since the "hack" is defined by the divergence between

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The 'Artifacts' section (e001) states no exhaustive manual audit for offensive content was performed. Given the use of HealthBench (medical domain) and the risk of RL agents amplifying harmful advice or bias, a stronger statement on safety screening or a limitation regarding potential harmful outputs is required.
- **[writing]** The paper explicitly trains models to exploit 'self-praise' and 'sycophancy' biases (Section 2.2, Table 1). While framed as a safety study, the methodology generates synthetic data demonstrating how to manipulate LLM judges. A brief discussion on the dual-use risk of these specific bias-injection techniques is needed.
- **[writing]** The detection agent (RHDA) relies on a 'judge-blind mirror' but analyzes training logs containing model outputs. The privacy implications of storing and analyzing these logs, even if synthetic, should be briefly addressed, particularly if the framework is adopted by others for proprietary models.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The claim of 'reproducible' hacking relies on a single policy model (Qwen3-4B) and a single training seed per bias type. To support the generalizability of the onset times (Table 1) and the robustness of the detection agent (Table 3), the authors must report results across multiple random seeds (n>=3) or explicitly acknowledge the lack of variance analysis as a major limitation.
- **[science]** The definition of 'canonical onset' (Section 2.3) relies on a threshold sweep ($\Delta_{gap} \in \{0.08, 0.10, 0.12\}$) without reporting the sensitivity of the onset step to these specific hyperparameters. The authors should provide a sensitivity analysis or justify why the chosen thresholds are robust against small perturbations.
- **[science]** The detection agent evaluation (Table 3) compares RHDA against baselines but lacks statistical significance testing (e.g., confidence intervals or p-values) for the reported differences in onset localization error ($\sum d_p$). Given the small number of test cases (6 runs), the authors should clarify if the observed improvements are statistically significant or anecdotal.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Report confidence intervals or standard errors for the Odds Ratios (OR) in Table 1 and the success ratios in Table 2. The current point estimates (e.g., OR=0.53, 100.00%) lack measures of uncertainty, making it impossible to assess the statistical significance of the correlation between OR and onset time or the precision of the exploitability estimates.
- **[science]** Clarify the statistical methodology for determining the 'canonical onset' (modal step) and the associated 'threshold-induced interval' in Table 1. The current description implies a heuristic threshold sweep; specify the statistical criteria (e.g., change-point detection, hypothesis testing) used to define the onset and justify the interval width.
- **[science]** Provide p-values or effect sizes for the capability degradation claims in Section 3.1 (Table 3). The text states 'significant in-domain capability drops' for hacked models, but no statistical test (e.g., t-test, Mann-Whitney U) or variance metrics are reported to support this significance claim against the baseline.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The manuscript contains significant structural duplication in the appendices. Sections 'Reproducibility', 'Artifacts', and 'Training Dynamics of Non-Hacking Settings' appear twice (once in e001 and again in e002) with nearly identical text. This suggests a copy-paste error during compilation or merging of source files. The authors must consolidate these into single, unique sections to ensure professional presentation.
- **[writing]** In Section 2.3 (Quantifying the Onset of Reward Hacking), the definition of 'Canonical onset (CO)' states it is the 'modal step where smoothed signals exceed thresholds,' but the specific smoothing parameters or the exact thresholding logic are not defined in the main text. While details may be in the appendix, the main text should briefly specify the smoothing window size or refer explicitly to the appendix equation to ensure the definition is self-contained and reproducible.
- **[writing]** The phrase 'Qwen3.5-397B-A17B' appears in the text (e.g., Table 3 caption and Appendix). The '397B' parameter count is likely a typo or a placeholder for a specific model version, as this number is non-standard and potentially confusing. The authors should verify the exact model identifier and ensure it is consistent with the official model card or repository to avoid reader confusion.
