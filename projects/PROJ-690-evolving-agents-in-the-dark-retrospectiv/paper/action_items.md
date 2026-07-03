# Automated-review action items — Evolving Agents in the Dark: Retrospective Harness Optimization via Self-Preference

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[science]** Verify the baseline model for the 59% SWE-Bench Pro score. The paper cites 'openai2025codex' and 'openai2026gpt55'. If the baseline is GPT-3.5 Codex, 59% is anomalously high; if GPT-5.5, clarify the citation to avoid confusion with legacy Codex.
- **[writing]** Clarify the 'no ground-truth labels' claim. While optimization is label-free, evaluation uses standard benchmarks. Explicitly distinguish between the optimization loop (self-preference) and the evaluation phase (ground-truth grading) to prevent misinterpretation.
- **[science]** Confirm that citation 'liu2026webtrap' specifically supports the claim of 'adversarial content injected mid-task' in a general harness context, as the title suggests a web-specific focus that may not generalize.
- **[writing]** Acknowledge that 'self-validation' and 'self-consistency' generate internal proxy labels. Clarify that the method relies on the model's internal correctness judgment, which acts as a substitute for external ground truth.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption contains a placeholder 'after .' where the method name (RHO) should be, making the sentence grammatically incomplete and unclear.
- **[science]** Figure 1: The top row y-axis label 'Fraction of tasks solved by step k' is ambiguous; it is unclear if this represents the cumulative success rate (pass@1) or the fraction of currently active tasks solved at that specific step.
- **[writing]** Figure 1: The legends in the bottom row (e.g., 'Verify +61%') lack context for the baseline; it is unclear if these percentages represent the increase over the Vanilla baseline or the absolute difference in action frequency.
- **[science]** Figure 2: The caption claims 'Difficulty or diversity alone trails even random sampling,' but the bar chart in (b) shows 'Difficulty' (0.62) and 'Coverage' (0.58) outperforming 'Random' (0.64) is false; specifically, Difficulty (0.62) is lower than Random (0.64), but Coverage (0.58) is also lower, yet the text implies both trail random, while the chart shows Difficulty is close to Random but Coverage is worse. Wait, actually 0.62 < 0.64 and 0.58 < 0.64, so both do trail random. However, the capt
- **[writing]** Figure 2: The caption contains an incomplete phrase 'and 's DPP balancing both' — the method name (likely 'RHO') is missing before 's DPP', making it unclear which method uses the DPP. Additionally, the 'Vanilla Codex: 0.59' baseline in panel (b) is not defined in the caption or legend, leaving its purpose ambiguous.
- **[fatal]** Figure 3: The caption contains unreadable placeholders ('=-1', 'on', 'Appendix .') instead of the specific method name (likely 'rho=-1'), the verb 'produced by [method]', and the appendix number, rendering the figure description incomplete.
- **[fatal]** Figure 4: The rendered image is a schematic diagram illustrating a workflow, but the caption describes a quantitative comparison ('versus validation-feedback harness optimization') that is not shown. The figure lacks axes, data points, or metrics to support the comparison claimed in the caption.
- **[science]** Figure 4: The diagram contains placeholder text (e.g., '= -1') and generic icons without specific data or labels, making it impossible to verify the scientific claims regarding 'validation-feedback' vs 'retrospective' optimization methods described in the caption.
- **[writing]** Figure 5: The caption contains a placeholder '= -1' at the start, likely a missing variable name (e.g., 'RHO' or 'EvoAgent').
- **[writing]** Figure 5: The 'Trajectory Distribution' plot lacks axis tick labels and a legend defining the red vs. pink dots, despite the caption mentioning 'difficulty-diverse'.
- **[writing]** Figure 5: The 'Harness Proposal' section uses specific numerical values (-0.5, +1.4, +0.7) without a legend or axis explaining what these scores represent (e.g., reward delta, win rate).

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Define "harness" immediately upon its first introduction.
- **[writing]** Spell out "Determinantal Point Process" before using the acronym DPP.
- **[writing]** Provide a plain-English explanation of "self-preference" and "coreset" before diving into the algorithmic details.
- **[writing]** Ensure that every mathematical variable introduced in the text is accompanied by a brief, non-technical description of its role. These changes are necessary to ensure the paper's novel contributions are understandable to a broader audience beyond those already familiar with specific agent optimization jargon.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** Causal Ambiguity in "Long-Horizon" Claims: The Abstract and Figure 4 caption claim the method "sustains accuracy in long-horizon sessions" and "shifts action mix toward verification." While the data shows improved pass rates on benchmarks known for long horizons (SWE-Bench), the paper does not explicitly present data correlating the *duration* or *step count* of sessions with the optimized harness. The logical leap from "higher success on long tasks" to "sustains accuracy in long sessions" (impl
- **[writing]** Evaluation vs. Optimization Logic: The paper repeatedly emphasizes "no ground-truth labels used" (Abstract, Fig 1). While this is true for the *optimization signal* (the self-preference mechanism), the *evaluation* of the final harness relies entirely on ground-truth test suites (SWE-Bench, etc.). The logical distinction between the *training signal* (label-free) and the *evaluation metric* (label-dependent) is blurred. A reader might incorrectly infer that the method is entirely unsupervised in
- **[writing]** Threshold Logic in Best-of-N: The acceptance condition $S_j > 0$ is clearly defined, but the text in Appendix e002 mentions "mean zero is rejected." Given the ranking scale of [-10, 10], a mean of 0 represents a tie between the candidate and the baseline. The logic that a tie should be rejected is sound, but the paper should explicitly address the probability of ties and whether the "strictly positive" condition is robust against statistical noise in the ranking scores. If the ranking model is u

