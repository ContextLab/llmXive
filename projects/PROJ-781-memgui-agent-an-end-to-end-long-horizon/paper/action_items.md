# Automated-review action items — MemGUI-Agent: An End-to-End Long-Horizon Mobile GUI Agent with Proactive Context Management

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Clarify in Section 3.1 that the performance regression for smaller models (2B-8B) with CONACT is specific to the zero-shot setting, and that SFT (MemGUI-8B-SFT) reverses this trend, to avoid implying the architecture is inherently harmful.
- **[science]** In Section 4.1, verify that 'Qwen3-VL-8B-Instruct' is the only relevant open-data 8B baseline omitted from Table 2. If other open-data 8B models exist (e.g., UI-Venus), either include them or qualify the 'best among open-data' claim to reflect the specific baselines compared.
- **[writing]** In Section 4.3, clarify that the reported gains for 'history folding' (+5.0%) and 'self-describing steps' (+7.5%) are marginal improvements in the sequential ablation, not independent additive contributions to the ReAct baseline.
- **[writing]** In Section 4.4, explicitly state that the -42% and -57% reductions for hallucination types refer to the decrease in the count of those specific errors, not their proportional contribution to the total 41% failure reduction, to prevent ambiguity.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The final output label 'MemGUI-3K' lists '64,430 stpes' with a typo ('stpes' instead of 'steps').
- **[writing]** Figure 1: The 'Five-part ConAct Rollout' box contains a symbol (interlocking rings) that is not defined in the figure or caption.
- **[science]** Figure 2: The caption states the trajectory contains 'step-level reasonableness labels,' but the visual only labels steps 8 and 9 as 'Unreasonable' in a summary box at the bottom; individual step cards (e.g., step 1) lack explicit 'Reasonable' labels, making the annotation scheme visually ambiguous.
- **[writing]** Figure 2: The instruction text at the top is cut off on the right side ('...published more recently.' is incomplete in the screenshot), reducing readability.
- **[writing]** Figure 3: The x-axis label 'train/global_step' is rendered as a tiny, illegible watermark in the bottom-right corner of the subplots rather than a clear axis label.
- **[writing]** Figure 3: The y-axis for 'train/learning_rate' lacks a unit (e.g., 'lr' or '1e-4'), making the absolute scale ambiguous without external context.
- **[science]** Figure 3: The 'train/global_step' and 'train/epoch' subplots display perfectly linear, noise-free lines, which is atypical for training logs and suggests these are synthetic or idealized plots rather than empirical data.
- **[science]** Figure 4: The figure displays a complex multi-step failure trajectory with specific annotations (red circles, text bubbles) and a 'MemGUI-Eval' decision block, but the caption 'Qwen3-VL-8B-Instruct base' is insufficient to explain the content, context, or the specific failure mode being illustrated.
- **[writing]** Figure 4: The figure title 'Trajectory of Qwen3-VL 8B-Instruct's Failure in MemGUI-Bench' and the bottom 'MemGUI-Eval' block are not referenced or described in the provided caption, creating a disconnect between the visual evidence and the figure description.
- **[science]** Figure 5: The caption claims to show 'Qwen3-VL-235B-Thinking with ReAct-style prompting,' but the image displays a 'Failed' decision with a 'Reason' block explaining the failure. This contradicts the caption's implication of a successful demonstration or standard ReAct output, and the figure lacks the specific 'Thought/Action/Observation' formatting typically associated with ReAct style, instead showing a raw failure log.
- **[writing]** Figure 5: The image is a screenshot of a failure case (labeled 'MemGUI-Eval' and 'Failed') rather than a structured visualization of the 'ReAct-style prompting' process. It is unclear how this specific failure trajectory illustrates the prompting method described in the caption.
- **[science]** Figure 6: The rendered image is a detailed 20-step failure trajectory of a mobile agent, but the caption describes it merely as 'Qwen3-VL-8B-Instruct base' without explaining the content, task, or failure mode shown.
- **[science]** Figure 6: The image contains specific annotations (e.g., 'Stops after one swipe', 'Hallucinates fake number') and a final 'Failed' decision, but the caption provides no context for these elements or the task being performed.
- **[fatal]** Figure 7: The rendered image is a detailed failure case walkthrough of a mobile agent task (labeled 'Trajectory of Qwen3-VL 235B-Thinking's Failure in MobileWorld'), which contradicts the caption 'Qwen3-VL-235B-Thinking with ReAct-style prompting' and the filename 'MobileWorld-base-235b.png' (which implies a benchmark result table or chart). The image content does not match the figure label.
- **[fatal]** Figure 7: The image contains a large text overlay at the top ('My friend Olivia has left...') and a bottom overlay ('<Decision> Failed') that are not defined in the caption, making the figure's purpose ambiguous without external context.
- **[writing]** Figure 10: The image contains a large 'Instruction' block at the top and a 'MemGUI-Eval' decision block at the bottom, which are not mentioned in the caption. The caption should explicitly describe these components to clarify the figure's structure.
- **[writing]** Figure 10: The red annotations (e.g., 'Directly adding ingredients after the title line...') are not defined in the caption. The caption should explain that these callouts highlight specific UI operation failures.
- **[writing]** Figure 12: The caption contains unrendered variable placeholders 'casebenchpurplebg' and 'casebenchbluebg' instead of the actual dataset names (MemGUI-Bench and MobileWorld), likely due to a template rendering error.
- **[writing]** Figure 12: The caption states 'Read rows left to right', but the layout consists of two distinct horizontal panels (one for each task) rather than a single multi-row table, making the directional instruction confusing.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on domain-specific acronyms and jargon that are not defined upon first use, creating barriers for non-specialist readers. In the Introduction (Section 1), the term ReAct is used immediately without expansion. While standard in the sub-field, it should be spelled out as "Reasoning and Acting" on first mention. Similarly, SFT (Supervised Fine-Tuning) appears in Section 1 and Section 3 without definition. The phrase "prompt explosion" is used metaphorically; replacing

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** In Section 3.1 (Table 1), the text claims smaller models 'regress' with CONACT, yet the table shows Qwen3-VL-235B-Instruct also regresses (23.4% -> 19.5% P@1). The conclusion that 'Only 235B-Thinking benefits' is logically incomplete without explaining why the Instruct variant fails despite similar scale.
- **[writing]** Section 5.1 claims CONACT reduces 'process hallucination (-42%)' and 'output hallucination (-57%)'. The text cites Figure 2 (failure_heatmap) for this, but the figure caption only lists total failure counts (99->58). The specific breakdown percentages for these two categories are missing from the text and cannot be verified from the provided figure description.
- **[science]** The ablation study (Table 3) presents additive gains for components (+12.5, +5.0, +7.5) summing to 25.0, yet the full system achieves 40.0. The text does not explain the non-linear synergy or interaction effects that account for the remaining 15.0% gain, leaving the causal mechanism of the full system's performance unexplained.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim that CONACT 'saves ~1.5k input tokens by step 150' (Intro) lacks a defined baseline comparison or calculation methodology. Specify the exact ReAct context growth rate and the folding compression ratio used to derive this figure.
- **[writing]** The statement that MemGUI-8B-SFT 'generalizes to MobileWorld' (Conclusion) overstates the evidence. The results in Table 4 show a 17.9% SR, which is lower than the 43.9% SR of GUI-Owl-1.5-32B. Clarify that the gain is relative to the 8B baseline, not a generalization to state-of-the-art performance.
- **[writing]** The claim that the method 'reduces total failures by 41%' (Sec 5.4) is based on a specific ablation variant (Full CONACT vs ReAct) on a specific model (235B). Ensure the text does not imply this reduction applies universally to all model sizes or task difficulties without qualification.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper lacks an explicit statement regarding IRB approval or ethical review for the human-in-the-loop data collection or annotation processes used to construct the MemGUI-3K dataset. Please add a statement in Section 3 (Dataset) confirming whether human annotators were involved and if their participation was reviewed by an ethics board.
- **[writing]** The dataset construction involves 'entity substitution' and 'task simplification' on seed tasks. The authors must clarify the provenance of these seed tasks. If they were scraped from public app stores or user forums, a statement on data privacy, terms of service compliance, and the exclusion of PII (Personally Identifiable Information) is required.
- **[writing]** The agent is designed to perform autonomous actions (click, type, swipe) on mobile devices. The paper should include a 'Safety and Limitations' subsection explicitly stating that the agent is not intended for use in environments where it could cause financial harm, privacy violations, or unauthorized access, and that it lacks a 'human-in-the-loop' safety override mechanism.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The ablation study (Table 3) presents component contributions (e.g., +35.0% P@1 for UI memory) but lacks statistical significance testing (e.g., p-values or confidence intervals). Given the small test set size (128 tasks), random variance could explain these gains. Please report significance tests or bootstrap CIs.
- **[science]** The dataset construction relies on 'reasonableness filtering' of teacher rollouts (Sec 3.2, Appx D.3). The criteria for 'reasonable' are not quantified, and the filter rate is not reported. This introduces potential selection bias where only easy or obvious trajectories are retained, inflating SFT performance. Clarify the filtering protocol and report the rejection rate.
- **[science]** The claim that MemGUI-8B-SFT is the 'best open-data 8B model' (Sec 4.1) is based on a single benchmark (MemGUI-Bench) and MobileWorld. No comparison is made against other open-weight 8B models fine-tuned on similar data (e.g., UI-TARS, Mobile-Agent-V3 variants) on these specific long-horizon metrics. Broaden the baseline comparison to ensure the 'best' claim is robust.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Report statistical significance (e.g., p-values, confidence intervals, or bootstrapped error bars) for the performance gains in Table 1 (Main Results) and Table 2 (Ablation). The current presentation of point estimates (e.g., 37.5% vs 32.8%) lacks evidence of robustness against variance in the evaluation protocol.
- **[science]** Clarify the statistical methodology for the 'Offline Skill Analysis' (Table 3). Specifically, define the sample size (N) used for the F1 and accuracy metrics and state whether the reported improvements (e.g., 19.9% to 48.0%) are statistically significant or if they represent mean values over a single test split.
- **[writing]** In Section 3.3 (Dataset Statistics) and Appendix D, specify the variance or standard deviation for the reported trajectory lengths (avg. 28.8 steps) and fold spans. A single mean value is insufficient to characterize the distribution of task complexity used for training and evaluation.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 2, the phrase 'The model emits a 5-part structured output' is followed by a Verbatim block that uses non-standard LaTeX syntax (e.g., `\{\}`) which may not render correctly in all viewers. Ensure the code block is properly escaped or use a standard `lstlisting` environment for better readability and compilation safety.
- **[writing]** Section 3.1 (Motivation) states 'smaller models regress' but does not explicitly define the baseline for regression in the text (though Table 1 shows it). Clarify that regression is relative to the ReAct baseline to ensure the sentence stands alone without requiring the reader to cross-reference the table immediately.
- **[writing]** The caption for Figure 1 (teaser) is repetitive: 'Context management in mobile GUI agents.' appears twice (once in the caption text, once in the caption setup). Remove the redundant phrase in the caption body to improve flow.
