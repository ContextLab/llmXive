# Automated-review action items — Achieving Gold-Medal-Level Olympiad Reasoning via Simple and Unified Scaling

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: full_revision

- **[science]** The paper makes several critical factual claims that are currently unsupported or factually impossible given the current timeline and public knowledge. First, the Abstract and Section 4.1 repeatedly claim the model achieved gold-medal-level performance on "IMO 2025" and "USAMO 2026". The International Mathematical Olympiad (IMO) and USAMO for the years 2025 and 2026 have not yet taken place. It is impossible for a model to have solved the actual competition problems for these years. The authors

## paper_reviewer_claim_accuracy — verdict: full_revision

- **[fatal]** The claim of achieving gold-medal performance on "IMO 2025" and "USAMO 2026" (Abstract, Section 4.1, Table 3) remains factually impossible as these competitions have not yet occurred. The authors must replace these with actual past competitions (e.g., IMO 2024, USAMO 2025) or clearly label the data as synthetic/prognostic, as the current phrasing asserts a factual impossibility.

## paper_reviewer_code_quality_paper — verdict: full_revision

- **[fatal]** The manuscript relies on external LaTeX inputs (e.g., \input{section/report_introduction}) and figure files (e.g., figure/proofbench_overall_simple.pdf) that are not provided in the submission. Reproducibility from scratch is impossible without these artifacts. The submission must include the full directory tree or a single-file compilation script.
- **[fatal]** The paper claims to release code and models (GitHub/HuggingFace links), but the submission contains no training scripts, data processing pipelines, or evaluation harnesses. Without the actual code artifacts, the 'simple and unified recipe' cannot be verified or reproduced.
- **[fatal]** The LaTeX source includes hardcoded paths and external dependencies (e.g., \input{appendix_solutions/imo2025_p1.tex}) without providing the content of these files in the submission. This breaks the compilation chain and prevents independent verification of the claimed solutions.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The legend defines three series (ProofBench-Basic, ProofBench-Advanced, AnswerBench), but the plot displays four distinct data lines. The light blue line with triangle markers is not defined in the legend, making it impossible to identify which metric it represents.
- **[writing]** Figure 1: The x-axis label 'Coarse RL' is positioned under the 'SFT + SU-01' tick marks, creating ambiguity about which training stage corresponds to the 'Coarse RL' phase.
- **[fatal]** Figure 2: The caption is 'Figure 2: 1', which is non-descriptive and fails to explain the plot's content, axes, or data series.
- **[science]** Figure 2: The legend defines three series (ProofBench-Basic, ProofBench-Advanced, AnswerBench), but the plot displays four distinct lines (three blue, one green), leaving one data series unidentified.
- **[science]** Figure 2: The x-axis labels are inconsistent; the first label 'P1-30B-A3B' differs in format from the subsequent labels (e.g., 'SFT', 'SU-01'), and the final label 'SU-01 w/ TTS' is split across two lines, reducing readability.
- **[science]** Figure 3: The legend defines 'ProofBench-Advanced' with a solid blue line and triangle markers, but the plot shows two distinct blue lines with triangles (one at ~33-91, one at ~6-50). The caption does not distinguish between these two series, making it impossible to identify which line corresponds to 'ProofBench-Advanced'.
- **[writing]** Figure 3: The x-axis label 'Coarse RL' is positioned under the 'SFT + Coarse RL' tick, but the tick label itself is split across two lines ('SFT +' and 'Coarse RL'), creating visual clutter and potential misalignment with the data points.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on domain-specific acronyms and internal shorthand that are not defined at their first occurrence, creating unnecessary friction for non-specialist readers. First, the term A3B appears in the Abstract ("30B-A3B backbone") and throughout the text without definition. It is unclear if this refers to a specific architecture type (e.g., "Adaptive 3-Bit" or a specific MoE configuration) or a dataset version. This term must be spelled out or clearly defined immediately upo

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** The paper claims a perfect 35/35 score on IMO 2025, yet the appendix shows IMO P6 scored 0/7. The conclusion that the model matches the max human score is logically inconsistent with the provided evidence of failure on specific problems.
- **[science]** The abstract claims gold-medal performance on USAMO 2026, but the appendix shows USAMO P2 scored 0/7 with a admitted gap. The paper must reconcile the reported total scores with the explicit 0/7 failures in the solution appendix.
- **[writing]** The paper asserts that reverse-perplexity ordering (high to low) prevents overwriting competence but offers no causal mechanism. The logic that starting with the most mismatched examples stabilizes the policy is asserted without derivation.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** The paper claims a perfect 35/35 score on IMO 2025, yet the appendix shows IMO P6 scored 0/7. The conclusion that the model matches the max human score is logically inconsistent with the provided evidence of failure on specific problems.
- **[science]** The abstract claims gold-medal performance on USAMO 2026, but the appendix shows USAMO P2 scored 0/7 with an admitted gap. The paper must reconcile the reported total scores with the explicit 0/7 failures in the solution appendix.
- **[writing]** The paper asserts that reverse-perplexity ordering (high to low) prevents overwriting competence but offers no causal mechanism. The logic that starting with the most mismatched examples stabilizes the policy is asserted without derivation.

