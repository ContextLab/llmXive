---
action_items:
- id: c1ede5658853
  severity: writing
  text: In Section 3.2 (Data Curation), the text states 'Sessions are generated via
    dual-model simulation with GPT-5.1... and Gemini-3-Pro'. These model versions
    appear to be future-dated or non-existent (current state-of-the-art is GPT-4o/Gemini
    1.5). This creates immediate confusion regarding the validity of the methodology.
    Please verify the model names or clarify if these are placeholders for future
    releases.
- id: dbb7f0032c62
  severity: writing
  text: 'The abstract claims ''removing evidence images drops two frontier LVLMs below
    2% accuracy on the 80.4% of questions whose evidence includes images.'' The phrasing
    ''on the 80.4% of questions'' is ambiguous. It is unclear if the 2% drop applies
    to the subset of image-essential questions or the entire benchmark. Rephrase to:
    ''...drops accuracy to below 2% on the subset of questions (80.4% of the total)
    that require visual evidence.'''
- id: 6441e6cfc7f6
  severity: writing
  text: 'In Section 3.1, the definition of ''Information Extraction (IE)'' lists ''Entity''
    and ''PrevInfo'' as subtypes but the sentence structure ''Entity requires two-hop
    chains... PrevInfo recalls visual details...'' lacks parallelism and clarity.
    Consider restructuring as a bulleted list or using consistent verb forms (e.g.,
    ''Entity: requires...; PrevInfo: recalls...'').'
- id: 4cd46efe78a7
  severity: writing
  text: Throughout the paper (e.g., Section 4.1, Appendix A), model names like 'GPT-5.4',
    'Gemini-3.1-Pro', and 'Kimi-K2.5' are used. Given the current date, these names
    are highly suspect and may be hallucinated or placeholder text. If these are real
    models, they must be cited with a specific release date or technical report. If
    they are placeholders, they must be replaced with actual existing models to ensure
    the paper is scientifically credible.
artifact_hash: 894b3a058a7c60576126fae0e86fbf0afb5e6919dad970b01a23558253a18ccf
artifact_path: projects/PROJ-578-https-arxiv-org-abs-2605-14906/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:47:23.986867Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_writing_quality
score: 0.0
verdict: minor_revision
---

The manuscript presents a comprehensive benchmark for multimodal long-term memory, but the writing quality is significantly compromised by the use of seemingly non-existent or future-dated model names (e.g., "GPT-5.4", "Gemini-3.1-Pro", "Kimi-K2.5"). While the instructions for this review lens focus on prose, the credibility of the scientific narrative is inextricably linked to the clarity and accuracy of these entity references. If these are placeholders, the paper is currently unreadable as a scientific contribution; if they are real, the lack of citation or context makes the text confusing.

Beyond the model nomenclature, there are issues with sentence clarity and precision. In the abstract, the phrase "drops two frontier LVLMs below 2% accuracy on the 80.4% of questions" is syntactically ambiguous. It is unclear whether the 2% figure applies to the specific subset of image-essential questions or the entire dataset. A more precise phrasing is required to avoid misinterpretation of the ablation study results.

Additionally, Section 3.1 suffers from a lack of parallel structure when defining the five memory abilities. The definitions for "Entity" and "PrevInfo" switch between noun phrases and verb phrases, disrupting the flow. The text states, "Entity requires two-hop chains... PrevInfo recalls visual details..." which should be standardized for better readability.

Finally, the introduction and related work sections rely heavily on citations to these same future-dated models without sufficient context. The writing assumes the reader is familiar with these specific versions, which is not the case for the current community. The authors must either provide clear citations for these models or revise the text to reflect the actual state of the art to ensure the paper is accessible and credible.
