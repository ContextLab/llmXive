---
field: computer science
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/312
paper_authors:
  - Wenbo Pan
  - Shujie Liu
  - Chin-Yew Lin
  - Jingying Zeng
  - Xianfeng Tang
  - Xiangyang Zhou
  - Yan Lu
  - Xiaohua Jia
---

# Evolving Agents in the Dark: Retrospective Harness Optimization via Self-Preference

A paper was submitted via the website for consideration / review.

Source URL: https://arxiv.org/abs/2606.05922
Paper authors (from arXiv): Wenbo Pan, Shujie Liu, Chin-Yew Lin, Jingying Zeng, Xianfeng Tang, Xiangyang Zhou, Yan Lu, Xiaohua Jia

Submitted by: github-actions[bot]

(Intake from human-submission issue #312.)

## Rejection rationale (2026-06-29)

Paper-stage review found one or more `fatal`-severity action items. The underlying research question is returned to the backlog so a fresh approach can be considered:

- **[4075d9653622]** Multiple citations reference 2025-2026 papers (e.g., liu2026webtrap, deng2025swebenchpro, froger2026gaia2, openai2026gpt55) that cannot be verified as existing sources. These future-dated citations undermine claim accuracy.
- **[43b2734f77b0]** The paper claims to use "Codex gpt-5.5" (Table 1, Appendix) but GPT-5.5 is not a publicly available model. This factual claim about the experimental setup cannot be verified.
- **[b8b39666ee29]** arXiv ID 2606.05922 indicates June 2026 submission date, which is in the future. This creates inconsistency between the paper's provenance and its citation timeline.
- **[d48b2aca4433]** Claims about baseline performance (e.g., Meta-Harness 0.62 at 1 round, 0.80 at 10 rounds in Table 3) cite lee2026metaharness which cannot be verified. Baseline comparisons require verifiable sources.
- **[a99fa92adaa5]** Code repository link (https://github.com/wbopan/retro-harness) is cited but not accessible for review. Full implementation must be provided for reproducibility verification.
- **[4412c91c8f6c]** Appendix code snippets (bash/Python) lack complete implementation details. Scripts like bin/repair-verify and are_helper.py are truncated with '(... omitted ...)' markers.
- **[5c979507d4a5]** No test suite or CI configuration is visible in the paper. Reproducibility statement claims persistence of artifacts but does not specify test coverage or validation procedures.
- **[6ef77177218a]** Add explicit license declarations for all datasets (SWE-Bench Pro, Terminal-Bench, GAIA-2) and the code repository.
- **[9aedba857dfc]** Pin the GAIA-2 dataset version with a specific commit hash or Hugging Face revision ID, similar to SWE-Bench Pro.
- **[fa728dd085af]** Provide a formal schema (e.g., JSON Schema) for the persisted artifacts (trajectories, diagnoses) to ensure reproducibility.
- **[c31956d1c8cc]** No alt text provided for any of the 5 figures. Add descriptive alt text for accessibility compliance (e.g., lttext{...} or figure environment alternatives).
- **[1dff2f1846d8]** Figure captions lack sufficient detail for standalone comprehension. Expand captions to describe key visual elements, not just high-level purpose (e.g., Fig. 2 should describe pipeline stages visually).
- **[e2dc2cff9ca0]** Cannot verify axis labels, units, or color choices without viewing actual figure PDFs. Authors should confirm all plots have labeled axes with units where applicable, and colors are print-safe (grayscale compatible).
- **[e341f27ed7cf]** Figure 5 (fig-coreset-selection.pdf) caption references subfigures (a) and (b) but the LaTeX source does not show subfigure environments. Ensure subfigure labels are visible in the rendered PDF.
- **[cc8713297e18]** Define or replace the term “harness” early on; most readers will understand “toolset” or “environment configuration” more readily.
- **[6805a22255dc]** Introduce the acronym “LLM” (large language model) at first use; it appears without definition in the abstract and later sections.
- **[3ac5c47b5c7a]** Explain the symbols k, G, N, θ, α, S_j, etc., when they first appear; many are used in equations before any textual description.
- **[34159609e68f]** Replace “self‑preference” with a clearer phrase such as “agent’s own ranking of its outputs” and provide a brief intuitive explanation.
- **[5f5026c01dd2]** The phrase “best‑of‑N” is jargon; consider rephrasing to “select the best among N candidates”.
- **[3dad8ac93899]** Clarify “DPP” (determinantal point process) on first mention; a short parenthetical definition will aid non‑specialists.
- **[3469b5052110]** Avoid overloading the word “rank” – it appears as a function name, a scoring metric, and a verb. Use distinct terms like “score”, “compare”, or “evaluate”.
- **[4d5fdce594db]** In the abstract, replace “AI agents rely on a harness of skills, tools, and workflows” with a plain statement such as “AI agents need a set of tools, prompts, and skills to operate”.
- **[e72a9a203c5e]** The abbreviation “SWE‑Bench Pro” is introduced without context; add a short clause describing it as a software‑engineering benchmark.
- **[cdf811759fed]** The term “coreset” may be unfamiliar; add a brief explanation (e.g., “a small, representative subset of tasks”).
- **[064f9f87e817]** When referring to “self‑validation” and “self‑consistency”, provide a one‑sentence lay explanation of each.
- **[3decb7db2c0a]** In Table captions, replace technical shorthand like “Pass” and “Δ” with full words (“Pass rate”, “Absolute change”).
- **[806dcc616ced]** The term “agent calls” in cost tables may be confusing; consider renaming to “model invocations”.
- **[a96fa5443cac]** Clarify Abstract to specify 'without external grading during optimization' rather than implying the evaluation is label-free. The pass rate metric requires the external grader.
- **[89085c2337c8]** Refine 'using only past trajectories' to 'using past trajectories to select tasks for re-solution' to accurately reflect the active rollout phase.
- **[3a5788b64847]** The Limitations section acknowledges the method may inherit adversarial content from compromised trajectories. Expand this discussion with specific mitigation strategies and risk assessment.
- **[69a2fdf2731c]** The method enables agents to modify executable scripts in the harness. Discuss potential security implications of self-modifying code and any safeguards against introducing vulnerabilities.
- **[3aeb12220d6c]** The self-preference mechanism could optimize for unintended objectives. Add discussion of alignment risks and whether any alignment constraints are enforced during optimization.
- **[793e522e70f7]** Report confidence intervals or p-values for main results in Table 2 to establish statistical significance given test set sizes (100, 59, 100).
- **[928c7afa944e]** Disclose if hyperparameters (k=10, G=3, N=3, theta=0.7) were tuned on the test set or provide sensitivity analysis to rule out selection bias.
- **[926f242a2c12]** Provide variance across multiple independent optimization runs (different seeds) rather than just candidate variance within a single run (Table 4).
- **[7c5adbbb1500]** Report confidence intervals or standard errors for all pass rate results in Table 1. Single-run point estimates (0.59→0.78) lack uncertainty quantification needed to assess statistical significance.
- **[76a82a10e89b]** Conduct multiple independent runs (n≥5) for each method-benchmark combination to enable proper statistical testing (e.g., paired t-tests or bootstrap CIs) of improvement claims.
- **[949cf0efae54]** Apply multiple-comparisons correction (Bonferroni or FDR) when reporting results across 3 benchmarks and 5+ methods. Current analysis treats each comparison independently.
- **[a3fceaa1f44c]** Table 2 (Ablation) shows performance drops but no statistical tests. Report whether differences (e.g., 0.78 vs 0.56 for -self-consistency) are statistically significant.
- **[ae0e1f647fc9]** Table 3 (Best-of-N) reports Std but only for candidate selection, not for main results. Clarify whether the 0.78 pass rate is mean over multiple runs or single-run.
- **[6b7d0624c89b]** Duplicate content detected: Introduction, Experiments and Results, and Algorithm 1 appear in multiple chunks (e002, e003). Consolidate to single instances to avoid compilation errors and inconsistent numbering.
- **[73c7d3ae7a0d]** Inconsistent table formatting: tab:main uses esizebox in e003 but not in e002. Standardize all tables to consistent width handling (prefer esizebox or fixed column widths, not both).
- **[732a44658c6f]** Figure caption placement inconsistency: Some captions appear before egin{figure} (e.g., fig:steps in e002) while others appear after. LaTeX convention requires caption inside figure environment, after \includegraphics.
- **[2bdbb8e530f8]** Undefined color command: \cellcolor{rhoBlue} used in tab:main but color 'rhoBlue' is not defined in preamble. Either define \definecolor{rhoBlue}{...} or remove color highlighting.
- **[2a10d22a59e9]** Custom environment egin{promptbox} used throughout appendices but not defined in standard LaTeX. Either provide package definition or replace with standard listing environments (lstlisting, verbatim).
- **[88a1e45acb24]** Inconsistent citation style: \citep{} used predominantly but \cite{#1} appears in e000 critical elements. Standardize to \citep{} for parenthetical citations throughout.
- **[9c6edf33e2c7]** Algorithm formatting inconsistency: alg:rho appears twice with different styling (one uses hostage{}, one does not). Consolidate to single definition with consistent algorithmic environment.
- **[8629213f8a0b]** Appendix ordering: app:datasets appears in both e001 and e002 with different content. Ensure appendices are in logical order (Prompts, Hyperparameters, Pipeline, Datasets, Baselines, Cost, Artifacts) without duplication.
- **[84c55d3d3c3a]** Standardize citation style: paper uses both \cite and \citep interchangeably. Choose one and apply consistently throughout.
- **[64ca2a475893]** Remove duplicate Limitations section: appears in front matter and again at end of paper. Keep one instance.
- **[7a0ef071cf7e]** Fix figure caption formatting: some captions contain \looseness=-1 LaTeX command that should not appear in final text.
- **[abdbd17468b6]** Standardize appendix references: some use Appendix~\ref{app:...}, others use Appendix~\ref{app:...}. Ensure consistent capitalization.
- **[4405c4d979ff]** Improve section transitions: Section 5.1 to 5.2 has abrupt jump. Add transition sentence to improve flow.
- **[8fa08ab29867]** Define abbreviations on first use: SWE-Bench Pro appears without brief explanation for unfamiliar readers.
- **[f4ff80900359]** Standardize table caption style: some have full sentences, others have fragments. Choose one format.
- **[21069e57b946]** Consistent mathematical notation: use \mathrm for operators and \mathcal for sets consistently throughout.
