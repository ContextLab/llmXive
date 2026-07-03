# Automated-review action items — Audio Interaction Model

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** In Section 3.2 (Streaming Data Construction), the text claims the TFJP module uses 'half-chunk alignment δ=1/2 of Audio-Interaction'. This is semantically incorrect; δ is a time duration (200ms), not a fraction of the model. The text should read 'δ=1/2 of the chunk size' or 'δ=200ms' to match the Appendix and Algorithm 1.
- **[writing]** Table 1 (MMAU) and the Abstract claim Audio-Interaction achieves 58.15 on MMAU, surpassing Qwen2.5-Omni-3B (57.81). However, the table shows Qwen2.5-Omni-7B achieving 65.60. The claim 'surpasses them' is ambiguous and potentially misleading if interpreted as surpassing all baselines. Clarify that it surpasses the 3B initialization and specific 7B models in audio-instruction settings, not all 7B models generally.
- **[writing]** Section 4.2 claims the model improves over initialization by '+15.72/+17.04 BLEU' on CoVoST2. Table 2 shows Audio-Interaction (55.22/35.21) vs Qwen2.5-Omni-3B (39.50/18.17). The math holds (55.22-39.50=15.72), but the text implies this is a general improvement over 'its initialization' without explicitly stating the baseline is the 3B version, which could be confused with the 7B version (41.40/29.40) where the gain is smaller. Explicitly cite the 3B baseline in the text.
- **[writing]** The Abstract states StreamAudio-2M is a '2.6M-item' corpus, but Figure 3 caption and Table 3 in the Appendix list '2.34M items'. This numerical inconsistency between the abstract, main text, and appendix tables must be resolved.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption contains a typo ('capabilitie' instead of 'capabilities').
- **[writing]** Figure 1: The caption text is not fully legible in the rendered image due to low resolution.
- **[writing]** Figure 2: The caption text 'new_main_newnane.pdf' appears to be a filename artifact rather than a proper description.
- **[science]** Figure 2: The diagram shows 'Mini-Omni3' and 'SoundStream' as examples but does not clearly distinguish which parts represent the proposed Audio-Interaction model versus existing systems being compared.
- **[science]** Figure 3: The caption describes a 'training framework' with 'supervision signals' and 'streaming training strategy,' but the figure depicts an inference pipeline (input audio -> encoder -> adapter -> response generation) without showing loss functions, gradients, or training-specific components.
- **[writing]** Figure 3: The text 'Audio-Interaction' and 'Adapter' are accompanied by fire emojis (🔥) which are undefined in the caption or legend, creating ambiguity about whether they denote specific model components, training phases, or are merely decorative.
- **[writing]** Figure 3: The diagram shows specific text inputs (e.g., 'What is your name?', 'Count only upon hearing a dog bark') but lacks a clear legend explaining the color coding of the output blocks (orange vs. green) or the meaning of the '<Silent>' vs '<Res>' tokens.
- **[writing]** Figure 4: The text '2.4M source dataitem' in the Data collection panel contains a typo and should be 'data items'.
- **[writing]** Figure 4: The 'Preprocessing' panel contains illegible text inside the 'ASR checking' box due to low resolution.
- **[science]** Figure 5: The caption claims to show '(c) Statistics of source data', but the rendered figure only contains the taxonomy chart (a) and the round distribution/tokens/silence plots (b); the source data statistics are missing.
- **[writing]** Figure 5: The legend for the top-right line chart ('Rounds distribution') is placed outside the plot area without clear visual grouping, making it difficult to associate with the specific data series.
- **[science]** Figure 6: The x-axis labels 'Encoder' and 'Projector' are positioned under the first two data points, but the caption claims 'GPT Layer 0 alone recovers most of the continuity.' The graph shows the massive jump occurs at 'L0', yet the visual grouping of 'Encoder' and 'Projector' in the shaded regions suggests they are the primary stages, potentially obscuring the specific contribution of the projector versus the encoder as described in the text.
- **[writing]** Figure 6: The x-axis labels 'Encoder' and 'Projector' are rotated 45 degrees and overlap significantly with the 'L0' label, reducing legibility.
- **[writing]** Figure 7: The caption describes the plot as showing 'cross-chunk continuity ratio', but the y-axis label reads 'Continuity Ratio (boundary / internal)', which is a specific metric definition not explained in the caption.
- **[writing]** Figure 7: The x-axis labels 'Encoder' and 'Projector' are ambiguous regarding the specific layer indices they represent compared to the 'L0' through 'L35' sequence, and the caption does not clarify if these correspond to specific layers or blocks.
- **[science]** Figure 8: The caption claims to report 'end-to-end latency', but the third subplot (right) displays 'Response Trigger Token Acc (%)' on the y-axis. The figure fails to visualize the metric described in the text.
- **[writing]** Figure 8: The legend in the rightmost subplot lists 'Ours (w/o Streaming Loss)', whereas the legends in the left and middle subplots list 'Baseline'. This inconsistency in naming conventions across the panels is confusing.
- **[science]** Figure 9: The caption claims the second case study shows Audio-Interaction handling the 'audio cue directly' while others rely on transcription, but the 'Sound Events' row explicitly lists '<Sound effect - Cat> 🐱 <End>' as a recognized event. This implies the baseline models also have access to the audio cue, contradicting the caption's narrative that they only detect the cat via transcribed words.
- **[writing]** Figure 9: The 'TRIGGERED / RESPONSE ACC' column header is ambiguous; it is unclear if the two values (e.g., 100.0% / 100.0%) represent Trigger Accuracy and Response Accuracy respectively, or if they refer to different metrics entirely. A legend or explicit definition is missing.
- **[writing]** Figure 10: The caption 'Case study: Home' is insufficient for a complex timeline visualization; it should describe the specific scenario (e.g., 'Weekend Childcare') and the model's multi-modal responses shown.
- **[writing]** Figure 10: The legend at the bottom lists 'Real-time ASR' and 'Instruction Following' as task categories, but the timeline does not explicitly label any segments with these specific tags, creating ambiguity about which interactions fall under these definitions.
- **[fatal]** Figure 12: The caption is a placeholder ('Enter Caption') and does not describe the figure's content, making it impossible to verify if the chart supports the paper's claims.
- **[science]** Figure 12: The x-axis labels (e.g., 'Daily Affairs', 'House Equipment States') do not match the legend categories (e.g., 'Daily Living', 'Human'), creating a disconnect between the data points and their defined groups.
- **[writing]** Figure 12: The x-axis labels are rotated at a steep angle, causing significant overlap and reducing legibility for labels like 'Ecological & Biological Context'.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on acronyms and domain-specific shorthand that hinders accessibility for non-specialist readers. First, the paper introduces LALM (Large Audio Language Model) in the abstract but introduces LAIM (Large Audio Interaction Model) in the Introduction without explicitly spelling out the acronym or defining it as a distinct class of models, forcing the reader to deduce the pattern. Similarly, the term SALM appears in the "Additional Analysis" section without any prior def

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** In Section 3.2, the text describes an iterative TFJP loop, but Algorithm 1 lacks a mechanism to re-evaluate stability after boundary refinement (S3-S4), creating a gap between the prose description and the formal algorithm.
- **[writing]** In Section 4.2, the claim that Audio-Interaction 'matches SOTA' (58.15 vs 57.81) contradicts Table 1, where Qwen2.5-Omni-7B scores 65.60. The conclusion does not follow from the data unless 'SOTA' is restricted to 3B models, which is not stated.
- **[science]** In Section 5, the ablation logic conflates the gain from Streaming SFT (V1->V2) with the specific contribution of TFJP (V2->V3). The causal claim that TFJP is 'essential' needs clearer isolation of variables to support the 7.1% drop attribution.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim that the model 'unlocks capabilities inaccessible to offline LALMs' overreaches. Offline models can simulate streaming; the paper shows efficiency gains, not theoretical impossibility for others. Qualify to 'unlocks efficient, low-latency implementations'.
- **[writing]** The claim that Audio-Interaction 'matches SOTA (58.15 vs 57.81)' is misleading. Table 1 compares Audio-Interaction (audio instruction) against Qwen2.5-Omni (text instruction). Compare like-for-like (audio vs audio) or clarify the modality mismatch to avoid over-interpretation.
- **[writing]** The assertion that a single head (L35H14) dominates 'across all four tasks' implies universality. The data only covers four specific tasks. Limit the claim to the evaluated tasks and avoid generalizing to the model's full 28 sub-tasks without evidence.
- **[writing]** The statement that offline baselines 'collapse to 0.0' on audio instructions is an over-interpretation of a single data point. This may reflect prompt/format failure rather than a fundamental capability gap. Provide context or nuance to avoid overstating the failure mode.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[science]** The 'Proactive-Sound-Bench' reports a 40.2% false negative rate on safety-critical events (App E). Given the risk of physical harm from missed interventions, authors must discuss deployment risks and mitigation strategies (e.g., human-in-the-loop) rather than treating this as a standard metric.
- **[writing]** The dataset uses synthesized 'distress' sounds via ElevenLabs/AudioX (Sec 4.2, App D). Authors must clarify the consent and licensing of source data for these generators and ensure synthesized sounds do not replicate identifiable private individuals.
- **[science]** The 'Real-World Validation' (App A) uses naturally recorded audio from private spaces without mentioning IRB approval, informed consent, or anonymization. This is a critical ethical omission for research involving human subjects in private settings.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The claim that the model 'retains over 91% of its single-segment accuracy' as stream length N grows to 5 (Section 5.2, Enh.3) lacks explicit statistical evidence. The text references Figure 7 (fig:ablation_stability) for this data, but the specific accuracy values, standard deviations, or confidence intervals for N=1 through N=5 are not provided in the text or tables. Please report the exact accuracy percentages and variance metrics for each N to substantiate the 91% retention claim.
- **[science]** The ablation study in Table 4 (tab:ablation_data) reports trigger accuracy improvements (e.g., V2 to V5) but omits standard deviations or significance tests. Given the sparse nature of 'proactive' events, small sample fluctuations could drive these gains. Please include standard deviations over multiple seeds or a statistical significance test (e.g., paired t-test) to confirm the robustness of the TFJP and event selection contributions.
- **[science]** The real-world validation in Appendix A.1 (Real-World Validation) reports a drop in trigger accuracy from 62.0% (synthetic) to 58.9% (natural) but does not specify the sample size (number of events or hours) or the confidence interval for this 3.1% drop. To support the claim that the model 'retains the bulk' of performance, please provide the N value and statistical bounds for the real-world evaluation.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Report statistical significance (e.g., p-values, confidence intervals, or standard deviations) for the reported improvements on MMAU (58.15 vs 57.81) and CoVoST2 (+15.72 BLEU). Single-point averages without variance estimates make it impossible to assess if gains are robust or due to random seed variance.
- **[science]** Clarify the statistical methodology for the 'Proactive-Sound-Bench' results. With 644 events, report the 95% confidence intervals for the Single (61.2) and Multi (62.8) tier accuracies. Additionally, specify if the 'human-designed' events were evaluated by multiple annotators and report inter-annotator agreement (e.g., Cohen's kappa) to validate the ground truth labels.
- **[science]** The ablation study (Table 4) presents performance differences (e.g., V2 vs V5 on Trigger Acc: 92.42% vs 96.77%) as absolute facts. Include standard deviations or results from multiple random seeds to demonstrate that these improvements are statistically significant and not artifacts of a specific initialization or data split.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In the caption of Figure 1 (e000), the word 'capabilitie' is a typo and should be corrected to 'capabilities'.
- **[writing]** In the caption of Table 2 (e001), the phrase 'spee ch translation' contains an erroneous space and should be 'speech translation'.
- **[writing]** In Section 3.2 (e000), the phrase 'forming a always-on' contains a grammatical error; it should be 'forming an always-on'.
- **[writing]** In the Appendix (e003), Table 1 contains inconsistent delimiters (e.g., 'Physiological states | Human | Bodily functions') where some rows use '|' instead of tabs or proper alignment, disrupting the table structure.
