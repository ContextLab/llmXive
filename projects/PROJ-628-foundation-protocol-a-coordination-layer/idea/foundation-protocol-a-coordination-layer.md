---
field: computer science
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/237
paper_authors:
  - Bang Liu
  - Yongfeng Gu
  - Jiayi Zhang
  - Zhaoyang Yu
  - Sirui Hong
  - Maojia Song
  - Xiaoqiang Wang
  - Mingyi Deng
  - Zijie Zhuang
  - Ronghao Wang
  - Mingzhe Cao
  - Yutong Zhu
  - Xingjian Li
  - Yifan Wu
  - Jianhao Ruan
  - Yiran Peng
  - Shuangrui Chen
  - Jinlin Wang
  - Yizhang Lin
  - Dongjie Zhang
  - Dekun Wu
  - Chen Ma
  - Lizi Liao
  - Han Yu
  - Jian Pei
  - Heng Ji
  - Qiang Yang
  - Yuyu Luo
  - Chenglin Wu
---

# Foundation Protocol: A Coordination Layer for Agentic Society

A paper was submitted via the website for consideration / review.

Source URL: https://arxiv.org/abs/2605.23218
Paper authors (from arXiv): Bang Liu, Yongfeng Gu, Jiayi Zhang, Zhaoyang Yu, Sirui Hong, Maojia Song, Xiaoqiang Wang, Mingyi Deng, Zijie Zhuang, Ronghao Wang, Mingzhe Cao, Yutong Zhu, Xingjian Li, Yifan Wu, Jianhao Ruan, Yiran Peng, Shuangrui Chen, Jinlin Wang, Yizhang Lin, Dongjie Zhang, Dekun Wu, Chen Ma, Lizi Liao, Han Yu, Jian Pei, Heng Ji, Qiang Yang, Yuyu Luo, Chenglin Wu

Submitted by: github-actions[bot]

