---
field: computer science
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/310
paper_authors:
  - Kwai Keye Team
  - Bin Wen
  - Changyi Liu
  - Chengru Song
  - Chongling Rao
  - Guowang Zhang
  - Han Li
  - Haonan Fan
  - Hengrui Ju
  - Jiankang Chen
  - Jiapeng Chen
  - Jiawei Yuan
  - Kaixuan Yang
  - Kaiyu Jiang
  - Kun Gai
  - Lingzhi Zhou
  - Na Nie
  - Sen Na
  - Tianke Zhang
  - Tingting Gao
  - Xuanyu Zheng
  - Yulong Chen
  - Fan Yang
  - Haixuan Gao
  - Lele Yang
  - Mingqiao Liu
  - Muxi Diao
  - Qi Zhang
  - Qile Su
  - Wei Chen
  - Wentao Hong
  - Xingyu Lu
  - Yancheng Long
  - Yankai Yang
  - Yingxin Li
  - Yiyang Fan
  - Yu Xia
  - Yuzhe Chen
  - Ziliang Lai
  - Chuan Yi
  - Haonan Jia
  - Tianming Liang
  - Weixin Xu
  - Xiaoxiao Ma
  - Yang Tian
  - Yufei Han
  - Feng Han
  - Hang Li
  - Jing Wang
  - Jinghui Jia
  - Junmin Chen
  - Junyu Shi
  - Ruilin Zhang
---

# Kwai Keye-VL-2.0 Technical Report

A paper was submitted via the website for consideration / review.

Source URL: https://arxiv.org/abs/2606.10651
Paper authors (from arXiv): Kwai Keye Team, Bin Wen, Changyi Liu, Chengru Song, Chongling Rao, Guowang Zhang, Han Li, Haonan Fan, Hengrui Ju, Jiankang Chen, Jiapeng Chen, Jiawei Yuan, Kaixuan Yang, Kaiyu Jiang, Kun Gai, Lingzhi Zhou, Na Nie, Sen Na, Tianke Zhang, Tingting Gao, Xuanyu Zheng, Yulong Chen, Fan Yang, Haixuan Gao, Lele Yang, Mingqiao Liu, Muxi Diao, Qi Zhang, Qile Su, Wei Chen, Wentao Hong, Xingyu Lu, Yancheng Long, Yankai Yang, Yingxin Li, Yiyang Fan, Yu Xia, Yuzhe Chen, Ziliang Lai, Chuan Yi, Haonan Jia, Tianming Liang, Weixin Xu, Xiaoxiao Ma, Yang Tian, Yufei Han, Feng Han, Hang Li, Jing Wang, Jinghui Jia, Junmin Chen, Junyu Shi, Ruilin Zhang

Submitted by: github-actions[bot]

