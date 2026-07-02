# Automated-review action items — Visual Generation in the New Era: An Evolution from Atomic Mapping to Agentic World Modeling

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer — verdict: major_revision_writing

- **[writing]** Complete the truncated bibliography file: the entry for 'Fang2025TBStarEditFI' is cut off mid-title. Ensure all 411+ references are fully defined with valid BibTeX syntax.
- **[writing]** Fix LaTeX compilation errors: The 'tab:unified_methods' table in section 2.1 contains '... (N rows omitted) ...' which breaks the tabular environment. Replace with actual data rows or remove the table if data is unavailable.
- **[writing]** Resolve missing figure files: The source references 'img/stress_test/physics/physics_solver_case.jpg' (mentioned in text) and 'img/method/fig_unified_architecture.jpg' (listed in inventory but not in source) which causes compilation failure. Either add the missing images or update the LaTeX references to match existing files.
- **[writing]** Remove placeholder text: The manuscript contains multiple instances of '... (N rows omitted) ...' in tables (e.g., tab:industrial_training_recipes, tab:unified_methods). These must be replaced with actual content or the tables must be reformatted to exclude the omitted rows.

## paper_reviewer_claim_accuracy — verdict: full_revision

- **[science]** Figure 1 caption claims 2025 contributed 188 papers (45.7%) of 411 total. However, the bibliography contains numerous 2026-dated citations (e.g., he2026gems, team2026longcat). If 2026 papers are included in the 411 total, the 2025 percentage is mathematically impossible. If excluded, the total count is likely wrong. The statistical claim is unsupported by the provided bibliography.
- **[writing]** Section 2.1 and 2.2 cite 'GEMS' (he2026gems) and 'Gen-Searcher' (feng2026gen) as representative L4 methods. These are dated 2026 in the bibliography. Citing future-dated papers as established 'representative methods' without clarifying they are pre-prints or hypothetical misrepresents the current state of the art.
- **[writing]** Section 3.1 claims '60% of recent frontier reports' use unified architecture based on a cohort of ten 2025-2026 reports. The specific calculation (6/10) is not verifiable from the text or bibliography. Additionally, the claim that 'Z-Image declines proprietary distillation' lacks a direct, verifiable citation to a technical report, making it an unsupported generalization.
- **[fatal]** Section 5.1 claims 'GPT 5.5 verified mismatches in 9s'. As of 2026, 'GPT 5.5' is not a publicly released or standard benchmarked model. This appears to be a hallucinated model name used as a factual claim, undermining the credibility of the stress test results.

## paper_reviewer_code_quality_paper — verdict: full_revision

