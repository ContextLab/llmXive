# Automated-review action items — Anti-Self-Distillation for Reasoning RL via Pointwise Mutual Information

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** In Section 4.1 (Main results), the text claims a speedup of 10x for Qwen3-4B-IT-2507. Table 1 shows GRPO peaks at step 200 and AntiSD at step 100. The ratio is 2x, not 10x. The 10x figure likely refers to reaching a specific threshold (e.g., GRPO's step 200 accuracy) rather than the peak step, but the text 'reaches the GRPO baseline's accuracy in 2 to 10x fewer training steps' is ambiguous and numerically inconsistent with the peak-step data presented in the table for this specific model.
- **[writing]** In Section 4.1, the text states AntiSD improves final accuracy by 'up to 11.5 points'. Table 1 shows the largest gain is on Qwen3-8B (65.7 - 57.4 = 8.3 points) or Qwen3-30B (66.8 - 59.1 = 7.7 points). The 11.5 point figure does not appear in the provided table data for any model. This claim appears unsupported by the provided results table.
- **[writing]** In Section 4.3 (Ablations), the text claims that removing the gate causes the Qwen3-4B-IT-2507 run to collapse near step 90. However, Table 3 (ablation_q4_table) lists the 'JSD, none' (no-gate) configuration with an Average of 60.6 at step 30 and a speedup of 10x, implying it did not collapse before step 30. The text description of the failure mode timing contradicts the data presented in the ablation table.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[fatal]** Figure 1: The caption describes two panels (a) and (b), but the image only contains the schematic for panel (a). The quantitative performance data for panel (b) (Qwen3-8B on HMMT 2025) is missing.
- **[science]** Figure 1: The 'Solution' on the scroll explicitly states 'Try x = 3', which is a heuristic guess rather than the 'factoring' method described in the label 'teacher: factoring'.
- **[fatal]** Figure 2: The rendered image displays a math problem and solution interface, not the 'Per-token signal' trace or heatmap described in the caption.
- **[science]** Figure 2: The caption describes a heatmap and trace with specific color coding (blue/red), but the image contains no such data visualization.
- **[science]** Figure 3: The caption claims to show 'peak-mean snapshot' results, but the x-axis displays a range of k values (1 to 32) rather than a single snapshot point, creating a contradiction between the visual data and the description.
- **[writing]** Figure 3: The y-axis label 'HMMT25 pass@k' is ambiguous; it should explicitly state the unit (e.g., 'HMMT25 pass@k (%)' or 'fraction') to clarify that the values 0.0–1.0 represent percentages or probabilities.
- **[writing]** Figure 4: The legend at the top center ('GRPO', 'SD', 'AntiSD') is not explicitly defined in the caption or the figure itself; while the colors match the traces, the caption does not state which color corresponds to which method, relying on the user to infer from the legend which is technically outside the figure's rendered area.
- **[writing]** Figure 4: The y-axis label 'avg@32' in the first two columns is ambiguous without context; the caption does not define this metric, and while it likely refers to pass@32, the specific meaning is not self-contained in the figure or caption.
- **[science]** Figure 5: The legend at the top defines five methods (AntiSD, GRPO, SD, No-teacher, No-gate), but the 'No-teacher' (orange) and 'No-gate' (brown) lines are missing from the 'Olmo3-7B-IT' column plots, making it impossible to assess failure modes for these ablations on that model.
- **[writing]** Figure 5: The caption states 'Line truncation indicates run termination after collapse,' but the 'No-teacher' line in the Qwen3-4B-IT-0527 reward plot drops to zero and stays there rather than terminating, which contradicts the definition of collapse provided.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Define 'RLVR' (Reinforcement Learning from Verifiable Rewards) at first use in Section 1. The acronym is used immediately without expansion, assuming reader familiarity.
- **[writing]** Define 'OPD' (On-Policy Distillation) at first use in Section 1. The text introduces it as a 'main direction' but fails to spell out the acronym.
- **[writing]** Define 'PRM' (Process Reward Model) at first use in Section 1. The term appears in the context of 'training a separate PRM' without prior definition.
- **[writing]** Define 'JSD' (Jensen-Shannon Divergence) at first use in Section 3.2. The text refers to 'ascend Jensen-Shannon divergence' and then immediately uses the acronym 'JSD' in the next sentence without explicit definition.
- **[writing]** Define 'f-divergence' at first use in Section 2. The text mentions 'family of per-token f-divergences' assuming the reader knows the mathematical class without a brief explanatory clause.
- **[writing]** Define 'avg@k' notation in Section 4. The text uses 'avg@32' and 'avg@4' in the setup and table captions without explicitly stating that this refers to the average pass rate over k sampled rollouts.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** Section 3.2 claims JSD ascent caps the advantage on the deliberation side to handle heavy tails. However, Lemma 4.3 shows phi(u) is bounded below, meaning -phi(u) is bounded above. The text conflates the bound on phi with the bound on the advantage, creating a logical gap in justifying why this shape stabilizes the negative u regime.
- **[science]** Section 3.2 asserts the entropy gate is needed because JSD ascent is 'not self-terminating.' This causal claim lacks a premise: the paper does not derive why ascent on JSD specifically fails to self-terminate compared to other directions, nor why standard descent is self-terminating. The link between ascent and the gate requirement is asserted but not derived.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim that AntiSD 'opens a path to scalable self-improvement' (Abstract) overreaches. The method relies on privileged context (verified solutions) from the rollout group or dataset, not true label-free self-improvement. Clarify that 'self' refers to parameter sharing, not absence of external supervision.
- **[science]** The claim that the signal 'leaves the set of optimal policies invariant' (Section 5) is an over-claim. The entropy-triggered gate introduces a non-potential, state-dependent modification. Qualify this to 'in the limit' or 'under standard assumptions' to reflect the finite-sample, gated reality.
- **[writing]** The 'drop-in replacement' claim (Abstract) overstates robustness. Table 3 shows significant sensitivity to the entropy threshold (0.90 vs 0.95) on Qwen3-4B. Temper the claim to acknowledge this model-conditional sensitivity despite the auto-calibration.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The 'Broader Impacts' section (Appendix A.6) acknowledges dual-use risks but lacks a concrete mitigation strategy for the accelerated training of reasoning models. Given the 2-10x speedup, explicitly discuss potential safeguards or monitoring for misuse in adversarial contexts.
- **[writing]** The 'No-teacher' ablation (Section 4.3) demonstrates a 'self-reinforcement collapse' when privileged context is removed. The paper should clarify if this collapse mechanism could be exploited to generate harmful content or if the method inherently prevents such generation without the external signal.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** Report standard deviations or results from multiple seeds for the 'speedup' metric in Table 1. Single-run RL results are insufficient to robustly claim consistent 2-10x speedups across models.
- **[science]** Provide quantitative teacher entropy traces (e.g., a plot) for both Qwen and Olmo models under the 'No-gate' ablation to substantiate the claim that initial entropy differences drive the divergent failure modes.
- **[science]** Explicitly confirm in the text that all hyperparameters (learning rate, batch size, etc.) were identical between the canonical AntiSD runs and the 'No-teacher' ablation to rule out optimization instability as a confounder.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Section 4.1 (Main results) and Table 1 report point estimates for accuracy and speedup but omit measures of statistical uncertainty (e.g., standard deviation, confidence intervals, or error bars) across the 32 rollouts or multiple seeds. Given the small margins in some benchmarks (e.g., Olmo3-7B-TK MinervaMath -0.6pp), statistical significance testing (e.g., paired t-test or bootstrap) is required to validate that AntiSD's gains are not due to variance.
- **[science]** The entropy gate threshold (tau_down = 0.93 * H_warm) is auto-calibrated from 5 warmup steps (Section 4 Setup). The paper does not report the variance of H_warm across the batch or models, nor does it provide a sensitivity analysis on the stability of this threshold. A statistical justification for the 0.93 multiplier or a confidence interval for the entropy collapse point is needed to ensure the gate is not overfitting to a specific batch realization.
- **[science]** In Section 4.3 (Ablations), the 'No-gate' configuration shows model-dependent failure (collapse on Qwen, survival on Olmo). The paper attributes this to initial teacher entropy but does not provide statistical evidence (e.g., distributions of initial entropy values) to support this claim. Quantitative comparison of the entropy distributions between model families is required to substantiate the 'model-conditional' argument.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 3.2, the phrase 'JSD's f-divergence-derived advantage is asymmetrically bounded' is dense and slightly ambiguous. Clarify whether the bounding applies to the advantage term itself or the gradient update, and consider simplifying the phrasing for better flow.
- **[writing]** In Section 4.1, the sentence 'The gap is widest on the weaker baselines... still substantial at scale... and narrowest on the strongest GRPO baseline' is a long, complex list. Break this into two sentences or use a bulleted list to improve readability and ensure the comparison logic is immediately clear.
- **[writing]** In the Appendix (Section app:impacts), the phrase 'leaving extensions to multi-turn agentic settings... as natural next directions' is slightly clunky. Rephrase to 'leaving extensions to... as natural future directions' or 'suggesting natural next directions in...' for smoother syntax.