## paper_reviewer_overreach — verdict: full_revision

- **[fatal]** The claim of solving 'IMO 2025' and 'USAMO 2026' is factually impossible as these events are in the future. The paper presents full solutions with '7/7' scores for these non-existent competitions, implying fabrication or hallucination. This invalidates the 'Gold-Medal' claim.
- **[science]** The 'Gold-Medal-Level' claim for IPhO 2024/2025 lacks comparison to official cutoff scores. The paper provides raw scores (e.g., 25.3) but does not prove these meet the specific gold-medal threshold or account for evaluation variance.
- **[writing]** The abstract claims 'stable reasoning' on 100K+ token trajectories, yet the model fails 1/6 IMO and 2/6 USAMO problems. The data supports long generation, not reliability. The term 'stable' is an unjustified extrapolation given the failure cases.

## paper_reviewer_overreach — verdict: reject

- **[fatal]** The claim of solving 'IMO 2025' and 'USAMO 2026' remains factually impossible as these events are in the future. The paper still presents full solutions and '7/7' scores for these non-existent competitions. This is a fatal overreach implying fabrication, invalidating the 'Gold-Medal' claim.
- **[science]** The 'Gold-Medal-Level' claim for IPhO 2024/2025 persists without comparison to official cutoff scores. Providing raw scores (e.g., 25.3) without proving they meet the specific gold-medal threshold or accounting for evaluation variance is an unjustified extrapolation.
- **[writing]** The abstract's claim of 'stable reasoning' on 100K+ token trajectories is unsupported. The data shows the model fails 1/6 IMO and 2/6 USAMO problems (Table 4). The term 'stable' is an over-extrapolation given these documented failure cases.

## paper_reviewer_safety_ethics — verdict: full_revision

- **[science]** The problems are synthetic or leaked, which would constitute a severe breach of competition integrity if leaked.
- **[science]** The claims are hallucinated or fabricated, representing a fundamental lack of scientific rigor.
- **[science]** The authors are using a simulation or a "future-dated" dataset that is not clearly distinguished from real competition data. This ambiguity creates a critical trust and safety issue. If the model is being evaluated on leaked or synthetic data presented as real future competitions, the results are misleading and potentially harmful to the academic community. The authors must explicitly clarify the source of these problems, the timeline of their creation, and the verification process. Without this
- **[science]** Automate cheating in mathematics competitions, university entrance exams, and advanced coursework.
- **[science]** Generate sophisticated, plausible-looking but potentially incorrect mathematical proofs (hallucinations) that could mislead researchers or students. The manuscript currently lacks a Safety and Ethics section. It does not discuss:
- **[science]** Mitigation strategies for preventing misuse (e.g., watermarking, usage restrictions).
- **[science]** The potential for the model to be fine-tuned for malicious purposes (e.g., generating disinformation with a veneer of mathematical authority).
- **[science]** The authors' stance on the release of weights for such a powerful reasoning engine. 3. Data Privacy and Copyright Section 3.1 ("SFT Data Curation") lists sources including "DeepMath problems," "Evan Chen's olympiad materials," and "AoPS." The paper does not address:
- **[science]** Whether these datasets were used with proper licensing or consent.
- **[science]** If any personally identifiable information (PII) from forum users (AoPS) was inadvertently included.
- **[science]** Compliance with copyright laws regarding the distribution of competition problems. Recommendation The paper requires a full revision before it can be considered for acceptance. The authors must:
- **[science]** Provide a transparent explanation of the "IMO 2025" and "USAMO 2026" data sources.
- **[science]** Add a comprehensive Safety and Ethics section addressing dual-use risks and academic integrity.
- **[science]** Include a data governance statement confirming the legality and ethical sourcing of all training data. Failure to address these points renders the paper's claims scientifically invalid and ethically problematic.

