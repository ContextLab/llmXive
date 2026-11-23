# Quickstart: Running the LLM Code‑Security Evaluation Pipeline

## Prerequisites
* GitHub Actions runner (or local Linux 22.04 environment) with **Python 3.11**.  
* Docker installed (access to the public `gcc` image based on a recent Bullseye release).  
* Internet access to the verified HuggingFace datasets and inference API.

## Step‑by‑Step

0. **Set up deterministic environment**  
   ```bash
   python code/setup_env.py
   ```

1. **Clone the repository and install Python dependencies**  
   ```bash
   git clone 
   cd llm-code-security
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Download the human reference dataset**  
   ```bash
   python code/download_human.py \
       --output data/raw/codeforces_cpp.jsonl \
       --min-problems 50 \
       --seed 20231027
   ```

3. **Generate LLM variants** (requires HuggingFace API token in `HF_TOKEN` env)  
   ```bash
   export HF_TOKEN=your_hf_token
   python code/generate_llm_variants.py \
       --model codellama-7b-instruct \
       --input data/raw/codeforces_cpp.jsonl \
       --output data/generated/codellama/
   python code/generate_llm_variants.py \
       --model starcoder-15b \
       --input data/raw/codeforces_cpp.jsonl \
       --output data/generated/starcoder/
   ```

4. **Create ProblemPair file** (merges human and LLM sources, records compile‑fail status)  
   ```bash
   python code/create_problem_pairs.py \
       --human data/raw/codeforces_cpp.jsonl \
       --llm-dir data/generated/ \
       --output data/raw/problem_pairs_v${HASH}.jsonl
   ```

5. **Compile and fuzz**  
   ```bash
   python code/compile_and_fuzz.py \
       --pairs data/raw/problem_pairs_v*.jsonl \
       --output data/results/fuzz_results_v${HASH}.jsonl \
       --timeout 1800   # 30 min per binary
   ```

6. **Parse crashes and score severity**  
   ```bash
   python code/parse_crashes.py \
       --fuzz-results data/results/fuzz_results_v${HASH}.jsonl \
       --output data/results/scored_fuzz_results_v${HASH}.jsonl
   ```

7. **Statistical analysis**  
   ```bash
   python code/statistical_analysis.py \
       --results data/results/scored_fuzz_results_v${HASH}.jsonl \
       --output data/analysis/stat_summary_v${HASH}.jsonl
   ```

8. **Generate the final report**  
   ```bash
   python code/generate_report.py \
       --summary data/analysis/stat_summary_v${HASH}.jsonl \
       --output report.md
   ```

9. **Verify reproducibility** (optional)  
   ```bash
   pytest -m contract
   ```

All intermediate files are content‑hashed; rerunning any step will automatically detect changes and recompute downstream artifacts.
