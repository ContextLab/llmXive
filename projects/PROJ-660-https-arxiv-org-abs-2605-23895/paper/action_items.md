# Automated-review action items — From Activation to Causality: Discovery of Causal Visual Representations in the Human Brain

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The claim that 260 concepts were constructed using 'ChatGPT (GPT-5)' (Sec 3, line 1) is factually unsupported. GPT-5 is not a publicly released model as of the paper's context (2025/2026), and the citation 'openai2025gpt5systemcard' refers to a system card that likely does not exist or is speculative. Authors must clarify the actual model used (e.g., GPT-4o) or remove the specific version claim to avoid misrepresentation of the experimental setup.
- **[writing]** The claim that 'over 70% [of activation-based localizations] failing to exhibit concept-specific responses' (Abstract, line 12; Intro, line 24) is slightly overstated based on the provided text. The Results section (Sec 4.1, 'Activation-Based Regions Have High False Positive Rate') explicitly states the rate is 'nearly 70%' and later specifies '73.4%'. While close, the abstract should align precisely with the specific statistic reported in the results to maintain strict factual accuracy.
- **[writing]** The citation 'Bao2025MindSimulator' is used to support the claim that MindSimulator 'retrieves images from COCO using CLIP scores' (Sec 4.1, line 3). However, the bibliography entry for Bao2025MindSimulator is an arXiv preprint. Authors should verify that the specific implementation details (COCO retrieval, CLIP usage) are explicitly described in that preprint and not conflated with other works, as the citation does not inherently prove the specific dataset source without the text of the paper.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 3: The caption describes the figure as showing 'regions discovered by BrainCause' and 'regions discovered by an activation-based method' (implying brain maps), but the rendered image displays generated images (e.g., 'Market to mountains', 'Pizza') with numerical scores. The visual content does not match the caption's description of the data type.
- **[science]** Figure 3: The caption states the figure shows 'high activation' and 'lower activation', but the image displays numerical values (e.g., +1.72, -0.26) without specifying the metric (e.g., correlation, z-score, log-odds) or units, making the magnitude of 'activation' uninterpretable.
- **[writing]** Figure 3: The 'Semantic negatives' row in the top section contains images (e.g., sleeping person, office desk) that do not visually correspond to the 'Market to mountains' or 'Party to empty room' causal edit pairs above them, making the relationship between the positive and negative examples unclear.
- **[science]** Figure 4: The caption claims the figure shows 'Causal ranking reduces false discoveries' and compares BrainCause to activation-based methods, but the plot axes are labeled 'Activation Train Score' and 'Causality Train Score' (training metrics) rather than evaluation metrics. Furthermore, the plot displays raw scatter points without any 'ranking' visualization (e.g., a curve or threshold line) to demonstrate the reduction of false positives.
- **[writing]** Figure 4: The x-axis label in panel (a) is 'Activation Train Score' while panel (b) is 'Causality Train Score', yet the y-axis is 'Causality Eval Score' for both. This inconsistency in axis labeling (Train vs Eval) makes it unclear if the comparison is between training performance or evaluation performance.
- **[writing]** Figure 5: The caption states 'three example concepts' are shown, but the image displays three columns labeled 'Animal Face', 'Food', and 'Tool' without explicitly defining these as the specific concepts in the text.
- **[writing]** Figure 5: The caption mentions 'warmer colors indicate higher concept-specific causal evidence', but no colorbar or scale is provided to quantify the causal score values.
- **[writing]** Figure 6: The figure displays six brain maps corresponding to six concepts (Human Leg, Human Hand, Human Face, Symbolic Signs, Logo, Handwritten Text), but the caption only lists the concepts in text without explicitly mapping them to the specific panels (Left vs. Right) or providing a clear legend linking the top images to the bottom maps.
- **[writing]** Figure 6: The brain maps lack a colorbar or legend indicating the scale of the 'causal scores' or activation levels, making it impossible to determine the magnitude of the colored regions relative to the background.
- **[writing]** Figure 7: The text labels for the visual regions (e.g., 'OPA', 'EBA', 'VWFA-1') are extremely small and low-contrast against the background, making them illegible in the rendered image.
- **[writing]** Figure 7: The colorbar or scale indicating the specific range of 'causal scores' is missing; the caption describes warmer colors as higher evidence but provides no quantitative reference.
- **[writing]** Figure 8: The row labels 'Activation Score' and 'Causal Score' are rotated 90 degrees and placed outside the plot area, making them difficult to read and visually disconnected from the data rows.
- **[writing]** Figure 8: The brain flatmaps contain numerous small text labels (e.g., 'OPA', 'EBA', 'VWFA-1') that are illegible at the current resolution, hindering the ability to verify the caption's claim about specific region suppression.
- **[writing]** Figure 9: The top histogram's x-axis label ('# Positive Examples per Target Concept') and the bottom-left's ('# Negative Examples per Target Concept') are ambiguous; the caption states these counts are 'For each target concept,' implying the x-axis should represent the count value (bin) and the y-axis the number of concepts, but the labels could be misread as the x-axis being the concepts themselves. Clarify axis labels to 'Count of Examples' (x) and '# of Target Concepts' (y) for precision.
- **[writing]** Figure 9: The bottom-right plot's x-axis label ('# Successfully Retrieved Images per Semantic-Negative') is slightly confusing given the y-axis is '# Semantic Negatives'; it implies the x-axis is the number of images retrieved for a single negative, but the caption says 'for each target--negative pair'. While likely correct, the label could be clearer, e.g., '# Retrieved Images per Pair'.
- **[science]** Figure 10: The caption claims these are 'semantic negatives' that failed to exclude the target concept, but the images shown (e.g., 'Sky', 'Reflection') appear to be standard, high-quality photographs of the target concepts themselves rather than generated images containing artifacts or failures. It is unclear if these are the 'generated' images or the 'positive' ground truth used for comparison, making the 'failure' claim visually unsubstantiated.
- **[writing]** Figure 10: The row labels ('Image with lighting contrast', 'Sky', 'Image with reflection') are rotated 90 degrees and placed on the far left, which is a poor layout choice that makes them difficult to read and visually disconnected from the specific images they describe.
- **[science]** Figure 11: The caption claims histograms show p-values for 'five validation criteria,' but only five subplots are shown without labels identifying which criterion corresponds to which plot, making it impossible to verify the claim or interpret the results.
- **[writing]** Figure 11: The y-axis label '# Concepts' is present on the first subplot but missing from the other four, creating visual inconsistency and potential confusion about whether all plots share the same metric.
- **[science]** Figure 12: The maps lack a colorbar or legend defining the binary scale (e.g., 0 vs 1 or 'negative' vs 'positive'), making it impossible to distinguish the background from the active voxels without relying on the caption.
- **[science]** Figure 12: The brain maps are unlabeled; there are no axis ticks, anatomical landmarks, or ROI outlines (unlike Figure 5) to identify the specific cortical regions shown.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Define 'fMRI' at first use in the Abstract and Introduction. While standard in neuroscience, it is jargon to general readers.
- **[writing]** Replace the acronym 'NSD' with 'Natural Scenes Dataset' at first mention in Section 4 (Results) and define it clearly.
- **[writing]** Replace the acronym 'VLM' with 'vision-language model' at first use in Section 3.1 and Section 4.1 to aid non-specialist readers.
- **[writing]** Replace the acronym 'ROI' with 'region of interest' in Table 1 and Section 4.2, or ensure it is defined earlier in the text.
- **[writing]** Replace the acronym 'TPR' and 'FPR' with 'true positive rate' and 'false positive rate' in Section 4.1, or define them immediately upon use.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** The voxel selection rule (S_causal > 0) in Sec 3.2 does not logically enforce high activation. A silent voxel with low response to both positives and negatives yields a positive causal score but is not a representation. The conclusion that selected voxels represent the concept is unsupported without an explicit activation threshold.
- **[science]** The claim that 70% of activation-based findings are false positives (Sec 4.1) assumes negative controls are perfect. Since Appendix A.6 admits semantic-negative generation fails for broad concepts, a low causal score may reflect failed controls rather than true false positives. The conclusion is not fully supported without validating control quality.
- **[science]** The statistical test in Appendix A.7 compares target scores against baselines on the *same* region selected to maximize the target score. This circular logic inflates significance. The p-value does not prove causal specificity independent of selection bias, undermining the claim of rigorous validation.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim that 'over 70% of localizations would be false positives' (Abstract) overgeneralizes. The 73.4% figure (Sec 3.1) applies only to regions found by the MindSimulator baseline, not all activation-based methods in the field. Qualify this claim to reflect the specific baseline comparison.
- **[writing]** The Abstract claims BrainCause 'successfully recovers known functional localizations.' Table 1 shows alignment with broad categories (e.g., 'Faces'), but does not demonstrate recovery of specific fine-grained sub-regions (e.g., FFA vs. OFA) with higher fidelity than baselines. Temper the claim to 'broad functional regions'.
- **[writing]** The conclusion states 'without causal validation, a large fraction of localizations would be false positives.' This generalizes beyond the study's scope (NSD, 260 concepts, specific baselines). Restrict the claim to the evaluated methods and datasets to avoid overreach regarding the broader literature.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The manuscript relies on fMRI data from the Natural Scenes Dataset (NSD) involving human subjects. While the data is public, the paper must explicitly state that the original NSD study obtained IRB approval and informed consent, and confirm that this secondary analysis adheres to the original consent scope regarding computational modeling.
- **[writing]** The framework uses generative AI (FLUX.2) to create counterfactual stimuli, including edits that remove human features (e.g., faces, hands). The authors should briefly address potential safety risks regarding the generation of misleading or harmful synthetic imagery and confirm that the generated stimuli were filtered to prevent the creation of prohibited content (e.g., deepfakes, hate speech).
- **[writing]** The paper proposes a framework that could be used to map specific cognitive or visual concepts to brain regions. While currently for research, this capability has potential dual-use implications for neuro-privacy or targeted manipulation. A brief discussion on the ethical boundaries of such causal mapping and data privacy safeguards is recommended.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** Clarify that the '70% false positive' claim (Sec 1) reflects failure against *generated* alternatives, not ground-truth biological false positives, to avoid overclaiming about prior literature validity.
- **[science]** The statistical test in Appx S.5.5 compares target vs. other concepts on the same region. Add a null distribution test (e.g., shuffled labels) to rigorously rule out noise or random concept responses as the driver of specificity.
- **[science]** Quantify how semantic-negative generation failures (Appx S.5.4) impact the reported false positive rate. If 'hardest negatives' are actually positives due to generation errors, causal scores are biased; a sensitivity analysis is required.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The empirical p-value method in Appendix A uses LLM-selected baselines rather than a null distribution. Clarify if this controls for confounds. Crucially, no multiple-comparison correction (e.g., FDR) is reported for the 260 concepts tested, which is vital given the claimed 70% false positive rate in baselines.
- **[science]** Table 1 and ablation tables report mean scores without variance (SD/SE) or confidence intervals. Without error bars or statistical tests (e.g., paired t-tests) comparing methods across the 50 concepts, the significance of reported improvements (e.g., 0.62 vs -0.44) cannot be rigorously assessed.
- **[science]** The voxel selection threshold (S_causal > 0) in Sec 3.2 ignores the multiple testing problem across ~40k voxels. A permutation test or FDR control for voxel-wise selection is required to validate the reported false positive reduction and ensure the threshold is not arbitrary.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 3.1, the caption for Figure 2 contains a typo: 'Casulity' should be corrected to 'Causality' in the label 'fig:Good_and_bad_Casulity_Edits' and the caption text.
- **[writing]** In Appendix A.5, the table label 'tab_sup:Abaltion_scores' contains a typo ('Abaltion' instead of 'Ablation'). Additionally, the main text reference in Section 4.3 to 'Appendix~\ref{sec_sup:Quantitative_across_sbuecjts}' contains a typo ('sbuecjts' instead of 'subjects').
- **[writing]** In Section 3.1, the phrase 'MindSimulator+VLM' is used, but the table in the same section lists the method as 'MindSimulator+'. Ensure consistent naming throughout the text and tables to avoid reader confusion.
