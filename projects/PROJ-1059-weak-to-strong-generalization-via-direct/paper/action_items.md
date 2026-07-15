# Automated-review action items — Weak-to-Strong Generalization via Direct On-Policy Distillation

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The paper presents a novel method (Direct-OPD) for weak-to-strong generalization, and the core experimental claims regarding the performance gains of the proposed method (e.g., Qwen3-1.7B improving from 48.3% to 58.3% on AIME 2024) are well-supported by the internal data in Table 1 and the corresponding figures. The logical derivation of the policy-shift-as-reward mechanism is sound and consistent with the cited literature on KL-regularized RL. However, there are specific instances where quantit

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The caption claims to show two panels ('Left: R1-Distill...' and 'Right: Nemotron...'), but the rendered image displays only a single plot titled 'JustRL overlap dynamics' containing both transfer pairs. The figure fails to visually separate the two distinct teacher-student pairs as described.
- **[writing]** Figure 1: The legend labels 'JustRL -> R1-7B' and 'JustRL -> Qwen3-1.7B' do not match the caption's description of the 'Left' pair ('R1-Distill-1.5B -> JustRL-1.5B'). The axis label 'Student top-k overlap ratio' is also inconsistent with the caption's 'Teacher--student top-k overlap'.
- **[science]** Figure 2: The top-left subplot is titled 'Qwen3-1.7B' but the caption identifies the first column as 'student entropy'. Since the student is Qwen3-1.7B, the title is redundant and potentially confusing; it should explicitly label the metric (e.g., 'Student Entropy') to match the caption's description of the columns.
- **[writing]** Figure 2: The y-axis tick labels on the top row (0.225, 0.300, 0.375, 0.450) are rendered in a font size that is significantly smaller and less legible than the x-axis labels or subplot titles, reducing readability.
- **[writing]** Figure 3: The y-axis label 'AIME 2024/2025' is illegible due to vertical rotation and small font size, making it difficult to read the metric name.
- **[writing]** Figure 3: The y-axis label 'avg. accuracy (ave@32)' is rotated 90 degrees and compressed, reducing readability.
- **[fatal]** Figure 4: The provided caption is truncated mid-sentence ('...actors tra'), failing to describe the middle and right panels shown in the image.
- **[science]** Figure 4: The legend defines '6k fixed KL1' (pink), but the middle panel's pink curve remains flat at 0 while the caption implies all actors should show drift; the legend does not explain this baseline behavior.
- **[writing]** Figure 4: The mathematical definition of the cumulative gap $G_T$ in the caption contains a typo ('=_t T g_t') and is missing the summation symbol and index range.
- **[science]** Figure 5: The top row y-axis label 'AIME 2024/2025' contradicts the caption's claim that the plot shows 'AIME 2024/2025 validation accuracy (ave@32)'; the axis label implies a single metric combining both years, while the caption suggests the plot represents the average of the two. This ambiguity makes it unclear if the data is an aggregate or a specific year.
- **[writing]** Figure 5: The legend in the top row is split across three separate panels with inconsistent entries (e.g., 'KL 0.8' only in the right panel), which is redundant and cluttered. A single unified legend or consistent labeling across all subplots would improve readability.
- **[writing]** Figure 6: The caption contains a broken cross-reference ('Together with Figure , this shows...') where the figure number is missing.
- **[science]** Figure 6: The plot titles ('Qwen3-1.7B', 'QuestA teacher', 'QuestA teacher ref', 'QuestA delta') do not explicitly label the y-axis units (entropy bits) or confirm the metric is entropy, relying entirely on the caption for context.
- **[science]** Figure 7: The legend defines 'QuestA -> R1-7B' and 'QuestA -> Qwen3-1.7B', but the plot titles are 'R1-Distill-7B' and 'Qwen3-1.7B'. The legend label 'R1-7B' is an inconsistent abbreviation that does not match the full model name in the title.
- **[science]** Figure 7: The legend entry 'Initial' corresponds to a dashed line, but the legend does not specify the numerical value of this baseline, forcing the reader to estimate it from the y-axis.
- **[writing]** Figure 8: The caption contains multiple grammatical fragments and missing terms (e.g., 'transfers RL-induced...', 'showing that is not specific...'), making the text difficult to read.
- **[science]** Figure 8: The legend defines 'Initial Student' as a dashed line, but the plots contain multiple horizontal lines (dashed, dotted, and solid) representing baselines (e.g., 'JustRL 0.512'), creating ambiguity about which line corresponds to the legend entry.
- **[writing]** Figure 8: The y-axis label 'AIME 2024 Accuracy (ave@32)' is repeated for the top row, but the bottom row y-axis label is 'AIME 2025 Accuracy (ave@32)'; however, the caption text 'evaluated on AIME 2024 and AIME 2025' is vague about which specific subplot corresponds to which year without explicit row headers.
- **[science]** Figure 9: The legend defines 'T1500' (orange line) but the caption text is truncated ('...short transf'), failing to define what T1500 represents or how it relates to the 'T$N$' notation described.
- **[science]** Figure 9: The rightmost subplot ('Qwen3 nonthinking: AIME 2025') contains a dashed blue line labeled '0.635' but lacks a corresponding legend entry or caption definition explaining what this baseline represents.
- **[writing]** Figure 9: The caption text is truncated at the end ('...short transf'), cutting off the description of the wall-clock time calculation for the transfer points.
- **[science]** Figure 10: The caption states the figure contains 'Left: trajectories... Right: endpoint scores', but the rendered image displays only a single plot of trajectories (steps 0–600) and lacks the promised 'Right' panel showing endpoint scores.
- **[writing]** Figure 10: The title 'Qwen3-1.7B: JustRL then QuestA policy-shift transfer' and the vertical dashed line at step 300 labeled 'Switch to QuestA' are not explicitly defined in the figure's own caption, which only describes the signals generally.
- **[science]** Figure 11(a): The caption claims the blue curve 'transfers the JustRL-1.5B - R1-Distill-1.5B policy shift,' but the legend labels it 'Direct-OPD.' This contradicts the paper's distinction between 'vanilla OPD' (red) and the proposed method, creating ambiguity about whether the blue curve represents the proposed method or a different baseline.
- **[writing]** Figure 11(a): The y-axis label 'AIME 24 ave@32' is truncated and difficult to read due to tight spacing; expand the label or increase font size for clarity.
- **[writing]** Figure 11(b): The bar chart lacks explicit y-axis tick labels (only gridlines are visible), making it hard to verify the exact values of the bars and the 'Teacher' reference line.

