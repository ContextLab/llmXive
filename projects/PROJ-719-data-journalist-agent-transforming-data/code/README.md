# Data2Story Adaptation: Completeness Audit & Dataset Discovery

This adaptation reproduces the **quantitative "Completeness Gates"** mechanism described in the Data Journalist Agent paper (Section: *Verifiability* and *Find-Data* skills).

### Original vs. Adapted
| Feature | Original Paper Implementation | Adapted (CPU-Safe) |
| :--- | :--- | :--- |
| **Scope** | Full multi-agent newsroom (Detective, Analyst, Inspector, etc.) running on real news datasets. | Isolated **Completeness Audit** engine (`audit.py`) + **Local Discovery** (`browse_local.py`). |
| **Data Source** | Real, large-scale datasets (Economist, Pudding, TidyTuesday) requiring significant I/O. | **Synthetic Realism**: A small, self-contained CSV dataset embedded in the code (simulating a "Climate" dataset) to prove the logic works without external downloads. |
| **Compute** | Distributed agents, potential GPU for LLM scoring. | **Pure CPU**: Python `pandas` + `json` logic. No LLMs, no GPU. |
| **Output** | Full HTML stories, interactive maps, video assets. | **Verification Report** (`data/audit_report.json`) and **Discovery Index** (`data/discovery_index.json`) + **Quality Plot** (`figures/quality_distribution.png`). |
| **Metric** | Human evaluation of story quality + automated claim verification. | **Gate Pass/Fail Rate**: % of synthetic datasets passing the 4 completeness gates (Rows > 50, Non-null > 50%, etc.). |

### Simplification Strategy
1.  **Removed LLM Dependencies**: The original uses LLMs for "angle coverage" and "design". This adaptation focuses solely on the *deterministic* data validation logic (the "Inspector" and "Find-Data" gates).
2.  **Embedded Data**: Instead of downloading the full Economist/Pudding archives (which might fail or be too large), we generate a small, realistic "Climate" dataset in memory that mimics the structure of real data (Entity, Year, Metric columns).
3.  **Single Script Pipeline**: Combined the discovery and audit logic into a single reproducible script.
