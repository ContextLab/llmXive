---
action_items:
- id: 3e072ef64eb9
  severity: writing
  text: The claim of 'real-time' at 23.8 FPS (Abstract, Intro) is misleading without
    explicit context. 23.8 FPS is below standard 30 FPS video. Clarify if 'real-time'
    refers to streaming latency or throughput, and qualify the claim to avoid over-extrapolation.
- id: 2a994dcfae9c
  severity: science
  text: The '30-180x faster' claim (Abstract) compares streaming FPS to batch FPS,
    which is asymmetric. Clarify if this speedup refers to time-to-first-frame or
    total generation time to ensure the magnitude is scientifically accurate.
- id: 2e6876fecf9a
  severity: science
  text: The claim of 'consistent long-video extrapolation' (Abstract) lacks quantitative
    metrics for drift over extended sequences. Provide quantitative evidence for long-form
    consistency or temper the claim to reflect only tested lengths.
artifact_hash: 8ac732f80d31fee19845b13e35eb49deeae5414cb6cb993b15f1b25017de2aa1
artifact_path: projects/PROJ-598-https-arxiv-org-abs-2605-15824/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:59:56.937557Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several strong claims regarding "real-time" performance and "consistent long-video extrapolation" that require tighter qualification to align with the presented data.

First, the repeated assertion of "real-time" generation at 23.8 FPS (Abstract, Section 1, Section 4) risks over-claiming. While 23.8 FPS is a high frame rate, it falls short of the standard 30 FPS often associated with "real-time" video playback. More critically, the term "real-time" in interactive systems usually refers to low latency (time-to-first-token/frame) rather than just throughput. The paper mentions the H200 GPU and 720p resolution in passing, but the headline claim of "real-time" without these qualifiers could mislead readers into expecting 30+ FPS or lower latency than what is achieved. The authors should clarify whether "real-time" refers to the streaming nature (interactive switching) or the raw throughput, and consider qualifying the claim (e.g., "interactive-speed" or "near real-time") to avoid over-extrapolation.

Second, the claim of being "30-180x faster" (Abstract) relies on comparing the streaming FPS of the proposed method against the batch FPS of bidirectional baselines. While the numerical difference is large, the comparison is methodologically asymmetric. Bidirectional models generate the entire video in parallel (or near-parallel) steps, whereas the proposed method generates autoregressively. The total wall-clock time to generate a fixed-length video (e.g., 81 frames) might not differ by 180x if the bidirectional model's steps are highly parallelized. The paper should explicitly state whether this speedup refers to "time-to-first-frame" (latency) or "total generation time" to ensure the magnitude of the claim is supported by the experimental setup.

Finally, the claim of "consistent long-video extrapolation" (Abstract, Conclusion) is primarily supported by qualitative visualizations (Figures 5, 10, 11) and a short ablation on 165 frames (Table 2). There is no quantitative metric provided for identity or garment consistency over extended sequences (e.g., >200 frames) to substantiate the claim of "consistent" extrapolation. Without quantitative evidence of drift suppression over longer horizons, the claim of robust long-video consistency is an overreach of the current experimental evidence. The authors should either provide quantitative long-form metrics or temper the claim to reflect the specific lengths tested.
