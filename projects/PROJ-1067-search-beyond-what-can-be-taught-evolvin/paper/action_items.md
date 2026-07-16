# Automated-review action items — Search Beyond What Can Be Taught: Evolving the Knowledge Boundary in Agentic Visual Generation

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Section 3.1 cites 'Gemini-3-Flash' as the judge. The bib entry 'nanobanana2025gemini' lists 'Gemini 2.5 Flash / Gemini 3 Pro'. Verify if 'Gemini-3-Flash' is a hallucinated name or a typo for 'Gemini 2.5 Flash', as the specific model identity is critical for the reported 0.87 correlation.
- **[writing]** Section 3.1 claims 'Qwen-Image-1 drops nearly 40 points', but Table 1 lists 'Qwen-Image' (NoSearch 67.4, Search 27.9). Clarify if 'Qwen-Image' in the table corresponds to 'Qwen-Image-1' in the text to ensure the 40-point claim is supported by the correct model identifier.
- **[writing]** Section 4.1 states Phase 2 'slightly exceeding' the Oracle (31.8 vs 31.2). While mathematically correct, claiming a 0.6 point gain as 'exceeding' without statistical significance (e.g., p-value or std dev) is an overstatement of the result's robustness. Qualify the claim or add statistical context.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The caption claims the heatmap shows 'knowledge-driven degradation' and 'failure modes,' but the cells contain positive percentages (e.g., 65%, 42%) without a defined baseline or metric. It is unclear if these values represent failure rates, entity frequencies, or another metric, making the claim of 'degradation' unsupported by the visual data.
- **[writing]** Figure 1: The caption contains a dangling reference 'in .' where a dataset or section name is missing, leaving the context of the data undefined.
- **[science]** Figure 1: The colorbar scale (0–60+) contradicts the data labels (percentages). The cell labeled '65%' is colored dark red, but the colorbar's maximum tick is 60, and the color mapping for values >60 is undefined.
- **[fatal]** Figure 2: The rendered image is a black-and-white photograph of women carrying baskets in a field, which completely contradicts the caption's description of 'Yang Chaoyue request' references and 'end-to-end example's visual output' for an AI generation system.
- **[science]** Figure 2: The image fails to support the paper's claims about agentic visual generation, as it shows a historical photograph rather than the described 'retrieved references' (scene, costume, likeness) or the 'generated image'.
- **[fatal]** Figure 3: The rendered image is a collage of unrelated AI-generated images (portraits, anime, diagrams) that does not match the caption's claim of showing 'representative search-augmented generations' or 'failure categories'.
- **[science]** Figure 3: The image contains no labels, annotations, or visual indicators to identify the 'twelve failure categories' mentioned in the caption, making the figure impossible to interpret.
- **[writing]** Figure 3: The caption contains grammatical errors and missing references (e.g., 'from ,', 'captures the production-scale') that render the text incoherent.
- **[fatal]** Figure 5: The caption contains a missing dataset name ('distribution of .') and the chart labels use 'Chinese' and 'English' without specifying the dataset source, making the figure contextually incomplete.
- **[science]** Figure 6: The caption states 'area reflects relative prompt counts,' but the treemap is dominated by two massive blocks ('People & Professions' and 'Screen & Performance Media') that are not defined as categories in the smaller blocks, creating a confusing hierarchy where the visual 'mass' does not clearly map to the 'domain categories' mentioned.
- **[writing]** Figure 6: The caption contains a broken cross-reference ('deferred to Appendix (Figure )') with a missing figure number, making it impossible to verify the claim about 'uniform severity' mentioned in the text.
- **[science]** Figure 7(b): The caption states the mean number of knowledge gaps is 5.2, but the histogram bars are centered on bins (0-2, 3-5, 6-8, 9-12, 13+) where the highest frequency is in the 3-5 bin. A mean of 5.2 would imply a distribution skewed heavily towards the higher bins (6-8, 9-12, 13+), yet the bar for 6-8 is significantly lower than 3-5, and the bars for 9-12 and 13+ are very small. The visual distribution contradicts the stated mean of 5.2.
- **[writing]** Figure 7(b): The right y-axis label 'Cumulative %' is present, but the red line plot representing the cumulative percentage lacks a clear legend entry within the figure itself to distinguish it from the blue bars, relying solely on the caption for interpretation.
- **[science]** Figure 8: The caption claims drop magnitudes range from -0.1 to -39.1, but the chart labels show -0 (GPT-Image-2) and -39 (Qwen-2), creating a discrepancy between the text and the visual data.
- **[science]** Figure 8: The x-axis labels are slanted and overlap significantly (e.g., 'Bagel', 'Klein-4B', 'Klein-9B'), making them difficult to read and potentially illegible in lower resolutions.
- **[writing]** Figure 8: The y-axis label 'Score (0-100)' is present, but the specific metric being averaged (e.g., '93.1% of unique visual entities' or a specific quality score) is not defined in the caption or axis.
- **[writing]** Figure 9: The caption text is truncated at the end ('...reasoned sear'), cutting off the description of Phase 2.
- **[science]** Figure 9: The diagram shows a 'Rejection Finetuning' loop on the bottom right, but the arrow direction and connection to the 'VLM Reasoner' are ambiguous, making the feedback mechanism unclear.
- **[science]** Figure 10(a): The caption claims 'All three tiers show monotonic improvement,' but the Klein-4B chart shows a score drop from Set I (34.1) to Set III (27.4), and the Bagel-7B chart shows a drop from Set II (29.3) to Set III (22.6). The bars represent difficulty tiers, not a temporal progression of improvement.
- **[writing]** Figure 10(a): The caption states the bars show stages for 'Klein-4B', but the rendered figure explicitly contains a second panel for 'Bagel-7B' which is not mentioned in the caption text.
- **[writing]** Figure 10(b): The caption describes the shaded region as 'newly internalized knowledge' but does not explicitly define the shaded area in the plot (which visually represents the area between the base and DPO curves).

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Undefined Symbols in Equations: In Section 3.2, the symbols κ (tolerance), Q (quality function), and v_θ (velocity field) appear in equations or algorithm descriptions without explicit definitions in the surrounding prose. While the context implies their meaning, a rigorous definition (e.g., "where κ is the tolerance threshold") is missing at the point of first use.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** Section 2.2 states the training set has 20,188 rows, but the Abstract claims 20,839 total prompts. With a 751-prompt test set, 20,188 + 751 = 20,939, contradicting the 20,839 total. Clarify if the training count is 20,088 or if the total is 20,939 to ensure numerical consistency.
- **[writing]** Section 2.3 defines 'Search-Intensive' as 651 prompts, while Table 2 lists 'VisualSearch' (387) and 'TextualSearch' (264). Explicitly state that 'Search-Intensive' is the union of these two subsets to avoid ambiguity about whether it is a distinct category or a superset.
- **[writing]** The text in Section 4.1 claims a +7.0 gain for Phase 2 over the no-search DPO baseline. Verify that the values 56.9 (Phase 2) and 49.9 (baseline) in Table 3 are the correct figures to support this specific calculation, as the table layout separates these rows.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** Abstract claims 'recursive self-improvement' but experiments (Sec 5) show only one DPO/RFT pass. Appendix admits multi-round is future work. Change 'recursive' to 'single-step' or add multi-iteration results.
- **[writing]** Conclusion claims 'No model, regardless of scale, can internalize knowledge' universally. Experiments test only 4B/7B models. Narrow to 'within tested scales' or cite scaling law literature to support the universal claim.
- **[writing]** Finding 1 calls the bottleneck 'universal' across all generators. Data covers only a subset of models. Rephrase as 'observed across all tested generators' to avoid overgeneralizing beyond the empirical scope.

