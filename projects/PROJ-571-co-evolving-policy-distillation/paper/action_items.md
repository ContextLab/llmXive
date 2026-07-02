# Automated-review action items — Co-Evolving Policy Distillation

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer — verdict: major_revision_writing

- **[writing]** The LaTeX source fails to compile because the custom class 'jingdong' is missing from the repository. The review cannot proceed until the paper is compiled into a valid PDF or the missing class file is provided.
- **[writing]** The command '\beginappendix' is used in paper.tex and appendix.tex, but the 'appendix' package is loaded with options [toc,page,header] which typically requires '\begin{appendix}' or a specific environment. The code likely fails to compile due to this syntax mismatch.
- **[writing]** The bibliography file 'cite.bib' is truncated in the provided input (ends abruptly at 'eprint={2311.16502},'). The full bibliography must be provided to verify citation completeness and formatting.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Section 3.3 claims a 'linear fit' with R^2=0.79. This implies 21% unexplained variance, making the strict linearity claim overstated. Qualify the claim or provide residual analysis to support the linear model assertion.
- **[science]** Section 4.1 claims CoPD 'surpasses' experts. Verify that Text/Image-Expert baselines used identical data filters and hyperparameters as CoPD branches. Without this, the comparison is invalid.
- **[science]** Section 3.2 defines overlap using student's visitation distribution. Section 3.3 does not specify which policy generated trajectories for the pilot study. Clarify to ensure metric validity.
- **[writing]** Section 5 cites 'li2026rethinkingonpolicydistillationlarge' for inspiration, but this entry is missing from cite.bib. Add the reference to verify the claim.

## paper_reviewer_code_quality_paper — verdict: minor_revision

- **[writing]** The manuscript relies on external LaTeX files (e.g., `common.tex`, `abstract.tex`, `intro.tex`, `tables/*.tex`) that are not provided in the input. This prevents verification of code quality, reproducibility, and dependency hygiene. The authors must provide a self-contained repository or a single compiled artifact to allow for a full code quality review.
- **[writing]** The bibliography file `cite.bib` is truncated in the provided input (ends abruptly at `yue2024mmmumassivemultidisciplinemultimodal`). This breaks the build process and prevents verification of citation correctness. The full `.bib` file must be provided.
- **[writing]** The paper references specific figures (`figs/copd-motivation.pdf`, etc.) and tables (`tables/main_results.tex`) as external files. For reproducibility, the source code for generating these figures (e.g., Python scripts, Jupyter notebooks) and the raw data used for the tables must be included in the artifact.

## paper_reviewer_data_quality_paper — verdict: full_revision

- **[science]** The review focuses strictly on data quality, provenance, and reproducibility. The manuscript fails to provide sufficient detail regarding the specific datasets used for training and evaluation, rendering the results unverifiable. First, the training data provenance is opaque. In eval.tex (lines 12-14), the authors state they use "Polaris-Dataset-53K," filtered from "DeepScaleR-Preview-Dataset" and "AReal-boba-Data." While the bibliography cites the sources for DeepScaleR (a Notion blog) and ARea

## paper_reviewer_figure_critic — verdict: minor_revision

- **[writing]** Figure 1 (teaser) and Figure 2 (method) lack explicit axis labels or quantitative scales where implied. The caption for Fig 1 claims 'best overall performance' but the visual does not show the data points or error bars supporting this claim, relying entirely on the reader to trust the text. Add a small inset chart or explicit data markers to the teaser to substantiate the 'best performance' claim visually.
- **[writing]** Figure 3 (pilot study) and Figure 4 (analysis) contain multiple subplots (a, b, c) with dense data. The current scale (0.34 and 0.36) may render the text labels for axes and legends illegible in print. Ensure all axis labels, tick marks, and legend text are at least 8pt in the final PDF. Specifically, the 'Symmetric KL' axis in Fig 4(b) and the 'Top-k overlap' axis in Fig 4(a) need clear units and grid lines to verify the 'order of magnitude' claim.
- **[writing]** The color palette in Table 1 (main_results) and Table 2 (main_tri_results) uses blue highlighting for averages. While not a figure, these are often rendered as figures in supplementary materials. Ensure the color contrast meets WCAG AA standards for print accessibility. The red/green color scheme in the ablation table (Table 3) for 'w/o I-OPD' vs 'w/o T-OPD' might be indistinguishable for colorblind readers; consider adding distinct patterns or symbols.

## paper_reviewer_jargon_police — verdict: full_revision

- **[science]** The manuscript relies heavily on unexplained acronyms and domain-specific jargon that significantly hinders accessibility for non-specialist readers. The most critical issue is the immediate introduction of 'RLVR' and 'OPD' in the Abstract without defining them. While these are standard in the specific sub-field of LLM post-training, a general paper should define them upon first use (e.g., "Reinforcement Learning with Verifiable Rewards (RLVR)"). Similarly, 'MOPD' (Multi-teacher OPD) and 'GRPO'

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The paper presents a coherent narrative regarding the limitations of static distillation and mixed RLVR, proposing CoPD as a solution. However, there are specific logical inconsistencies between the textual description of the method and its algorithmic formulation, as well as gaps in the theoretical justification for the proposed utility improvements. First, there is a direct contradiction between the description of the training dynamics and the provided algorithm. In Section 3.2, the authors st

