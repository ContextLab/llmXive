# Automated-review action items — Intern-Atlas: A Methodological Evolution Graph as Research Infrastructure for AI Scientists

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer — verdict: major_revision_science

- **[science]** The paper cites and claims acceptance from conferences in 2025 and 2026 (e.g., ICLR 2026, NeurIPS 2025) which are in the future relative to the current date. This invalidates the 'Strata Dataset' and the 'Human Evaluation' results. The research pipeline must be re-run with a temporally consistent corpus (e.g., up to 2024) to ensure scientific validity.
- **[science]** The bibliography contains multiple entries with future years (2025, 2026) that appear to be hallucinated or speculative (e.g., 'DeepInnovator', 'Spark', 'THE-Tree'). These citations must be verified against real publications or removed, as they undermine the credibility of the related work and experimental baselines.
- **[science]** The 'Strata Dataset' relies on 'Rejected submissions from ICLR 2026'. Since this conference has not occurred, the dataset cannot exist as described. The experimental design must be revised to use a real, completed dataset (e.g., ICLR 2024/2025) to support the claims of idea evaluation utility.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The paper claims the corpus spans '1965–2025' (Abstract, Sec 3.2) and lists 'ICLR 2026' papers in the Strata Dataset (Sec 4.2, App D.3). Since the current date is prior to 2026, these claims are factually impossible. The authors must correct the end-year to the actual data cutoff (e.g., 2024 or 2025) and remove future-dated conference entries from the dataset description.
- **[writing]** The paper cites 'nanoresearch2026' (Papers With Code) and 'DeepInnovator' (2026) as existing works to support claims about current research infrastructure gaps. Citing works with future publication years (2026) as established literature undermines the factual basis of the 'Related Work' and 'Introduction' arguments. These citations must be verified or replaced with existing, verifiable sources.
- **[science]** The claim that the graph contains '9,410,201 semantically typed edges' (Abstract) is derived from a corpus of '1,030,314 papers' (Abstract, Sec 3.2). However, Appendix C.2 Table 1 lists a 'Grand total edges' of only 1,410,183 (including stubs). The discrepancy between the abstract's edge count and the appendix's detailed breakdown is unexplained and suggests a potential error in the reported statistics or a misunderstanding of what constitutes an 'edge' in the graph definition.

## paper_reviewer_code_quality_paper — verdict: minor_revision

- **[writing]** The manuscript references external assets (e.g., `intro.pdf`, `method.pdf`, `figures/Figure3.pdf`) and a bibliography file (`ref.bib`) that are not present in the provided source bundle. To ensure reproducibility from scratch, the build process must either include these binary assets or provide a script to fetch them. Currently, the LaTeX source is incomplete for a standalone compilation.
- **[writing]** The code quality of the LaTeX source itself is compromised by commented-out blocks (e.g., lines 230-235, 1050-1055) and inconsistent formatting. While not fatal, cleaning up these dead code sections and ensuring all `\includegraphics` paths are valid relative to the source directory is necessary for a clean build.

## paper_reviewer_data_quality_paper — verdict: full_revision

- **[science]** The paper claims to process 1,030,314 papers from 1965-2025 (Sec 3.2, App C.1), but the venue breakdown table (App C.1) only lists editions from 2023-2025, totaling ~66k papers. The source of the remaining ~960k papers (1965-2022) is not specified, nor is the license status or provenance of this historical corpus. Without a clear data source and license for the majority of the dataset, the reproducibility and legal validity of the graph are compromised.
- **[fatal]** The evaluation relies on a 'Strata Dataset' of 1,200 papers from 'ICLR 2026', 'ICML 2025', and 'NeurIPS 2025' (Sec 4.2, App D.3). As of the current date, these conferences have not occurred. The paper does not clarify if this data is synthetic, projected, or if the dates are typos for past years. If the evaluation data is synthetic or fabricated to simulate future events, the claims regarding 'human-alignment' and 'publication strata' are invalid.
- **[writing]** The paper mentions a 'released registry' and 'code release' (App C.1, App D.3) but provides no specific URLs, DOIs, or repository paths for the raw data, the processed graph, or the evaluation scripts. The HuggingFace link in the title page is a placeholder. Data quality review requires access to the actual data artifacts to verify schema, missing data handling, and version control.
- **[writing]** The 'Method entity curation' section (App C.1) states that an LLM expansion pass was used to find methods, but it does not specify the version of the LLM used for this specific step, the temperature settings, or the exact prompt. Furthermore, the 'hand-curated negative-surface list' for alias resolution is not provided. This lack of transparency prevents verification of the schema's integrity and potential bias in method identification.

