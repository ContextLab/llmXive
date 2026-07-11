# Automated-review action items — Ideas Have Genomes: Benchmarking Scientific Lineage Reasoning and Lineage-Grounded Idea Generation

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The paper presents a novel benchmark for scientific lineage reasoning, but several factual claims regarding the evaluated systems and data composition require verification or clarification to ensure accuracy. The most critical issue concerns the evaluation baselines. The text and Table 1 repeatedly cite "GPT-5.5" and "Claude Opus 4.7" as the primary models tested. As of the current date, neither of these models has been released by OpenAI or Anthropic. The reported performance metrics (e.g., 27.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The x-axis labels (e.g., 'CS', 'Neuro') are abbreviations that are not defined in the caption or on the axis itself, making the specific domains ambiguous to the reader.
- **[writing]** Figure 1: The y-axis labels use inconsistent formatting; some entries are prefixed with '+' (e.g., '+ Claude Code') while others are not, and the color coding for these prefixes is not explained in the caption.
- **[writing]** Figure 2: The caption 'PES rubric decomposition (H / V / S)' does not define the abbreviations H, V, and S; the x-axis labels ('Heredity', 'Variation', 'Selection') should be explicitly linked to these abbreviations in the caption for clarity.
- **[writing]** Figure 2: The y-axis labels use inconsistent color coding (blue, orange, green) without a legend or caption explanation to define what these colors signify (e.g., model families or categories).
- **[science]** Figure 3: The legend defines 'Niche Competition' (dark grey), but this color is not visible in the 'Question' bar despite the bar reaching 100%. The visible segments (Mutation, Adaptive Radiation, Hybridization, Speciation) sum to ~98%, leaving a gap that is not accounted for by the 'Other' (light grey) category or the missing 'Niche Competition' segment.
- **[writing]** Figure 3: The legend entry for 'Other' (light grey) does not appear to correspond to any visible segment in the 'Question' bar, creating ambiguity about whether the missing ~2% is 'Other' or 'Niche Competition'.
- **[science]** Figure 4: The x-axis labels are rotated 45 degrees and overlap significantly (e.g., 'G5.5 + Codex' vs 'G5.5 + Claude'), making the system names difficult to read and distinguish.
- **[science]** Figure 4: The caption claims systems are 'sorted by aggregate Lineage PES', but the visual ordering of the bars does not appear to follow a strict descending or ascending order of the average height of the three bars (e.g., 'G5.5 + Codex' is first, but 'G5.5 + Claude' has a higher average).
- **[writing]** Figure 4: The y-axis label 'Subscore' is generic; the caption defines the metrics as Heredity, Variation, and Selection, but the axis does not specify the unit or scale range (e.g., 0-100).
- **[science]** Figure 5: The heatmap contains 14 rows of data, but the caption states 'all evaluated systems' without listing them; the row labels (e.g., 'GPT-5.5 + Claude Code') are not defined in the caption or cross-referenced captions, making it impossible to verify if the systems match the paper's scope.
- **[writing]** Figure 5: The colorbar legend is present but lacks a title or unit label (e.g., 'Exact accuracy (%)'), which is only implied by the y-axis label of the adjacent bar chart; this should be explicitly stated for clarity.
- **[science]** Figure 5: The bar chart on the right shows 'Axis mean' values (e.g., T1=28.5) that do not match the average of the corresponding column in the heatmap (e.g., T1 column average ≈ 28.1), suggesting a calculation or labeling inconsistency.
- **[science]** Figure 6: The legend at the top lists specific error types (e.g., 'verify', 'swapped_gene_role') that are not mapped to the E1-E9 error classes shown on the right axis, making it impossible to trace specific error mechanisms as the caption implies.
- **[writing]** Figure 6: The legend at the top is rendered in a font size that is illegible and overlaps with the Sankey flows, rendering the specific error type labels unreadable.
- **[writing]** Figure 9: The caption 'PES across information settings' is too generic and fails to describe the specific comparison (Question vs. Library vs. Lineage) or the metric (PES gain) shown in the plot.
- **[science]** Figure 9: The y-axis labels are color-coded (blue, green, orange) to match the legend, but the text colors for 'G5.5 + Codex' and 'G5.5 + Claude' are orange, while the corresponding data points are green and orange respectively, creating potential confusion between model names and information settings.
- **[writing]** Figure 9: The x-axis label 'PES (0-100)' is present, but the plot displays delta values (e.g., +4.4, +9.9) next to the points, which are not explicitly defined in the axis label or caption as 'PES Gain' or 'Delta PES'.
- **[writing]** Figure 10: The caption 'Five capability dimensions' is too vague; it should explicitly list the five dimensions (e.g., Inheritance Tracing, Evolutionary Reasoning, etc.) shown on the radar chart axes.
- **[writing]** Figure 10: The radial axis label 'best' is ambiguous without a corresponding 'worst' or '0' label at the center, making the scale direction implicit rather than explicit.

## paper_reviewer_jargon_police — verdict: accept

The manuscript demonstrates excellent self-containment for a competent reader from an adjacent field (e.g., a researcher in NLP, AI safety, or computational social science). The authors successfully avoid the common pitfall of assuming familiarity with their specific subfield's private vocabulary.

Key strengths in accessibility include:
1.  **Operational Definitions:** The core concepts—`Idea Genome` (genome), `GenomeDiff` (genomediff), and the six `Evolutionary Dynamics`—are rigorously defined upon first introduction in Section 2 (Framework) and Section 3 (Benchmark). The paper explicitly states that these are "operational categories" rather than requiring a broad biological ontology, which immediately grounds the reader.
2.  **Acronym Management:** All custom acronyms (IG-Bench, IG-Exam, IG-Arena, PES) are expanded at their first occurrence in the Abstract or Introduction. Standard field terms (LLM, RL, Transformer, ELO) are used correctly without needing definition, as they are foundational to the target audience.
3.  **Notation Clarity:** Mathematical notation (e.g., Equation 1 for the genome object, Equation 2 for PES) is accompanied by clear prose explanations of every variable ($t_i, z_i, e_i, c_i, H, V, S$). There are no overloaded symbols or undefined operators.
4.  **Contextualization:** When referencing specific benchmarks or methods (e.g., SWE-bench, GAIA, Chatbot Arena), the authors provide brief, one-sentence glosses explaining their relevance or nature, ensuring a reader outside the immediate LLM-evaluation niche can follow the comparison.

The paper avoids "in-group shorthand" and buzzwords by consistently linking abstract terms (like "lineage competence") to concrete, measurable tasks (T1-T4). A reader from a neighboring discipline could follow the logic of the benchmark construction and the interpretation of the results without needing to consult external literature to decode the terminology. No undefined terms or opaque symbols were found.

## paper_reviewer_logical_consistency — verdict: accept

The paper's argument structure is logically sound and internally consistent. The definitions of the core concepts—specifically the `Idea Genome` (Section 2.2), `GenomeDiff` (Section 2.4), and the six `Evolutionary Dynamics` (Section 2.5)—are established clearly and applied consistently throughout the benchmark construction (Section 3) and experimental evaluation (Section 4).

The logical flow from the problem statement (paper-centric retrieval is insufficient for lineage reasoning) to the proposed solution (genome-centric representation) to the empirical validation is coherent. The distinction between the two evaluation modes, `IG-Exam` (closed-form reasoning) and `IG-Arena` (open-ended generation), is maintained without contradiction. The metrics defined (Exact Accuracy for Exam, PES for Arena) align perfectly with the stated goals of each section.

Specifically, the causal claims regarding the "plausibility-coherence gap" (Finding 4) are supported by the decomposition of the PES metric into Heredity, Variation, and Selection, as presented in the results. The paper correctly attributes the performance gap to Heredity scores rather than Variation, which is a valid inference from the provided data breakdown. The limitations section appropriately qualifies the scope of the evolutionary dynamics without contradicting the main results. No non-sequiturs, circular arguments, or numerical inconsistencies were found.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** Abstract: 'Experiments on 14 LLM-based scientists' implies broad diversity, but Section 5.1 shows 12/14 are GPT-5.5 variants. Narrow to '14 configurations primarily based on GPT-5.5' or explicitly note the lack of open-weight model testing.
- **[writing]** Abstract/Conclusion: 'Reshuffles rankings rather than helping' implies ineffectiveness, yet Section 5.3 notes a median gain of +4.4. Rephrase to 'reshuffles rankings despite providing an average gain' to accurately reflect the data.
- **[writing]** Conclusion: 'Need compositional verification modules' prescribes a causal solution from a correlational finding (Fig 5.4b). Change to 'suggest that compositional verification modules may be a necessary component' to align with the evidence.

## paper_reviewer_safety_ethics — verdict: accept

This paper presents a benchmark for evaluating scientific lineage reasoning and idea generation. The work is low-risk by construction. The dataset consists of "golden lineage traces" and "curated genome objects" derived from published scientific literature (e.g., YOLO, BERT, DETR) and frontier questions. The data construction process explicitly mentions "anonymization leakage" checks in Section 4.1, and the examples provided in the Appendix (e.g., Appendix A.2) use anonymized or generic descriptions of scientific concepts rather than raw, sensitive personal data.

The "human subjects" component involves 50 graduate annotators validating the benchmark construction and difficulty. The paper states in the Appendix ("Human Agreement") that these annotators were recruited to validate labels and solve items. While the paper does not explicitly cite an IRB approval number or exemption statement, the nature of the task (validating benchmark items and solving reasoning problems on public scientific papers) typically falls under exempt categories in many jurisdictions, or involves minimal risk where formal IRB review is not strictly mandated by all venues, though it is best practice. However, given the context of benchmark construction using public data and expert annotators performing standard validation tasks, the absence of a specific IRB citation is not a fatal safety failure, nor does it indicate a foreseeable, non-trivial risk of harm that is unmitigated. The risk of re-identification or privacy violation is negligible as the data is derived from public publications and the annotators are consenting experts.

There are no dual-use capabilities described that lower the barrier to harm (e.g., automated vulnerability discovery, biological synthesis). The "idea generation" capability is evaluated on scientific reasoning, not on generating harmful content, disinformation, or deceptive personas. The paper does not release any PII, nor does it scrape data in violation of terms of service (it uses existing public papers and curated traces).

Consequently, there are no specific, nameable gaps in disclosure or mitigation that require action. The paper is safe to publish as is.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[writing]** The paper presents a novel benchmark for scientific lineage reasoning, but the evidentiary strength of the experimental results is currently insufficient to support the specific claims of system differentiation and ranking stability. The primary concern is the complete absence of variance reporting in the main results. Table 1 presents exact accuracy scores for 14 different systems on the \geneexam{} benchmark (1,029 instances) as single point estimates (e.g., 27.3% for Claude Code vs 23.1% for

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** Table 1 and Section 5.2 report exact accuracy to one decimal place (e.g., 27.3%) for 1,029 instances. This implies a precision of ~0.1%, but the standard error for a proportion p=0.273 with n=1029 is ~1.4%. Report accuracy as an integer or with a confidence interval (e.g., 27.3% ± 1.4%) to avoid false precision.
- **[writing]** Section 5.3 claims PES gains are 'Heredity-driven' and cites specific values (e.g., Heredity 61.9 vs 84.2) derived from a 3-judge panel. No uncertainty metric (SD, SE, or CI) is reported for these mean scores. Given the small number of judges (n=3) and the potential for inter-judge variance, report the standard deviation or 95% CI for the PES and its components to support the magnitude of the claimed gaps.
- **[writing]** Section 5.3 reports a Spearman correlation (ρ = 0.82) between ELO and PES rankings without a p-value or confidence interval. With only 14 systems, this correlation is subject to high sampling variance. Report the 95% CI for the correlation coefficient or the p-value to confirm the statistical significance of the divergence claim.

## paper_reviewer_writing_quality — verdict: accept

The manuscript demonstrates a high standard of writing quality, allowing the reader to move through the complex theoretical framework and experimental results with minimal friction. The prose is precise, the sentence structures are generally clean, and the logical flow between sections is well-maintained.

The abstract effectively summarizes the benchmark's construction, the two evaluation modes (IG-Exam and IG-Arena), and the headline empirical findings without burying the main points. The introduction successfully establishes the "scientific lineage competence" gap and introduces the *Idea Genome* framework with clear, statable definitions.

Paragraphs are consistently well-structured, each focusing on a single point. For instance, the "Data Construction and Quality Assurance" section in Section 4 uses a numbered list to break down the four stages of construction, followed by a distinct paragraph for quality assurance metrics, preventing the common issue of mixing methodology with validation results in a single block. Transitions between the framework definition (Section 3) and the benchmark instantiation (Section 4) are smooth, with the text explicitly linking the abstract concepts to the concrete dataset.

Terminology is used consistently throughout; terms like "genome," "genomediff," and the specific task axes (T1–T4) are defined early and maintained without confusing synonym switching. The tense usage is appropriate, shifting logically between the present tense for describing the framework and the past tense for reporting experimental results.

While the text is dense with technical concepts, the authors avoid unnecessary wordiness. Sentences are generally direct, and complex ideas (such as the Population-Evolution Score decomposition) are broken down into clear, itemized components. There are no instances of garden-path sentences or ambiguous pronoun references that would force a re-read. The paper is a model of clear technical communication.
