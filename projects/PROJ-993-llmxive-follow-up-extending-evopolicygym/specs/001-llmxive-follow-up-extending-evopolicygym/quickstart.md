# Quickstart: llmXive follow-up

## Prerequisites

- Python 3.11+
- Git
- Access to GitHub Actions runner (or local equivalent)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd <repo-name>
   ```

2. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: `requirements.txt` includes `torch` (CPU), `transformers`, `bitsandbytes`, `gymnasium`, `radon`, `statsmodels`.*

3. **Verify environment**:
   ```bash
   python -c "import gymnasium; print(gymnasium.__version__)"
   ```

## Running the Study

### 1. Discover Environments
```bash
python code/main.py --task discover
```
*Output*: `data/discovered_envs.json`

### 2. Validate Dynamic Shifts
```bash
python code/main.py --task validate_shifts
```
*Output*: `data/sensitivity_report.csv`

### 3. Run Evolutionary Harness
```bash
python code/main.py --task evolve --seeds 5 --conditions baseline,counterfactual
```
*Output*: `data/evolution_results.csv`, `data/fallbacks.log`

### 4. Statistical Analysis
```bash
python code/main.py --task analyze
```
*Output*: `data/analysis_report.txt` (p-value, effect size)

## Troubleshooting

- **LLM Timeout**: If the LLM times out, the system automatically uses the `TemplateExplanation` fallback. Check `data/fallbacks.log` for `timeout` events.
- **Environment Count < 16**: If fewer than 16 environments are found, a warning is logged, but the study proceeds with the available count (as per spec relaxation).
- **Memory Error**: If CPU memory is exceeded, the script will attempt to reduce batch size or offload to a GPU (if available).
