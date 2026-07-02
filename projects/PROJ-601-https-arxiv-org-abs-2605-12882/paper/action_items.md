# Automated-review action items — CiteVQA: Benchmarking Evidence Attribution for Trustworthy Document Intelligence

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Unreachable Citation: The abstract cites 2605.12882 (arXiv) as the source for the benchmark introduction. The bibliography explicitly flags this link as "unreachable". A claim about the existence and nature of a benchmark cannot be supported by a dead link. This is a critical failure in claim accuracy verification. The authors must provide a working URL or a stable archive link.
- **[writing]** Unresolved Claim Placeholder: The abstract contains a raw placeholder: [UNRESOLVED-CLAIM: c_10e39cd2 — status=not_enough_info]. This indicates that the specific claim regarding the "strongest open-source MLLM" (stated as 22.5) currently lacks the necessary evidentiary support or citation in the manuscript's logic. Leaving this in the final text renders the claim unsupported.
- **[writing]** Precision of "Caps at": The text states the strongest system "caps at 76.0". While Table 1 shows an Overall SAA of 76.0 for Gemini-3.1-Pro-Preview, the "Multi (1-Gold)" sub-category shows 79.7. While "Overall" is the standard metric, the phrasing "caps at" is slightly imprecise if a higher score exists in a valid sub-scenario. It is recommended to clarify "achieves an Overall SAA of 76.0" to avoid ambiguity.
- **[writing]** Sub-category Verification: The claim of "30 sub-categories" in Section 3.1 is not explicitly broken down in Table 1 or the main text. While the number 711 and 7 domains are verified, the specific count of 30 sub-categories should be referenced to a specific table or appendix to ensure the claim is fully supported by the provided data. The presence of the unresolved claim placeholder and the unreachable citation are significant issues that prevent the claims from being fully verified.

## paper_reviewer_jargon_police — verdict: full_revision

- **[science]** The manuscript is heavily laden with domain-specific jargon and unexplained acronyms that significantly hinder accessibility for non-specialist readers, including those in law, medicine, or general policy who are the intended beneficiaries of "trustworthy document intelligence." First, the abstract and introduction introduce MLLMs (Multimodal Large Language Models) and Doc-VQA (Document Visual Question Answering) without fully expanding them or providing a brief, plain-language definition. "Doc-

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** Abstract claims strongest open-source MLLM reaches 'just 22.5' SAA. Table 1 shows Qwen3-VL-235B-A22B at 22.5, but others are lower. Explicitly name the model in the abstract to avoid ambiguity about which model is 'strongest'.
- **[science]** SAA definition (Sec 4.1) uses 'OR' (Rel>=4 OR Rec>=0.6), allowing pass if only one metric is high. This contradicts the text claiming 'both' answer and region must be correct. Fix logic or text to align.
- **[science]** Ground-truth 'Crucial Evidence' relies on ablation by a single model (Qwen3-VL-235B-A22B). If this model fails due to its own limits, evidence is mislabeled. Address this circularity in the methodology.

## paper_reviewer_overreach — verdict: full_revision

- **[science]** The Abstract claims ground-truth citations are "validated through expert review," implying full dataset verification. However, Section 3.3 and Appendix D.3 state experts only sampled 200 of 1,897 items. This overstates the human validation of the gold standard.
- **[science]** Section 5.2 claims precise localization "facilitates correct answering" based on correlation and restricted search space ablations. This conflates retrieval difficulty with reasoning causality; the data does not prove attribution causes better answers, only that models fail with large search spaces.
- **[writing]** The conclusion that small models are "extremely risky" in high-stakes domains (Section 4.1) overgeneralizes. The benchmark tests element-level citation in complex PDFs, not actual domain workflows. This risk assessment exceeds the experimental scope.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper addresses a critical safety issue in Document Intelligence: the risk of "Attribution Hallucination" where models provide correct answers based on incorrect evidence, which is particularly dangerous in high-stakes domains like law and medicine. The proposed benchmark, CiteVQA, is a significant step toward safer AI deployment. However, several ethical and safety concerns regarding data provenance, privacy, and labor practices require clarification before acceptance. First, regarding data

## paper_reviewer_scientific_evidence — verdict: full_revision

- **[science]** The scientific evidence supporting the central claims of the CiteVQA benchmark is currently insufficient to warrant acceptance. The primary concern lies in the validity of the ground-truth labels. The paper asserts that "Crucial Evidence" is identified via an automated masking ablation pipeline (Section 3.2, "Relevance Filtering and Crucial Evidence Identification"). However, there is no quantitative evidence provided (e.g., inter-annotator agreement, precision/recall against a human-annotated s

## paper_reviewer_statistical_analysis — verdict: full_revision

- **[science]** The statistical analysis presented in the CiteVQA paper is currently insufficient to support the strong claims regarding model performance gaps and the validity of the proposed metrics. First, the validation of the automated evaluation pipeline (Appendix, Table tab:model-eval) relies exclusively on the Friedman test to compare LLM judges against human experts. The authors report p-values > 0.05 and conclude there is "no statistically significant deviation." This is a fundamental statistical erro

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The abstract contains a broken URL placeholder: 'Our repository is available at \url{.}'. This must be replaced with the actual repository link (e.g., GitHub) or removed if unavailable.
- **[writing]** In the abstract, the phrase 'Auditing 20 MLLMs reveals a pervasive Attribution Hallucination' is followed by a raw artifact tag '[UNRESOLVED-CLAIM: c_10e39cd2 — status=not_enough_info]'. This internal debugging tag must be removed before publication.
- **[writing]** Section 3.1 contains a broken footnote command: 'Common Crawl\footnote{\url{; see Appendix...'. The URL inside the footnote is incomplete and missing the closing brace. This will cause a LaTeX compilation error.
- **[writing]** In Section 5.2, the phrase 'As the issue of hallucination in Large Language Models (LLMs) remain a persistent threat' contains a subject-verb agreement error. 'Issue' is singular, so 'remain' should be 'remains'.
- **[writing]** The caption for Table 2 (Section 3.4) uses the command '\highlightblue' and '\highlightgreen' which are defined in the preamble but the table content relies on them for highlighting. Ensure these commands are robust in the table environment or use standard LaTeX highlighting if the custom commands fail in tabular contexts.
