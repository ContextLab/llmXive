# Automated-review action items — SynthDocBench: Controlled Benchmark for Long-Context Visual Document Understanding

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Abstract claims 'five of six models show a negative Early→Late trend' but Table 5 (positional bias) shows GPT-5.4 (+0.028) and Qwen3-VL-235B (+0.019) have positive trends. Only 4 of 8 models show negative trends. Correct the count to 'four of eight' or remove the specific 'five of six' claim.
- **[writing]** Section 4 lists 'GPT-5.4' as a baseline model, but the bibliography cites 'openai2025gpt5' (GPT-5) and the text elsewhere refers to 'GPT-5'. The version number '.4' appears unsupported by the citation or standard naming conventions. Verify the exact model version used and align the text and citation.
- **[writing]** Section 5 claims 'five of six models' show a negative trend, but the table includes 8 models. The abstract also says 'five of six'. The denominator is inconsistent with the data presented in Table 5 (which has 8 rows). Clarify the subset of models being referenced or correct the count to match the full table.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The diagram depicts a single PDF page being converted to an image, whereas the caption states that pages are 'grouped into concatenated 5-page strips'; the visual representation contradicts the described input format.
- **[science]** Figure 1: The caption specifies that the judge model is 'GPT-5', but this model name is not labeled in the diagram (only 'Judge LLM' is shown), creating a disconnect between the visual schematic and the specific methodology described.
- **[science]** Figure 2: The 'Qwen2.5-VL-7B' row displays only outlier markers (circles) and a minimum whisker, but lacks a visible box (interquartile range) and median line, making the distribution incomparable to other models.
- **[writing]** Figure 2: The legend 'ACC threshold (6)' is rendered as a semi-transparent white box that obscures the x-axis tick mark and label for '6', reducing readability.
- **[science]** Figure 3: The legend lists 8 models (including GPT-5.4 and Qwen3-VL-235B), but the chart only displays 6 bars per group. The legend entries for GPT-5.4 and Qwen3-VL-235B are not represented in the data visualization.
- **[science]** Figure 3: The legend contains duplicate colors for distinct models (e.g., two distinct blue entries for 'Claude-Sonnet-4.5' and 'Qwen3.5-VL-122B', and two distinct teal entries for 'Gemini-3.1-Pro' and 'Qwen3-VL-235B'), making it impossible to distinguish which bar corresponds to which model.
- **[science]** Figure 4: The x-axis labels ('Chart', 'Complex', 'Cross-Modal') do not match the caption's description of 'question subset' if the caption implies a different categorization; however, the labels are clear. The main issue is the lack of error bars or confidence intervals for the accuracy scores, which are single point estimates without indication of variance or statistical significance.
- **[writing]** Figure 4: The legend uses color swatches but does not explicitly state that each color corresponds to a different model; while the model names are listed, the mapping between color and model is only implied by the bar colors in the chart, which could be clarified with a direct legend entry per model.
- **[science]** Figure 5: The caption states the corpus covers 24 distinct types, but the chart displays 22 bars. The two missing types (likely Sankey and Radar, given the caption's examples) are not accounted for in the visualization.
- **[science]** Figure 6: The chart title reads '2015-2022' but the x-axis extends to 2023, creating a contradiction between the title and the data range shown.
- **[science]** Figure 6: The y-axis label 'Formal Employment Rate (%)' is illegible due to low resolution, making it impossible to verify the scale or units visually.
- **[writing]** Figure 6: The caption references 'Figure 15' and 'Figure 18' as examples, but the image shown is a composite of two unrelated charts without clear labeling of which is which.
- **[writing]** Figure 8: The caption describes the pipeline as parsing reports into 'structured evidence channels' and extracting key information, but the figure visually depicts these as two distinct, disconnected stages (Panel a and Panel b) without showing the data flow or connection between them.
- **[science]** Figure 8: The 'Autocorrection' and 'Adversarial Verification' loop is shown as a feedback mechanism, but the diagram lacks arrows indicating the direction of data flow or the specific inputs/outputs for these steps, making the process ambiguous.
- **[science]** Figure 9: The middle panel's x-axis (Word count) extends to 20,000, yet the caption states the corpus spans 38–65 pages; a 20k-word document is inconsistent with this page range for standard reports, suggesting a potential labeling error or outlier skew not addressed.
- **[writing]** Figure 9: The middle panel's x-axis label 'Word count' is missing units (e.g., 'words'), while the other panels implicitly use counts; add explicit units for clarity.
- **[writing]** Figure 9: The right panel's x-axis label 'Charts' is ambiguous—does it mean 'number of charts per document'? Clarify in the axis label or caption.
- **[science]** Figure 10: Subplot (a) shows counts of 597, 597, and 594, which are not 'balanced equally' as claimed in the caption; the discrepancy should be explained or the claim corrected.
- **[science]** Figure 10: Subplot (c) histogram shows a mean of 51, but the caption states the mean is 50.8; the values should match for consistency.
- **[science]** Figure 10: Subplot (d) lists only 10 chart types, but the caption claims 24 distinct types are shown; the figure does not match the description.
- **[science]** Figure 11: The caption claims 'Vision dominates on Chart', but the chart shows the blue bar (GPT-4o vision, 0.46) is higher than the orange bar (OCR + GPT-4o, 0.30). However, the orange bar is labeled '0.30' while the blue bar is labeled '0.46', which contradicts the visual height where the blue bar is clearly taller. Wait, looking closer, the blue bar is indeed taller. The issue is the caption says 'Vision dominates on Chart' which matches the data (0.46 > 0.30). But the caption also says 'OCR
- **[writing]** Figure 12: The caption states 'Full numerical values are in Table (Appendix )', but the specific table number or appendix section is missing, making the reference unresolvable.
- **[writing]** Figure 12: The x-axis labels (model names) are rotated at a steep angle, which reduces readability and makes it difficult to quickly identify the models.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Section 4, Eq. 1: The symbol $	au$ is used as a threshold ($	au{=}6$) but defined in Appendix A as a 'Topic seed'. This overloaded notation forces page-flipping. Define $	au$ as the accuracy threshold at first use in Section 4 and rename the topic seed symbol in the appendix (e.g., to $	au_{seed}$).
- **[writing]** Section 3, 'Grounded visualization synthesis': The symbol $V_k$ is introduced without explicitly stating that $k$ indexes visualizations within document $\mathcal{D}$. Add a clause clarifying the index range (e.g., 'where $k \in \{1, \dots, K\}$ indexes visualizations in $\mathcal{D}$').
- **[writing]** Section 5, 'Positional Bias': The term 'Early$	o$Late trend' is used without defining the bucket boundaries in the prose. Add a parenthetical definition at first use (e.g., '...negative Early$	o$Late trend (comparing the first, middle, and last thirds of the document)...').

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** Section 5 claims 'five of six models' show a negative Early→Late trend, but Table 5 shows only 3 of 8 models (or 3 of 6 if excluding small models) have negative deltas. Correct the count in the text to match the table data.
- **[writing]** Appendix B states Claude-Sonnet-4.5 'was excluded,' implying it wasn't in the study, but Table 1 lists it as a candidate. Clarify that it was excluded only as a *judge*, not as a *candidate* model.
- **[writing]** The Abstract and Introduction refer to 'six models' for positional bias, while Section 5 and Table 5 present eight. Update the summary sections to reflect the full set of evaluated models for consistency.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** Abstract claims 'five of six models show a negative Early→Late trend,' but Table 5 (Section 5) shows only 3 of 8 models (GPT-4o, Claude, Qwen3.5) have a negative Δ (Late-Early). GPT-5.4, Qwen3-VL, InternVL3, and Qwen2.5-VL show positive or near-zero trends. The claim overstates the prevalence of the trend and miscounts the models. Revise to 'three of eight models' or specify the subset.
- **[writing]** Abstract states 'five of six models' for positional sensitivity, but the study evaluates eight models (Table 4). The conclusion (Section 6) repeats 'four of six models' for the same metric. The denominator 'six' is inconsistent with the actual experimental scope (eight models) and the numerator counts are factually unsupported by the provided data. Align the text with the actual model count and observed trends in Table 5.
- **[writing]** Conclusion states the benchmark serves to 'ultimately improve model capabilities,' implying a direct causal link between the diagnostic signal and future performance gains. The paper only demonstrates diagnostic signal (correlation with MMLongBench-Doc, identification of failure modes). It does not demonstrate that using this benchmark leads to improved models. Rephrase to 'provides signals to guide future model development' to avoid implying unproven efficacy.

## paper_reviewer_safety_ethics — verdict: accept

This paper presents a low-risk research artifact: a fully synthetic benchmark for long-context visual document understanding. The authors explicitly state in the **Ethics Statement** (main.tex, lines 138–168) that the dataset is constructed entirely from programmatically generated synthetic documents, involves no human subjects, and contains no personally identifying information (PII) or real-world sensitive data. The content is grounded in broad, public topic seeds and reviewed to exclude hate speech or harmful material.

The methodology avoids the primary safety pitfalls associated with data collection: there is no scraping of private user data, no use of human-subject logs requiring IRB approval, and no release of re-identifiable information. The "dual-use" risk is minimal; while the benchmark evaluates model capabilities in reading charts and documents, it does not provide a mechanism for generating disinformation, bypassing safety filters, or executing cyberattacks. The synthetic nature of the data actually mitigates the risk of the benchmark being used to train models on harmful real-world content.

The paper includes a dedicated **Reproducibility Statement** and **Ethics Statement** that address environmental impact, benchmark integrity (Goodhart's Law), and intended use limitations. No specific, foreseeable, non-trivial risks of harm were identified that are unacknowledged or unmitigated in the text. The work is safe to publish.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[writing]** The paper presents a well-constructed synthetic benchmark with a clear factorial design, but the evidentiary support for two central claims requires strengthening to rule out plausible alternative explanations. First, the headline result—that Gemini-3.1-Pro significantly outperforms other models (Table 1)—is potentially confounded by the benchmark's generation pipeline. The authors acknowledge in Section 5 that the use of D3.js/HTML rendering might favor models with high exposure to web-rendered

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** Tables 1 and 2 report ACC to 3 decimals without uncertainty metrics. Add mean ± SD/SE or explicitly state these are single-point estimates to avoid false precision.
- **[writing]** Section 5 claims 'middle third is hardest' based on descriptive counts in Table 3. Rephrase as observed trends or run a repeated-measures test (e.g., Friedman) to support statistical significance.
- **[writing]** The claim that 'gaps exceed combined CI half-widths' implies significance. Clarify that non-overlapping CIs are a conservative proxy, or run a bootstrap test on the difference of means.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The paper is generally well-structured, but the abstract contains a critical editing error where two distinct drafts of the same text are pasted sequentially without merging. The first paragraph begins "Multimodal large language models..." and the second "Vision language models..."; both attempt to summarize the work but with inconsistent phrasing and slightly different result claims (e.g., the first mentions "six layout archetypes" while the second repeats it but adds different specific failure
