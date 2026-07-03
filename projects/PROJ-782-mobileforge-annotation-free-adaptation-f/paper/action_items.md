# Automated-review action items — MobileForge: Annotation-Free Adaptation for Mobile GUI Agents with Hierarchical Feedback-Guided Policy Optimization

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Clarify the '+9.0% relative gain' claim in Section 4.2. While mathematically correct (3.4/37.6), the phrasing risks confusion with absolute percentage points. Explicitly state '9.0% relative improvement' to distinguish from the 3.4pp absolute gain.
- **[science]** In Section 4.3, the claim that the [0.0, 0.9] filter yields the 'best' performance relies on 'representative rows' in Table 4. Verify if the full ablation curve was checked or if other ranges (e.g., [0.1, 0.8]) might outperform, as the current data only compares two specific points.
- **[writing]** Ensure consistent distinction between 'base' and 'adapted' model scores in the Abstract and Section 4.1. The 69.0% figure is the base GUI-Owl score; ensure the text does not inadvertently imply this is the adapted score when comparing to the 67.2% adapted Qwen3 score.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption contains a sentence fragment ('summarizes the failure...') that lacks a subject, likely referring to the 'MobileGym-Critic' module shown in the diagram; the text should be edited to explicitly name the subject.
- **[writing]** Figure 1: The labels 'attampt 1' and 'attampt 2' contain a spelling error ('attampt' instead of 'attempt').
- **[writing]** Figure 2: The caption states the task is to delete 'Streaming Services, Unexpected Expenses, and Pet Supplies', but the bottom panel (b) only shows the successful deletion of 'Streaming Services' and 'Pet Supplies'. The 'Unexpected Expenses' item is missing from the visual workflow.
- **[science]** Figure 3: The y-axis labels ('ForgeQwen3-8B vs. Qwen3-VL-8B' and 'ForgeOwl-8B vs. GUI-Owl-1.5-8B') imply a comparison between two different base models, but the caption states the metric is 'relative to the corresponding base agent'. This creates ambiguity: it is unclear if the 'reduction' is calculated against the specific base model listed in the label or a unified baseline, and the heatmap does not explicitly show the base model's performance for context.
- **[writing]** Figure 3: The x-axis labels (e.g., 'Req', 'Data entry', 'Compose UI') are rotated 90 degrees and rendered in a font size that is difficult to read, reducing the figure's accessibility.
- **[writing]** Figure 4: The caption text is grammatically incomplete and confusing, starting with 'converts hierarchical feedback...' and 'performs hint-guided...' without specifying the subject (likely 'HiFPo' or the method name), making it unclear what entity is performing these actions.
- **[writing]** Figure 4: The caption contains a typo in the title 'Trajectory-Level Muti-Attempt Rollout' (should be 'Multi-Attempt').
- **[fatal]** Figure 5: The caption reads 'Overview of .' with a missing subject, failing to identify the system (MobileForge) or components being overviewed.
- **[science]** Figure 5: The diagram shows 'MobileGym' and 'HiFPO' as separate blocks but lacks explicit arrows or text indicating how they combine to form 'MobileForge' as claimed in the title.
- **[writing]** Figure 6: The caption contains multiple grammatical gaps where the system name 'MobileForge' and component names 'MobileGym' and 'HiFPO' are missing (e.g., 'Overview of .', 'combines for', 'with for'). These should be filled to match the labels in the figure.
- **[writing]** Figure 6: The caption text 'Existing annotation-free GUI learning lacks a unified adaptation substrate' is a sentence fragment that does not clearly connect to the visual elements without the missing subject 'MobileForge'.
- **[writing]** Figure 7: The caption contains multiple grammatical errors and missing terms (e.g., 'as the annotation-free adaptation substrate', 'grounds adaptation', 'through ,', 'with to produce'), likely due to missing bolded component names like 'MobileGym' or 'MobileGym-Critic'.
- **[writing]** Figure 7: The diagram contains a typo in the 'Target-App Exploration' section, where 'Depth-fist Traversal' is written instead of 'Depth-first Traversal'.
- **[science]** Figure 8: The caption states the task is 'ExpenseDeleteMultiple2' (deleting three expenses), but the figure shows the 'Broccoli' app and a task to delete three recipes. The visual content contradicts the caption's description of the task and environment.
- **[writing]** Figure 8: The figure title 'Trajectory of Qwen3-VL 8B's Failure in AndroidWorld' and the instruction text at the top are not defined in the caption, creating a disconnect between the visual narrative and the provided description.
- **[science]** Figure 9: The caption states 'Qwen3-VL-8B base: failed', but the image shows a successful completion of the task (graduates list found, email open ready to send) with no visible failure state or error message.
- **[writing]** Figure 9: The image contains extensive red annotations (step numbers, error bubbles, red X marks) and a '<Decision> Failed' footer that are not defined or explained in the caption, making the failure mode unclear.
- **[science]** Figure 9: The trajectory shows the agent successfully navigating to the email inbox and finding the graduates list (steps 11-12), yet the figure is labeled as a failure without explaining where the actual failure occurred.
- **[science]** Figure 10: The figure displays a 14-step trajectory of a failed task, but the caption 'GUI-Owl-1.5-8B base: failed' is insufficient. It fails to describe the specific task (recalculating invoice payment) or the nature of the failure (calculation error), making the figure's scientific contribution unclear without external context.
- **[writing]** Figure 10: The figure lacks a formal caption describing the visual content. The provided text 'GUI-Owl-1.5-8B base: failed' acts as a label rather than a descriptive caption, and the figure title 'Trajectory of GUI-Owl-1.5 8B's Failure in MobileWorld' is not integrated into the standard caption format.
- **[writing]** Figure 11: The x-axis label 'Step' is positioned in the bottom-right corner without an axis line or tick marks, making it ambiguous whether it refers to the x-axis or is a stray label.
- **[writing]** Figure 11: The y-axis lacks a descriptive label (e.g., 'Reward' or 'Score'); the title 'reward/overall' is present but axis labels are standard for clarity.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Define the acronym 'GRPO' (Group Relative Policy Optimization) at its first occurrence in Section 3.3. Currently, it appears as 'GRPO' without expansion, assuming reader familiarity with specific RLHF variants.
- **[writing]** Replace the custom macro '\ourmethod' with the full system name 'MobileForge' in the Abstract and Introduction. While defined in LaTeX, the rendered text should not rely on the reader knowing the macro expansion to understand the subject.
- **[writing]** Define the term 'substrate' in the context of 'unified mobile substrate' (Section 1). The word is used metaphorically here; a brief clarification (e.g., 'framework' or 'environment') would aid non-specialist readers.
- **[writing]** Expand the acronym 'FSDP' (Fully Sharded Data Parallel) in the training details (Section 5/Appendix) if it appears for the first time there, or ensure it is defined earlier in the methodology.
- **[writing]** Clarify the term 'curriculum' in 'Curriculum mining' (Section 1). While standard in RL, explicitly stating it refers to 'task difficulty scheduling' or 'progressive task selection' would improve accessibility.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** Task Filtering Logic (Section 3.3, Table 4): The paper argues that retaining tasks with success rates (SR) in $[0.0, 0.9]$ yields better out-of-domain (MobileWorld) performance than including all tasks ($[0.0, 1.0]$). The logic implies that removing "mastered" tasks (SR=1) improves generalization. However, the table shows the "Medium + hard" filter has 1910 samples while "All tasks" has 2137. The conclusion that the *filtering strategy* (excluding easy tasks) is the cause of the MobileWorld gain
- **[writing]** Evaluator Abalation Causality (Section 4.4, Table 5): The table compares "Decision Model" (Gemini vs. Qwen) and reports "Pass@3". The logical leap here is whether the Pass@3 metric reflects the performance of the *adapted policy* trained with that specific evaluator, or the performance of the *base policy* re-evaluated by the new model. The text states "Replacing the final-decision model... improves Pass@3," which suggests the policy was re-trained. If so, the causal claim is that a stronger cri
- **[writing]** Learning from Failure (Section 3.3): The method selects the "best" attempt for training. If no attempt succeeds, it selects the one with the highest "reasonable step" count. The logical consistency of training a policy to succeed using data from *failed* trajectories relies entirely on the validity of the "process label" $v_k^{(t)}$ as a proxy for the correct action. The paper assumes that a "reasonable" step in a failed trajectory is a correct step. This is a strong assumption. The review shoul

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim of establishing the 'strongest open-data mobile GUI agent' is overreaching given ForgeQwen3-8B's 10.3% MobileWorld score, which is lower than OpenMobile-8B's 17.7%. Qualify this claim to specify 'strongest among 8B models' or 'strongest using annotation-free adaptation' to avoid misleading readers.
- **[writing]** The abstract states the adapted generalist (67.2%) is 'close to' the closed-data base (69.0%), but omits that the adapted specialized model reaches 77.6%. This framing conflates the adapted generalist's performance with the specialized model's potential, overstating the generalist's relative capability. Clarify the comparison targets.
- **[writing]** The paper claims 'annotation-free' adaptation, yet relies on human-curated benchmarks (AndroidWorld/MobileWorld) for task generation and evaluation. The system is not fully autonomous in an open world. Clarify that 'annotation-free' applies to training data generation, not the entire evaluation or task definition pipeline.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The manuscript presents MobileForge, an annotation-free adaptation system for mobile GUI agents. From a safety and ethics perspective, the primary concerns revolve around the autonomy of the agent during the exploration and training phases, and the provenance of the data used to train the policy. Data Privacy and Consent: In Section 3.2 ("MobileGym: Building an Adaptation Substrate"), the authors describe "Target-App Exploration" using depth-first traversal to collect transition records. While t

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** Report statistical significance (e.g., p-values, confidence intervals, or standard deviations over multiple seeds) for the key performance gains in Table 1 (AndroidWorld) and Table 2 (MobileWorld). Single-run point estimates (e.g., 67.2% vs 69.0%) are insufficient to claim robust improvement given the variance typical in RLHF/GRPO training.
- **[science]** Clarify the sample size and selection bias in the 'Evaluator model' ablation (Table 5). The claim that Gemini 2.5 Pro yields higher Pass@3 (71%) than Qwen3-VL-8B (70%) is based on a single run of 200 tasks. Provide variance estimates or a larger sample size to confirm this difference is not due to stochasticity or task-specific noise.
- **[science]** The 'Task filtering' ablation (Table 4) shows identical AndroidWorld performance (48.3%) for two different filtering strategies but different MobileWorld results. Explain the statistical stability of this metric; a 0.0% difference in the primary metric despite a change in training data composition suggests potential overfitting or lack of sensitivity in the evaluation protocol.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Report confidence intervals or standard deviations for Pass@k and success rates in Tables 1 and 2. Single-point estimates from 116/117 tasks lack statistical context for significance claims.
- **[science]** Clarify the statistical test used to compare baselines (e.g., McNemar's test for paired binary outcomes). The paper claims 'strongest' performance without p-values or effect sizes.
- **[science]** Define the variance estimation method for the GRPO advantage estimator (Eq. 12). Specify if group normalization uses population or sample variance, and how KL penalty variance is controlled.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 3.2, the phrase 'Target-App Exploration' uses a hyphen where an en-dash or no hyphen is standard for compound modifiers in this context. Ensure consistent hyphenation for 'target-app' throughout the manuscript (e.g., Abstract, Intro) to match the style of 'annotation-free'.
- **[writing]** Table 1 (AndroidWorld results) and Table 2 (MobileWorld results) use inconsistent formatting for the 'Pass@k' and 'SR' columns. Table 1 mixes raw counts and percentages (e.g., '47/116 (40.5%)'), while Table 2 uses only percentages. Standardize the presentation of success metrics across all tables for better readability.
- **[writing]** The caption for Figure 3 (hifpo) is extremely dense and contains multiple distinct concepts (hint-guided rollout, task removal, step selection, GRPO). Consider splitting the caption into two sentences or using a bulleted list to improve clarity and flow.
- **[writing]** In Section 4.3 (Ablations), the text references 'Table~\ref{tab:hint_rollout_ablation_main}' but the table caption itself is 'Hint ablation (200 tasks, Qwen3-VL-8B)'. Ensure the table caption explicitly mentions the metric being ablated (e.g., 'Corrective hints') to align with the section header and improve skimmability.