(Intake from human-submission issue #310.)

## Rejection rationale (2026-06-21)

Paper-stage review found one or more `fatal`-severity action items. The underlying research question is returned to the backlog so a fresh approach can be considered:

- **[527c80a99aee]** The claim that the model supports lossless 256 K token contexts via DeepSeek Sparse Attention (DSA) is cited to \cite{deepseek2025v32}, which describes a language model and does not provide evidence for multimodal DSA or 256 K context capability. Either provide a more appropriate citation that demonstrates this capability or qualify the statement.
- **[92076a8512d8]** The statement that the Vision Encoder uses a “native‑resolution SigLIP‑400M‑384‑14 backbone from Keye‑VL‑1.5 \cite{kwaikeye2025vl}” is not directly supported by the cited technical report, which does not detail this specific backbone. Add a citation that explicitly describes the SigLIP‑400M‑384‑14 model or adjust the claim.
- **[7b7192247c4c]** The description of the Language Decoder as “Qwen3‑30B‑A3B‑Thinking‑2507 \cite{qwen3}” lacks a supporting reference; the Qwen3 technical report does not mention this exact variant. Provide a citation to a source that defines this model or rephrase to avoid implying a specific, documented variant.
- **[8579c71fb6b7]** The claim of pre‑training on “≈ 1 T tokens” and “≈ 2 T tokens” across stages, as well as “500 B tokens from DataComp, LAION, CC12M, PD12M, COCO”, is not substantiated by the dataset citations (\cite{datacomp}, \cite{laion}, \cite{cc12m}, \cite{pd12m}, \cite{coco}). Those papers describe the datasets but do not report token counts. Either add a citation that quantifies the token usage or temper the claim.
- **[8850da0f9a17]** Performance improvement statements such as “>2× speedup over a baseline” for DSA optimizations and “20 % throughput gain” for ViT‑LM heterogeneous parallelism are presented without any experimental reference or benchmark citation. Include a table or citation to a performance study that validates these numbers.
- **[207e45b2e24f]** The evaluation tables claim state‑of‑the‑art results on several benchmarks (LongVideoBench, Video‑MME‑v2, TimeLens, etc.). While the benchmark papers are cited, the specific numbers for competing models (e.g., Qwen3.5‑35B) are not sourced. Provide citations or footnotes indicating where those comparative scores were obtained.
- **[9a59f165b849]** The description of Cross‑Modal Multi‑Teacher On‑Policy Distillation (MOPD) includes detailed algorithmic steps but no citation to prior work on similar distillation methods. If this is novel, state so explicitly; otherwise, cite relevant prior literature.
- **[af666f32b1c9]** The manuscript does not provide any source code, build scripts, or environment specifications required to reproduce the model training and evaluation.
- **[023f4d3d1645]** A public repository link with a clear, modular code layout (e.g., separate directories for model definition, data pipelines, training loops, inference utilities, and evaluation scripts) is missing.
- **[441f853eed58]** No test suite or validation scripts are included to verify the correctness of data preprocessing, model components (ViT, MoE, DSA), or benchmark evaluation pipelines.
- **[fc663dc702b1]** Dependency declarations (e.g., requirements.txt, environment.yml, or Dockerfile) are absent, preventing reproducibility of the software stack.
- **[91b89518e40f]** Detailed instructions for reproducing the 256 K token context experiments—including video I/O setup, DSA kernel compilation, and hyper‑parameter schedules—are not provided.
- **[1181842cb086]** Add an explicit data‑statement section (e.g., a “Data Card”) that lists each pre‑training corpus (DataComp, LAION, CC12M, PD12M, COCO) with its version, size, licensing terms, and any preprocessing steps. This should also describe how missing or corrupted samples are detected and handled.
- **[cfb648a27125]** Provide persistent, versioned URLs (DOI or archived arXiv links) for every bibliography entry that references an external dataset or model. For entries that currently lack a URL (e.g., \cite{qwen3}, \cite{qwen3.5}, \cite{internvl3}), add a stable link or DOI to avoid future link rot.
- **[ad86959bb731]** Include checksums (e.g., SHA‑256) or other fingerprinting for each external dataset used, and reference a public manifest (e.g., a JSON file in the repository) that records these hashes. This enables reproducible data acquisition and verification.
- **[7fd19cc11379]** State the licensing conditions under which the released model checkpoints can be used, and clarify whether the training data licenses (e.g., CC‑BY‑4.0 for CC12M) impose any downstream restrictions on model redistribution.
- **[bf1ade7fc785]** Add explicit axis labels and units to Figure 2 (Inference cost) – the current plot shows only a curve with no indication of what the y‑axis represents (e.g., $$/hour, latency) or the x‑axis scaling (tokens, seconds).
- **[5d309e0cec27]** Replace the default colormap in Figure 1 (Performance Comparison) with a color‑blind‑friendly palette and ensure that the legend uses distinct patterns or shapes for open‑source vs. closed‑source models.
- **[031470d82f86]** Provide concise alt‑text descriptions for all case‑study figures (Figures 4‑8) so that screen‑reader users can understand the content without seeing the images.
- **[b483da835103]** Increase the line‑weight and font size of axis tick labels in the PDF figures (e.g., keye_inference_cost.pdf) to guarantee legibility when printed at 80 % scale.
- **[ceaeb77d0912]** Ensure every figure is referenced in the main text before its first appearance; currently Figure 5 (dense caption example) is introduced only in the appendix.
- **[369f8fa89348]** Define every acronym at first use (e.g., MoE, DSA, MOPD, RL, KV, GQA, ViT‑LM, Top‑k, MQA, ACC, mIoU) or replace with a plain‑language description.
- **[3ea9edfc26e0]** Replace overly technical compound nouns such as “Cross‑Modal Multi‑Teacher On‑Policy Distillation” and “heterogeneous ViT‑LM parallelism” with simpler phrasing (e.g., “multi‑teacher distillation” and “mixed vision‑language parallelism”).
- **[14294fb429a8]** Add brief, non‑technical explanations for numeric hyper‑parameters and scaling factors (e.g., why k=2048, what 256 K token context means for a non‑expert reader).
- **[402fce216e5d]** Rewrite abstract and introduction sentences that bundle multiple buzzwords, e.g., replace “open‑source MoE multimodal foundation model (3 B active parameters) that supports lossless 256 K token contexts via DeepSeek Sparse Attention (DSA) integrated into a GQA‑based architecture” with a clearer statement of the model’s purpose and capability.
- **[38259eb0d2e9]** Clarify metric abbreviations in tables (e.g., ACC = accuracy, mIoU = mean Intersection‑over‑Union) either in table captions or a glossary.
- **[09eab3b26240]** The abstract and introduction claim the model provides *lossless* 256 K token contexts, but Section 3.3 describes a top‑k (k=2048) sparse attention that discards many token‑pair interactions. This contradicts the “lossless” claim. Revise the claim to acknowledge the approximate nature of the attention, or provide a theoretical/empirical justification that the top‑k selection does not lose information.
- **[47ff27d795d1]** The paper states the model achieves state‑of‑the‑art results on long‑video benchmarks while remaining competitive on coding and tool‑use tasks. However, on tool‑use benchmarks (e.g., BFCL‑V4, VitaBench) it is not the top performer. Clarify the criteria for “state‑of‑the‑art” versus “competitive” to avoid contradictory implications about superiority across all evaluated domains.
- **[4af62b4a0013]** The abstract and Section 1 claim “state‑of‑the‑art performance” on long‑video benchmarks, yet Table 1 shows that on several key metrics (e.g., MLVU accuracy, Video‑MME‑v2 non‑linear scores) competing models outperform Keye‑VL‑2.0. Revise the claim to reflect only the benchmarks where it truly leads, and add a discussion of where it falls short.
- **[0dc6d7933671]** The paper asserts “lossless 256 K token contexts via DeepSeek Sparse Attention” (Abstract, lines 1‑3) but provides no quantitative analysis of information loss (e.g., perplexity or retrieval fidelity) compared to dense attention. Include an ablation that measures degradation, or qualify the claim as “effectively maintains performance up to 256 K tokens.”
- **[93705759a2d2]** Section 3 describes a staged curriculum up to 2 T tokens of pre‑training data, yet the total compute budget, hardware requirements, and carbon cost are omitted. Add a clear limitation paragraph quantifying the resources needed for reproducibility.
- **[5b88a7f0a4e3]** The manuscript promotes “agentic collaboration across Code, Tool, and Search tasks” (Abstract) but only reports results on LiveCodeBench, OJBench, and a few tool benchmarks. No evaluation of search or multi‑turn planning is presented. Either provide such evaluations or temper the claim to match the presented evidence.
- **[663f808ac1fa]** Claims of “competitive on coding, tool‑use, OCR, and visual reasoning benchmarks” ignore cases where Keye‑VL‑2.0 is outperformed (e.g., BFCL‑V4 where Qwen3.5 scores higher). Add a balanced comparison and discuss why the model lags on those tasks.
- **[4b2171c7e9ac]** The paper does not discuss potential biases introduced by the massive multimodal pre‑training data (DataComp, LAION, CC12M, etc.). Include a limitations section addressing data quality, representation bias, and possible downstream harms.
- **[5b9aafde4cdb]** Add a dedicated safety and ethics section (≈1 page) that discusses potential dual‑use risks of the model’s agentic, code‑generation, and long‑video capabilities, and outlines concrete mitigation measures (e.g., usage policy, red‑team testing, content filters).
- **[e55a94b44cc2]** Provide a data‑privacy audit for the pre‑training corpus (DataComp, LAION, CC12M, PD12M, COCO) confirming that personal data were removed or consented, and cite any relevant IRB or data‑use approvals.
- **[836f14cc382c]** Include quantitative evaluation of harmful content generation (e.g., toxicity, disinformation, deep‑fake video synthesis) and report failure cases, especially for the agentic RL and tool‑use pipelines described in Section 4.3 and the multi‑domain service case (Fig 13).
- **[2bd9bb46925f]** Specify a responsible‑release plan (e.g., model‑card, licensing, access controls) and describe how downstream developers are required to enforce safety constraints when deploying the model for code or tool use.
- **[a06de2490a0b]** Clarify whether any human‑in‑the‑loop data (e.g., user profiles used in the multi‑domain service case) were collected with informed consent and IRB approval; if not, remove or anonymize such examples.
- **[d2af1ab95730]** The benchmark tables (e.g., Table 1, Table 2) report single-point scores without any indication of variance, confidence intervals, or number of evaluation runs. Add standard deviations or confidence intervals and describe how many random seeds were used.
- **[78e0fda77f82]** The paper does not describe the size or composition of the validation/test splits for the long‑video and agentic benchmarks (e.g., LongVideoBench, Video‑MME‑v2, LiveCodeBench). Provide exact sample counts and any filtering criteria.
- **[70baeb365aaf]** No ablation study isolates the contribution of each major component (DSA, MOPD, Context‑RL, Video‑RL). Include controlled experiments that remove or replace each module to quantify its impact.
- **[2550bc256815]** Statistical significance testing is absent when claiming state‑of‑the‑art performance over baselines. Perform appropriate tests (e.g., paired t‑test, bootstrap) to support claims of superiority.
- **[f64478a38565]** Potential p‑hacking risk: multiple benchmark rows are omitted ("... N rows omitted ...") and only the best‑performing numbers are shown. Provide the full result tables or a clear statement of selection criteria.
- **[d59043bacdb8]** The training data scale (e.g., "500 B tokens from DataComp, LAION, CC12M, PD12M, COCO") lacks precise token counts per modality and does not report data quality controls. Detail the token distribution and any filtering steps.
- **[5e47c7731e2d]** Reinforcement learning sections (Synthetic‑Data RL, General RL, Specialized RL) report percentage improvements (e.g., "temporal IoU by ≈1 %") without confidence intervals or statistical tests. Include variance measures and describe the evaluation protocol.
- **[1bf78587e593]** The inference cost analysis (Figure 2) presents cost reductions but does not specify the hardware configuration, batch sizes, or measurement methodology. Add a reproducible cost benchmarking protocol.
- **[a7abe224a29e]** The paper claims "no degradation of core reasoning" after multi‑task injection, yet no quantitative comparison to a pre‑injection baseline is shown. Provide a controlled comparison on core reasoning benchmarks.
- **[3bea507e85b2]** Add statistical reporting (e.g., mean ± std, confidence intervals) for all benchmark results in Tables \ref{tab:video_eval}, \ref{tab:code_agent_eval}, and \ref{tab:tool_use_eval}. Specify the number of evaluation runs, random seeds, and any data‑splitting strategy.
- **[e611d1658525]** Perform appropriate significance testing (e.g., paired t‑test, bootstrap) when claiming superiority over baselines such as Qwen3.5‑35B or InternVL3.5. Report p‑values or effect sizes.
- **[ab5de23d515c]** Address multiple‑comparison concerns: when evaluating on dozens of benchmarks, control the family‑wise error rate (e.g., Bonferroni or Holm correction) or clearly state that each benchmark is considered independently.
- **[1fc8a45608cd]** Provide a reproducibility checklist: list software versions, hardware configuration, and exact commands used for inference cost measurement (Figure \ref{fig:inference_cost}). Include scripts or seeds to enable independent replication.
- **[8d48b092b2e6]** Clarify handling of missing entries (marked “--”) in evaluation tables: explain whether the model was not evaluated, the benchmark was unavailable, or results were omitted for other reasons.
- **[28dd6906245d]** Replace all non‑standard heading commands such as `\subsubsubsection` with supported LaTeX levels (`\paragraph` or `\subparagraph`) or define a custom hierarchy, and ensure a consistent depth order (section → subsection → subsubsection → paragraph).
- **[a695d5ddc506]** Remove the duplicated “Introduction” and “Case Study” sections that appear both before and after the appendix; consolidate content to a single occurrence to avoid confusion.
- **[9ef8ae89d921]** Ensure each figure has a unique label; the teaser figure is labeled `\label{fig:teaser}` twice, which will cause cross‑reference collisions. Rename one of them (e.g., `fig:teaser_alt`).
- **[b7b89740e087]** After `\appendix`, use proper sectioning commands (`\section{Appendix}` or `\section*{Appendix}`) before lower‑level headings, rather than starting directly with `\subsubsubsection`.
- **[a4cdeb79aa26]** Verify that all tables include a `\centering` directive (some tables rely on the surrounding `\begin{center}` environment, which is deprecated) and that column specifications match the number of columns to avoid compilation warnings.
- **[7f9ef3786f7f]** Standardize citation formatting: multiple citations should be grouped with a single `\cite{...}` command (e.g., `\cite{ref1,ref2,ref3}`) and ensure a consistent bibliography style throughout the document.
- **[7ca942b03bcd]** Check line wrapping in the source file to keep lines under 80 characters where possible; long lines in tables and figure captions can hinder readability and version control diffs.
- **[8154307cbeac]** Several sentences contain overly long clauses and missing commas, which hampers readability (e.g., the abstract sentence starting with “We present Kwai Keye‑VL‑2.0‑30B‑A3B…”).
- **[e8dd708a4512]** Inconsistent use of hyphens and en‑dashes (e.g., “MoE multimodal foundation model (3 B active parameters)” vs. “DeepSeek Sparse Attention (DSA)”). Standardize punctuation.
- **[b8addf95ef2b]** Section headings sometimes lack parallel structure (e.g., “Model Architecture” uses bullet list, while “Pre‑Training” mixes narrative and tables). Re‑organize for uniform flow.
- **[5ae763ccec3e]** Figure and table captions are duplicated (the teaser figure appears twice with identical caption). Remove redundancy to avoid confusion.
- **[3a1d192fed10]** References to sections/tables use inconsistent labeling (e.g., “Sec.~\ref{stage_0}” vs. “Section 2”). Ensure consistent cross‑reference style.
- **[bd4336cca157]** The case study subsections use non‑standard headings like “Case I: Logical Constraint Solving” without clear hierarchy; consider using \\subsection or \\subsubsection consistently.
- **[e4259d85bd31]** Numerical values are sometimes presented without units or context (e.g., “20 % throughput gain”). Add clarifying units or explanations.
- **[8797b2dee32f]** The bibliography contains mixed citation styles and missing punctuation (e.g., missing periods after journal names). Standardize to a single bibliography style.
