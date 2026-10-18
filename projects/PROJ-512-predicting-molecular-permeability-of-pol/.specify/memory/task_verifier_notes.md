# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T006** — The file `code/models/polymer_graph.py` exists but is only a bare dataclass container (`nodes`, `edges` as generic lists) with no node/edge feature schemas at all — no atom type, hybridization, or bond type feature definitions, encodings, or validation, which the task explicitly requires. It is effectively a placeholder that does not implement the required schemas (though it does correctly omit 3D features per FR-001).
- **T020** — Requested task execution failed; rerun successfully: code/data/preprocessing.py exit=1