## paper_reviewer_jargon_police — verdict: accept

The paper demonstrates excellent adherence to the "adjacent-field PhD" standard regarding terminology and notation. The authors are rigorous in defining their core contributions and specific symbols at their first occurrence.

Specifically, the central concept of "Direct On-Policy Distillation" and its acronym `\method{}` (Direct-OPD) are explicitly defined in the Abstract and Introduction. The mathematical notation for the policy shift ($\Delta_T$, $\pi_T$, $\pi_{T_{\mathrm{ref}}}$) is introduced with clear prose definitions in the Introduction (Eq. 1) and formalized in Section 2 (Eq. 2), ensuring a reader from a neighboring field (e.g., standard RL or NLP) can follow the derivation without guessing.

The paper also handles subfield-specific acronyms well. Terms like "RLVR" (Reinforcement Learning with Verifiable Rewards) and "OPD" (On-Policy Distillation) are either spelled out immediately upon first use or are standard enough within the broader ML community that their usage does not constitute a barrier. The distinction between the "teacher" and "student" policies, and the specific "top-$k$" approximation used, is explained operationally rather than assumed.

There are no instances of undefined symbols, overloaded notation, or "lab slang" that would cause a competent reader to stall. The use of "policy shift" is consistently defined as the log-ratio of the post-RL and pre-RL policies, preventing ambiguity. The paper is self-contained regarding its specific vocabulary.

## paper_reviewer_logical_consistency — verdict: accept

The paper's argument structure is logically sound and internally consistent. The central thesis—that the policy shift ($\log \pi_T - \log \pi_{T_{\mathrm{ref}}}$) serves as a transferable implicit reward distinct from the teacher's final policy—is defined clearly in Section 2 (Eq. 1) and consistently applied throughout the methodology and experiments.

The logical flow from premises to conclusions holds:
1.  **Premise:** Standard OPD fails in weak-to-strong settings because it imitates the teacher's capacity-limited final policy (Section 1, Fig 1a).
2.  **Mechanism:** The proposed method isolates the RL-induced shift, which mathematically corresponds to the implicit reward under KL-regularized RL (Section 2.2, Eq. 2-3).
3.  **Evidence:** Experiments show that applying this shift improves students stronger than the teacher (Section 4.1, Table 1a), whereas standard OPD degrades them. This directly supports the claim that the *shift* is the transferable object, not the *policy*.
4.  **Consistency:** The analysis in Section 5 confirms the mechanism by showing that transfer occurs even without high token-overlap (Fig 2), validating the "shift" hypothesis over the "imitation" hypothesis.

