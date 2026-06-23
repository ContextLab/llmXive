---
field: linguistics
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/337
paper_authors:
  - Byung-Kwan Lee
  - Ximing Lu
  - Shizhe Diao
  - Minki Kang
  - Saurav Muralidharan
  - Karan Sapra
  - Andrew Tao
  - Pavlo Molchanov
  - Yejin Choi
  - Yu-Chiang Frank Wang
  - Ryo Hachiuma
---

# Zone of Proximal Policy Optimization: Teacher in Prompts, Not Gradients

A paper was submitted via the website for consideration / review.

Source URL: https://arxiv.org/abs/2606.18216
Paper authors (from arXiv): Byung-Kwan Lee, Ximing Lu, Shizhe Diao, Minki Kang, Saurav Muralidharan, Karan Sapra, Andrew Tao, Pavlo Molchanov, Yejin Choi, Yu-Chiang Frank Wang, Ryo Hachiuma

Submitted by: github-actions[bot]

(Intake from human-submission issue #337.)

## Rejection rationale (2026-06-23)

Paper-stage review found one or more `fatal`-severity action items. The underlying research question is returned to the backlog so a fresh approach can be considered:

- **[7f852ae62879]** Remove or replace citations to works that are dated 2025/2026 (e.g., \citep{Lee_2025_CVPR,NEURIPS2025_e5849736,Lee_2026_CVPR_Masters}) as they cannot provide supporting evidence for the claims made.
- **[25f556517e14]** Correct the statement in Appendix § 2 that ZPPO “exceeds the 27B teacher on several LLM benchmarks” – the presented tables show the teacher’s scores are substantially higher; re‑phrase to indicate that ZPPO narrows the gap on specific benchmarks.
- **[9b5b55fee2ba]** Add explicit citations for the claim that “RL avoids logit imitation but discards hard questions whose rollouts all fail (zero advantage)” or qualify it as an observation rather than a literature‑backed fact.
- **[c563c25e400d]** Supply a complete, version‑controlled code repository (e.g., GitHub) containing training scripts, data preprocessing pipelines, model definition modules, and a reproducible environment (Dockerfile or conda env) so that ZPPO can be re‑run from scratch.
- **[a0cd25a806aa]** Add an explicit Data Availability statement that describes where the ZPPO‑77K multimodal RL corpus can be accessed, includes a persistent identifier (e.g., DOI or Zenodo record), and specifies the license under which the data are released.
- **[1148890d6b4e]** Provide a Code Availability statement with a link to a public repository (e.g., GitHub) that contains the training scripts, model checkpoints, and evaluation code, and clearly state the software license (e.g., Apache‑2.0, MIT).
- **[a996779ceeb1]** Archive all external URLs referenced in the paper (project page, HuggingFace dataset links, figure PDFs) using a service such as archive.org or Zenodo, and include the archived URLs to mitigate future link rot.
- **[169006967587]** Document the version of each external resource used (e.g., specific commit hash of the HuggingFace dataset, version tag of the teacher model) to ensure reproducibility.
- **[466aacbb7865]** If the paper relies on any proprietary or non‑open datasets, explicitly state the licensing terms and any usage restrictions.
- **[3f98a1473613]** Add explicit axis labels (including units) to all line‑plot figures (e.g., Fig. 2, Fig. 3, Fig. 4, Fig. 5, and the appendix dynamics plots).
- **[7ee091c3312a]** Replace the current red‑green colour scheme in Fig. 2 and Fig. 4 with a colour‑blind‑safe palette or add distinct line styles/markers.
- **[3fb1c9f5edde]** Provide concise alt‑text descriptions for each figure in the PDF (e.g., via \caption[Alt‑text]{...}) to improve accessibility.
- **[27764b3bc667]** Ensure that the high‑resolution conceptual diagram (figure_high_concept.png) includes a legend explaining all symbols and arrows; currently some symbols are undocumented.
- **[66171abcabec]** In Fig. 5 (qualitative examples), increase the font size of the overlaid text (e.g., ‘Candidate A’, ‘Student’s BCQ rollout’) so it remains legible when printed at 80 % scale.
- **[74914efd6b6c]** For the teacher‑scale plot (figure_teacher_scale.pdf), add a grid or tick marks on both axes and label the x‑axis with ‘Teacher size (B parameters)’ and the y‑axis with ‘Δ accuracy (pp)’. This will make the trend easier to read.
- **[ba8639bf25c1]** Define every acronym on first use (e.g., ZPPO, BCQ, NCQ, GRPO, DAPO, REINFORCE++, FIFO) to avoid alienating readers unfamiliar with the specific RL or distillation literature.
- **[b7eb86c5be09]** Replace overly technical jargon such as “zone of proximal policy optimization”, “super‑additive”, “hard‑question threshold τ”, and “advantage normalization” with clearer, plain‑English alternatives or add brief explanatory footnotes.
- **[3f172c41c3b6]** Simplify dense metric reporting in tables (e.g., “Avg Δ (pp)”, “macro‑average results (percent)”) by providing a short legend and using full words instead of symbols.
- **[527b3cd5b426]** Avoid excessive use of domain‑specific shorthand in figure captions (e.g., “BCQ converts all‑wrong groups into mixed groups”) and instead describe the process in plain terms.
- **[8895b06a921c]** Introduce a concise glossary of specialized terms (e.g., “prompt replay buffer”, “candidate compression”, “graduation”) to aid non‑specialist readers.
- **[142a5c38d4bc]** When referencing prior work, replace citation‑heavy sentences with a brief narrative and only include the most relevant citation; for example, summarize the idea and cite a single representative paper rather than a long list.
- **[280f43b574ce]** Clarify the meaning of symbols like “ρ_replay”, “ρ_aug”, and “τ” in the main text rather than assuming familiarity; provide a short inline definition when they first appear.
- **[d80c593ce281]** Reduce the use of abbreviations in the abstract (e.g., replace “pp” with “percentage points”) to improve readability for a broader audience.
- **[d440b2e456cf]** Explain the term “on‑policy” in lay terms when first introduced, as many readers may not be versed in reinforcement‑learning terminology.
- **[4683c7971cfe]** Rephrase the phrase “teacher‑bounded zone” to something like “the method’s effectiveness is limited when the teacher also fails” to provide immediate context.
- **[162a5773b697]** The abstract states a +9.3 pp gain for the 0.8 B VLM benchmark, but Table 1 shows the actual improvement is +7.9 pp (33.1 % vs 25.2 %). Align the numeric claim with the reported results.
- **[5af0790ac2f5]** The manuscript claims ZPPO “resolves” the brittleness of distillation and the on‑policy drift problem. This is an over‑strong conclusion given the evidence is limited to a set of benchmarks and does not demonstrate broader generalization or theoretical guarantees. Re‑phrase to a more modest claim about empirical improvement.
- **[5a78bff1b1a5]** The paper reports that 9 B students “approach” the 27 B teacher within ≤1 pp on several benchmarks, yet the overall macro‑average gap remains >30 pp (teacher LLM Avg 71.8 % vs student 33.1 %). Provide a clearer statement of the specific benchmarks where the gap is ≤1 pp, and avoid implying near‑parity overall.
- **[ee3169281824]** Statistical significance is presented for some ablations (bootstrap CIs) but not for the primary claim that ZPPO outperforms all baselines across every benchmark block. Add significance testing (e.g., paired bootstrap) for the main comparison to substantiate the universal positive Δ claim.
- **[ab18ed94b7dd]** The discussion of “super‑additive” gains from combining replay and reformulations lacks a quantitative decomposition of interaction effects. Include an explicit analysis (e.g., interaction term in ANOVA) to support the super‑additivity assertion.
- **[fbc825832fe2]** The manuscript inherits the teacher’s biases and the dataset’s spurious correlations without any mitigation strategy; add a dedicated bias‑analysis section and discuss mitigation (e.g., debiasing prompts, safety‑aligned fine‑tuning).
- **[bfe6ef3c2a3c]** The reward signal optimises only for answer correctness and explicitly states it does not address safety or fairness; incorporate at least one safety‑oriented evaluation (e.g., toxicity, harmful content) to demonstrate that ZPPO does not exacerbate unsafe behaviours.
- **[f8322551ac81]** Potential dual‑use risk: improving small VLM/LLM capabilities can lower the barrier for malicious actors; include a brief discussion of misuse scenarios and recommended safeguards for deployment.
- **[d2431d288fcd]** The data used for ZPPO‑77K multimodal RL corpus is not described in detail; verify that no personally identifiable information (PII) or copyrighted content is present, and add a data‑privacy statement.
- **[f961f7ee65d6]** Report per‑run variability (e.g., standard deviations or confidence intervals) for the main ZPPO vs. baseline comparisons; currently only point estimates are shown, which makes it hard to assess statistical significance across random seeds.
- **[d3f991e457e6]** Clarify the hyper‑parameter selection protocol (e.g., how replay fraction ρ_replay=0.25 and augmentation fraction ρ_aug=0.25 were chosen) and demonstrate that results are not overly sensitive to these choices.
- **[49ddb891e7f8]** Include an explicit held‑out benchmark set or cross‑validation split to guard against over‑fitting to the 31 reported tasks; the current evaluation uses the same suite for development and final reporting.
- **[6abfa0b1b456]** Provide a power analysis or justification for the sample size (31 benchmarks) relative to the effect sizes reported (e.g., +7.5 pp macro‑average); this will help readers gauge whether the observed gains are practically significant.
- **[b7ad362fb047]** Add replication details such as random seed values, number of training runs per configuration, and hardware reproducibility notes to enable independent verification.
- **[62c2fa987dbd]** Provide statistical significance estimates (e.g., confidence intervals or hypothesis‑test p‑values) for the primary macro‑average gains reported in Table 1 and Table 2; the current presentation shows only point percentages without uncertainty, making it unclear whether the observed improvements are robust.
- **[5fbcb08fac51]** Address the multiple‑comparisons problem arising from evaluating many benchmarks (31 total) and several baselines; consider applying a correction (e.g., Bonferroni, Holm) or reporting family‑wise error rates.
- **[fbf561563466]** Report results over multiple random seeds (at least three) for each method to quantify run‑to‑run variance; include standard deviations or confidence intervals for the main tables.
- **[0b1ea0d0bd56]** Clarify the bootstrap procedure used in Appendix C (e.g., resampling unit, number of replicates) and release the code used for the cluster‑bootstrap analysis to ensure reproducibility.
- **[ea885da39730]** Specify the random seed(s) and any nondeterministic settings (e.g., GPU nondeterminism, data shuffling) used during training and evaluation so that exact replication is possible.
- **[3c06ae253192]** Add missing package imports for custom environments (e.g., prompttemplate, questionbox) or replace them with standard LaTeX constructs; undefined environments cause compilation failures.
- **[910cfc56bb93]** Define or import color macros used in tables/figures such as \rowcolor{colorful}, \dpos, \posgain, and ensure the colortbl/xcolor packages are loaded.
- **[32341ca92b79]** Ensure all \citep/\citet commands are supported by loading the natbib (or biblatex) package and that bibliography style matches the journal’s requirements.
- **[582c9c239e36]** Verify that every \ref{...} has a corresponding \label defined (e.g., Fig.~\ref{fig:concept}a) and that labels are placed immediately after \caption within figure/table environments.
- **[f4c030ea7b3b]** Check heading hierarchy: the abstract uses \section* but the document lacks a \maketitle; either add a proper title block or move the abstract into a \begin{abstract} environment.
- **[6380d08e7e14]** Place all \caption commands directly after \begin{figure} or \begin{table} and before any \includegraphics or \resizebox content to follow LaTeX conventions.
- **[4d146d9a1e1e]** Wrap long lines (especially in tables and algorithm listings) to stay within ~80 characters for readability; consider using the 'tabularx' package for automatic column width management.
- **[54d67fd00c42]** Add missing \usepackage{booktabs, colortbl, xcolor, amsmath, amssymb, algorithm2e} (or similar) to support \toprule, \midrule, \bottomrule, \SetAlgoLined, and other commands used throughout.
- **[0e99aa8aecdb]** Standardize citation punctuation (e.g., ensure a period follows each \citep command) and verify that all cited keys exist in the .bib file.
- **[90c1b97f83f2]** Long, comma‑heavy sentences in the Abstract and Introduction impede readability (e.g., the first sentence of the Abstract and the opening paragraph of Section 1). Break them into shorter clauses and add missing commas.
- **[4dc61f427a01]** Inconsistent terminology and capitalization (e.g., “hard questions” vs. “Hard questions”, “BCQ” vs. “binary‑candidate prompt”) cause confusion. Standardize naming and use sentence case for section headings.
- **[5610e4b48339]** Table and figure captions often omit units or context (e.g., Table 1 caption “average scores, %” and Fig. 2 caption lack explanation of axes). Revise captions to be self‑contained.
- **[ea2b86571e6d]** Bullet‑point lists in Sections 2 and 3 mix full sentences with fragments and lack parallel structure. Re‑write each item as a complete sentence or a consistent fragment.
- **[58eb969bdf30]** Frequent use of abbreviations without first definition (e.g., “GRPO”, “DAPO”, “REINFORCE++”) makes the text hard to follow for readers unfamiliar with the prior work. Introduce each abbreviation on first use.
- **[ba517f81ff9a]** The “Limitations” and “Ethical Considerations” sections contain run‑on sentences and missing articles (e.g., “ZPPO builds on publicly released Qwen3.5 models; any upstream biases are inherited.”). Edit for grammatical completeness.
- **[4e49b4e79a50]** Cross‑references sometimes point to missing or ambiguous labels (e.g., “Fig. ef{fig:zone}” is not present in the excerpt). Verify that all ef commands resolve to existing figures/tables.
- **[fca61e51bf5b]** The algorithm pseudocode (Algorithm 1) lacks descriptive comments for several steps, making it difficult to follow. Add brief inline explanations for each block.
