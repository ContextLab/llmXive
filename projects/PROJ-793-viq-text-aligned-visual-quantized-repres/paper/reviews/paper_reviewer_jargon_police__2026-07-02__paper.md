---
action_items:
- id: c194111bcd06
  severity: writing
  text: Define 'proximal representation' at first use in Section 3.2. The term is
    introduced as a 'regularization function' but lacks a plain-English explanation
    of what 'proximal' implies in this specific context for non-specialists.
- id: a68e7d42a7eb
  severity: writing
  text: Replace the acronym 'VQ' with 'vector quantization' on its first occurrence
    in Section 3.2 ('Since our vector quantization (VQ) implementation...'). While
    common in the field, the paper targets a broader audience and should define it
    explicitly upon first use.
- id: 352282d9138a
  severity: writing
  text: Clarify the term 'native resolution' in Section 3.1. The phrase is used repeatedly
    to describe input handling, but the text does not explicitly define what constitutes
    'native' versus 'fixed' or 'resized' resolution for a general reader.
- id: 64d8883725c1
  severity: writing
  text: Define 'RoPE' (Rotary Position Embedding) at first use in Section 3.2. The
    text introduces '2D rotary position embedding (RoPE)' but assumes the reader knows
    the acronym; spell it out fully before using the abbreviation.
- id: 7726b99653a4
  severity: writing
  text: Replace the jargon-heavy phrase 'optimization-free' in Section 3.2 with a
    clearer description, such as 'does not require learning a codebook,' to ensure
    non-specialist readers understand the distinction from other quantization methods.
artifact_hash: b0d13f79598805d86a50b3ae742d6ff735642238ad128fe0a6c96ca6ef0ec5e0
artifact_path: projects/PROJ-793-viq-text-aligned-visual-quantized-repres/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T21:09:45.226757Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript relies heavily on specialized terminology that may alienate readers outside the immediate subfield of discrete visual representation learning. While the technical depth is appropriate for the target venue, the "jargon police" lens identifies several instances where plain language could improve accessibility without sacrificing precision.

First, the term **"proximal representation"** (Section 3.2, Paragraph "Proximal Representation") is introduced as a core contribution but is never defined in plain English. The text describes it as a "regularization function" that projects features onto a hypercube, but the word "proximal" itself carries specific mathematical connotations (e.g., proximal operators in optimization) that are not explained. A non-specialist reader is left guessing whether this refers to proximity in feature space, optimization steps, or something else. The authors should add a brief clause explaining the intuition, e.g., "a strategy that keeps features close to a constrained boundary."

Second, the acronym **"VQ"** (Vector Quantization) is used frequently (e.g., Section 3.2, "Since our vector quantization (VQ) implementation...") but is only defined in the context of the sentence where it appears. While standard in computer vision, the paper's abstract and introduction discuss "discrete representations" generally. To ensure clarity for a broader audience, "vector quantization" should be spelled out fully at the very first mention in the main text, not just in the method section.

Third, the phrase **"native resolution"** (Section 3.1) is used as a key selling point but lacks a clear definition. Does it mean the original pixel dimensions of the image file? The resolution at which the image was captured? The text contrasts it with "fixed input size" but does not explicitly define the operational meaning of "native" for the reader. A simple clarification, such as "the original pixel dimensions of the input image," would suffice.

Finally, the term **"optimization-free"** (Section 3.2) is used to describe the FSQ method. While technically accurate in the context of not learning a codebook, it is jargon that might confuse readers unfamiliar with the training dynamics of VQ-VAEs. Replacing this with "does not require learning a codebook" or "avoids codebook optimization" would be more transparent.

These changes are minor edits that significantly lower the barrier to entry for readers from adjacent fields (e.g., NLP or general ML) without altering the scientific content.