## paper_reviewer_overreach — verdict: minor_revision

- **[science]** The 'label-free' claim overreaches by ignoring that LLM judges act as implicit, uncalibrated reward signals. The paper must explicitly acknowledge this proxy-labeling risk and the potential for hallucinated preferences.
- **[science]** The claim of 'outperforming validation-feedback' is unsupported; Meta-Harness (10 rounds) achieves 0.80 vs. 0.78. Qualify the claim to 'outperforms single-round baselines' or 'achieves comparable performance with fewer rounds'.
- **[science]** Claims of 'altered behavior patterns' lack statistical significance testing (p-values/CIs) for the observed shifts in action mix, risking over-interpretation of variance as robust change.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The Ethics Statement (Section e000) acknowledges risks of amplifying unsafe procedures but lacks a concrete mitigation strategy for the 'adversarial content' risk cited from Liu et al. (2026). Explicitly detail the proposed 'audit logs' and 'human approval' mechanisms (e.g., specific triggers, human-in-the-loop checkpoints) to satisfy safety review standards.
- **[science]** The method relies on 'self-preference' and 'self-validation' to optimize agent behavior without ground truth. This creates a high risk of reward hacking or reinforcing latent biases in the training trajectories. The paper must include a dedicated subsection analyzing potential failure modes where the agent optimizes for 'plausible but unsafe' behaviors that pass internal consistency checks.
- **[writing]** The dataset specifications (Appendix e002) mention 'judge-relaxation switches' for GAIA-2. The Ethics Statement must clarify if these switches were used during the reported experiments and, if so, how this impacts the validity of the safety claims regarding 'unsafe procedures' or 'adversarial content' injection.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** Report statistical significance (p-values or confidence intervals) for the +0.19 gain on SWE-Bench Pro and other benchmarks. With N=100 test tasks, a 19% absolute jump is large, but the variance across tasks is unknown. Without error bars or significance tests, the robustness of the claim against random fluctuation is unverified.
- **[science]** Clarify the independence of the coreset selection and evaluation sets. The paper states the first 100 tasks are used for training (coreset selection) and the next 100 for testing. However, the coreset is selected from the *past trajectories* of the training set. If the 'past trajectories' were generated by the same model version being optimized, ensure there is no data leakage where the test set influenced the training distribution or the difficulty scores used for DPP selection.
- **[science]** Provide effect size metrics beyond raw pass rates. The paper reports absolute improvements (e.g., +0.19) but lacks normalized effect sizes (e.g., Cohen's d) or variance measures (standard deviation of pass rates across multiple seeds if applicable). Given the stochastic nature of LLM rollouts, a single run per method may not represent the true expected performance.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Report statistical significance for the reported performance gains (e.g., +0.19 on SWE-Bench Pro). The paper presents point estimates in Table 1 but lacks confidence intervals, p-values, or variance estimates across multiple random seeds to confirm the gains are not due to stochasticity.
- **[science]** Clarify the statistical basis for the 'Best-of-N' selection. The paper reports a single 'Chosen' score in Table 4 against a 'Mean' and 'Lowest', but does not specify if the 'Mean' is derived from a distribution of N=3 candidates across multiple seeds or a single run. Re-run experiments with multiple seeds to provide standard deviations for all reported metrics.
- **[science]** The coreset selection uses a DPP with a fixed weight theta=0.7. Provide a sensitivity analysis or justification for this specific hyperparameter choice. Without reporting performance variance across different theta values, the robustness of the coreset selection strategy remains unverified.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The LaTeX source contains a critical truncation error in Section 4 (Problem Setting). The text ends abruptly at 'tau = \mathrm{so' (end of e003), cutting off the definition of the execution process and the subsequent algorithm description. The manuscript must be completed to be readable.
- **[writing]** The document structure is fragmented with duplicate content. Section 2 (Introduction) and Section 5 (Experiments and Results) appear to be repeated or split across chunks (e000, e001, e002) with inconsistent formatting and redundant figure captions. The authors should consolidate these into a single, linear narrative flow.
- **[writing]** In the 'Problem Setting' section (e003), the mathematical notation for the trajectory generation is incomplete due to the truncation. Ensure all equations are fully rendered and the text following the equation is present to maintain logical flow.
