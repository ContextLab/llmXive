# Automated-review action items — When Vision Speaks for Sound

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The review focuses on the factual accuracy of claims and their supporting evidence within the manuscript. 1. Unsubstantiated Perfect Scores: In Table 1 (e001), the model "Qwen3-Omni" is listed with an accuracy of 100.0% on the "Orig." (Original) Temporal Sync task. The text in Section 3.2 reinforces this, stating "Qwen3-Omni's perfect original temporal-sync accuracy drops to 1.4% under Shift." Achieving a perfect 100% score on a complex multimodal benchmark is statistically highly improbable and

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 2: The caption states the figure shows failure cases for 'Gemini and Qwen3-Omni', but the rendered image does not label which specific model generated the 'Shift', 'Mute', or 'Swap' predictions shown.
- **[writing]** Figure 2: The caption describes 'Shift, Mute, and Swap' interventions, but the figure includes a fourth column labeled 'Original' which is not mentioned in the caption's scope.
- **[science]** Figure 3: The 'Mute task' legend defines 'Hallucinated synced' (red) and 'Correct (muted)' (green), but the bars for Gemini-3.1-Pro and Qwen3-Omni are entirely red (0.87, 0.99) with no green segment, implying 0% correct predictions. However, the caption claims 'Errors cluster around a synced default,' which is consistent, but the lack of a visible green bar for these models makes it impossible to visually verify the '0.13' and '0.01' (implied) correct rates without relying solely on the red bar'
- **[writing]** Figure 3: The x-axis labels are rotated at a steep angle and overlap significantly (e.g., 'Gemini-3.1-Pro', 'Qwen3-Omni'), making them difficult to read without tilting one's head. A horizontal or less steep rotation would improve legibility.
- **[science]** Figure 4: The y-axis is labeled 'Accuracy' (0.0–1.0), but the data labels on the bars (e.g., 89.9, 64.8, 43.7) are clearly percentages (0–100 scale). This creates a visual contradiction where the bars appear to reach ~0.9 while the label says 89.9.
- **[science]** Figure 4: The legend defines 'direction acc. (desync subset)' with a hatched pattern, but the 'Ours' group in the 'Sync' subplot contains a hatched bar. Direction accuracy is logically undefined for perfectly synced data, suggesting a labeling error or misplaced bar.
- **[writing]** Figure 4: The x-axis labels for 'Qwen3-Omni (vanilla)' and 'MiniCPM-o 4.5' are cramped and overlap, reducing legibility.
- **[writing]** Figure 5 caption contains a typo ('pipelinebluedata') and missing text ('We create , , and variants' lacks the intervention names Shift, Mute, and Swap).
- **[writing]** Figure 6: The caption contains a typo 'alignorangealignment' and a stray color name 'orange' that appears to be a rendering artifact or editing error.
- **[writing]** Figure 6: The 'SFT warm-up' box contains a typo 'pertained model' which should likely be 'pretrained model'.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on field-specific acronyms and jargon that are not consistently defined at their first point of use, creating barriers for non-specialist readers. First, the Abstract introduces "MLLMs" without the full expansion "Multimodal Large Language Models," which only appears in the Introduction. Similarly, "SOTA" is used in the Abstract without being spelled out as "state-of-the-art." The term "alignment tax" is used in the Abstract and Section 3.3 without a plain-language

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** The claim that the model 'ranks first on Swap' (Sec 4.3) is not supported by Table 1. The table shows MiniCPM-o-4.5 has a 4.9% accuracy on Swap (vs 95.8% Orig), while Qwen3-Omni has 37.3% (vs 75.4% Orig). The 'Avg Gap' metric (78.4% for MiMo) suggests high shortcut reliance, not first-place performance. Clarify the metric used for this ranking or correct the claim.
- **[science]** The abstract states the recipe improves performance by '28 percentage points,' but Section 4.3 attributes this gain to 'Adding Mute/Swap SFT' to the best recipe. However, Table 2 only reports results for the 'Ours' (10K DPO) recipe, not the specific contribution of the added Mute/Swap SFT stage. The causal link between the specific training step and the 28% gain is not explicitly quantified in the provided tables.
- **[writing]** In Section 4.2, the text claims 'Mute Hallucination > 0.63' based on Figure 3 (heatmap). However, the heatmap caption and axis labels in the text description do not explicitly define the scale or confirm that 0.63 is the specific value for Mute Hallucination across the board. Ensure the text explicitly references the specific data point in the figure to support the >0.63 claim.

## paper_reviewer_overreach — verdict: minor_revision

