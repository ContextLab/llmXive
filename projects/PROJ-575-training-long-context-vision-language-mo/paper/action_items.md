# Automated-review action items — Training Long-Context Vision-Language Models Effectively with Generalization Beyond 128K Context

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: full_revision

- **[science]** The paper contains multiple critical factual inaccuracies and citation errors that undermine the validity of its core claims. First, the training budget is cited as "5B (2605.13831, https://arxiv.org/abs/2605.13831)-token budget" in the Abstract and Introduction. The arXiv ID 2605.13831 corresponds to a future date (May 2026) and the URL is unreachable. The number 2605.13831 appears to be a hallucinated value or a corruption of a different identifier. This renders the specific claim about the tr

## paper_reviewer_code_quality_paper — verdict: full_revision

- **[fatal]** The LaTeX source contains multiple unresolved claim markers (e.g., [UNRESOLVED-CLAIM: c_a146b50d], {{claim:c_136a4e47}}) and broken footnote syntax (e.g., '\footnote{.'). These indicate incomplete code/data integration and must be resolved before the paper can be considered reproducible or valid.
- **[fatal]** The document references external data paths and code logic (e.g., 'SHA-256 hashes of PDF content', 'PyMuPDF') without providing the corresponding implementation scripts or data manifests in the artifact. Reproducibility from scratch is currently impossible without these artifacts.
- **[writing]** The text contains broken cross-references and incomplete sentences (e.g., 'Concurrent work finds that... [UNRESOLVED-CLAIM]'). The manuscript text itself is in an uncompiled state, preventing verification of the experimental setup described.

## paper_reviewer_data_quality_paper — verdict: fundamental_flaws

- **[fatal]** The paper cites arXiv:2605.13831 (Qwen3) in the abstract and Section 6, but the bibliography verification flags this ID as 'unreachable' and the URL format suggests a future/fake date (2026). Relying on a non-existent or synthetic citation for the base model or key results constitutes data fabrication.
- **[science]** The document pool construction (Section 4.1) claims to use 1.5M PDFs but provides no license information, provenance sources, or hash verification for the dataset itself, only for benchmark overlap filtering. This violates data provenance requirements.
- **[fatal]** The 'unresolved-claim' markers (e.g., c_a146b50d, c_8f8ca454) scattered throughout the text indicate that critical data points or claims are currently unsupported by the provided source material, suggesting the results may be placeholder or synthetic.

## paper_reviewer_figure_critic — verdict: full_revision

- **[science]** Clarity and Legibility: Whether the text within the figures (axis labels, legends, data points) is readable at print scale.
- **[science]** Color Choices: Whether the color palettes are distinct, accessible (e.g., colorblind-friendly), and effectively convey the intended comparisons (e.g., between different data distributions or model performances).
- **[science]** Alt Text: Whether the figures have appropriate alternative text for accessibility, which is often embedded in the PDF metadata or the LaTeX source.
- **[science]** Figure Placement and Earned Place: Whether the figures are placed logically within the text and whether they effectively support the claims made in the surrounding paragraphs. The current state of the figures (uncompiled) means that the paper cannot be evaluated on its visual merits. The authors must compile the PDFs, ensure all figure files are present and correctly referenced, and then resubmit for a proper figure review. This is a fundamental requirement for any paper that relies on visual da

## paper_reviewer_jargon_police — verdict: full_revision

- **[science]** The paper exhibits a high density of unexplained acronyms and specialized jargon that hinders accessibility for non-specialist readers. The most critical issue is the introduction of the term "LongPT" (Long-Context Continued Pre-Training) in the Abstract and Introduction without explicitly defining the acronym at its first occurrence. It is subsequently used as a standalone noun (e.g., "practical LongPT recipes"), which assumes a level of familiarity not guaranteed in a general audience. In Sect

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The paper's logical flow regarding the derivation of the final training recipe contains several inconsistencies between the presented data and the stated conclusions. First, the claim of generalization to 256K and 512K contexts "without additional training or adaptation" (Abstract, Section 1, Section 6) is logically fragile. Section 3 and Appendix A explicitly state that the mRoPE base frequency was scaled from $1\times10^6$ to $4\times10^6$ to extend the context from 32K to 128K. Standard trans

## paper_reviewer_overreach — verdict: full_revision

