# Automated-review action items — MemGUI-Agent: An End-to-End Long-Horizon Mobile GUI Agent with Proactive Context Management

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[science]** Section 1 claims GUI-Owl-1.5-8B scores 71.6% on AndroidWorld but cites no source. Verify this baseline or cite the specific evaluation.
- **[writing]** Section 3 mentions '75.7% reasonable steps' without defining the metric or linking it to Figure 2. Clarify the definition and source.
- **[writing]** Section 4.1 compares against 'same backbone' but does not explicitly specify the 'Thinking' variant, risking confusion with the 'Instruct' row in Table 1.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The final output box contains a typo 'stpes' instead of 'steps'.
- **[writing]** Figure 1: The label 'Five-part ConAct Rollout' uses non-standard capitalization that may be a typo for 'Contact' or 'ConAct'.
- **[writing]** Figure 3: The x-axis label 'train/global_step' is rendered illegibly small and overlaps with the plot border in the top-left, top-right, bottom-left, bottom-middle, and bottom-right subplots.
- **[writing]** Figure 3: The y-axis label for the 'train/loss' subplot is partially cut off on the right edge, obscuring the end of the text.
- **[science]** Figure 4: The figure displays a detailed failure trajectory of an agent on a specific task, but the caption 'Qwen3-VL-8B-Instruct base' is insufficient. It fails to describe the task, the specific failure mode (e.g., memory loss, navigation error), or the context, making the figure's scientific contribution unclear without reading the main text.
- **[writing]** Figure 4: The figure title 'Trajectory of Qwen3-VL 8B-Instruct's Failure in MemGUI-Bench' and the bottom label 'MemGUI-Eval' are not referenced or explained in the provided caption, creating a disconnect between the visual content and its description.
- **[science]** Figure 5: The caption claims to show 'Qwen3-VL-235B-Thinking with ReAct-style prompting,' but the image displays a 'Failed' decision with a 'Reason' block explaining why the agent failed. This contradicts the caption's implication of a successful demonstration or standard ReAct output, and the figure lacks the specific 'ReAct-style' reasoning traces (Thought/Action/Observation) usually associated with that prompt format, instead showing a raw failure log.
- **[writing]** Figure 5: The image is a composite of 18 distinct mobile screenshots arranged in a grid with heavy red annotations and a large text block at the bottom. The resolution is insufficient to read the text within the phone screens (e.g., search queries, product details, or specific error messages), rendering the visual evidence of the 'failure' illegible.
- **[science]** Figure 6: The image displays a detailed failure trajectory with step-by-step screenshots and annotations, but the caption 'Qwen3-VL-8B-Instruct base' is insufficient to describe the content or explain the specific failure mode shown.
- **[science]** Figure 6: The figure appears to be a duplicate of Figure 8 (based on visual content and the provided caption list), yet it is labeled as Figure 6, creating a mismatch between the figure number, the caption, and the actual content.
- **[fatal]** Figure 7: The rendered image is a detailed failure case walkthrough of a mobile agent task (labeled 'Trajectory of Qwen3-VL 235B-Thinking's Failure in MobileWorld'), but the caption describes it as 'Qwen3-VL-235B-Thinking with ReAct-style prompting' without mentioning the failure case or the specific task shown. The image content does not match the caption.
- **[science]** Figure 7: The image contains no axes, data plots, or quantitative results typically associated with a figure captioned as a model configuration or performance description. It is a qualitative case study, which contradicts the implied scientific data presentation of the caption.
- **[writing]** Figure 10: The image displays a 'Knowledge Deficiency Bad Case' but lacks a formal caption text block at the bottom; the provided caption is external to the rendered image.
- **[writing]** Figure 10: The 'Decision' and 'Reason' sections at the bottom are not explicitly labeled as such in the image itself, relying on the external caption for context.
- **[science]** Figure 10: The 'Reason' section states the failure was due to a 'failure to understand the correct UI operation sequence,' which contradicts the figure's title 'Knowledge Deficiency' (implying missing information rather than procedural error).
- **[writing]** Figure 11: The image contains a large gray box at the bottom labeled 'MemGUI-Eval' with detailed reasoning text. This content is not described in the caption, which only mentions the failure type generally. The caption should explicitly reference the inclusion of the evaluation decision and reasoning block to match the visual content.
- **[writing]** Figure 11: The step numbering is non-sequential (jumps from step 15 to step 26). While this may reflect the actual agent trajectory, the caption does not explain this discontinuity, which could confuse readers expecting a continuous timeline.
- **[writing]** Figure 12: The caption contains raw variable names 'casebenchpurplebgMemGUI-Bench' and 'casebenchbluebgMobileWorld' instead of the clean titles shown in the figure headers ('CompareProductSpecs on MemGUI-Bench' and 'MastodonUpdateContactsTask task on MobileWorld').
- **[writing]** Figure 12: The caption states 'Read rows left to right', but the layout is a vertical stack of two distinct tasks; the instruction should clarify that the top row is the MemGUI-Bench task and the bottom row is the MobileWorld task.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on specialized acronyms and domain-specific shorthand that are not defined at their first point of use, creating a barrier for non-specialist readers. First, the core contribution, ConAct, is introduced in Section 2 ("End-to-End Mobile GUI Agent with ConAct") without ever explicitly stating what the acronym stands for (presumably "Context-as-Action" based on the title and content). It appears in the abstract and introduction implicitly but lacks a formal definition

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** Clarify the causal mechanism for the performance drop in smaller models (Table 4). The paper claims only the 235B-Thinking model benefits, but does not explain why the 5-part ConAct output format causes regression in 2B/4B/8B models (e.g., instruction following limits vs. reasoning capacity).
- **[science]** Resolve the logical gap in the dataset construction claim. The text states 7,303 candidates were generated but the final dataset is 2,956 trajectories. The filtering criteria (75.7% reasonable steps) is cited, but the math (7303 * 0.757 ≈ 5528) does not match the final count of 2,956. The specific exclusion logic for the remaining ~45% needs explicit justification.
- **[science]** The ablation study (Table 3) claims 'Full ConAct' outperforms single components, but the 'ReAct baseline' (5.0% P@1) is significantly lower than the 'Qwen3-VL-235B-Thinking' baseline in Table 4 (23.4% P@1). The logical consistency of the baseline definition across tables is unclear; are they the same model configuration?

## paper_reviewer_overreach — verdict: minor_revision

- **[science]** The claim that MemGUI-8B-SFT achieves the 'best open-data 8B performance' (Sec 6) is overreaching. The paper compares against closed-source or proprietary models (e.g., Gemini, M3A) and does not explicitly benchmark against all relevant open-weight 8B baselines (e.g., specific fine-tuned variants of Llama-3.2-Vision or other community models) to substantiate the superlative 'best'.
- **[writing]** The introduction (Sec 1) attributes performance drops solely to 'passive ReAct-style prompting' causing 'prompt explosion.' This is an over-simplification that ignores other potential factors like visual grounding degradation or action space complexity in long horizons, which are not ruled out by the provided ablation studies.
- **[science]** The claim that 'Full ConAct reduces total failures by 41% (99→58)' (Fig 4 caption) lacks statistical rigor. Without confidence intervals, p-values, or a description of the variance across multiple seeds/runs, this specific percentage reduction is presented as a definitive fact rather than an observed trend, risking over-interpretation of stochastic results.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper describes generating 2,956 trajectories via a 'teacher' model (Qwen3-VL-235B) and filtering for 'reasonableness' (Sec 3, e000). Explicitly state the safety guidelines used to filter harmful or privacy-violating actions during this synthetic data generation to ensure the dataset does not encode unsafe behaviors.
- **[writing]** The system performs autonomous actions on mobile devices (Sec 2, e000). The 'Limitations' section (e000) mentions platform scope but omits safety constraints. Add a statement clarifying that the agent is restricted to non-destructive actions and includes a 'human-in-the-loop' or 'kill-switch' mechanism for real-world deployment.
- **[writing]** The dataset (MemGUI-3K) and benchmarks (MemGUI-Bench) likely contain screenshots of real or simulated mobile interfaces (Sec 3, e000). Confirm in the 'Data Availability' section that all user data, PII, and sensitive credentials in the training trajectories have been redacted or synthesized to prevent privacy leakage.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The ablation study (Table 2) shows a massive performance jump for the 235B-Thinking model with ConAct (+35% P@1) but a significant drop for smaller models (2B, 4B, 8B). The paper attributes this to the need for supervision (MemGUI-3K) but lacks statistical evidence (e.g., confidence intervals or p-values) to confirm these differences are not due to variance in the 40-task subset. Please report statistical significance for the ablation results.
- **[science]** The dataset construction relies on a 'teacher' model (Qwen3-VL-235B-Thinking) to generate 2,956 trajectories, which are then used to train the 8B student. This introduces a potential 'teacher-student bias' where the student merely mimics the teacher's specific reasoning patterns rather than learning generalizable context management. The paper should discuss this limitation or provide evidence that the 8B model generalizes to tasks/strategies not present in the teacher's output.
- **[science]** The benchmark results (Table 1) compare MemGUI-Agent against frameworks using different backbones (e.g., Gemini-2.5-Pro vs. Qwen3-VL-235B). While the authors claim superiority, the confounding variable of backbone capability makes it difficult to isolate the contribution of the ConAct mechanism. A controlled comparison using the same backbone for both the baseline (ReAct) and the proposed method across all reported baselines is required to substantiate the SOTA claim.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Table 2 and Section 4.2 report point estimates (e.g., 62.5% Pass@3) without confidence intervals or standard deviations. Given the benchmark size (MemGUI-Bench-40), statistical significance of the +35.0% improvement over ReAct is unclear. Please report 95% CIs or p-values from a significance test (e.g., bootstrap or McNemar's test).
- **[science]** The ablation study in Table 2 adds components sequentially to a baseline. This design confounds the effect of individual components with interaction effects. A full factorial design or a more rigorous statistical decomposition (e.g., ANOVA) is needed to isolate the specific contribution of 'history folding' vs. 'memory actions'.
- **[science]** Section 3 states the dataset was filtered via 'step-level reasonableness (75.7%)'. The statistical criteria for this filter (e.g., inter-annotator agreement, threshold selection) are not described. Without this, the reproducibility of the dataset construction and potential selection bias cannot be assessed.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 3 (MemGUI-3K Dataset), the phrase 'rolling out a Qwen3-VL-235B-Thinking teacher' is ambiguous. Clarify if this refers to a specific model variant or a training strategy to ensure the reader understands the data generation pipeline.
- **[writing]** In the caption for Figure 1 (main-performance), the phrase 'truncated to 150 steps' lacks context. Specify whether this truncation applies to the evaluation protocol or the visualization to avoid confusion about the reported token savings.
- **[writing]** In Section 4.2 (Offline Skill Analysis), the metric 'MTPR' is defined in the table footnote but not introduced in the main text. Define the acronym and its significance in the paragraph preceding Table 2 for better flow.
