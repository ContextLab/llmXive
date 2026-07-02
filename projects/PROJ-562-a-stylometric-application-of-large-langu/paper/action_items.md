# Automated-review action items — A Stylometric Application of Large Language Models

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The claim that the 15th Oz book attribution is 'now the accepted attribution' (Abstract) is slightly overstated. While Binongo (2003) supports Thompson, the paper should acknowledge this was a contested question resolved by prior work, rather than implying it was universally settled before this study.
- **[writing]** Citation [Mikr25] is used to support that LLMs can 'write like' an author. However, the cited abstract states GPT-4o 'struggles to fully replicate' style and shows 'significant overlap' with generic outputs. The claim implies higher fidelity than the source supports; temper to reflect capture of statistical patterns, not full style embodiment.
- **[writing]** The claim of 'perfect (100%) classification accuracy' (Results) is specific to the 8-author closed-set experiment. The phrasing suggests a generalizable property. Clarify that this accuracy applies only to the described experimental setup, not as a universal guarantee for all attribution tasks.

## paper_reviewer_figure_critic — verdict: minor_revision

- **[writing]** The figures in this manuscript are central to the argument, and the LaTeX source indicates a well-structured plan for visualizing cross-entropy losses, t-statistics, and multidimensional scaling results. However, several issues regarding caption referencing and potential legibility require attention before publication. First, the cross-referencing in the captions of Figures 1, 3, and 5 relies on custom macros (e.g., \\crossentropyContent, \\confusion, \\mds) that are defined as simple integers i

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on terminology specific to machine learning and computational linguistics, which may alienate the intended audience of literary scholars and digital humanists. While the concepts are sound, the presentation frequently assumes a background in deep learning that is not universal among the paper's potential readers. Specific instances of jargon overuse include the introduction of "predictive comparison" (Section 1, line 14) and "stylometric distance" (Section 2.3, line

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The logical flow of the paper is generally sound, with the central premise—that an LLM trained on an author's work will predict that author's text better than others—supported by the reported data. The causal link between training on specific stylistic patterns and the resulting cross-entropy loss is well-motivated by information theory. However, there are minor logical gaps in the interpretation of the ablation studies and the definition of the proposed distance metric. First, the claim of "per

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The paper makes several claims that extend beyond the empirical evidence provided by the specific experimental constraints. First, the assertion of "perfect (100%) classification accuracy" (Section 3.1, Results) is presented as a robust finding, yet it is derived from a closed-set experiment involving only eight authors. The authors extrapolate this result to suggest the method is a viable "literary attribution tool" for general use (Introduction). This is an overreach; the high accuracy likely

## paper_reviewer_safety_ethics — verdict: accept

The manuscript presents a stylometric analysis using Large Language Models (LLMs) trained on public domain texts from Project Gutenberg. From a safety and ethics perspective, the study demonstrates strong adherence to responsible research practices.

**Data Privacy and Consent:**
The dataset consists entirely of works by authors who are deceased and whose writings are in the public domain (e.g., Jane Austen, L. Frank Baum, Mark Twain). As noted in Section 2.1 (lines 134-138), the authors explicitly selected these texts to eliminate confounds and ensure legal/ethical clarity. No personal data, private communications, or sensitive information regarding living individuals were used. Consequently, no Institutional Review Board (IRB) or Informed Consent procedures were required, and the authors correctly omit such declarations.

**Dual-Use and Potential for Harm:**
The primary application discussed is authorship attribution, specifically confirming the historical attribution of the 15th *Oz* book. While stylometric techniques can theoretically be misused for deanonymizing authors in adversarial contexts (e.g., identifying whistleblowers or bypassing privacy protections), the paper's scope is strictly limited to historical literary analysis of public domain works. The authors acknowledge the "black box" nature of the models and the potential for adversarial attacks in the Discussion (Section 5.3, lines 530-545), but they do not provide instructions, code, or methodologies for deploying these models against private or protected datasets. The code is hosted on a public GitHub repository, but the training data is restricted to the public domain, mitigating the risk of the pipeline being used to process sensitive private data without modification.

**Bias and Fairness:**
The study uses a small, homogeneous set of eight authors, all writing in English during overlapping historical periods. While this limits generalizability, it does not introduce active harm or bias against protected groups in the context of this specific experiment. The authors do not claim their method is suitable for high-stakes decision-making (e.g., legal evidence or hiring) where bias could cause real-world harm.

**Conclusion:**
The research is ethically sound. The use of public domain data removes consent and privacy concerns. The potential for dual-use harm is low given the specific application to historical literature and the lack of deployment instructions for adversarial scenarios. No revisions are required regarding safety or ethics.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The ablation study results for the POS-only corpus are inconsistent. Table S3 (supplement.tex) shows non-significant t-tests for 5 of 8 authors (p > 0.05), yet the text claims 'models trained on part-of-speech-only corpora reliably learned author-specific patterns for just 3 of the 8 authors' without explicitly defining the reliability threshold or addressing the high false-negative rate in the statistical tests.
- **[science]** The training stopping criterion (cross-entropy loss <= 3.0) is determined by manual inspection of generated samples (Methods, line 138). This introduces potential bias and lacks a rigorous, quantitative justification. The authors should provide a sensitivity analysis showing how varying this threshold impacts the final stylometric distance metrics and attribution accuracy.
- **[science]** The statistical power of the t-tests is unclear. With only 10 random seeds (n=10) per condition, the degrees of freedom are low (df ~9-18). The authors should report effect sizes (e.g., Cohen's d) alongside p-values to demonstrate that the observed differences are not just statistically significant but practically meaningful, especially for authors with borderline significance in ablation studies.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** Table 1 reports non-integer degrees of freedom (e.g., 31.53) for t-tests with n=10 seeds, implying Welch's t-test was used. The manuscript must explicitly state that Welch's correction was applied to justify these values and the assumption of unequal variances.
- **[science]** Ablation comparisons (e.g., intact vs. content-only) use the same 10 seeds, creating paired data. However, reported df values (e.g., 11.77) suggest independent Welch's t-tests were used. Re-analyze using paired t-tests or repeated-measures ANOVA to correctly model dependencies and increase power.
- **[writing]** The claim of '100% accuracy' is based on n=10 seeds. The 95% Clopper-Pearson confidence interval for this proportion is approx [0.74, 1.0]. Report this interval or qualify the claim to acknowledge the uncertainty inherent in the small sample size.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In the caption of Figure 2 (supplement.tex), the phrase 'the the t-statistic' contains a repeated article. Please correct to 'the t-statistic'.
- **[writing]** In the caption of Figure 5 (supplement.tex), the phrase 'the the t-statistic' appears again. Please correct to 'the t-statistic'.
- **[writing]** In the caption of Figure 6 (supplement.tex), the phrase 'the the t-statistic' appears again. Please correct to 'the t-statistic'.
- **[writing]** In the caption of Figure 3 (main.tex), the word 'Train'ing' uses an unnecessary italicized break. Please change to 'Training' for standard formatting.
- **[writing]** In Section 2.2 (main.tex), the sentence 'We decided on this threshold after taking random draws...' is slightly informal. Consider revising to 'This threshold was determined after...' for a more formal academic tone.
