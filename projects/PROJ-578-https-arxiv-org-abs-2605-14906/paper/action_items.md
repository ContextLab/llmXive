# Automated-review action items — MemLens: Benchmarking Multimodal Long-Term Memory in Large Vision-Language Models

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer — verdict: major_revision_science

- **[science]** Verify existence of all cited models (GPT-5.4, Gemini-3.1-Pro, Kimi-K2.5, Qwen3.5). The paper cites models with future dates (2026) and versions not yet released. If these are hypothetical, the entire experimental section is invalid and must be re-run on available models. If real, provide proof of access. This is a fatal scientific flaw if unverified.
- **[science]** Re-run the image-ablation study and main evaluation on a verified set of existing models. The current results (e.g., GPT-5.4 93.13% accuracy) are based on non-existent or unverified models, rendering the benchmark's conclusions about 'complementary failure modes' scientifically unsound.
- **[science]** Clarify the 'LLM-as-Judge' validation. The paper claims a Qwen3-VL-235B judge with high agreement, but if the judge model itself is unverified or future-dated, the evaluation metric is circular or invalid. Re-validate with a confirmed judge model.
- **[science]** Address the 'Synthetic conversations' limitation more rigorously. While the paper admits to LLM-generated sessions, the claim that 'DeBERTa F1 57.92% confirms negligible stylistic signal' is weak. Provide a more robust human evaluation or a stronger statistical argument for the naturalness of the synthetic data, as this is a core component of the benchmark's validity.

## paper_reviewer_claim_accuracy — verdict: full_revision

- **[fatal]** The paper cites 'GPT-5.4' (e.g., Abstract, Table 2, Appendix A) and 'Gemini-3.1-Pro' as evaluated models. These model versions do not exist as of the current date (2026 context in paper vs reality). The citations (singh2025openaigpt5card, googledeepmind2026gemini3procard) appear to reference fictional or future-dated technical reports. This invalidates the empirical claims regarding model performance and the image-ablation study results.
- **[fatal]** The paper claims an image-ablation study shows accuracy drops below 2% for 'GPT-5.4' and 'Gemini-3.1-Pro' (Abstract, Section 3.4). Since these models are not real, the specific numerical results (93.13% vs 1.74%) are unverifiable and likely hallucinated or fabricated. The core claim that 'solving MemLens requires visual evidence' relies on this invalid data.
- **[fatal]** The bibliography contains citations for non-existent papers (e.g., 'singh2025openaigpt5card', 'googledeepmind2026gemini3procard', 'kimiteam2026kimik25visualagentic'). The paper presents a benchmark for '2026' (NeurIPS 2026 template), but the cited works and models are not available in the public domain or arXiv, making the reproducibility and validity of the evaluation impossible to verify.

## paper_reviewer_code_quality_paper — verdict: minor_revision

- **[writing]** The LaTeX source contains a commented-out NeurIPS Checklist section (lines 1040-1080) and a placeholder table with '...' rows (line 630). These must be removed or fully populated before final submission to ensure reproducibility and professional presentation.
- **[writing]** The 'Reproducibility Statement' cites specific URLs (HuggingFace, GitHub) but the provided LaTeX source lacks a `bibliography` file or `\bibliography{}` command to resolve the 100+ citations. The build will fail without the `.bib` file, preventing verification of the code/data links.
- **[writing]** The code quality of the manuscript itself is compromised by the inclusion of a massive, unstructured list of critical elements (lines 1-200) which appears to be a debug artifact or ingestion log rather than part of the paper. This should be stripped to ensure the source is clean and maintainable.

## paper_reviewer_data_quality_paper — verdict: full_revision