- **[fatal]** The bibliography file (citation.bib) is truncated mid-entry (e.g., @article{Fang2025TBStarEditFI, ... 'Consi' cut off). This prevents compilation and breaks all citations. The file must be completed or split into multiple .bib files to ensure reproducibility.
- **[fatal]** The LaTeX source contains multiple placeholder comments like '... (N rows omitted) ...' in tables (e.g., tab:unified_methods, tab:industrial_training_recipes). These prevent the document from compiling into a complete, verifiable artifact. All data rows must be included or the tables must be refactored to load from external CSV/JSON data.
- **[writing]** The manuscript relies on external image assets (e.g., img/stress_test/physics/orange_sink.jpg) referenced in the LaTeX but the provided figure list suggests these are raw assets, not compiled PDFs. The build pipeline must be documented (e.g., a Makefile or script) to ensure figures are generated from source code if they are not static images, or the static images must be verified as present in the artifact bundle.

## paper_reviewer_data_quality_paper — verdict: full_revision

- **[science]** TextAtlas5M (Section 4.2): Cited with specific accuracy metrics (60.69%--82.88%). There is no public repository or preprint currently accessible for a dataset of this name with these exact stats.
- **[science]** GenExam (Section 4.2): Claims open-source models score <5% while closed-source score 72.7%. The source of this benchmark and the specific model versions tested are not provided.
- **[science]** FDABench (Section 6.1): Cited as a 2025 benchmark. The provided .bib entry points to an arXiv ID that must be verified for existence and accessibility. Without direct links to the data, code, or preprints for these resources, the quantitative claims regarding model performance and data density cannot be validated. This risks the paper being a "hallucinated survey" where statistics are fabricated or misattributed. 2. Synthetic Data Provenance and Licensing: Section 2.1 discusses a shift to "activ
- **[science]** The claim that "91K frontier-quality samples can match millions of web-scraped ones" (citing chen2025sharegpt) requires the full disclosure of the distillation pipeline. If the "frontier-quality" data is generated by closed models (e.g., GPT-4o, DALL-E 3), the paper must address the licensing implications of using such outputs to train open-weight models. Many closed-source models prohibit using their outputs for training other models.
- **[science]** The paper mentions "Z-Image declines proprietary distillation" but does not detail the alternative data sources used, leaving a gap in the reproducibility of the training recipe. 3. Reproducibility of Stress Tests: The "Stress Testing" section (Section 5) presents compelling visual case studies (e.g., the Metro Map, Jigsaw Puzzle). However, the input prompts used to generate these specific failures are not listed in the text or captions.
- **[science]** To verify that the failures are genuine model limitations and not artifacts of poor prompt engineering, the exact prompts and the specific model checkpoints (including version numbers) used for the "failure" images must be provided.
- **[science]** The claim that "GPT 5.5 verified mismatches" is problematic as GPT-5.5 is not a publicly released model. This suggests either a hallucinated model name or a reliance on an unreleased internal tool, which undermines the scientific rigor of the evaluation. 4. Bibliographic Integrity: The bibliography contains numerous entries with future dates (2026) and arXiv IDs that may not yet be public or may be placeholders. A rigorous review requires that every citation points to a real, accessible document

## paper_reviewer_figure_critic — verdict: full_revision

- **[fatal]** Figure 1 (fig_pub_trend) and Figure 2 (fig_research_landscape) are referenced in the text but the source files (img/intro/fig_pub_trend.pdf, img/intro/fig_research_landscape.pdf) are missing from the provided asset list. The paper cannot be reviewed for visual clarity or data accuracy without these files. Regenerate or include these PDFs.
- **[writing]** Figure 3 (fig_5levels_overview) is a JPG image (img/level/fig_5levels_overview.jpg). For a survey paper, this resolution is likely insufficient for print. Convert to a vector format (PDF/SVG) to ensure legibility of the taxonomy axes and text labels at 100% zoom.
- **[writing]** The stress-test figures (e.g., fig:fluid_case, fig:driving_causal_test) are provided as JPGs. Ensure these images include clear, high-contrast bounding boxes or arrows indicating the specific failure modes (e.g., the 'missing hub' in the metro map) to support the textual claims. Current file list suggests raw outputs; annotate them.
- **[fatal]** Figure 4 (fig_model_timeline) and Figure 5 (fig_modeling_paradigms) are referenced but their source files (img/method/fig_model_timeline.pdf, img/method/fig_modeling_paradigms.jpg) are not in the provided asset list. Verify file paths and include the missing assets.

## paper_reviewer_jargon_police — verdict: full_revision

- **[science]** The manuscript suffers from significant jargon overuse and a failure to define acronyms at first use, which creates a barrier for non-specialist readers and even researchers from adjacent fields. The paper frequently relies on community-specific shorthand and proprietary codenames without explanation. Specifically, the term "MM-DiT" is used repeatedly (e.g., Section 1, Section 2.1) without being expanded to "Multimodal Diffusion Transformer." Similarly, "VLM," "SFT," "MoE," "VQ," and "NFEs" appe

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** Closed-Source vs. Open-Source Logic: The claim that open-source systems are "L3-bounded by construction" (Section 2.4) while closed systems are "L4" is a strong logical assertion. This implies that the architecture of open models *prevents* them from being agents, which contradicts the paper's own discussion of "Agentic Visual Generation" (Section 6.3) where open frameworks like JarvisArt and GEMS are cited. The logic here is slightly circular: it defines L4 by the presence of an agent loop, the
- **[writing]** Solution-Problem Alignment: The paper proposes Visual Chain-of-Thought (vCoT) as a solution to spatial and compositional failures. However, the stress test results (Section 5) do not explicitly show that vCoT *fixes* the specific topological errors described (e.g., the metro map hub). The logical link between the identified problem (lack of discrete constraints) and the proposed solution (vCoT) is asserted but not rigorously demonstrated in the provided text. To improve logical consistency, the

## paper_reviewer_overreach — verdict: full_revision

- **[science]** The paper exhibits significant overreach in its characterization of the current state of visual generation, particularly regarding the capabilities of closed versus open systems and the fundamental nature of model reasoning. First, the distinction drawn between closed-source and open-source systems in Section 2.4 is speculative and unsupported. The authors claim that closed systems realize "L4 agentic generation" while open systems are "L3-bounded by construction" (Section 2.4, Highlight Box). T

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** This review focuses exclusively on safety, ethics, and potential for harm within the scope of the manuscript. Data Privacy and Consent: The manuscript cites the use of user-generated content from Reddit (r/PhotoshopRequest) for the REALEDIT dataset (Section 4.2.2, citing \citep{sushko2025realedit}). While the paper notes the scale of this data, it lacks a specific statement regarding the ethical handling of this data. Given that such datasets often contain personal images and requests that may r

## paper_reviewer_scientific_evidence — verdict: full_revision

- **[science]** Sample Size: There is no indication of how many prompts were tested per category, nor how many models were evaluated. A single failure case (e.g., Figure 6.1) demonstrates a *possibility* of failure, not a *systemic* limitation.
- **[science]** Controls: There are no control groups (e.g., comparing against a baseline model or a specific prompt engineering technique) to isolate the cause of failure.
- **[science]** Action: The authors must aggregate results. For example, "We tested 500 prompts across 5 models; 85% failed the spatial constraint." Without N > 1 and variance reporting, these sections are illustrative, not evidentiary. 2. Unsubstantiated Data Efficiency Claims (Section 4.1) The paper asserts that "91K frontier-quality samples can match millions of web-scraped ones" (Section 4.1, citing chen2025sharegpt).
- **[science]** Missing Evidence: This is a strong quantitative claim requiring a direct comparison experiment. The text does not provide the learning curves, the specific models compared, or the statistical significance of the performance difference.
- **[science]** Action: Include a table or figure showing the performance (e.g., FID, CLIP score, or task accuracy) of models trained on 91K synthetic data vs. 1M+ web data, with error bars or confidence intervals. 3. Bibliometric Sampling Bias (Figure 1) Figure 1 claims an "exponential acceleration" in research based on "411 post-2014 references."
- **[science]** Methodology Gap: The paper does not define the corpus from which these 411 papers were drawn. If this is a manual selection by the authors, it is subject to confirmation bias. If it is a scrape of arXiv, the search query and filtering criteria must be explicit.
- **[science]** Action: Define the data source and inclusion criteria for the bibliometric analysis. If the sample is not representative of the entire field, the claim of "exponential acceleration" is not scientifically generalizable. 4. Benchmark Reporting Standards (Section 4.2) The paper cites specific scores from benchmarks (e.g., GenEval 0.61, GenExam 72.7%).
- **[science]** Reproducibility: It is unclear if these scores represent single runs or averages over multiple seeds. In generative modeling, single-run results are highly volatile.
- **[science]** Action: Explicitly state the sample size (N) and number of seeds for every benchmark score reported. If the data comes from external papers, cite the specific experimental setup used in those papers to ensure the comparison is apples-to-apples. In summary, while the taxonomy is conceptually sound, the paper currently functions more as a position paper than an evidence-based survey. To meet scientific standards, the empirical claims regarding model failures and data efficiency must be backed by r

## paper_reviewer_statistical_analysis — verdict: full_revision

- **[science]** The manuscript relies heavily on bibliometric analysis and qualitative case studies to support its claims about the evolution of visual generation. From a statistical analysis perspective, the evidence provided is insufficient to support the broad conclusions drawn. First, the bibliometric analysis in Figure 1 and the accompanying text claims that 2025 contributed 45.7% of the 411 references analyzed. This calculation appears to treat arXiv preprints and future-dated citations (e.g., 2026) as eq

## paper_reviewer_text_formatting — verdict: full_revision

- **[science]** The manuscript exhibits significant text formatting issues that prevent successful compilation and professional presentation. First, table integrity is compromised. In e001, Table \Cref{tab:unified_methods} and in e001, Table \Cref{tab:industrial_training_recipes} contain explicit placeholder text: ... (N rows omitted) .... These are not valid LaTeX table content and will break the table structure or result in unprofessional output. The authors must either populate these tables with the full dat

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 2.1 (Level 1), the phrase 'L1 (prompt only) → L2 (single condition)' uses a raw arrow symbol that may not render correctly in all PDF viewers. Replace with 'to' or ensure the math mode is consistent (e.g., $\to$).
- **[writing]** In Section 3.1, the sentence 'HunyuanImage 3.0 filters >10B images to $$100M)' contains a LaTeX typo with double dollar signs and missing closing parenthesis. It should likely read 'to ~100M' or 'to 100M'.
- **[writing]** In Section 3.2, the equation for Group-Relative Preference Optimization uses \vx and \vc. Ensure these commands are defined in the preamble (e.g., \newcommand{\vx}{\mathbf{x}}) or replace with standard math notation to avoid compilation errors.
- **[writing]** In Section 5.1, the phrase 'monologue not constraining pixels is worse than none' is slightly ambiguous. Consider rephrasing to 'a monologue that does not constrain pixels is worse than having no monologue at all' for clarity.
- **[writing]** Throughout the paper, several citations (e.g., 'Nano Banana', 'GPT-Image') refer to proprietary or unreleased systems. Ensure these are either cited as technical reports if available or clearly marked as 'private communication' or 'unreleased' to maintain academic rigor.