## paper_reviewer_safety_ethics — verdict: full_revision

- **[science]** The authors must explicitly clarify the source of "IMO 2025" and "USAMO 2026" problems. If these are future-dated or synthetic, presenting them as real competition data is a critical trust and safety issue. The manuscript currently lacks a clear distinction between real and simulated data, creating ambiguity that could mislead the academic community.
- **[science]** Add a comprehensive Safety and Ethics section addressing dual-use risks. The paper currently lacks discussion on: (1) Mitigation strategies for preventing misuse (e.g., automating cheating in exams); (2) The potential for generating plausible but incorrect proofs (hallucinations) that could mislead students; (3) The authors' stance on releasing weights for such a powerful reasoning engine.
- **[science]** Include a data governance statement confirming the legality and ethical sourcing of all training data. Section 3.1 lists sources like "AoPS" and "Evan Chen's materials" but does not address: (1) Whether these datasets were used with proper licensing or consent; (2) If any personally identifiable information (PII) from forum users was inadvertently included; (3) Compliance with copyright laws regarding competition problems.

## paper_reviewer_scientific_evidence — verdict: full_revision

- **[fatal]** The central claim of 'Gold-Medal-Level' performance on IMO 2025 and USAMO 2026 relies on the model solving problems from future competitions (2025/2026) which are not yet public. The paper provides no evidence that these problems were not leaked or that the evaluation was blind. Without independent verification of the problem set's secrecy and the evaluation protocol, the claim of gold-medal status is scientifically unsupportable.
- **[science]** The evaluation of non-verifiable proofs (ProofBench, IMO/USAMO) relies on LLM judges (Gemini-2.5-Pro, GPT-5-high) rather than human experts. The paper cites '3 gold-medal experts' for scoring but does not provide inter-rater reliability statistics, the specific rubric used, or the raw scores. Relying on LLM judges for complex mathematical proofs introduces significant bias and hallucination risks that are not quantified.
- **[science]** The reported performance jump from 21 to 35 points on IMO 2025 via 'Test-Time Scaling' (TTS) lacks statistical rigor. The paper does not report the number of independent runs, the variance in scores, or the computational cost (inference time) required to achieve the perfect score. A single successful run does not constitute robust evidence of gold-medal capability without a distribution of outcomes.
- **[science]** The SFT data curation section mentions filtering 'contaminated problems' but does not define the contamination detection method or provide a list of excluded problems. Given the use of future-dated problems (IMO 2025), there is a high risk of data leakage or overfitting to specific problem statements if the training data was not rigorously audited.

## paper_reviewer_scientific_evidence — verdict: reject

- **[fatal]** The central claim of 'Gold-Medal-Level' performance on IMO 2025 and USAMO 2026 remains scientifically unsupportable. The paper relies on solving problems from future competitions (2025/2026) which are not yet public. No evidence is provided regarding the secrecy of the problem sets, the blind nature of the evaluation, or independent verification that these problems were not leaked. Without this, the claim is fundamentally flawed.
- **[science]** The evaluation of non-verifiable proofs (IMO/USAMO) still relies on LLM judges (Gemini-2.5-Pro, GPT-5-high) and a small panel of '3 gold-medal experts' without providing inter-rater reliability statistics, the specific scoring rubric, or raw scores. The risk of bias and hallucination in LLM judges for complex proofs is not quantified, undermining the validity of the 35-point scores.
- **[science]** The reported performance jump to 35 points on IMO 2025 via Test-Time Scaling (TTS) lacks statistical rigor. The paper does not report the number of independent runs, the variance in scores, or the computational cost (inference time) required to achieve the perfect score. A single successful run (or a small, unreported sample) does not constitute robust evidence of gold-medal capability without a distribution of outcomes.
- **[science]** The SFT data curation section mentions filtering 'contaminated problems' but fails to define the contamination detection method or provide a list of excluded problems. Given the use of future-dated problems (IMO 2025), there is a high risk of data leakage or overfitting if the training data was not rigorously audited against the specific problem statements used in evaluation.

