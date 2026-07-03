# Automated-review action items — Measuring Epistemic Resilience of LLMs Under Misleading Medical Context

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The bibliography entry for MedMCQA (c-001) lists a Hugging Face dataset URL but lacks the primary citation (e.g., Pal et al., 2022) required to support the claim that MedMCQA is a standard medical benchmark. Verify the reference key 'pal2022medmcqa' exists in references.bib and is correctly cited in the text.
- **[science]** The paper cites 'openai2026gpt54', 'google2026gemini31pro', and 'anthropic2026sonnet46' for models released in 2026. As this is a preprint on arXiv (2606.12291), verify that these citations refer to actual, publicly available technical reports or papers from those future dates, or if they are placeholders for unreleased models. If the models are hypothetical or unreleased, the claims of 'expert-level scores' and specific ASR metrics cannot be factually supported by existing literature.
- **[writing]** The claim that 'Automatic ASR aligns with clinician correctness in 98.1% of annotations' (Section 5.6) relies on a specific definition of 'correctness' derived from the clinician review. Ensure the citation or internal reference clearly defines the ground truth metric used for this alignment calculation, as the text does not explicitly link the 98.1% figure to a specific statistical test or validation protocol in the provided text.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[fatal]** Figure 1: The caption filename '[Figure2.pdf]' contradicts the label 'Figure 1' and the content, which matches the description of Figure 2 in the provided caption list (turning clean QA into resilience tests).
- **[science]** Figure 1: The 'Injection Sentence' box contains a specific medical claim ('lesions under 1.2 mm require... no lymph node evaluation') that is not defined or sourced in the caption, making the 'Authority' provenance claim unverifiable.
- **[science]** Figure 2: The workflow diagram displays numbered steps 1, 2, and 4, but Step 3 ('Taxonomy Generation & Attack Creation') is positioned below the main flow without a connecting arrow, obscuring the logical sequence of the pipeline.
- **[writing]** Figure 2: The caption refers to 'Figure1.pdf' in brackets, which contradicts the figure label 'Figure 2' and suggests a file naming or cross-reference error.
- **[science]** Figure 3: The caption claims 'Clean accuracy overstates epistemic resilience' and cites a drop to 38.0% under Type 1, but the chart shows Type 1 (red bars) varies wildly by model (e.g., 29.9% for Gemini-3.1-pro vs 54.0% for GPT-5.4). The 38.0% value is an aggregate mean not explicitly labeled as such on the chart, making the claim misleading without a clear 'mean' bar or annotation for Type 1.
- **[writing]** Figure 3: The x-axis labels are cluttered and inconsistent; some models have sub-labels like 'high', 'median', 'low', 'none', 'medium', 'minimal' while others do not, and the meaning of these sub-labels is undefined in the caption or legend.
- **[writing]** Figure 3: The legend defines 'mean reference' as a dashed line, but there are three horizontal dashed lines (blue, green, red) with no legend entry explaining which corresponds to which mean (clean, Type 1, Type 2), despite the caption mentioning all three values.
- **[fatal]** Figure 4: The caption cites 'Figure5.pdf' instead of the correct file name 'Figure4.pdf'.
- **[science]** Figure 4: The legend defines 'gap' as a solid line, but the plot uses solid lines to connect paired data points (T2/T1) for each model rather than representing a 'gap' metric.
- **[writing]** Figure 4: The legend entry 'T2 all-option ASR' is ambiguous; the plot shows blue circles for T2, but the label does not clarify if this represents the mean or individual data points.
- **[science]** Figure 5: The image displays a single case (MEDMISMCQA) with a 'Neutral False Statement' injection, but the caption claims to show 'Rubric A/B controls' which are not visible in the provided screenshot.
- **[writing]** Figure 5: The image is a screenshot of a UI rather than a rendered figure; the 'Provenance vehicle' and 'Misinformation type' sections appear to be metadata definitions rather than the actual 'injected context' or 'model output' mentioned in the caption.
- **[science]** Figure 6: The x-axis is labeled 'Attack success rate (%)' but the data points for the 'GPT-5.4 generator' (green circles) are plotted at values (e.g., 63.8, 61.5) that are significantly higher than the 'Main generator' (grey circles, e.g., 35.0, 40.6). This contradicts the caption's claim that 'Type 1 remains more damaging' (implying the new generator should not drastically increase ASR) and suggests a potential labeling error or data inversion.
- **[writing]** Figure 6: The legend at the bottom is split into two disconnected parts ('Main generator' on the left, 'GPT-5.4 generator' on the right) without a unifying title or box, making it slightly ambiguous whether these are mutually exclusive categories or separate series.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Define 'ASR' (Attack Success Rate) and 'TASR' (Targeted ASR) at their first occurrence in Section 5.1. Currently, they appear as acronyms without expansion, hindering non-specialist readers.
- **[writing]** Replace the term 'epistemic resilience' with a plain-language definition or synonym (e.g., 'resistance to misinformation') upon first introduction in Section 1. The current definition is abstract and relies on specialized philosophical terminology.
- **[writing]** Clarify 'Type 1' and 'Type 2' delivery protocols in Section 4.4. While described, the labels are arbitrary jargon; consider renaming them to 'Focused Injection' and 'Full Bundle Injection' for immediate clarity.
- **[writing]** Define 'Gwet AC2' in Section 5.7. The statistical metric is used to report inter-rater agreement but is not explained, excluding readers unfamiliar with this specific coefficient.
- **[writing]** Replace 'content/provenance decomposition' in Section 2 and Table 1 with 'separating the false claim from its source type' to avoid unnecessary technical phrasing.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** The claim that 'clean accuracy vastly overestimates epistemic resilience' relies on a comparison between clean accuracy (71.1%) and Type 1 ASR (51.5%). These are not directly comparable metrics (accuracy vs. attack success rate). The paper should explicitly compare clean accuracy to Type 1 accuracy (38.0%) to logically support the 'overestimation' claim, or clarify the metric relationship.
- **[writing]** In Section 3.4, the paper states Type 2 accuracy 'returns to 70.5% without eliminating ASR failures.' However, Table 2 shows Type 2 ASR is 18.7%. The text implies a contradiction between high accuracy and high failure rate, but the numbers show a significant drop in failure rate. The narrative needs to reconcile the high accuracy with the remaining ASR to avoid logical confusion.
- **[writing]** The conclusion states 'Formal rule-like injections cause the most failures,' citing authority framing (69.5% ASR) and exception poisoning (64.1% ASR). However, Table 3 shows 'Threshold/Reference Corruption' has a mean ASR of 60.9%, which is close to exception poisoning. The text should clarify if 'rule-like' encompasses both or if the distinction is statistically significant, as the current phrasing implies a clear hierarchy that the data only partially supports.