## paper_reviewer_figure_critic — verdict: minor_revision

- **[writing]** Figure 1 (intro.pdf) and Figure 2 (method.pdf) are referenced but the source files are missing from the provided asset list. The review cannot verify axis labels, color choices, or legibility for these primary figures. Please ensure all referenced PDFs are included in the submission.
- **[writing]** Figure 3 (Figure3.pdf) caption describes a 'detailed view of the LLM continent' but the file is listed as 'figures/Figure3.pdf'. The caption text is dense; ensure the visual legend or color coding for the 'six paradigm continents' is distinct enough to be legible at print scale without relying solely on the caption text.
- **[writing]** Figure 4 (main_four_results) combines a bar chart (a) and a scatter plot (d) in a single caption. The scatter plot (exp02_overall_tier_scatter.pdf) lacks visible axis labels in the filename description; verify that the final PDF includes explicit axis titles (e.g., 'Overall Score', 'Publication Stratum') and units where applicable, as the current LaTeX source does not show the plot generation code.
- **[writing]** Figure 5 (downstream-results) includes a heatmap (exp02_judgment_spearman_heatmap.pdf). Heatmaps require high-contrast color maps for print legibility. Verify that the color scale is colorblind-friendly and that the correlation values (Spearman coefficients) are legible within the cells or clearly indicated in a legend, as the current source does not show the plotting code.

## paper_reviewer_jargon_police — verdict: full_revision

- **[science]** The manuscript suffers from significant jargon overuse, frequently employing technical terms from graph theory, information retrieval, and deep learning without definition or simplification. This creates a barrier for non-specialist readers, including researchers in adjacent fields who might benefit from the infrastructure. Specific instances include the use of 'SGT-MCTS' in the Abstract (line 14) and 'MCTS' in the Introduction (line 45) without defining the acronym first. The term 'parametric m

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The paper presents a compelling architecture for a methodological evolution graph, but several logical gaps exist between the stated premises and the derived conclusions. First, the evaluation of the SGT-MCTS algorithm (Table 1, Sec 4.1) claims a 39.9 point improvement in Node Recall over Beam@10. While the arithmetic (84.8 - 44.9) is correct, the causal explanation—that MCTS's exploration of "under-visited branches" leads to higher recall than a beam search that retains top-k paths—is not rigor

## paper_reviewer_overreach — verdict: full_revision

- **[science]** The claim of "verbatim source evidence" for 9.4M edges is over-claimed given the 70.4% Phase-1 extraction accuracy (Appendix). A 30% error rate invalidates the "causal" certainty implied in the Abstract.
- **[science]** The Idea Generation evaluation (Sec 4.3) over-attributes win-rate gains to the graph. The LLM generates the text; the graph only identifies gaps. The study fails to isolate the graph's contribution from the LLM's parametric knowledge.
- **[writing]** The Conclusion claims "faithful" recovery of expert chains, yet Table 1 shows ~15-20% Node/Edge Recall loss. Describing this as faithful without quantifying the error rate in the main text is an over-interpretation.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper claims to process 1M+ papers from 1965-2025 (Sec 2.2, App C). Explicitly state the data licensing status for all venues (e.g., arXiv vs. paywalled proceedings). Confirm that the 'verbatim quote' extraction (Eq 1) complies with fair use and copyright restrictions for the specific venues included.
- **[science]** The 'Strata Dataset' (Sec 4.2) includes rejected submissions from ICLR 2026. Clarify the consent and anonymization protocol for these rejected papers. If authors were not explicitly consented for this specific evaluation, the use of their rejected work for training/evaluating an automated idea generator raises ethical concerns regarding academic privacy and potential bias against rejected work.
- **[writing]** The 'Idea Generation' operator (Sec 3.3) proposes new research ideas based on 'structural gaps.' Discuss the risk of the system amplifying existing citation biases (e.g., favoring well-cited methods) or generating ideas that inadvertently infringe on ongoing, unpublished work by the community. A 'Broader Impact' section is present but lacks specific mitigation strategies for these dual-use risks.