There are no contradictions between sections. The limitations section (Section 6) appropriately qualifies the claims made in the conclusion, noting that the signal is conditional on the meaningfulness of the teacher's shift, which aligns with the analysis in Section 5.3 regarding KL control and reward reliability. The numerical claims in the abstract (48.3% to 58.3%) match the results in Table 1a and the introduction exactly. The definitions of $\pi_T$, $\pi_{T_{\mathrm{ref}}}$, and the student $\pi_\theta$ remain stable across the text. No non-sequiturs or scope inflation were detected.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** Abstract: The claim 'boosts Qwen3-1.7B... in just 4 hours' presents a specific result from one teacher pair as a general method capability. Scope this to 'in our primary setting' or clarify it applies to the JustRL pair to avoid implying universal efficiency.
- **[writing]** Introduction: The comparison to Polaris ('at least a week') relies on external estimates rather than an internal matched experiment. Clarify this is a comparison to reported external results, not a direct internal ablation, to avoid overstating the empirical basis.
- **[writing]** Conclusion: The claim 'outperforms step-matched direct RL' is broad. The data only supports this for specific pairs (R1-Distill 1.5B->7B, Qwen3 1.7B->4B). Narrow the claim to 'in our tested teacher-student pairs' to match the evidence scope.

## paper_reviewer_safety_ethics — verdict: accept

This paper presents a method for weak-to-strong generalization in mathematical reasoning, utilizing a "policy shift" derived from a smaller model's reinforcement learning (RL) run to guide a larger model. The research focuses on algorithmic efficiency and performance gains on standard benchmarks (AIME 2024/2025).

From a safety and ethics perspective, the work is low-risk. The methodology does not involve:
1.  **Human Subjects:** The data used (Skywork-OR1-RL-Data, DAPO-Math-17K) consists of mathematical problems and solutions, not personal data, private communications, or human behavioral logs requiring IRB approval.
2.  **Dual-Use for Harm:** The method optimizes for mathematical reasoning capabilities. It does not lower the barrier for generating disinformation, cyberattacks, biological synthesis, or other harmful content. The "policy shift" is a mathematical abstraction of RL updates, not a mechanism for deception or manipulation.
3.  **Data Privacy/PII:** No Personally Identifiable Information (PII) is released or discussed. The datasets are standard public benchmarks for math reasoning.
4.  **Vulnerable Populations:** The study does not involve children, patients, or other protected groups.

The paper includes a "Limitations" section (Section 6) acknowledging technical constraints (e.g., signal reliability, hyperparameter sensitivity) but does not require an expanded ethical disclosure because the research topic (math reasoning optimization) does not inherently carry foreseeable, non-trivial risks of harm that are currently unmitigated. The use of public, pre-existing datasets and the focus on a benign capability (math) align with standard low-risk ML research norms. No specific safety disclosures or mitigations are missing.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[writing]** The paper presents a compelling method for weak-to-strong generalization, but the experimental design has gaps that prevent the reported results from definitively establishing the claimed mechanisms. First, the primary evidence for the method's efficacy relies on single-run results reported in Table 1 and Figure 2. For instance, the claim that Direct-OPD boosts Qwen3-1.7B from 48.3% to 58.3% on AIME 2024 is presented as a definitive improvement. However, Reinforcement Learning with Verifiable Re

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** Table 1 and Section 4.1 report single-point accuracy (e.g., 58.3%) without uncertainty metrics (SD/SE/CI) or seed counts. Report mean ± SD over ≥3 seeds for all main results to distinguish signal from noise.
- **[science]** Section 4.2 claims Direct-OPD 'outperforms' direct RL based on single runs. Report mean ± SD over ≥3 seeds for both methods to statistically validate the comparative claim.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The paper is generally well-written, with a clear logical flow and precise technical exposition. The abstract effectively summarizes the method and key results. However, there are a few instances where sentence structure impedes immediate comprehension, requiring the reader to re-parse or untangle clauses. In Section 4.1, the second paragraph contains a run-on sentence that attempts to define the second experimental setup and its limitations simultaneously. The clause "This setting is not intend
