---
action_items:
- id: 20dc5d3faa57
  severity: fatal
  text: The paper states the evaluation benchmark includes '1,500 real-world recordings
    collected from internet sources and 16 human participants' (Section 3.3) but lacks
    explicit details on IRB approval, informed consent procedures, or data privacy
    safeguards for these participants. This is a critical ethical gap for human-subject
    research.
- id: 785ab785ff67
  severity: science
  text: The dataset construction relies on 'clean speech from LibriSpeech, Common
    Voice, WenetSpeech, and AISHELL-1' (Section 3.2). The authors must explicitly
    confirm that the licensing terms of these source datasets permit the creation
    of a new, derivative synthetic dataset ('Voices-in-the-Wild-2M') and its public
    release, including any restrictions on commercial use or redistribution.
- id: b92a3c3cecfb
  severity: writing
  text: The methodology involves generating '54 physically plausible compound scenarios'
    including 'electronic distortion' and 'transmission dropout' (Section 3.2). While
    intended for robustness, the authors should briefly discuss potential dual-use
    risks, such as the possibility of these simulation techniques being adapted to
    generate adversarial audio attacks or deepfake audio that evades detection systems.
artifact_hash: b76830428db6f31ab0213200b5916231003e882ec498765fb220acf8020a5333
artifact_path: projects/PROJ-615-mega-asr-towards-in-the-wild-2-speech-re/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T03:54:07.769475Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The paper presents a significant technical contribution to robust ASR but raises several safety and ethics concerns that require clarification before acceptance.

First, regarding human subjects, Section 3.3 ("Voices-in-the-wild-Bench") explicitly mentions the collection of "1,500 real-world recordings... from 16 human participants." However, the manuscript contains no mention of Institutional Review Board (IRB) approval, ethical oversight, or the specific informed consent process used for these participants. Given that these recordings are part of a public benchmark, the authors must provide evidence of ethical compliance, including how participant privacy was protected and whether consent covered the specific use of their voice data for training and evaluating AI models. Without this, the inclusion of human data is a fatal ethical oversight.

Second, the dataset construction (Section 3.2) aggregates clean speech from multiple public sources (LibriSpeech, Common Voice, etc.) to create a new, large-scale synthetic dataset. The authors must explicitly address the licensing compatibility of these source materials. Specifically, they need to confirm that the terms of service and licenses of the source datasets permit the creation of a derivative work and its subsequent public release. Ambiguity here could lead to copyright infringement or license violation, particularly if the source data has restrictions on commercial use or redistribution.

Finally, while the paper focuses on improving robustness, the techniques described—specifically the simulation of "electronic distortion" and "transmission dropout" to create adversarial-like conditions—carry potential dual-use risks. The authors should include a brief discussion in the "Limitations" or "Ethical Considerations" section acknowledging that these simulation methods could theoretically be repurposed to generate adversarial audio examples designed to bypass ASR security filters or create undetectable deepfakes. A proactive statement on the intended defensive use of this technology is recommended.
