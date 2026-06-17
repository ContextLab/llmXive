---
field: other
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/280
---

# https://arxiv.org/abs/2606.03746

A paper was submitted via the website for consideration / review.

Source URL: https://arxiv.org/abs/2606.03746

Submitted by: github-actions[bot]

(Intake from human-submission issue #280.)

## Rejection rationale (2026-06-17)

Paper-stage review found one or more `fatal`-severity action items. The underlying research question is returned to the backlog so a fresh approach can be considered:

- **[423e4f2e9780]** Provide a brief description of how the step‑wise teacher weighting coefficients λ_{k,m}(c) are chosen (e.g., schedule, validation procedure) and include any ablation results showing their impact.
- **[64e2db787afa]** Supplement the automatic LLM‑based evaluation with at least a small human study (e.g., AMT or expert rating) to validate that Gemini 3.1 Pro and GPT 5.5 scores correlate with human preference.
- **[afa20f5cce78]** Clarify the hyper‑parameter settings for the DMD training (learning rate schedule, batch size, number of diffusion steps per iteration) and report any stability tricks used.
- **[faec58995e17]** Discuss the observed limitations in dense text rendering more concretely, possibly providing quantitative analysis (e.g., OCR accuracy) and outlining future directions to address them.
- **[400bd8f8de6e]** The submission does not include any source code, training scripts, or environment specifications required to reproduce the experiments (e.g., the DMD distillation pipeline, data preprocessing, multi‑teacher guidance implementation). Provide a public repository with well‑documented code.
- **[0046d70946ef]** Add a `README.md` that lists all dependencies (exact package versions, CUDA/cuDNN requirements) and step‑by‑step instructions to train and evaluate the few‑step student from scratch.
- **[2e2a0fd0b939]** Structure the code into logical modules (e.g., `data/`, `models/`, `training/`, `evaluation/`) and ensure each module has a concise docstring explaining its purpose and public API.
- **[2fee65e4025d]** Include unit and integration tests for critical components such as data loaders, the DMD loss implementation, and the multi‑teacher weighting logic. Tests should be runnable via a standard framework (e.g., pytest) and cover edge cases.
- **[3d61bd701cf4]** Provide scripts or notebooks that generate the two benchmark suites (T2I‑Bench and Editing‑Bench) and the automatic evaluation pipelines using Gemini 3.1 Pro and GPT 5.5, together with instructions for obtaining the necessary API keys.
- **[8879d3b2a186]** Add a dedicated Data Availability statement that specifies the exact sources, licenses, and version identifiers for the T2I‑Bench and Editing‑Bench datasets (e.g., URLs, DOI, or repository commit hashes).
- **[f183bbc61e72]** Provide a clear schema description for the prompts used in each benchmark (fields such as category, prompt text, image dimensions, etc.) and explain how missing or malformed entries are handled during training and evaluation.
- **[2d6d97158767]** Document the provenance of all external resources (e.g., Qwen‑Image‑2.0 teacher weights, Qwen‑Image‑Flash checkpoints) and include licensing information for each model and dataset.
- **[55e1fb629d4c]** Include version control metadata (e.g., git commit SHA, tag) for the code used to generate the results, and make the training scripts publicly accessible in a persistent repository.
- **[e0ebaabe52ac]** Verify that any URLs referenced in the paper (e.g., links to the arXiv source, evaluation scripts, or model checkpoints) are stable and consider archiving them via a service like Zenodo to prevent link rot.
- **[31de8741c32d]** Define every acronym (e.g., NFEs, DMD, FM, T2I, CFG, KL, ODE, etc.) at first appearance; add a short glossary if many remain.
- **[2c03dd2ff163]** Replace overly technical jargon with plain English equivalents where possible (e.g., “trajectory‑level alignment” → “matching the teacher’s step‑by‑step behavior”).
- **[909ef98b0a1c]** Explain domain‑specific concepts such as “score field”, “distribution matching”, and “flow matching” in lay terms or with illustrative examples.
- **[4fed14649e6d]** Avoid vague buzz‑words like “beyond the objective” without concrete clarification; rewrite to state the specific additional factors (data composition, teacher guidance, task mixture).
- **[87c56c959168]** In Section 3 and Section 5, replace repetitive use of “multi‑teacher guidance”, “step‑wise multi‑teacher guidance”, and similar phrases with a single clear term and refer back to it.
- **[20a208be4fab]** The manuscript lacks an explicit discussion of dual‑use risks associated with low‑latency, high‑quality image generation and instruction‑guided editing (e.g., deepfakes, misinformation, illicit content creation). Add a dedicated section outlining potential misuse scenarios and proposed mitigation measures (watermarking, content filters, usage licenses).
- **[7b5c24cfe669]** Training data provenance is not described. Clarify the source of the images used by the teacher model, including any copyrighted or personally identifiable content, and confirm that appropriate licenses or consent were obtained.
- **[2444860ed709]** No ethical review (IRB/IACUC) is required for the current work, but the authors should reference any institutional guidelines they followed for handling large web‑scraped datasets, especially regarding privacy and consent.
- **[21e79333c86e]** The paper does not address privacy concerns for any potential downstream applications that involve user‑provided images (e.g., editing personal photos). Include a brief analysis of how the model could be constrained to respect privacy (e.g., refusing to process identifiable faces without consent).
- **[439dc39f448e]** Consider adding a statement on responsible release practices (e.g., staggered rollout, model licensing, community guidelines) to prevent unrestricted access to the 4‑NFE student model.
- **[3250412f03e7]** Report variability (e.g., standard deviation, confidence intervals) for all quantitative scores (Gemini 3.1 Pro and GPT 5.5) across the benchmark samples.
- **[a12a1426b887]** Conduct appropriate statistical significance tests (e.g., paired t‑test, Wilcoxon signed‑rank) when comparing models in Tables 1‑5 and clearly state p‑values.
- **[f65ec40d5ea8]** Apply a multiple‑comparisons correction (e.g., Bonferroni, Holm) given the large number of metrics, categories, and model variants evaluated.
- **[f8707c8e86e7]** Provide details on random seeds, number of generated images per prompt, and any stochastic sampling settings to enable exact reproducibility of the evaluation.
- **[01d4216d121f]** Release the evaluation scripts (including the system prompts for Gemini and GPT evaluators) and the generated outputs used for the reported scores.
- **[31eec9d11c63]** The preamble contains many duplicated package imports (e.g., enumitem, inputenc, fontenc, babel, booktabs, array, makecell). Remove redundant \usepackage lines to improve LaTeX hygiene and reduce compilation overhead.
- **[96895d7563fc]** Several packages are loaded but never used (e.g., CJKutf8, pifont, bbding, fontawesome, supertabular, suptabular, longtable, svg, tcolorbox multiple times). Clean up unused packages to avoid unnecessary bloat.
- **[31132874b1b3]** The document loads both `natbib` and `cleveref` but does not configure `natbib` options (e.g., citation style). Ensure a consistent bibliography style or set `\bibliographystyle{...}` options to match the journal’s requirements.
- **[f1a8febcb7ba]** Figure environments use the `[h!]` placement specifier, which can lead to overfull pages if LaTeX cannot honor the request. Consider using `[tbp]` or allowing more flexible placement.
- **[099342391519]** Tables use a custom `\tablestyle` macro that changes `\tabcolsep` and `\arraystretch` globally. Scope these changes locally within each table to avoid unintended side effects on subsequent tables or figures.
- **[619f263c13c9]** Split overly long sentences (e.g., the first sentence of the Abstract and several sentences in the Introduction) into shorter, clearer statements; add missing commas to improve readability.
- **[7292ea8f872e]** Standardize hyphenation and terminology (e.g., use "few‑step" consistently instead of alternating with "few-step").
- **[bdef2672ffb9]** Add paragraph breaks after each of the three key takeaways in Sections 3–5 to avoid dense blocks of text.
- **[b03fbe373e2c]** Correct minor typographical inconsistencies such as missing Oxford commas in enumerations and inconsistent capitalization of "T2I" versus "t2i".
- **[9bbd08d22de7]** Ensure all figure and table references match their labels (e.g., verify that Figure~\ref{fig:training_data} points to the correct figure and that Table captions are concise).
- **[2682b09fc670]** Refine the phrasing of several complex sentences (e.g., the sentence starting with "We first show that naively replacing the base teacher..." in Section 4) for smoother flow.
- **[70817f623e9b]** Consider tightening the Conclusion to avoid repetition of earlier messages and to provide a concise summary of contributions.
