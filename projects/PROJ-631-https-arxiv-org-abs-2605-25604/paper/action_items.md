# Automated-review action items — DVAO: Dynamic Variance-adaptive Advantage Optimization for Multi-reward Reinforcement Learning

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The review focuses on the accuracy of factual claims and the alignment between these claims and the provided evidence (proofs, tables, figures). 1. Magnitude of Advantages (Abstract, Introduction, Proposition 1): The paper claims that Reward Combination (RC) generates advantages with "excessively large squared magnitudes" leading to instability. Proposition 1 (Appendix A.1) mathematically proves that the *mean squared advantage* of RC is greater than or equal to that of Advantage Combination (AC

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[fatal]** Figure 1: The rendered image shows a single plot of 'Accuracy Reward' vs 'Training Step' with three lines (RC, AC, DVAO), but the caption describes a three-panel figure ('Left', 'Middle', 'Right') containing accuracy reward, length reward, and response length. The visual content does not match the caption description.
- **[science]** Figure 1: The caption states 'top=mean, bottom=std' implying error bars or shaded regions for standard deviation, but the plot displays only single jagged lines without any visible error bands or separate standard deviation plots.
- **[fatal]** Figure 2: The rendered image shows a single plot of 'Accuracy Reward' vs 'Training Step', but the caption describes a three-panel layout ('Left: accuracy reward... Middle: length reward... Right: average response length'). The figure is missing the middle and right panels described in the caption.
- **[science]** Figure 2: The caption states 'top=mean, bottom=std' for the accuracy reward panel, but the rendered image shows only a single line per method without the corresponding standard deviation (std) plot or error bands.
- **[science]** Figure 3: The caption 'Mathematical Reasoning Task' does not match the axes labels 'Acc.' and 'Len.', which imply a Pareto frontier or trade-off plot rather than a task-specific result. The plot lacks a clear definition of what the connected points represent (e.g., training steps, hyperparameter sweeps) or the specific metric being plotted.
- **[writing]** Figure 3: The y-axis label 'Len.' is ambiguous and likely truncated; it should be explicitly defined as 'Response Length' or similar to match the context of the paper.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on specialized reinforcement learning (RL) and optimization terminology that obscures the core contributions for non-specialist readers. The term "scalarization" appears in the Abstract and Introduction without definition; it should be replaced with "combining multiple rewards into a single score" or defined immediately. Similarly, "rollout group" is used frequently (Abstract, Method, Appendix) but is opaque to readers outside RL; "batch of generated responses" or "

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The logical consistency of the paper is generally strong, with the proposed DVAO method following a clear derivation from the identified limitations of Reward Combination (RC) and Advantage Combination (AC). The mathematical proofs in the appendix (Propositions 1-3) correctly establish the theoretical bounds and sensitivity properties claimed in the main text. Specifically, the derivation showing that DVAO bounds advantage magnitudes (Prop 2) and introduces cross-objective regularization (Prop 3

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The paper makes several claims that extend beyond the scope of the provided theoretical proofs and empirical evidence, specifically regarding the "hyperparameter-free" nature of the method and the universality of its theoretical guarantees. First, the Abstract and Conclusion repeatedly describe DVAO as a "hyperparameter-free weighting scheme." This is an overstatement. While the method dynamically adjusts the *combination* weights based on variance, it still relies on the initial base weights $\

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The 'Limitations' section (Appendix) acknowledges that DVAO may up-weight noisy or poorly designed rewards. Explicitly discuss the safety implications if a malicious actor uses this mechanism to amplify harmful reward signals (e.g., toxicity or jailbreak success) in a multi-objective setting.
- **[writing]** The paper uses datasets like DAPO-MATH-17K and ToolACE. While these appear to be standard benchmarks, the manuscript lacks a statement confirming that the training data does not contain personally identifiable information (PII) or sensitive user data, which is a standard requirement for RLHF/RLAIF pipelines.
- **[writing]** The 'Implementation Details' mention using Qwen3 and Qwen2.5 models. Clarify the provenance of these base models and confirm that their pre-training data usage complies with relevant licensing and ethical guidelines, as the paper builds upon them for alignment.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The paper claims DVAO achieves 'superior multi-objective Pareto frontier' and 'robust training stability' based on single-seed runs. To rule out stochastic variance in RL, report results averaged over at least 3 independent random seeds with standard deviation error bars in Tables 1 and 2, and explicitly state the seed count in Appendix A.
- **[science]** Theoretical Proposition 2 proves |A_DVAO| <= |A_sum|, but the empirical evidence for 'training stability' relies on visual inspection of smoothed curves (Figs 3-4). Provide quantitative metrics for stability, such as the coefficient of variation (CV) of the policy gradient norm or the final variance of the advantage distribution across the last 100 training steps, to substantiate the claim of 'suppressed variance'.
- **[science]** The experiments are limited to dual-objective scenarios (accuracy vs. length/format). The claim that DVAO handles 'conflicting reward functions' generally is not empirically supported for n > 2. Add a sensitivity analysis or a small-scale experiment with 3+ objectives (e.g., adding a safety or style reward) to validate the scalability of the variance-adaptive mechanism.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The paper claims DVAO achieves 'superior multi-objective Pareto frontier' and 'robust training stability' based on single-run averages. For RL experiments, statistical significance is critical. Please report standard deviations or confidence intervals for the main accuracy metrics in Tables 1 and 2, and clarify if the reported results are averages over multiple seeds or a single run.
- **[science]** The variance estimation in DVAO relies on a rollout group size of G=16. The paper acknowledges this might be noisy for smaller G but does not provide a sensitivity analysis or confidence intervals for the variance estimates themselves. Please discuss the statistical reliability of the variance estimator used for weighting, especially given the binary nature of some rewards (e.g., length/format) which can lead to zero variance in homogeneous groups.
- **[science]** In the Pareto frontier analysis (Section 4.3), the paper sweeps weights {0.1, 0.3, 0.5, 0.7, 0.9}. This is a sparse sampling of the weight space. To robustly claim 'dominance across the entire range,' please either increase the density of the weight sweep or provide error bars on the frontier points to demonstrate that the observed dominance is not an artifact of sparse sampling or random seed variance.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In tex/introduction.tex, the sentence 'Reward Combination frequently generates advantages with excessively large squared magnitudes than the Advantage Combination method' contains a grammatical error. The comparative 'than' requires a comparative adjective (e.g., 'larger') or a different structure (e.g., 'larger squared magnitudes than those of...').
- **[writing]** In tex/experiments.tex, the phrase 'length constrain' should be corrected to 'length constraint' to match standard terminology and grammatical number agreement.
- **[writing]** In tex/appendix.tex, the text contains multiple typos: 'interger' should be 'integer', 'model't' should be 'model's', and 'groud-truth' should be 'ground-truth'. These need correction for professional presentation.
- **[writing]** In tex/experiments.tex, the word 'comperhensive' is misspelled and should be 'comprehensive'. Additionally, 'challanges' should be corrected to 'challenges'.