(Intake from human-submission issue #237.)

## Rejection rationale (2026-06-20)

Paper-stage review found one or more `fatal`-severity action items. The underlying research question is returned to the backlog so a fresh approach can be considered:

- **[012ef585272c]** The manuscript makes several conceptual claims (e.g., the need for a “common substrate” for agents and that agents “provide reusable cognitive units”) without any supporting citation. Add appropriate references to prior work or surveys that discuss the lack of a coordination layer for agentic systems.
- **[6fc6506bcffe]** The citation key `schwab2016fourth` is used in the text, but the bibliography entry lists the year as 2017. Align the citation key/year with the bibliography to avoid confusion.
- **[e9b8931cff7c]** The statement that “Microsoft's security research team describes self‑hosted agent runtimes as untrusted code execution with durable privileges” is attributed to `microsoft_openclaw_security`. Verify that the cited blog post actually uses the phrase “self‑hosted agent runtimes” and discusses durable privileges; if not, rephrase the claim to match the source.
- **[73d8052dd590]** The manuscript references a reference implementation (GitHub repos) but does not include any concrete source files, module structure, or build scripts in the submission. Provide a minimal, self‑contained code snapshot (e.g., a `src/` directory with clear package layout) so reviewers can assess readability, modularity, and test coverage.
- **[05e5d2b31931]** Add a comprehensive `README.md` that documents required dependencies, installation steps (including Python version, virtual‑env setup, and TypeScript build for the web UI), and how to run the full stack from scratch. This is essential for reproducibility.
- **[9c6ba409a754]** Include an automated test suite (unit and integration tests) with instructions to execute `pytest` (or equivalent) and `npm test`. Tests should cover core protocol primitives (entity handling, envelope signing, checkpoint pipeline) and at least one bridge (e.g., the MCP bridge).
- **[9d513ac11929]** Ensure that all external dependencies are pinned (e.g., via `requirements.txt` and `package-lock.json`) and that the repository uses a lockfile to guarantee deterministic builds. List any non‑Python runtime requirements (e.g., Node.js version) explicitly.
- **[47314b195c35]** Provide a short script or Makefile target that builds the PDF from the LaTeX sources and runs the code‑quality checks (linting, type checking). This demonstrates end‑to‑end reproducibility of both the paper and the software artifact.
- **[eeb0a68596ec]** Add an explicit license declaration (e.g., CC-BY or MIT) to main.tex to clarify manuscript provenance and reuse rights.
- **[0421f55e1646]** Pin all GitHub repository links in the Appendix and bibliography to specific commit hashes or version tags to prevent link rot and ensure reproducibility.
- **[e17e16f042ec]** Correct bibliography access dates (currently 2026) to reflect actual review time or explain the temporal context to avoid provenance confusion.
- **[a80cbbb0d5fa]** Provide stable, machine-readable schema references (e.g., JSON Schema URLs) for the FP vocabulary objects described in Table 1.
- **[9b2b433f956c]** Figures lack alt text or description attributes for accessibility compliance. Add \alttext or equivalent metadata for figures/FP.pdf and figures/web-evolve.pdf.
- **[d836ffaa3053]** Figure~\ref{fig:fp-arch} caption is descriptive but does not explain the visual encoding (what do colors, shapes, arrows represent?). Add a brief visual legend in caption or nearby text.
- **[74a24bae589d]** The web-evolution figure (8.3MB PDF) is unusually large; verify it is not embedding unnecessary high-resolution assets that will bloat print output.
- **[70030960a253]** Define or replace 'Agentic Society' with 'autonomous agent ecosystem' for broader accessibility.
- **[5b0e8f14b561]** Replace 'first-class concerns' with 'core features' and 'graph-first' with 'graph-based' in Abstract.
- **[fde02cd57659]** Define acronyms (MCP, A2A, DIDComm) at first mention in Introduction rather than assuming specialist knowledge.
- **[d4c217817b55]** Replace 'behavioral closure' and 'evidence spine' with 'complete behavior set' and 'audit trail' in Section 1.3.
- **[d28158879be3]** Replace 'flag-day migration' and 'prompt stuffing' with 'sudden migration' and 'excessive prompt content' in Sections 1.3 and 2.6.
- **[3029d33b9a40]** The 'intelligence density' argument (Section 1.1, Table 1) assumes increased coordination requires a new protocol layer without establishing the causal mechanism. The historical progression does not logically entail that agentic systems need FP specifically—this premise requires explicit justification rather than rhetorical framing.
- **[05dc9ddb01a8]** The protocol fragmentation claim (Section 1, Table 2) asserts semantic drift and integration costs across MCP/A2A/DIDComm without empirical evidence. No comparative data or case studies demonstrate actual incompatibility. This central premise needs supporting analysis to be logically sound.
- **[050cad2ffb65]** FP claims to be 'transport-agnostic' (Section 1.3, 2.3) while the reference implementation uses a tree topology (Appendix 3.3). The paper states 'tree model is not a hard architectural constraint' but provides no evidence that the implementation supports alternative topologies without modification. This creates internal tension between claimed flexibility and actual design.
- **[6af2e582f05b]** The economic primitives section (Section 1.3, Appendix 3.4) asserts verification becomes 'scarce' and FP addresses this, but provides no economic model or data showing FP's specific primitives solve the problem better than existing solutions (e.g., UCP). The causal claim is asserted without demonstration.
- **[d9ed5fffe2e9]** Security claims (Section 2.4, Appendix 3.5) describe standard cryptographic practices (signatures, encryption, hash chains) as novel 'protocol-level oversight.' The logical leap from 'we use cryptography' to 'this makes safety a protocol concern' requires explicit mechanistic explanation of what FP-specific mechanisms enable beyond existing practice.
- **[e7f74595a205]** Claims about protocol effectiveness (e.g., 'FP is designed to make autonomous agency composable while keeping accountability non-negotiable' in abstract) lack empirical validation. Add limitations section acknowledging untested claims.
- **[452d4b3a92f4]** The paper states FP 'unifies heterogeneous entities' and 'supports native multi-party organization' but provides no comparative benchmarks against MCP, A2A, or DIDComm. Either add evaluation or soften claims to 'proposed' rather than 'demonstrated.'
- **[36c5661098ed]** Abstract claims FP enables 'a human–AI society that is open, pluralistic, and governable' without evidence this is achievable through protocol design alone. This is a societal claim beyond technical scope.
- **[e3eb9d715086]** Reference implementation appendix describes 'working FP stack' but omits implementation details and admits code is 'non-normative.' This creates gap between claimed functionality and demonstrated capability.
- **[c0af2abc0d58]** The manuscript lacks a concrete threat model and safety analysis for the Foundation Protocol, leaving dual‑use risks (e.g., automated malicious coordination, fraud, or large‑scale credential abuse) unaddressed.
- **[0aaf5d9996f6]** No discussion is provided on how personal data or human‑generated content exchanged within sessions is protected under privacy regulations (e.g., GDPR, CCPA) or how consent is obtained from human participants.
- **[cb1db7654eaf]** The paper does not describe mechanisms for revocation, emergency shutdown, or sandboxing of compromised entities, which are essential for preventing cascade failures in an open agentic society.
- **[67ed2fc25c47]** Potential conflicts of interest arising from Amazon Research Award funding are not disclosed in the main text, nor is there an assessment of how commercial incentives might bias protocol design toward proprietary control.
- **[ef02b5463307]** The reference implementation’s security guarantees (e.g., envelope signing, encryption) are described only at a high level without formal verification, algorithm agility analysis, or independent security audit results.
- **[041086f9580e]** Human‑in‑the‑loop approval is mentioned but the paper does not specify how consent dialogs are presented, logged, or audited, raising concerns about informed consent and accountability for decisions made by agents on behalf of users.
- **[23b6d4595b4d]** The central claims regarding reduced integration overhead and improved governance lack empirical support. Include a comparative study measuring token usage, latency, or integration time against baselines (e.g., MCP, A2A).
- **[57de922f07da]** The 'AI company' scenario (Section 3.2) is illustrative, not experimental. It does not provide data on failure rates, audit success, or economic settlement times. Convert this into a case study with measurable metrics.
- **[4c7e9a32e8cd]** The reference implementation (Appendix) describes architecture but lacks performance benchmarks (throughput, concurrency). Provide quantitative data to validate scalability claims.
- **[fbd93014d82a]** The paper makes empirical claims about FP's benefits (e.g., token overhead reduction, safety improvements, scalability) without statistical evidence. Future empirical evaluation should include sample sizes, confidence intervals, and hypothesis tests.
- **[b8cacd4c7e46]** Protocol comparisons in Table 1 (main.tex, lines 163-174) are qualitative. If quantitative performance metrics are added, appropriate statistical tests and multiple-comparisons corrections should be applied.
- **[605792b31ad6]** Add missing LaTeX packages required for the current source: include \usepackage{hyperref} (required for \hypersetup) and \usepackage{graphicx} (required for \includegraphics).
- **[e2598360fbd7]** Ensure all figure and table captions are placed before their corresponding \label commands (they already are, but double‑check for consistency across the document).
- **[01c2e22ce70f]** Verify that the custom class `foundationpaper` defines the \metadata command or replace it with a standard macro; otherwise LaTeX will raise an undefined‑command error.
- **[f03efaff96ec]** Consider adding line‑breaks or `%` comments to very long lines (e.g., the long author list) to improve source readability and avoid overfull hbox warnings.
- **[1250fc51a764]** Correct spacing before citation in subsec:intel-density: 'process further\cite{katz1985network}' should be 'process further \cite{katz1985network}'.
- **[5bc3394e9ce6]** Fix sentence-start capitalization in subsec:interaction: 'and \emph{Economic primitives}' should begin with 'And' or be merged with the preceding sentence.
- **[137d5944ac3b]** Rename section 'Acknowledge' to 'Acknowledgements' or 'Acknowledgments' per standard academic convention.
