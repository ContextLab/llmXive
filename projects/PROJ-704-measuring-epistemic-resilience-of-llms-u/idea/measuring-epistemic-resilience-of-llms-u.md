---
field: linguistics
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/329
paper_authors:
  - Hongjian Zhou
  - Xinyu Zou
  - Jinge Wu
  - Sean Wu
  - Junchi Yu
  - Bradley Max Segal
  - Tobias Erich Niebuhr
  - Sara Amro
  - Michael Petrus
  - Sheikh Momin
  - Alexandra M. Cardoso Pinto
  - Rachel Niesen
  - Laura Sophie Wegner
  - Dhruv Darji
  - Jung Moses Koo
  - Joshua Fieggen
  - Kapil Narain
  - Mingde Zeng
  - Lei Clifton
  - Linda Shapiro
  - Fenglin Liu
  - David A. Clifton
---

# Measuring Epistemic Resilience of LLMs Under Misleading Medical Context

A paper was submitted via the website for consideration / review.

Source URL: https://arxiv.org/abs/2606.12291
Paper authors (from arXiv): Hongjian Zhou, Xinyu Zou, Jinge Wu, Sean Wu, Junchi Yu, Bradley Max Segal, Tobias Erich Niebuhr, Sara Amro, Michael Petrus, Sheikh Momin, Alexandra M. Cardoso Pinto, Rachel Niesen, Laura Sophie Wegner, Dhruv Darji, Jung Moses Koo, Joshua Fieggen, Kapil Narain, Mingde Zeng, Lei Clifton, Linda Shapiro, Fenglin Liu, David A. Clifton

Submitted by: github-actions[bot]