- **[fatal]** The paper claims to release 4,695 unique images under CC-BY-4.0 (Ethics Statement, App 2.1), but the sourcing method (iCrawler from public web) implies third-party copyright. The license statement 'Third-party images not relicensed' contradicts the claim of releasing them under CC-BY-4.0. A clear, verifiable license manifest for every image URL is required to resolve this legal ambiguity.
- **[science]** The dataset construction relies on 'public web searches' via iCrawler (App 2.1) but lacks a formal datasheet detailing the specific search queries, timestamps, and source URLs for the 4,695 images. Without a persistent, versioned registry of source URLs and their original licenses, the dataset is subject to link rot and cannot be audited for provenance or copyright compliance.
- **[writing]** The paper states that 'no two questions share the same source image' (App 2.1) and uses perceptual hashing for deduplication. However, it does not provide the hash values or the specific deduplication threshold logic in a machine-readable format. This prevents independent verification of the uniqueness claim and the integrity of the dataset against future link rot or image replacement.
- **[writing]** The 'Ethics Statement' mentions a '7-day removal' takedown contact but does not provide the specific contact mechanism (email, form) or the current status of any takedown requests. This lack of transparency regarding the data removal process undermines the ethical compliance of the dataset release.

## paper_reviewer_figure_critic — verdict: minor_revision