## paper_reviewer_statistical_analysis — verdict: full_revision

- **[science]** The paper reports specific scores (e.g., 91.0% on ProofBench-Basic, 35/35 on IMO 2025) without any measure of statistical uncertainty. For benchmarks with small sample sizes (e.g., 6 IMO problems), a single run is insufficient to claim 'Gold-Medal-Level' performance. Confidence intervals or standard deviations over multiple seeds/runs are required to validate these claims.
- **[science]** The comparison against baselines (e.g., Qwen3.6-35B-A3B, GPT-5.5) lacks statistical significance testing. Differences of <1% (e.g., 77.3% vs 77.4% in Table 1) are presented as definitive performance characteristics without p-values or effect sizes, making it impossible to distinguish signal from noise.
- **[science]** The 'Reverse-Perplexity Curriculum' ablation (Section 3.3) compares single-point metrics (39.5% vs 55.8%) without reporting variance or conducting paired statistical tests. The claim that this ordering is superior requires evidence that the improvement is not due to random data split variance.
- **[science]** The evaluation of 'Test-time Scaling' (TTS) relies on a single trajectory per problem in the main tables. The methodology does not specify the number of independent trials or the variance in success rates across different random seeds, which is critical for assessing the stability of the proposed scaling laws.

## paper_reviewer_statistical_analysis — verdict: full_revision

- **[science]** The claim of 'Gold-Medal-Level' performance on IMO 2025 (35/35) and USAMO 2026 (35/35) is based on single-point estimates without confidence intervals. For small sample sizes (6 problems), a single run is statistically insufficient to distinguish signal from noise. Variance over multiple seeds or runs is required.
- **[science]** Baseline comparisons (e.g., SU-01 77.3% vs Qwen3.6 77.4% in Table 1) lack statistical significance testing. Differences <1% are presented as definitive without p-values or effect sizes, making it impossible to determine if the improvement is real or noise.
- **[science]** The 'Reverse-Perplexity Curriculum' ablation (Section 3.3, Fig sft_ppl_curriculum) reports single-point metrics (39.5% vs 55.8%) without variance or paired statistical tests. The claim of superiority requires evidence that the improvement is not due to random data split variance.
- **[science]** Test-time Scaling (TTS) evaluation relies on single trajectories per problem in main tables. The methodology does not specify the number of independent trials or variance in success rates across seeds, which is critical for assessing the stability of the reported scaling laws.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The LaTeX source contains significant formatting errors in the bibliography and URL handling. Specifically, lines like `http://simplified-reasoning.github.io/SU-01}{{\text{Project` and `https://github.com/huggingface/Math-Verify}.}.` show broken macro expansions or missing closing braces. These must be fixed to ensure the PDF compiles correctly and links are functional.
- **[writing]** In the 'Analysis and Discussion' section, the text abruptly ends with 'IMO-style tasks demand' followed by a truncation marker. The manuscript is incomplete in the provided source. The authors must ensure the full text is present before submission.
- **[writing]** In the 'SFT Data Curation' section, footnotes are used for URLs (e.g., 'Evan Chen's olympiad materials: \url{...}'). While functional, standard academic practice often prefers these in the bibliography or as inline text to avoid cluttering the page layout. Ensure the footnote style is consistent throughout the document.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The LaTeX source contains significant formatting errors in the bibliography and URL handling. Specifically, lines like `http://simplified-reasoning.github.io/SU-01}{{\text{Project` and `https://github.com/huggingface/Math-Verify}.}.` show broken macro expansions or missing closing braces. These must be fixed to ensure the PDF compiles correctly and links are functional.
- **[writing]** In the 'Analysis and Discussion' section, the text abruptly ends with 'IMO-style tasks demand' followed by a truncation marker. The manuscript is incomplete in the provided source. The authors must ensure the full text is present before submission.
- **[writing]** In the 'SFT Data Curation' section, footnotes are used for URLs (e.g., 'Evan Chen's olympiad materials: \url{...}'). While functional, standard academic practice often prefers these in the bibliography or as inline text to avoid cluttering the page layout. Ensure the footnote style is consistent throughout the document.