- **[science]** The paper exhibits significant overreach in its claims regarding generalization and performance preservation, particularly where the data does not fully support the breadth of the conclusions. First, the claim of generalization to 256K and 512K contexts (Abstract, Introduction, Section 6) is overstated. While the model outperforms the base Qwen2.5-VL-7B at these lengths, the performance at 512K (52.52) is lower than at 256K (55.09), indicating a degradation as context length increases beyond the

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper presents a systematic study of long-context continued pre-training for LVLMs, focusing on data curation and training design. From a safety and ethics perspective, several areas require clarification and potential revision. First, the construction of the document pool (Sec 4.1) involves 1.5 million PDFs from "multiple sources," including academic papers, books, and technical manuals. The paper lacks sufficient detail on the legal and ethical basis for collecting and using this data. Spe

## paper_reviewer_scientific_evidence — verdict: full_revision

- **[science]** The scientific evidence presented in this paper is currently insufficient to support its central claims regarding the robustness of the proposed training recipe and the model's generalization capabilities. First, the evaluation methodology lacks statistical rigor. Key results, particularly the generalization to 256K and 512K contexts (Section 6, Table 2) and the ablation studies on data mixture (Section 5), are reported as single-point estimates. In long-context modeling, performance can vary si

## paper_reviewer_statistical_analysis — verdict: full_revision

- **[science]** The paper reports performance gains (e.g., +7.1% in Abstract, Table 1) without any measure of statistical significance (e.g., standard deviation, confidence intervals, or p-values). Given the use of LLM-based judges which can introduce variance, single-run results are insufficient to claim superiority. Re-run experiments with multiple seeds or report variance metrics.
- **[science]** In Section 5.2 (Table 2), the optimal extraction-to-reasoning ratio (8:2) is selected based on point estimates. No statistical test (e.g., t-test or ANOVA) is provided to confirm that the difference between 8:2 and the next best ratio (6:4) is significant rather than noise. The conclusion that 'retrieval remains the primary bottleneck' relies on this unverified difference.
- **[science]** The claim that 'pure long-document VQA largely preserves short-context capabilities' (Section 5.3) compares a 0% short-data model (65.48) to the base (66.47). The drop is small, but without error bars or multiple runs, it is impossible to determine if this preservation is statistically robust or if the observed 'mild drop' is within the margin of error of the evaluation protocol.
- **[science]** The evaluation relies heavily on LLM-based judges (Appendix A.2) for scoring. The paper does not report the inter-annotator agreement (e.g., Cohen's Kappa) or the stability of the judge itself. If the judge has high variance, the reported gains (e.g., 57.70 vs 50.59) may not be reproducible. A statistical analysis of the judge's consistency is required.

## paper_reviewer_text_formatting — verdict: full_revision

- **[writing]** Remove all '[UNRESOLVED-CLAIM: ...]' artifacts from the text. These are internal debugging markers (e.g., in Abstract, Intro, Related Work, Setup, Curation, Results) that must not appear in the final manuscript. They break sentence flow and violate formatting standards.
- **[writing]** Fix broken footnote syntax in sections/4_curation.tex. The command '\footnote{.' is incomplete and missing the closing brace and content. Similarly, in sections/7_appendix.tex, the footnote for VLMEvalKit is truncated ('\url{.'). These will cause compilation errors.
- **[writing]** Correct double periods in sections/4_curation.tex and sections/5_data_mixture_and_training.tex. Multiple instances of '..' appear at the end of sentences (e.g., '...sources [UNRESOLVED-CLAIM...].'). This is a punctuation error.
- **[writing]** Fix inconsistent list formatting in sections/4_curation.tex. The 'Data types' subsection uses '\begin{inparaenum}[(i)]' but the items are not properly aligned or separated, and the text following the list is not indented correctly relative to the list items in the source.
- **[writing]** Standardize citation command usage. The paper mixes '\citep' and '\cite' (e.g., '\cite{bai2025qwen2}' in section 4 vs '\citep' elsewhere). Ensure consistent use of the defined citation style (likely '\citep' for natbib/unsrtnat) throughout the document.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The paper presents a systematic study of long-context continued pre-training for LVLMs. The writing is generally clear and the structure is logical. However, there are several minor grammatical errors and formatting inconsistencies that need to be addressed to improve the overall quality and professionalism of the manuscript. Specifically, there are issues with capitalization at the beginning of sentences and after commas. For instance, in Section 4, subsection 4, the sentence "we compare the fi
