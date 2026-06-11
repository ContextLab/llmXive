---
action_items:
- id: 8ecce37a9f1f
  severity: science
  text: Add IRB/IACUC approval statement for the 16 human participants mentioned in
    Section 3.3.
- id: 5389357b428c
  severity: writing
  text: Clarify consent and privacy protocols for the 1,500 internet-sourced recordings
    in Voices-in-the-wild-Bench.
- id: '710659513650'
  severity: writing
  text: Include a discussion on dual-use risks (e.g., surveillance) of robust ASR
    in noisy environments.
- id: 5bbe4f595e7f
  severity: science
  text: Verify license compatibility for the combined Voices-in-the-wild-2M dataset.
artifact_hash: b76830428db6f31ab0213200b5916231003e882ec498765fb220acf8020a5333
artifact_path: projects/PROJ-615-mega-asr-towards-in-the-wild-2-speech-re/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-11T02:15:52.169668Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

This review focuses on safety and ethics considerations. While the technical contribution is significant, there are critical gaps in the ethical framework regarding data collection and potential misuse.

First, Section 3.3 ("Voices-in-the-wild-Bench") states that the benchmark includes "1,500 real-world recordings collected from internet sources and 16 human participants." However, the manuscript lacks an Ethics Statement or IRB/IACUC approval reference. For the 16 human participants, standard research ethics require informed consent and institutional review board approval, which is not mentioned. For the internet-sourced recordings, the paper does not clarify how speaker consent was obtained or how personally identifiable information (PII) was handled. Collecting and publishing audio from the internet without explicit consent raises significant privacy concerns and may violate terms of service of the source platforms.

Second, the paper introduces a highly robust ASR system capable of transcribing speech in severe noise conditions (e.g., NOIZEUS 0dB). While beneficial for accessibility, this capability has dual-use risks. Improved robustness facilitates surveillance in adversarial environments, potentially enabling unauthorized transcription of private conversations in public spaces. The manuscript does not include a discussion on these risks or mitigation strategies (e.g., watermarking, access controls).

Third, the new dataset `Voices-in-the-wild-2M` combines multiple existing datasets (LibriSpeech, Common Voice, etc.). The paper should explicitly confirm license compatibility (e.g., CC-BY vs. non-commercial restrictions) to ensure the new dataset does not violate source licenses.

Finally, there is no discussion of bias or fairness regarding the speakers in the new dataset. Given the focus on English and Mandarin, the paper should address demographic representation and potential performance disparities across accents or dialects. Addressing these issues is necessary to ensure the research adheres to responsible AI practices.
