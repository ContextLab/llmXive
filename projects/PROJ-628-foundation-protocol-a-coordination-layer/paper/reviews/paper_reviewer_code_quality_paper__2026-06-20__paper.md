---
action_items:
- id: 73d8052dd590
  severity: fatal
  text: "The manuscript references a reference implementation (GitHub repos) but does\
    \ not include any concrete source files, module structure, or build scripts in\
    \ the submission. Provide a minimal, self\u2011contained code snapshot (e.g.,\
    \ a `src/` directory with clear package layout) so reviewers can assess readability,\
    \ modularity, and test coverage."
- id: 05e5d2b31931
  severity: writing
  text: "Add a comprehensive `README.md` that documents required dependencies, installation\
    \ steps (including Python version, virtual\u2011env setup, and TypeScript build\
    \ for the web UI), and how to run the full stack from scratch. This is essential\
    \ for reproducibility."
- id: 9c6ba409a754
  severity: science
  text: Include an automated test suite (unit and integration tests) with instructions
    to execute `pytest` (or equivalent) and `npm test`. Tests should cover core protocol
    primitives (entity handling, envelope signing, checkpoint pipeline) and at least
    one bridge (e.g., the MCP bridge).
- id: 9d513ac11929
  severity: writing
  text: "Ensure that all external dependencies are pinned (e.g., via `requirements.txt`\
    \ and `package-lock.json`) and that the repository uses a lockfile to guarantee\
    \ deterministic builds. List any non\u2011Python runtime requirements (e.g., Node.js\
    \ version) explicitly."
- id: 47314b195c35
  severity: writing
  text: "Provide a short script or Makefile target that builds the PDF from the LaTeX\
    \ sources and runs the code\u2011quality checks (linting, type checking). This\
    \ demonstrates end\u2011to\u2011end reproducibility of both the paper and the\
    \ software artifact."
artifact_hash: 25ed14dfad8b3fe5e099c671c1ec2f21f380f0a5e0f949e85912970c6e197b76
artifact_path: projects/PROJ-628-foundation-protocol-a-coordination-layer/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-20T04:42:52.022741Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_code_quality_paper
score: 0.0
verdict: minor_revision
---

The paper focuses on the conceptual design of the Foundation Protocol and includes an appendix that *describes* a reference implementation, but it does not ship any actual source code, configuration files, or test artifacts. From a code‑quality perspective this omission prevents any assessment of readability, modularity, test coverage, dependency hygiene, or reproducibility.

**Readability & Modularity**  
The manuscript mentions three abstraction layers (Entity, Host, Server) and several components (checkpoint pipeline, bridges, contract state machine) but provides no concrete module names, file hierarchy, or API signatures. Without visible code it is impossible to verify that the core protocol is isolated from transport or UI concerns, or that the suggested unidirectional dependency rule is enforced.

**Testing**  
No test files, test harnesses, or CI configuration are included. The claim that “the implementation supports high‑fanout scenarios” and that “handlers are pluggable” cannot be validated without unit or integration tests that exercise these paths.

**Dependency Hygiene**  
The description states that the core has no dependencies on web frameworks or databases, yet no `requirements.txt`, `pyproject.toml`, or `package.json` is present. Pinning versions and providing lockfiles is essential for deterministic builds, especially when the stack mixes Python and TypeScript.

**Reproducibility**  
The paper provides a compiled PDF and figures, but no instructions to reproduce the software stack from the source repository. A reviewer cannot clone the GitHub URLs, install the environment, and run the system end‑to‑end. The lack of a reproducible build script also hampers verification of the PDF generation pipeline.

**Actionable Recommendations**  
1. **Include Source** – Attach a minimal but complete code snapshot (e.g., `foundation_protocol/` and `ai_link_net/` directories) with clear package boundaries that reflect the three‑layer architecture described.  
2. **Documentation** – Add a `README.md` covering environment setup, dependency installation, and step‑by‑step commands to start a Host, register entities, and execute a sample workflow (such as the AI‑company scenario).  
3. **Testing Suite** – Provide automated tests for core primitives (entity creation, envelope signing/verification, checkpoint enforcement) and at least one bridge. Include instructions to run the suite and a CI badge.  
4. **Dependency Locking** – Supply `requirements.txt` (or `poetry.lock`) and `package-lock.json` with exact version pins, and list required runtimes (Python 3.11, Node 20, etc.).  
5. **Reproducible Build** – Offer a Makefile or script that builds the LaTeX PDF, lints the code, runs type checkers, and executes the test suite, demonstrating that the entire artifact can be reproduced from a fresh checkout.

Addressing these points will allow future reviewers to evaluate the actual code quality, ensure that the protocol implementation is maintainable, and confirm that the research claims are supported by a reproducible software artifact.