- **[writing]** Figure 1 (Table 1) uses a custom color 'softredbg' without a defined color model in the preamble. This will cause compilation failure. Define \definecolor{softredbg}{RGB}{255,240,240} or similar.
- **[writing]** Figure 2 (pipeline.pdf) and Figure 3 (per_type_heatmap.pdf) lack explicit axis labels and units in the LaTeX source. Ensure 'Context Length (tokens)' and 'Accuracy (%)' are clearly labeled on axes to meet print legibility standards.
- **[writing]** Figure 4 (specialization_heatmap_unified.pdf) and Figure 5 (context_degradation_lines.pdf) are referenced as 'wrapfigure' or 'figure*' but the source code does not include the \caption or \label commands for the sub-figures in the provided snippet. Verify all sub-captions are present and legible at 100% zoom.
- **[writing]** The 'wrong_answer_pie.pdf' (Figure 14) and 'context_delta_heatmap.pdf' (Figure 15) rely on color differentiation for error categories. Verify that the color palette is colorblind-safe (e.g., avoid red/green contrasts) and that a legend is included within the figure bounds, not just in the caption.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The paper relies heavily on a dense layer of acronyms and specialized terminology that creates a barrier for readers outside the immediate sub-field of long-context multimodal evaluation. In the Abstract and Introduction, the five core memory abilities are introduced solely as acronyms: IE (Information Extraction), MSR (Multi-Session Reasoning), TR (Temporal Reasoning), KU (Knowledge Update), and AR (Answer Refusal). While Table 1 lists them, the text repeatedly uses the acronyms (e.g., "IE and

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The paper presents a strong empirical benchmark, but several logical gaps exist between the stated premises and the drawn conclusions. First, the abstract claims that removing images drops accuracy below 2% for "80.4% of questions whose evidence includes images." This conflates two distinct categories defined in Section 3.2 and Table 2: "image-essential" (65.7%) and "image-supportive" (14.7%). The ablation study in Table 1 (tab:mm_purity) aggregates these into a single set ($n=634$). Logically,

## paper_reviewer_overreach — verdict: full_revision

- **[science]** Abstract claims 80.4% of questions require visual evidence and collapse below 2% without images. Section 3.4 shows only 65.7% are image-essential; 14.7% are supportive. The ablation (Table 2) validates only the essential subset. Claiming the full 80.4% collapses is an unsupported extrapolation.
- **[writing]** Conclusion states "neither approach solves the task" based on MSR scores <30%. This overgeneralizes a specific sub-task failure to the entire benchmark, where models score 50-90% on IE, TR, KU, and AR. The claim that hybrid architectures are required for the whole task is not supported by the data.
- **[writing]** Abstract claims "No existing benchmark systematically compares... on questions requiring visual evidence." This ignores LoCoMo and Mem-Gallery which evaluate multimodal memory. The claim should be narrowed to the specific "length-controlled comparison of long-context vs. memory-agent" novelty.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper presents a robust benchmark for multimodal memory but requires specific clarifications regarding data privacy and safety evaluation protocols before the dataset can be considered safe for public release. Data Privacy and PII: While the authors state in the Ethics Statement and Appendix E001 that "No person-centric topics" and "no face/identity search" were used, the dataset includes "Natural Photographs" of "lifestyle" and "scenes" (Table E001). In web-scraped imagery, incidental faces

## paper_reviewer_scientific_evidence — verdict: full_revision

- **[science]** The claim that 80.4% of questions require visual evidence is unsupported. Table 1 and Section 3.3 state 65.7% are image-essential and 14.7% supportive. The ablation in Table 2 tests the combined set (n=634) but does not isolate the 'essential' subset. If 'supportive' questions retain >2% accuracy without images, the aggregate drop to <2% is misleading. Separate ablation results for 'essential' vs 'supportive' are required to validate the claim.
- **[science]** The evaluation of 27 LVLMs lacks statistical significance testing. Reported accuracy differences (e.g., Gemini-3.1-Pro vs open-weight) have no confidence intervals or p-values. With small subtype sample sizes (e.g., MSR n=46), observed differences may be within margin of error. Bootstrap CIs are only provided for the 195-subset, not the main 789-question results used for conclusions.
- **[science]** The LLM-as-Judge metric (Qwen3-VL-235B) shows leniency bias (5.4% FP vs 1.0% FN). This may inflate scores for verbose models, skewing rankings. The impact of this bias on the final leaderboard is not quantified. A sensitivity analysis or bias-corrected scoring is needed to ensure rankings reflect memory fidelity rather than verbosity.
- **[writing]** The claim that 'Multi-session reasoning caps most systems below 30%' overstates the evidence. Table 1 shows Kimi-K2.5 achieving 44.06% on MSR at 32K. The abstract generalizes to 'most systems' without defining thresholds or excluding outliers. The data shows variance, not a hard cap. Refine the claim to reflect the observed distribution.

## paper_reviewer_statistical_analysis — verdict: full_revision

- **[science]** The statistical analysis in the paper is largely descriptive, relying on point estimates without sufficient measures of uncertainty or rigorous hypothesis testing to support the strength of the claims. First, the validation of the LLM-as-Judge metric (Section 4.2, Appendix B.2) reports Cohen's kappa values (0.93 and 0.86) but fails to provide 95% confidence intervals. For the human consensus sample (n=484), the margin of error for kappa is non-negligible; without CIs, the claim of "high agreemen

## paper_reviewer_text_formatting — verdict: minor_revision

- **[writing]** The bibliography section is missing. The LaTeX source contains numerous \cite and \citep commands (e.g., lines 15, 22, 45) but lacks a \bibliography{...} or \printbibliography command, and no .bib file content is provided. This will cause compilation failure.
- **[writing]** The 'NeurIPS Paper Checklist' in Appendix (lines 1330-1365) is commented out using \iffalse ... \fi. For a submission, this section must be active and visible to reviewers. Uncomment this block.
- **[writing]** Table formatting inconsistency: Table 1 (line 38) uses \columncolor{softredbg} but the color 'softredbg' is not defined in the preamble. This will cause a LaTeX error. Define the color or remove the command.
- **[writing]** Figure placement: Several figures in the Appendix (e.g., lines 1050, 1060) use the [H] float specifier from the 'float' package. Ensure the 'float' package is loaded (it is) and that these figures do not cause excessive vertical whitespace or page breaks in the final PDF.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In the author block (line 14), 'Deparment' is a typo and must be corrected to 'Department'. This is a basic spelling error in the affiliation line.
- **[writing]** The abstract contains a sentence fragment: 'An image-ablation study confirms that solving ench{} requires visual evidence: removing evidence images drops two frontier LVLMs below 2\% accuracy on the 80.4\% of questions whose evidence includes images.' The phrasing 'on the 80.4% of questions' is slightly awkward; consider 'for the 80.4% of questions' or restructuring for better flow.
- **[writing]** Section 3.1 (Memory Abilities) uses inconsistent capitalization in the list items. 'Entity' and 'PrevInfo' are capitalized, while 'Counting', 'arithmetic', and 'entity resolution' are not. Standardize capitalization (e.g., Title Case) for all subtypes to improve readability and professionalism.
- **[writing]** In Section 4.2 (Main Results), the phrase 'No model dominates' is followed by a reference to Figure 2, but the text says 'No single model dominates all types (Figure~ef{fig:specialization})'. Ensure the figure label matches the intended figure (specialization vs. per-type heatmap) and that the text flow clearly distinguishes between the two visualizations.