## paper_reviewer_safety_ethics — verdict: accept

This work presents a benchmark and co-training framework for agentic visual generation, focusing on the "world-knowledge bottleneck." From a safety and ethics perspective, the paper is well-constructed and appropriately addresses the primary risks associated with its contributions.

The authors explicitly acknowledge the dual-use potential of improving visual generation for real-world entities (e.g., public figures, cultural symbols) in Appendix \ref{app:broader}, noting the risk of "misinformation" and "privacy concerns." They propose concrete mitigations, including the exclusion of raw scraped images from the public release, the use of derived attributes/metadata instead, and the inclusion of usage guidelines prohibiting malicious identity synthesis. This aligns with responsible release practices for generative AI research.

Regarding data provenance, the paper details that the dataset (\dataset{}) is constructed from production user prompts and synthesized via template instantiation and LLM rewriting (Appendix \ref{app:benchmark}). The authors state that the seed entities are drawn from publicly available information and that the benchmark is designed for research evaluation. While the paper does not provide an IRB statement, this is appropriate as the work does not involve direct human subjects, sensitive personal data collection, or private user interactions; it analyzes aggregated, anonymized production logs and synthetic prompts. The "search corpus" consists of pre-executed, archived search sessions, and the authors commit to filtering out unsafe content (explicit sexual content, graphic violence, hateful material) before release (Appendix \ref{app:responsible_release}).

The paper does not disclose operational details for cyber-offense or biohazard methods, nor does it present a system designed for covert surveillance or deception. The "naive search" failures discussed (concept corruption, copy effects) are technical limitations of the current models, not vulnerabilities to be exploited. The evaluation protocol uses an automated VLM judge, and the authors note the correlation with human ratings, avoiding the release of potentially biased or harmful human-annotated data.

Overall, the paper demonstrates a clear understanding of the ethical implications of its work, implements reasonable safeguards for data release, and avoids the specific high-risk patterns (unconsented human data, actionable exploit details, PII exposure) that would necessitate a revision or rejection. The risk profile is low and well-managed.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[writing]** The paper presents a compelling hypothesis regarding the "knowledge boundary" in agentic visual generation and proposes a co-training framework to discover it. However, the evidentiary support for the central claims relies on experimental designs that do not fully rule out alternative explanations such as random variance, baseline asymmetry, or confounding model scale. First, the primary results in Table 1 (Section 4.2) and the progression in Figure 3 are reported as single-point estimates (e.g.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** Tables 1 and 2 report single-point scores (e.g., 31.8) without uncertainty metrics (SD/SE/CI). Given the stochastic nature of generation, this implies false precision. Report mean ± SD over ≥3 seeds for all results, or explicitly state results are from a single run and soften claims of 'monotonic improvement'.
- **[science]** Section 5.1 claims 'monotonic improvement' and implies statistical significance without reporting p-values, confidence intervals, or hypothesis tests. With no variance reported, differences like 31.8 vs 31.2 are indistinguishable from noise. Perform paired tests with multiple-comparison correction or rephrase claims as observed trends.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The paper presents a compelling argument for agentic visual generation, but the prose occasionally falters in clarity and flow, requiring the reader to re-parse sentences or infer missing grammatical elements. The most significant issue is the presence of sentence fragments and run-on sentences that disrupt the narrative momentum. In Section 1, the sentence "This renders an agentic visual generation problem: a generator is equipped with an agentic reasoner..." lacks a main verb for the subject "
