---
action_items:
- id: f5b9263a3fe3
  severity: writing
  text: Define 'SFT' (Supervised Fine-Tuning) and 'CPT' (Continual Pre-Training) at
    their first occurrence in the text. Currently, 'CPT' appears in Section 2.1 without
    definition, and 'SFT' is used in Section 2.2 without prior expansion. Acronyms
    must be spelled out on first use to ensure accessibility for non-specialist readers.
- id: eeaa41574809
  severity: writing
  text: Replace the acronym 'OD' with 'origin-destination' in Section 5.1 (Task Definitions)
    and Section 5.2 (Evaluation Metrics). The term 'OD' is used repeatedly without
    definition, creating a barrier for readers unfamiliar with transit planning jargon.
- id: 3ebb4f2168ef
  severity: writing
  text: Define 'PPU' in Section 4.1 (Experimental Setup). The text states 'All training
    is conducted on Alibaba Cloud PPU accelerators' without explaining what PPU stands
    for, assuming specific hardware knowledge from the reader.
- id: 6a62bb3583d9
  severity: writing
  text: Replace 'SFT-only' with 'supervised fine-tuning-only' or define 'SFT' immediately
    before using the hyphenated term in Section 6.3 (Effect of Continual Pre-Training).
    The current usage assumes the reader has already memorized the acronym from earlier
    sections.
- id: 84794b308141
  severity: writing
  text: Clarify 'IoU' in Section 5.2 (Evaluation Metrics). While 'Intersection-over-Union'
    is spelled out, the acronym 'IoU' is introduced abruptly. Ensure the transition
    from full term to acronym is explicit (e.g., '...using Intersection-over-Union
    (IoU).').
artifact_hash: edae6ae2d895f06d190c806d301a85f463bbdd062907b9af82e2ca86a0aa3cf7
artifact_path: projects/PROJ-621-transitlm-a-large-scale-dataset-and-benc/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T22:50:16.558335Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript relies heavily on domain-specific acronyms and abbreviations that are not defined upon their first appearance, creating unnecessary friction for non-specialist readers. In Section 2.1, the term "Continual Pre-Training (CPT)" is used in the text before the acronym is formally introduced, and "SFT" appears in Section 2.2 without prior expansion. These acronyms are then used extensively throughout the paper (e.g., "CPT corpus," "SFT data," "SFT-only baseline"), forcing the reader to constantly infer their meaning.

Furthermore, the term "OD" is used repeatedly in Section 5.1 and 5.2 to denote "origin-destination" without ever being defined. This is a classic example of insider jargon that excludes general computer science or urban planning audiences. Similarly, "PPU" is mentioned in Section 4.1 as a hardware accelerator without explanation. The use of "IoU" in Section 5.2 is slightly better but still lacks a clear introductory sentence linking the full term to the acronym.

To improve accessibility, the authors should adopt a strict policy of spelling out every acronym at its first occurrence in the main text (not just in captions or footnotes) and then using the acronym thereafter. Terms like "OD" should be replaced with "origin-destination" or defined immediately. This will ensure the paper is readable by a broader audience beyond transit routing specialists.