- **[science]** The abstract and introduction claim the proposed recipe improves performance 'across these dimensions' (Shift, Mute, Swap) by 28 percentage points. However, Section 5.3 and the Limitations (App. Limit) explicitly state that the training study for Mute and Swap is 'incomplete' and the recipe was primarily optimized for temporal alignment. The 28% figure appears to conflate the strong gains in Shift with unverified or marginal gains in Mute/Swap, overclaiming the universality of the solution.
- **[writing]** The paper asserts that the method avoids an 'alignment tax' while improving general benchmarks (Table 2). However, the 'Avg' column in Table 2 shows a gain from 51.3% to 63.3%, but the specific benchmark 'DO' (DailyOmni) drops from 68.2% to 67.9%. Claiming a complete absence of alignment tax without addressing this specific degradation or providing a statistical significance test over the aggregate is an over-extrapolation of the results.
- **[science]** The abstract states the framework is 'based on three counterfactual edits' and implies equal efficacy. Yet, the results in Table 1 show Qwen3-Omni drops to 0.0% on Mute and 37.3% on Swap, while Shift drops to 1.4%. The paper frames the 'Clever Hans' effect as a unified problem solved by the recipe, but the data suggests the solution is heavily skewed toward temporal synchronization, potentially overgeneralizing the 'cure' to existential and consistency failures which remain largely unaddressed.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The 'Ethics and Broader Impacts' section (Appendix) claims no human subjects were involved, yet Section 3.2 states audio timestamps were verified by 'human inspection.' Clarify the nature of this human involvement (e.g., crowdsourcing, internal staff) and confirm if IRB approval or informed consent was obtained, as this contradicts the 'no human subjects' claim.
- **[writing]** The paper releases a dataset of intervention-based video clips (Shift, Mute, Swap) derived from the 'Oops' dataset. Explicitly state the licensing terms of the derived dataset and confirm that the source videos do not contain personally identifiable information (PII) or faces that could be re-identified, given the potential for misuse in adversarial attacks.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The paper claims a 28 percentage point average gain across Shift, Mute, and Swap interventions (Abstract, Sec 3.4), but Table 1 only reports baseline 'Avg Gap' values. The post-training accuracy for Mute and Swap is missing from the main results table, making the 28% aggregate claim unverifiable from the provided text.
- **[science]** The annotation protocol relies on 'human inspection' for audio timestamps (Sec 3.2, App B) but does not report inter-annotator agreement (IAA) statistics. Without IAA scores (e.g., Cohen's Kappa) or a description of the human verification process, the ground truth reliability for the preference pairs is unquantified.
- **[science]** The study evaluates 6 models but provides no statistical significance testing (e.g., paired t-tests or bootstrap confidence intervals) for the reported accuracy differences. Given the large variance in model sizes (9B to 311B) and the binary nature of some metrics, point estimates alone are insufficient to claim robust superiority.
- **[science]** The 'Limitations' section (App E) admits the Mute/Swap training study is incomplete, yet the Abstract and Conclusion present the 28% gain as a definitive result. The evidence presented in the tables does not support the magnitude of the claim for all three intervention types equally.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** The statistical rigor of the evaluation framework requires clarification to support the paper's central claims regarding the "Clever Hans" effect and the efficacy of the proposed alignment recipe. First, the primary results in Table 1 (e001, line 134) and Table 2 (e001, line 168) present point estimates of accuracy (e.g., 83.1%, 1.4%) without any measure of variance (standard deviation, confidence intervals, or standard error). Given that these metrics are derived from finite test sets, the abse

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The manuscript contains two distinct abstracts with conflicting claims and phrasing. The first (e000) focuses on 'vision-driven' hallucination, while the second (e001) introduces 'semantic laziness' and 'cognitive decoupling.' These must be merged into a single, coherent abstract to avoid confusing the reader about the paper's primary contribution.
- **[writing]** In Section 2.1 (e001), the text states 'We use the Oops dataset... to build intervention data' but fails to specify the exact subset or filtering criteria used, unlike the more detailed description in the first version (e000). Clarify the data sourcing scope to ensure reproducibility.
- **[writing]** The Appendix in e002 contains two identical 'Shift Judge System Prompt' boxes with slightly different rule sets (one uses 'mismatched/synced/delay/early', the other uses boolean 'synced' and direction strings). This duplication and inconsistency in the evaluation protocol description must be resolved.
- **[writing]** In Table 1 (e001), the 'Orig.' column for Qwen3-Omni is marked with a superscript asterisk ($100.0^{*}$), but the footnote explaining this marker is missing from the table or the main text. Define the meaning of this annotation.
