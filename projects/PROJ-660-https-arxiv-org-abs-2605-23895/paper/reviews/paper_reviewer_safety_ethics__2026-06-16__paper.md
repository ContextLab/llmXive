---
action_items:
- id: 235807b81a73
  severity: science
  text: "Explicitly state that any new fMRI data collection (Section\u202F3.3 and\
    \ Appendix\u202FC) will be performed under a fully approved IRB protocol, describing\
    \ informed\u2011consent procedures, especially for stimuli containing human bodies,\
    \ faces, or potentially sensitive content."
- id: 0f39a89ffd5c
  severity: writing
  text: "Add a dedicated discussion of privacy and dual\u2011use considerations (e.g.,\
    \ potential for decoding personal visual experiences) and outline data\u2011handling\
    \ safeguards for the NSD data and any newly collected data."
- id: c6dc4d07e095
  severity: writing
  text: "Implement and describe a content\u2011filtering pipeline for generated and\
    \ edited images to prevent the inclusion of offensive, disturbing, or otherwise\
    \ inappropriate visual material in both the training set and any follow\u2011\
    up experiments."
artifact_hash: 3e7821bc4196322444417ea380054aced908f7d581b2fd2f7cbee1140a5fd1b0
artifact_path: projects/PROJ-660-https-arxiv-org-abs-2605-23895/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-16T10:18:37.176247Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript introduces **BrainCause**, a pipeline that leverages large language models, generative image models, and an image‑to‑fMRI encoder to identify visual‑concept representations in the human brain. From a safety‑and‑ethics standpoint the work raises several concerns that should be addressed before publication.

1. **Human‑subjects protections** – The core experiments rely on the publicly available Natural Scenes Dataset (NSD) (Section 3, Appendix C). While the NSD has already obtained IRB approval, the authors propose “follow‑up fMRI experiments” that generate novel stimulus sets (positive images, semantic negatives, counterfactual edits) (Sec. 3.1, Fig. 2). These stimuli can include human faces, body parts, and potentially sensitive scenes. The manuscript currently lacks any statement that new data collection will be covered by an updated IRB protocol, nor does it describe how participants will be informed about the nature of the generated images, how discomfort will be monitored, or how withdrawal will be handled. Adding this information is essential to ensure compliance with standard human‑subjects ethics (e.g., the Common Rule) and to protect participants from exposure to distressing content.

2. **Privacy and dual‑use risks** – Mapping visual‑concept representations in the brain, even for “public” concepts, may enable more invasive decoding of personal visual experiences if combined with more powerful encoders. The authors should explicitly discuss the privacy implications of releasing voxel‑wise maps that could be linked to individual participants, and outline safeguards (e.g., de‑identification, limited data‑sharing agreements). A brief dual‑use analysis (e.g., potential misuse for covert surveillance or targeted advertising) would demonstrate awareness of broader societal impacts and align the paper with emerging AI‑ethics guidelines.

3. **Content moderation of generated stimuli** – The pipeline automatically generates thousands of images per concept using FLUX.2 and edits them via language‑model‑driven instructions (Sec. 3.1, Fig. 2). Without a robust filtering step, there is a risk that generated images could contain nudity, violence, or culturally insensitive depictions, especially for concepts such as “human hands” or “human body”. The current verification step uses a vision‑language model (Qwen3‑VL‑8B) but the manuscript does not report any quantitative evaluation of false‑positive or false‑negative detection rates for inappropriate content. Adding a description of a content‑filtering pipeline (e.g., explicit blacklist, human review) and reporting its efficacy would mitigate the risk of inadvertently exposing participants or readers to harmful material.

4. **Data handling and reproducibility** – The authors use the NSD dataset, which contains voxel‑wise activation vectors. Even though the data are publicly released, it remains individually identifiable at a fine‑grained level. The manuscript should clarify storage, access controls, and the intended sharing of any derived representations (e.g., the candidate voxel sets). This is especially important if the authors plan to release the “BrainCause” code and associated region masks, as these could be combined with other datasets to increase re‑identification risk.

Overall, the scientific contribution is solid, but the manuscript needs clearer ethical safeguards regarding new human‑subjects data, privacy considerations, and the handling of generated visual content. Addressing the three action items above will bring the work into compliance with standard neuroscience and AI‑ethics best practices.
