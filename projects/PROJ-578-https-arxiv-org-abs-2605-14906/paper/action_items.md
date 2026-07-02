# Automated-review action items — MemLens: Benchmarking Multimodal Long-Term Memory in Large Vision-Language Models

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Abstract claims 'below 2%' accuracy on 80.4% of questions after image removal. Table 2 shows 1.74%/1.89% for the ablation set (n=634). Clarify if the 80.4% refers to the ablation subset or the full dataset, and ensure the 'below 2%' claim strictly matches the reported values without overgeneralizing.
- **[science]** Section 3.4 claims 65.7% of questions are image-essential. Summing counts in Table 3 for logical image-essential subtypes yields ~49.3%. Explicitly define which subtypes constitute the 'image-essential' category to justify the 65.7% figure or correct the percentage.
- **[writing]** Abstract claims MSR caps most systems below 30%. Section 4.2 says only Kimi-2.5 and Gemini-3.1-Pro clear 30% at 32K. Table 5 shows >10 models exceed 30% at 32K. Revise the claim to reflect the actual distribution or specify the context length where the 30% cap holds.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 2: The caption states 'Full rosters appear in Tables and .' but the table numbers are missing, leaving the reference incomplete.
- **[science]** Figure 2: The 'Overall' column aggregates accuracy across five distinct question types (IE, MSR, TR, KU, AR) with different question counts per type; the caption does not specify if this is a simple mean or a weighted average, making the metric ambiguous.
- **[science]** Figure 3: The legend lists five categories (IE, TR, AR, MSR, KU), but the caption states the plot shows 'LVLM average' and 'agent average' (two aggregates). The figure displays 10 distinct lines (5 solid, 5 dashed) corresponding to specific task types rather than the two aggregate groups described in the caption, creating a fundamental mismatch between the visual data and the textual description.
- **[writing]** Figure 3: The legend uses single-letter abbreviations (IE, TR, AR, MSR, KU) without defining what these acronyms stand for (e.g., Information Extraction, Temporal Reasoning). While these may be defined elsewhere in the paper, the figure and its caption do not provide the definitions, making the plot inaccessible to a reader viewing it in isolation.
- **[writing]** Figure 4: The title specifies '32k' context, but the caption claims to report 128K results (e.g., '0.94 at 128K') which are not visible in the heatmap.
- **[writing]** Figure 4: The caption contains formatting errors where the correlation symbol ($\rho$ or $r$) is missing before values like '= 0.87' and '= 0.20'.
- **[writing]** Figure 4: The 'Avg_std' column displays values like '0.35_0.30' without a legend or caption definition explaining the subscript notation (e.g., whether it represents standard deviation or a range).
- **[science]** Figure 5: The 'Evidence Facts' text contains a prompt asking 'what would you pay closest attention to...', but the 'Final Answer' is '24' (a temperature value). The question and answer do not match the stated task of identifying attention points, creating a logical disconnect in the example.
- **[writing]** Figure 5: The 'Evidence Facts' text includes the phrase 'Here's a photo of me checking smart home impact on my electricity bill in Singapore <image>', which appears to be a raw prompt template artifact rather than a coherent narrative description of the evidence.
- **[science]** Figure 8: The rendered image displays a 'Reasoning Chain' for a specific question but fails to show the 'conversation history' or 'sessions' mentioned in the caption; the evidence required to verify the count is missing from the visual.
- **[writing]** Figure 8: The image contains a large, distracting header 'Example Reasoning Chain — MSR - Counting' and a dashed vertical line that are not defined in the caption or standard figure elements.
- **[writing]** Figure 10: The image header reads 'Example Reasoning Chain — TR - Duration (Comparison Explicit Temporal Information)' rather than the figure number 'Figure 10' or the caption text, which is inconsistent with standard figure labeling.
- **[science]** Figure 10: The 'Evidence Facts' section contains a placeholder string '<image>' in item 2 ('...image of the boarding pass from <image> that day'), indicating a missing visual element required to fully understand the question context.
- **[science]** Figure 11: The caption claims to show 'chronological ordering and absolute date extraction' and mentions cues like 'clock face or calendar page', but the rendered image displays a single example of a conversational reasoning chain about living near Lake Zurich. It lacks the visual temporal cues (clocks/calendars) described and does not demonstrate the 'chronological ordering' task type mentioned.
- **[writing]** Figure 11: The rendered image is a screenshot of a reasoning trace (text + one photo) rather than a scientific figure or chart. It lacks standard figure elements such as axis labels, a legend, or a clear layout distinguishing the question, evidence, and answer components.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on domain-specific acronyms and technical shorthand that obscure meaning for non-specialist readers. The most critical issue is the introduction of the five core memory abilities—Information Extraction (IE), Multi-Session Reasoning (MSR), Temporal Reasoning (TR), Knowledge Update (KU), and Answer Refusal (AR)—in Table 1 and Section 3 without defining the acronyms first. The Abstract and Introduction use these abbreviations immediately, violating standard readability

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The paper presents a logically coherent argument for the necessity of a new benchmark, successfully establishing that existing benchmarks fail to test multimodal memory under length-controlled conditions. The causal chain from "current benchmarks lack visual evidence requirements" to "MemLens is needed" is sound. However, there is a significant logical inconsistency in the main conclusion. The abstract and introduction claim that "neither approach alone solves the task," implying a general failu

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** Abstract claims 80.4% of questions 'require' visual evidence, but Section 3.4 defines only 65.7% as 'essential' and 14.7% as 'supportive'. Conflating these overstates strict necessity. Clarify that the 2% drop applies to the combined set, but strict visual necessity is limited to the 65.7% subset.
- **[science]** Abstract and Conclusion state MSR 'caps most systems below 30%'. Table 1 shows Kimi-K2.5 (44.06%) and Gemini-3.1-Pro (32.17%) exceed this. The claim overgeneralizes by ignoring top performers. Qualify to 'most open-weight models' or adjust the threshold to reflect actual top performance.
- **[writing]** Conclusion calls Qwen3.5-122B the 'strongest LVLM' based on 58.68% overall score, yet Section 4.2 states 'No single model dominates all types'. Using 'strongest' implies holistic dominance contradicted by the paper's own findings. Rephrase to 'highest overall score' to avoid overclaiming general superiority.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** Clarify the status of the 4 annotators in the 3-round review (Appendix E002). If external, IRB exemption/approval is likely required despite the "NA" claim. Explicitly state if they were internal authors to justify the IRB exclusion.
- **[writing]** The 4,695 web-scraped images carry residual privacy risks despite automated filters. Replace the reactive 7-day takedown with a proactive "Right to be Forgotten" mechanism or explicitly acknowledge the limitation of automated privacy filtering in the datasheet.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The claim that 'removing evidence images drops two frontier LVLMs below 2% accuracy' (Abstract, Sec 3.4) relies on a sample of n=634. While the effect size is massive, the paper lacks a statistical test (e.g., McNemar's test) to confirm this drop is significant against the baseline, especially given the binary nature of the metric. Please add p-values or confidence intervals for the ablation study.
- **[science]** The error analysis in Sec 4.3 claims '90% of IE/KU errors are Visual' and '73% of MSR errors are Reasoning' based on LLM-as-Judge classification. Without a human-annotated gold standard for error types (only 484 items were human-verified for answer correctness, not error taxonomy), these percentages are subject to the judge's own hallucination biases. Provide inter-annotator agreement (Kappa) for the error classification task or a human audit of a stratified sample of these error labels.
- **[science]** The paper reports a correlation of ρ=0.62 (p=0.002) between model size and retention (App E002). However, the sample size for this regression is small (n=22 open-source models, but likely fewer with complete data across all lengths). The p-value seems suspiciously precise for such a small, noisy dataset. Please report the exact N used for the regression and the 95% confidence interval for the correlation coefficient to assess robustness.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Report confidence intervals or standard errors for all reported accuracy metrics (e.g., Table 1, Table 2, Appendix Tables). With n=789, point estimates lack precision context.
- **[science]** Clarify the statistical test used for the model size vs. retention correlation (rho=0.62, p=0.002). Specify if the p-value is from a permutation test or standard parametric test given the small sample of models (n=22).
- **[science]** Justify the use of Cohen's kappa for judge agreement on a 0/1 task with highly imbalanced classes (e.g., 96.40% agreement). Report prevalence-adjusted bias-adjusted kappa (PABAK) or Gwet's AC1 to avoid kappa paradox artifacts.
- **[science]** Define the bootstrap methodology for the 195-question subset analysis (e.g., stratified vs. simple random, number of iterations). Ensure the 1000 iterations mentioned are sufficient for stable CI estimation on small subgroups.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 3.2 (Data Curation), the text states 'Sessions are generated via dual-model simulation with GPT-5.1... and Gemini-3-Pro'. These model versions appear to be future-dated or non-existent (current state-of-the-art is GPT-4o/Gemini 1.5). This creates immediate confusion regarding the validity of the methodology. Please verify the model names or clarify if these are placeholders for future releases.
- **[writing]** The abstract claims 'removing evidence images drops two frontier LVLMs below 2% accuracy on the 80.4% of questions whose evidence includes images.' The phrasing 'on the 80.4% of questions' is ambiguous. It is unclear if the 2% drop applies to the subset of image-essential questions or the entire benchmark. Rephrase to: '...drops accuracy to below 2% on the subset of questions (80.4% of the total) that require visual evidence.'
- **[writing]** In Section 3.1, the definition of 'Information Extraction (IE)' lists 'Entity' and 'PrevInfo' as subtypes but the sentence structure 'Entity requires two-hop chains... PrevInfo recalls visual details...' lacks parallelism and clarity. Consider restructuring as a bulleted list or using consistent verb forms (e.g., 'Entity: requires...; PrevInfo: recalls...').
- **[writing]** Throughout the paper (e.g., Section 4.1, Appendix A), model names like 'GPT-5.4', 'Gemini-3.1-Pro', and 'Kimi-K2.5' are used. Given the current date, these names are highly suspect and may be hallucinated or placeholder text. If these are real models, they must be cited with a specific release date or technical report. If they are placeholders, they must be replaced with actual existing models to ensure the paper is scientifically credible.