## paper_reviewer_scientific_evidence — verdict: full_revision

- **[science]** The scientific evidence supporting the core claims of Intern-Atlas is currently insufficient to warrant acceptance. While the system architecture is sophisticated, the empirical validation relies heavily on proxies and lacks rigorous statistical grounding. First, the evaluation of the SGT-MCTS algorithm (Section 4.1, Table 1) presents point estimates (e.g., Node Recall 84.8%) without any measure of variance, confidence intervals, or statistical significance testing. Given that MCTS is a stochast

## paper_reviewer_statistical_analysis — verdict: full_revision

- **[science]** The statistical analysis presented in the paper is insufficient to support the strong claims made regarding the performance of Intern-Atlas. While the system architecture is sophisticated, the empirical validation lacks rigorous statistical grounding. First, the results in Table 1 (Section 4.1) regarding the SGT-MCTS algorithm are highly suspicious. The reported Node Recall (NR) and Chain Alignment Score (CAS) are identical to one decimal place for every method (e.g., Beam@10: 44.9 for both). Si

## paper_reviewer_text_formatting — verdict: minor_revision

- **[writing]** In Section 4.1 (exp01), the caption for Figure 4 references subfigure (b) ('Distribution of Overall scores...'), but the LaTeX code only defines subfigures (a) and (d). The caption text and labels are inconsistent with the provided code structure.
- **[writing]** The bibliography style 'unsrt' is used, but the .bib file contains duplicate @String definitions (e.g., 'PAMI', 'CVPR') and inconsistent formatting for conference proceedings (some use 'booktitle', others 'journal'). This will cause compilation warnings and inconsistent citation rendering.
- **[writing]** In Appendix A.1, the 'Bottleneck dimension taxonomy' table (tab:dim-taxonomy) is commented out in the source code (lines 630-650) but referenced in the text. The active table (lines 652-670) uses 'tabularx' which may cause line-breaking issues in the 'X' column if the definitions are too long; ensure the column width is sufficient or switch to 'longtable' if it spans pages.
- **[writing]** Figure 3 caption references 'Figure3.pdf' but the file path in the code is 'figures/Figure3.pdf'. Ensure the file path matches the actual directory structure to avoid 'File not found' errors during compilation.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 1 (Introduction), the sentence 'Their parametric memory is a lossy compression that underrepresents low-frequency or long-tail methodological knowledge.Their autoregressive inference...' is missing a space after the period. Please correct this typo.
- **[writing]** In Section 2 (Related Work), the phrase 'Intern-Atlas bridges this critical infrastructure gap' appears in the middle of a paragraph without a preceding sentence break or clear transition from the previous discussion of OpenAlex. Consider adding a transition sentence or breaking the paragraph for better flow.
- **[writing]** In Section 3 (Method), the phrase 'Idea evaluation places a research idea' in the first sentence of Section 3.2.2 is grammatically incomplete and unclear. It likely means 'Idea evaluation places a research idea within the methodological landscape.' Please rephrase for clarity.
- **[writing]** In Section 4 (Experiment), the caption for Figure 3 (Figure~ef{fig:intern-atlas-overview-half}) contains a minor inconsistency: it refers to 'Figure 3' in the text but the label is 'Figure3.pdf'. Ensure consistency between figure labels and references in the text.
- **[writing]** In Appendix A (Graph Construction), the table caption for Table~ef{tab:dim-taxonomy} is repeated twice in the source code (once commented out, once active). Remove the commented-out version to avoid confusion during compilation.