## paper_reviewer_overreach — verdict: full_revision

- **[science]** The paper significantly overreaches by presenting empirical results for LLMs that do not currently exist. The manuscript explicitly lists and evaluates "GPT-5.4", "Gemini-3.1-pro/flash-lite", and "Claude-sonnet-4.6" in Section 5.1 and throughout Tables 1, 2, and 3. As of the current date, these model versions are not publicly available or released. By presenting specific accuracy metrics, Attack Success Rates (ASR), and detailed failure modes for these non-existent models, the authors extrapolat

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The 'Ethics' section (Appendix E.2) lacks specific IRB approval numbers and details on the informed consent process for the 14-member clinician panel. Explicitly state the IRB status and consent methodology to ensure compliance with human subjects research standards.
- **[writing]** The public release of 'MedMisBench' contains realistic false medical claims, posing a dual-use risk for poisoning training data or generating misinformation. Add a specific license restriction or technical mitigation (e.g., watermarking) to prevent malicious reuse of these false statements.
- **[writing]** The paper evaluates non-existent models (e.g., GPT-5.4). The 'Ethics' section must explicitly clarify that these results are simulations based on projected capabilities, not evidence of actual safety failures in currently deployed systems, to prevent public misinterpretation.

## paper_reviewer_scientific_evidence — verdict: full_revision

- **[science]** The study relies on synthetic injections generated by LLMs (Gemini-3.1-flash) without independent human validation of the falsehoods' clinical plausibility or logical coherence prior to evaluation. The clinician review (n=89) is post-hoc and sampled; the paper must report the inter-rater reliability and failure rate of the *generation* process itself to ensure the benchmark measures resilience to plausible errors, not just random noise.
- **[science]** The sample size for the clinician harm assessment (n=89 tasks) is insufficient to support the precise confidence intervals (e.g., 95% CI 28.8–48.6%) reported for worst-case harm rates. The statistical power for detecting differences in harm severity across provenance types is likely underpowered; the authors should either increase the clinician review sample size or report the harm findings as qualitative trends with wider, more conservative uncertainty bounds.
- **[science]** The mitigation results (search, defensive prompts) are reported on specific subsets (e.g., HLE-only for search, n=600 for prompts) without a clear statistical test (e.g., McNemar's test or bootstrap CI) confirming that the observed reductions in ASR are statistically significant and not due to random variance in the subset selection.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Report confidence intervals or standard errors for the primary mean ASR metrics (e.g., 51.5% Type 1 ASR) in Tables 1 and 2. Currently, only the clinician review subset (n=89) includes 95% CIs, leaving the main benchmark results (n=10,932) without uncertainty quantification.
- **[science]** Clarify the statistical test used to compare Type 1 vs. Type 2 ASR and the differences across provenance types. The text claims significant differences (e.g., "2.8x higher") but does not specify the test statistic, p-values, or correction for multiple comparisons across the 5 content types and 3 provenance levels.
- **[writing]** Justify the use of Gwet AC2 over Cohen's Kappa for inter-rater reliability in the clinician review (Section 4.7). While AC2 is appropriate for ordinal data, the manuscript should explicitly state why this metric was chosen over others and confirm that the 0.78–0.95 range meets the threshold for "substantial" agreement in this specific medical context.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 3.3 (Injection Generation), the phrase 'single all-option call' is ambiguous. Clarify whether this refers to a single API invocation generating all distractors simultaneously or a specific prompting strategy to ensure consistency.
- **[writing]** Section 4.2 (Overall Results) states 'Type 2 accuracy ≈ 70.5%'. Replace the approximation symbol with the exact value or explicitly state the rounding convention used for this specific metric to maintain precision consistency with other reported figures.
- **[writing]** The Appendix contains multiple instances of '(... X rows omitted ...)' within table environments. While acceptable for a preprint summary, ensure the final camera-ready version includes full tables or clearly references the external repository for the complete data to avoid reader confusion.
