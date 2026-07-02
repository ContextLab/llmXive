---
action_items:
- id: 848415a5516e
  severity: writing
  text: The manuscript exhibits a moderate overuse of domain-specific acronyms and
    undefined abbreviations that hinder accessibility for non-specialist readers.
    While the core concepts are sound, the writing frequently assumes the reader possesses
    prior knowledge of specific method names and metric abbreviations. First, the
    primary method name, MIGA, is introduced in the caption of Figure 1 and the text
    of Section 3 without being explicitly defined in the Introduction. The acronym
    appears before the ful
artifact_hash: 2fc45fd89cfd8c3cc27102ad20713af6a66d4f721af1c258a0cd318f7ea682b3
artifact_path: projects/PROJ-614-enhancing-train-free-infinite-frame-gene/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T14:35:50.060549Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript exhibits a moderate overuse of domain-specific acronyms and undefined abbreviations that hinder accessibility for non-specialist readers. While the core concepts are sound, the writing frequently assumes the reader possesses prior knowledge of specific method names and metric abbreviations.

First, the primary method name, **MIGA**, is introduced in the caption of Figure 1 and the text of Section 3 without being explicitly defined in the Introduction. The acronym appears before the full name "MIGA" (which seems to be the method name itself, but the text treats it as an acronym without expansion) or a clear definition of what the letters stand for. If "MIGA" is the name, it should be introduced as "We propose MIGA (Method for Infinite-Frame Generation and Alignment, or similar)" or simply "We propose MIGA" if it is a proper noun, but currently, it feels like an undefined acronym. *Correction*: Upon closer inspection, the text uses "MIGA" as a proper noun but never defines what the letters stand for. If it is an acronym, it must be defined. If it is a name, it should be treated as such, but the lack of definition is jarring.

Second, **Table 2** (NarrLV results) relies heavily on the undefined acronym **TNA** (Text-Number-Alignment? Temporal-Noise-Alignment?). The columns are labeled "TNA=2", "TNA=3", etc., with no explanation in the table caption or the surrounding text. This is a significant barrier to understanding the experimental setup.

Third, the results tables (**Table 1**, **Table 3**, **Table 4**) consistently use the abbreviations **S.C.**, **B.C.**, **M.S.**, **T.F.**, and **O.S.** without a legend. While these are defined in the caption of Figure 3, a reader scanning the tables in isolation (or the PDF without scrolling) cannot interpret the data. Standard practice requires defining these in the table caption or the main text immediately preceding the table.

Fourth, specific technical terms like **UniPC** (Section 4.1) and **MMDiT** (Appendix A.2) are used without expansion. While "UniPC" is a known sampler, "MMDiT" is a specific architecture name that should be expanded (e.g., "Multimodal Diffusion Transformer") upon first use to ensure clarity for a broader audience.

Finally, the term **TTS** (Test-Time-Scaling) is used in Appendix A.3. While the expansion is provided, the acronym "TTS" is overwhelmingly associated with "Text-to-Speech" in the broader AI community. Using it for "Test-Time-Scaling" without a strong contextual warning or alternative phrasing risks confusion.

To improve accessibility, the authors should define all acronyms at their first occurrence in the main text, expand metric abbreviations in table captions, and ensure that method names like MIGA are clearly introduced.