## paper_reviewer_overreach — verdict: full_revision

- **[science]** The paper makes several strong claims that may overreach the evidence provided. First, the assertion that CoPD "significantly outperforms" baselines and "surpasses domain-specific experts" (Abstract, Conclusion) is not fully substantiated. While Table 1 and Table 2 show CoPD achieving higher *average* scores than the individual experts, the term "significantly" implies statistical significance, which is not demonstrated. The margins in some benchmarks are small (e.g., Video-Holmes: 43.77 vs 43.3

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper presents a novel method for co-evolving policy distillation but lacks sufficient detail regarding data ethics and potential dual-use risks. Data Privacy and Consent: In Section 4.1 ("Experimental Setting"), the authors describe collecting video reasoning data from sources like OneThinker and VideoChat-R1, filtering them with Qwen3-8B-VL. The manuscript does not specify whether these datasets contain human-generated content that requires informed consent or IRB approval. Video data, in

## paper_reviewer_scientific_evidence — verdict: full_revision

- **[science]** The pilot study in Section 3.3 (Fig 4) claims a strong linear correlation (r=0.89) between top-k overlap and OPD gain. However, the sample size (number of student checkpoints) is not specified, and the statistical significance (p-value) or confidence intervals are missing. Without this, the claim that overlap is a reliable predictor of distillation efficiency is not statistically robust.
- **[science]** The main results (Tables 1 & 2) show CoPD outperforming domain-specific experts (e.g., Text-Expert 57.89 vs CoPD 58.76). The paper attributes this to "mutual gains" but provides no statistical significance testing (e.g., t-tests across seeds) to rule out random variance, especially given the small margins on some benchmarks.
- **[science]** The implementation details (Section 4.1) state a fixed learning rate and batch size but do not report the number of random seeds used for the main experiments. RLVR training is notoriously stochastic; without multiple seeds and error bars (std dev) in the tables, the robustness of the reported SOTA results cannot be verified.
- **[science]** The ablation study (Table 3) removes the merge operation but does not isolate the effect of the "alternating" schedule versus simply running two independent models and averaging them. A baseline comparing CoPD to a simple ensemble of two independently trained experts is needed to prove the "co-evolution" mechanism itself is the driver of performance, not just the presence of multiple branches.

## paper_reviewer_statistical_analysis — verdict: full_revision

- **[science]** Statistical significance is absent. Table 1 and Table 2 report point estimates (e.g., 56.97 vs 56.44) without standard deviations, confidence intervals, or p-values. Given the small number of benchmarks per category (e.g., 7 image benchmarks), random variance could explain the marginal gains. Re-run experiments with multiple seeds (n>=3) and report mean ± std or conduct paired t-tests/Wilcoxon signed-rank tests to validate claims of superiority.
- **[science]** The pilot study in Section 3.3 (Fig 2) claims a strong linear correlation (r=0.89, R^2=0.79) between top-k overlap and OPD gain. However, the text does not specify the sample size (number of student checkpoints) used to generate this regression, nor does it provide a p-value for the correlation coefficient. Without n and p, the statistical validity of this 'motivating' finding is unverifiable.
- **[science]** The ablation study (Table 3) compares 'w/o I-OPD' and 'w/o T-OPD' against the full model. The reported differences (e.g., 58.76 vs 57.41) are presented as definitive. However, without error bars or variance estimates from repeated runs, it is impossible to determine if these drops are statistically significant or within the noise floor of the training process.
- **[science]** The implementation details (Section 4.1) state a fixed learning rate and batch size but omit the number of random seeds used for the main experiments. Reproducibility of statistical results in RLVR is highly sensitive to initialization and sampling. The paper must explicitly state the number of seeds and the variance across them to support the 'consistent' performance claims.

## paper_reviewer_text_formatting — verdict: minor_revision

- **[writing]** The manuscript exhibits several text formatting issues that require attention before final compilation and submission. First, in paper.tex, the command \authorbreak is invoked between author entries but is not defined in the preamble or the included common.tex file. This will result in a LaTeX error during compilation. The authors should either define this command (e.g., \newcommand{\authorbreak}{\\}) or remove it if it was intended as a placeholder. Second, the todonotes package is loaded with

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In `eval.tex`, Section 'Implementation Details', the word 'specifc' is misspelled twice ('specifc experts', 'specifc experts'). Correct to 'specific'.
- **[writing]** In `method.tex`, Section 'Mutual OPD', the sentence 'where $eta_k$ balancing the relative contribution...' contains a grammatical error. It should read 'where $eta_k$ balances...' or 'where $eta_k$ is used to balance...'.
- **[writing]** In `intro.tex`, the first paragraph contains a sentence fragment: 'By separating capability-specific training from cross-capability consolidation, OPD avoids the gradient conflicts caused by capability divergence % . Combined with its dense token-level supervision on the student's own trajectories, this design'. The comment and the following sentence break the flow. Integrate the thought about 'dense token-level supervision' into the main sentence or remove the fragment.
- **[writing]** In `motivation-new.tex`, Section 'Pilot Study', the phrase 'Experiment 1: $ta$ rises with teacher--student overlap' uses an en-dash in the text but the surrounding context suggests a hyphen or consistent formatting. Ensure consistent use of dashes for compound adjectives (e.g., 'teacher-student' vs 'teacher--student') throughout the manuscript.
