---
action_items:
- id: 369f8fa89348
  severity: writing
  text: "Define every acronym at first use (e.g., MoE, DSA, MOPD, RL, KV, GQA, ViT\u2011\
    LM, Top\u2011k, MQA, ACC, mIoU) or replace with a plain\u2011language description."
- id: 3ea9edfc26e0
  severity: writing
  text: "Replace overly technical compound nouns such as \u201CCross\u2011Modal Multi\u2011\
    Teacher On\u2011Policy Distillation\u201D and \u201Cheterogeneous ViT\u2011LM\
    \ parallelism\u201D with simpler phrasing (e.g., \u201Cmulti\u2011teacher distillation\u201D\
    \ and \u201Cmixed vision\u2011language parallelism\u201D)."
- id: 14294fb429a8
  severity: writing
  text: "Add brief, non\u2011technical explanations for numeric hyper\u2011parameters\
    \ and scaling factors (e.g., why k=2048, what 256\u202FK token context means for\
    \ a non\u2011expert reader)."
- id: 402fce216e5d
  severity: writing
  text: "Rewrite abstract and introduction sentences that bundle multiple buzzwords,\
    \ e.g., replace \u201Copen\u2011source MoE multimodal foundation model (3\u202F\
    B active parameters) that supports lossless 256\u202FK token contexts via DeepSeek\
    \ Sparse Attention (DSA) integrated into a GQA\u2011based architecture\u201D with\
    \ a clearer statement of the model\u2019s purpose and capability."
- id: 38259eb0d2e9
  severity: writing
  text: "Clarify metric abbreviations in tables (e.g., ACC\u202F=\u202Faccuracy, mIoU\u202F\
    =\u202Fmean Intersection\u2011over\u2011Union) either in table captions or a glossary."
artifact_hash: 5db0f3878ddf869f97ae5b85f5c21e6bee16133e4d0bee899b71eabf9aaf1f3a
artifact_path: projects/PROJ-692-kwai-keye-vl-2-0-technical-report/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-21T09:53:58.872948Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript is densely packed with domain‑specific jargon, acronyms, and compound technical terms that significantly hinder readability for any audience beyond specialists in multimodal large‑language models. Below are concrete examples and suggestions for each major section.

**Abstract (lines 1‑5).** The sentence “We present Kwai Keye‑VL‑2.0‑30B‑A3B, an open‑source MoE multimodal foundation model (3 B active parameters) that supports lossless 256 K token contexts via DeepSeek Sparse Attention (DSA) integrated into a GQA‑based architecture” contains at least six undefined abbreviations (MoE, DSA, GQA) and a cascade of buzzwords (“open‑source”, “foundation model”, “lossless”). A non‑expert reader would benefit from a plain‑language rewrite such as: “We introduce Keye‑VL‑2.0, a 30‑billion‑parameter multimodal model that can process very long inputs (up to 256 K tokens) by using a sparse attention technique called DeepSeek.” Define each acronym the first time it appears.

**Model Architecture (Section 2).** Items like “Vision Encoder (ViT)”, “Language Decoder (LLM)”, “Sparse Attention Module”, “Lightning Indexer (MQA‑style)”, and “GQA Sparse Aggregation” are introduced without any lay explanation. Replace “Vision Encoder (ViT)” with “image encoder (a Vision Transformer)”, and similarly expand “LLM” to “large language model”. The term “Lightning Indexer” is a proprietary name; consider describing its function (“a fast index that selects the most relevant tokens”) rather than relying on the brand name.

**Training Stages (Section 3).** The stage headings (Stage 0, Stage 1, etc.) are fine, but the descriptions are littered with shorthand such as “OCR”, “STEM”, “VCap”, “GUI”, “e‑commerce”, and “Chinese translation” without context. Briefly state why each data type is added (e.g., “Stage 2 adds optical‑character‑recognition data to improve reading of text in images”). Also, the phrase “Multi‑Task Capability Injection” is opaque; a simpler phrase like “adding new abilities” would suffice.

**Efficient Training and Inference Infrastructure (Section 5).** Phrases such as “ViT‑LM heterogeneous parallelism”, “DSA Optimizations”, “FlashInfer”, “TileLang”, “Deterministic Top‑k (flashinfer.topk)”, and “Chunk ViT” are introduced without definition. Provide a one‑sentence description for each (e.g., “FlashInfer is a library that speeds up attention calculations”). The repeated use of “> 2× speedup” and “> 5× speedup” could be clarified by stating the baseline (e.g., “compared to standard dense attention”).

**Evaluation Tables (Section 6).** Table 1 and Table 2 use metric abbreviations (ACC, mIoU) and benchmark names (LongVideoBench, Video‑MME‑v2, TimeLens) without explanation. Add a footnote or caption text that defines each metric and gives a brief description of the benchmark’s focus. This will help readers unfamiliar with the video‑understanding community.

**Case Studies (Appendix).** The case prompts and responses are valuable but are presented with dense technical language (“Cross‑Domain Order Execution”, “Agentic RL”, “Partial‑rollout caching”). Consider adding a short introductory paragraph that explains the purpose of each case in plain terms.

**General Writing Style.** Throughout the paper, long compound nouns (e.g., “Cross‑Modal Multi‑Teacher On‑Policy Distillation”, “Context‑RL”, “Video‑RL”, “Agentic Collaboration”) are used without breaking them into digestible pieces. Splitting them into two sentences or using simpler synonyms will improve flow. Also, avoid excessive numeric detail in the main text (e.g., “k=2048”, “top‑k=2048”) unless it is essential for understanding; such specifics belong in an appendix or implementation section.

By systematically defining acronyms, simplifying compound terms, and providing brief explanatory clauses for technical concepts, the paper will become far more accessible while retaining its technical contributions. This set of revisions is purely editorial and does not require any new experiments or data.
