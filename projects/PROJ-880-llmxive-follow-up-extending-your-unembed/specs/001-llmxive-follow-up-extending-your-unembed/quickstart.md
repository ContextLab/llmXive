# Quickstart: llmXive cross‑lingual edge‑spectrum analysis

These instructions let a new researcher reproduce the full experiment on a fresh GitHub Actions runner.

## Prerequisites
- Python 3.11 (installed by the CI environment).  
- Internet access (to download model checkpoints and verified datasets).  

## Step‑by‑Step

1. **Clone the repository and install dependencies**  
   ```bash
   git clone <repo-url>
   cd <repo-root>
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run the pipeline**  
   The entry‑point script orchestrates all phases in order:
   ```bash
   python -m src.pipeline.run_all \
       --models llama3 mistral bloom \
       --languages en fr zh ar sw de es hi ja pt \
       --top-k 100 \
       --bootstrap-replicates 1000 \
       --perm-iterations 10000 \
       --seed 0
   ```
   - The script writes every artifact under `data/derived/`.  
   - If any language‑subset fails the ≥ 1 M token guard (Phase 2), the run **aborts with a clear error message** (FR‑009). No fallback to an unverified corpus is performed.

3. **Validate contracts** (optional)  
   ```bash
   pytest -m contract
   ```
   This exercise runs `jsonschema` validation against all schemas in `contracts/`.

4. **Inspect results**  
   - Subspace similarities: `data/derived/similarity_matrix_<hash>.json`  
   - Δ‑similarity metrics: `data/derived/similarity_metric_<hash>.json`  
   - Anisotropy bias CI: `data/derived/anisotropy_bias_<lang>_<hash>.json`  
   - Correlations (exploratory): `data/derived/validation_<hash>.json`  
   - Full human‑readable summary: `final_report.md` (generated automatically).

5. **Re‑run with a smaller sample (debug mode)**  
   For quick debugging, add `--debug` to process only the first 10 k tokens per language and reduce permutation iterations to 1 000.

## Expected Runtime & Resources
- Total wall‑clock time ≤ 4.5 h on the default GitHub Actions runner.  
- Peak RAM ≈ a few GB.  
- No GPU is required; the pipeline runs entirely on CPU.

If the permutation phase exceeds 5 h, the script aborts with a warning, as mandated by **FR‑004**.

---