(Intake from human-submission issue #329.)

## Rejection rationale (2026-06-18)

Paper-stage review found one or more `fatal`-severity action items. The underlying research question is returned to the backlog so a fresh approach can be considered:

- **[a16a40a6a1b5]** Add a verification table indicating that every cited reference has been checked and marked as verified.
- **[00e9cfc33a3f]** Provide explicit scripts or detailed instructions for the applicability‑filtering and injection‑generation steps, including the exact prompts used, to enable full reproducibility of the MedMisBench construction.
- **[cb624884363c]** Discuss the limitations of using synthetic, model‑generated misleading context and how this may affect the generality of the reported results.
- **[e2b0b66bd579]** Clarify the evaluation protocol for proprietary APIs (e.g., GPT‑5.4, Gemini) and provide guidance for researchers who only have access to open‑weight models.
- **[bf74dd3a12a9]** The paper does not provide any accompanying source code, data‑generation scripts, or evaluation pipelines. Without a public repository containing the injection generation prompts, applicability‑filtering logic, and evaluation harness, the benchmark cannot be reproduced from scratch.
- **[abe7ca3693d3]** All benchmark construction steps are described only in prose and in the appendix. Critical components (e.g., the applicability‑filtering prompt, the option‑wise injection generation prompt, and the static release schema) are not released as executable scripts or notebooks, making it impossible for reviewers or downstream users to verify the pipeline.
- **[9a9432141c83]** The LaTeX source is a single monolithic file (main.tex) with no modular organization of figures, tables, or supplementary material. This hampers readability and makes it difficult to locate specific sections (e.g., the taxonomy definitions or the mitigation case‑study details) for inspection.
- **[df5599139e7c]** No dependency manifest (e.g., requirements.txt, environment.yml, or Dockerfile) is provided for the models, the local open‑weight inference setup, or the clinician‑review annotation tooling. This prevents reproducible environment recreation.
- **[78086dffa89c]** The benchmark release schema (Table 9) is described but the actual JSON/YAML files are not linked or attached. Reviewers cannot verify that the option‑aligned injection fields are correctly formatted or that the derived Type 1/Type 2 contexts are generated deterministically.
- **[326305b520ce]** There is no automated test suite for the benchmark generation pipeline (e.g., unit tests for applicability filtering, sanity‑check tests for injection validity, or integration tests that run a small model end‑to‑end). Absence of tests raises the risk of silent bugs in future updates.
- **[7387ebc57048]** The mitigation case studies (search‑based retrieval and defensive prompting) are presented only as result tables; the code that implements the search tool, the ReAct/OpenSeeker loops, and the defensive prompt wrapper is not released.
- **[f52efbfb5aed]** Figures are embedded as PDF files without source (e.g., .svg or .tex) or generation scripts. This limits the ability to regenerate or modify the visualizations for future work.
- **[87d09d46e398]** The bibliography is extensive but not managed via a version‑controlled .bib file linked from the repository; any future changes to citations would require manual edits to the LaTeX source.
- **[38e7c57df5a3]** The paper mixes commercial‑API calls (GPT‑5.4, Gemini, Claude) with locally‑run open‑weight models without documenting the exact API versions, temperature settings, or token limits used. This omission makes exact replication of the reported numbers impossible.
- **[78e569abe64e]** Add explicit licensing information for the released benchmark, code repository, and HuggingFace dataset (e.g., MIT, Apache‑2.0, CC‑BY‑4.0).
- **[1f83d42cadfe]** Provide a persistent version identifier (e.g., a DOI or a Git tag/commit hash) for each released snapshot of MedMisBench and its associated data files.
- **[0f17002a41bd]** Document the full JSON schema of the released items (field types, required/optional flags, enumerated values) in the paper or an accompanying README to ensure reproducibility.
- **[17c2937a47fd]** Include a statement about how long the external URLs (GitHub, HuggingFace, arXiv) are expected to be maintained, and consider archiving them (e.g., via Zenodo) to mitigate link rot.
- **[af611f623d75]** Describe how missing or filtered items (e.g., the 58 % of source questions that were discarded) are recorded in the release metadata, and provide a rationale for the filtering criteria.
- **[82b863ee7e37]** Specify the process for updating the benchmark (e.g., how new medical questions or new corruption types will be added) and how version control will be handled for future releases.
- **[d80f5dc80caa]** Add descriptive alt‑text for every figure (including sub‑figures) to improve accessibility for screen‑reader users.
- **[fd244c829b90]** Verify that all color schemes used in plots (e.g., Figures 4, 5, 6) are color‑blind safe; replace any red/green or similar problematic palettes with a palette that is distinguishable for deuteranopia and protanopia.
- **[569df7700927]** Increase the font size of axis labels and tick marks in wrapped figures (e.g., Figure 3) to ensure legibility when printed at typical conference sizes (column width ≈ 3.25 in).
- **[e229ad22d448]** Ensure every plotted figure includes explicit axis labels with units where applicable (e.g., accuracy percentages, attack‑success rates) and a legend that does not rely solely on color.
- **[b56f0199fb3c]** Provide a brief caption that fully explains the visual content of each figure without requiring the reader to refer back to the main text; include definitions of any abbreviations used in the figure.
- **[55007e74d46d]** Replace the term “epistemic resilience” with a plain phrase such as “ability to stay correct when given misleading medical information”.
- **[cc41f1e8b66f]** Define all acronyms at first use (e.g., RAG, LLM‑as‑judge, Gwet AC2, qw‑κ) or replace them with descriptive language.
- **[5f08cc3fae35]** Simplify the taxonomy description; avoid phrases like “content‑corruption” and “provenance framing” and instead say “type of false claim” and “who is said to have made the claim”.
- **[c6c084bd62cc]** Rename “Type 1” and “Type 2” delivery protocols to “focused false‑claim test” and “full‑evidence test” and explain them in plain language when first introduced.
- **[264618a3b81c]** Reduce reliance on specialist jargon such as “authority‑framed”, “exception poisoning”, “spurious anchoring”, and replace with everyday terms like “official‑sounding false claim”, “fabricated exception”, and “irrelevant detail”.
- **[d7d76a687f4f]** When mentioning model configurations (e.g., “high reasoning”, “medium reasoning”), briefly explain what the reasoning setting entails for non‑technical readers.
- **[6eb7f0df8a37]** Avoid dense abbreviation clusters in tables (e.g., “ASR”, “TASR”, “T1”, “T2”) without a clear legend; add a short caption or footnote that spells them out.
- **[b8f0ee129a27]** Clarify the meaning of statistical terms like “attack success rate” by adding a one‑sentence lay explanation (e.g., “the percentage of times a model’s correct answer was changed by the misleading context”).
- **[f771e2f5f8e8]** Replace the phrase “static reusable benchmark” with “a fixed set of test items that can be shared and reused by other researchers”.
- **[68cc8220564a]** Temper the claim that 38.2% of model outputs pose serious clinical harm; the figure is based on a limited 89‑task clinician review sample and should be presented as an indicative finding rather than a definitive prevalence across the whole benchmark.
- **[e0e3fcbfce7e]** Add a clear limitation stating that MedMisBench evaluates only multiple‑choice, answer‑grounded items and may not directly reflect epistemic resilience in open‑ended or multi‑turn clinical dialogues.
- **[a7eb45776a62]** Discuss the risk of contamination where commercial LLMs might have seen portions of the source datasets during training, which could affect clean‑accuracy and resilience measurements.
- **[f86141531827]** The release of a large corpus of fabricated medical statements (the misleading‑context injections) creates a clear dual‑use risk; malicious actors could repurpose the dataset to train or fine‑tune models that generate persuasive medical misinformation. Require a detailed risk‑mitigation plan (e.g., restricted access, watermarking, usage‑license clauses) before public distribution.
- **[1e9c51380955]** The manuscript mentions a 14‑member clinician panel but does not provide evidence of Institutional Review Board (IRB) or equivalent ethical approval for the human‑subject review process. Add a statement confirming IRB/ethics‑committee approval or an exemption justification.
- **[05b9549c1939]** Although the source questions are from public benchmarks, verify that no patient‑identifiable information (PHI) is present in any of the injected contexts or in the original vignettes. Include an explicit data‑privacy audit statement.
- **[84eaafc2d0e6]** The benchmark could inadvertently be used to improve adversarial attacks on medical LLMs. Discuss safeguards such as limiting the release to research‑only licenses, providing guidance on responsible use, and encouraging the community to develop defensive techniques alongside the benchmark.
- **[06d38599b286]** Provide statistical significance testing (e.g., chi‑square or Fisher’s exact test) when comparing ASR/accuracy across model families and reasoning settings, and report corresponding p‑values or confidence intervals.
- **[d8086741df62]** Apply a multiple‑comparisons correction (e.g., Bonferroni or Benjamini‑Hochberg) to the many stratified analyses (content type × provenance × dataset) to control the family‑wise error rate.
- **[95c0ceeef940]** Report confidence intervals (e.g., Wilson or Agresti‑Coull intervals) for all proportion metrics (clean accuracy, Type 1/2 accuracy, ASR, TASR) rather than only point estimates.
- **[05c7f4bb329d]** Clarify the independence assumptions underlying the paired clean‑injected evaluation (e.g., whether the same item appears in multiple model evaluations) and discuss potential clustering effects.
- **[c67726baf179]** Include a power analysis or sample‑size justification for the clinician review cohort (89 items) to demonstrate that the reported harm rates are statistically reliable.
- **[fbfbcf0eef01]** Document the exact random seeds and any stochastic decoding parameters used for each model run to ensure full reproducibility of the reported proportions.
- **[8c3d02119377]** The use of `wrapfigure` environments includes manual `\vspace{-1.0em}` (or similar) adjustments before `\centering`. This can lead to overlapping text or negative vertical space warnings. Replace the manual vertical spacing with proper placement options (e.g., `\begin{wrapfigure}[lineheight]{r}{0.55\textwidth}`) or consider using standard `figure` floats if wrapping is not essential.
- **[40c0ac74ce48]** Tables are created with `\begin{table}[t]` (or `table*`) followed by `\captionsetup{type=table}` and `\captionof{table}{...}`. This is unconventional and may cause numbering or caption placement issues. Use the standard `\caption{...}` command inside the `table` environment and remove the extra `\captionsetup{type=table}` unless a specific caption type is required.
- **[345aa6f81aa6]** Several sentences are overly long and contain multiple clauses, which hampers readability. Break them into shorter, clearer statements (e.g., the first sentence of the abstract and the opening paragraph of the Introduction).
- **[67bda7ce7564]** Inconsistent use of commas around parenthetical phrases leads to ambiguity (e.g., "...patients increasingly use them for health advice before or after seeing a clinician~\citep{costagomes2026publicuse}." should have a comma after the citation).
- **[180323f95566]** Figure captions sometimes repeat information already in the main text and lack concise descriptions of what the figure illustrates; revise for brevity and clarity.
- **[3835ef4e0342]** The transition between sections 3.1 and 3.2 is abrupt; add a brief linking sentence to improve flow.
- **[875b755f9b64]** Some terminology is introduced without definition (e.g., "exception poisoning"), which may confuse readers unfamiliar with the taxonomy. Provide a short definition on first use.
- **[496d0a449d47]** The use of LaTeX macros such as \yesmark and \nomark in the main text (e.g., Table 1) can be distracting; consider replacing them with plain text symbols for readability.
- **[1a31bc519399]** There are occasional mismatches between singular/plural forms (e.g., "a 14-member clinical panel" vs. "14‑member clinical panels"). Ensure grammatical agreement throughout.
- **[987800cada77]** The conclusion repeats several points from the abstract verbatim; rephrase to avoid redundancy and to provide a succinct take‑away.
- **[7fbfd01bf3c6]** References are sometimes placed after punctuation (e.g., "...medical examinations~\citep{nori2023gpt4medical},"), which is acceptable in LaTeX but can be visually jarring. Consider moving the citation before the period.
- **[670c4d984913]** The appendix sections are listed with custom commands that may not render correctly in all PDF viewers; verify that the table of contents entries are properly hyperlinked.
