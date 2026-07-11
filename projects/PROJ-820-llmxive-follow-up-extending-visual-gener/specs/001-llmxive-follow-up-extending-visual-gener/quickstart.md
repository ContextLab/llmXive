# Quickstart: llmXive follow-up: extending "Visual Generation in the New Era: An Evolution from Atomic Mapping to "

## Prerequisites
- Python 3.11+
- Git
- 7 GB RAM available (for CPU-only diffusion)
- 14 GB disk space

## 1. Environment Setup

```bash
# Clone the repository (if not already done)
git clone <repo-url>
cd projects/PROJ-820-llmxive-follow-up-extending-visual-gener

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Note**: Ensure `torch` is installed for CPU only (no CUDA). If using `pip`, it usually defaults to CPU if no CUDA is detected, but verify with `pip show torch` (look for `cpu` in version or `+cpu` suffix if available, otherwise standard `torch` is fine).

## 2. Data Preparation

### 2.1 Generate Scene Descriptions
If you do not have `data/raw/scene_descriptions.csv`, create it with 100 unique scene descriptions.
```bash
# Example: Create a dummy file for testing
echo "scene_id,description_text" > data/raw/scene_descriptions.csv
echo "1,a cup balancing on a tilted book" >> data/raw/scene_descriptions.csv
# ... (add 99 more lines)
```

### 2.2 Verify Dependencies
Run the physics engine test:
```bash
python code/simulation/physics_engine.py --test
```
This should generate a sample JSON and print "Physics engine OK".

## 3. Running the Pipeline

### 3.1 Full Pipeline (N=100)
**Warning**: This may take up to 6 hours on a CPU-only runner.
```bash
python code/main.py --n 100 --mode full
```
This will:
1. Simulate physics for 100 scenes.
2. Generate prompts (Baseline, Experimental, Control).
3. Generate images (300 total).
4. Evaluate violations.
5. Compute statistics.

### 3.2 Pilot Run (N=10)
To verify feasibility before running the full study:
```bash
python code/main.py --n 10 --mode full
```
Check `data/derived/evaluation_results/` and `data/processed/final_analysis.csv` for output.

### 3.3 Individual Steps
- **Physics Simulation**: `python code/simulation/physics_engine.py --input data/raw/scene_descriptions.csv --output data/derived/physics_constraints/`
- **Prompt Engineering**: `python code/generation/prompt_engine.py --input data/derived/physics_constraints/ --output data/derived/prompts/`
- **Image Generation**: `python code/generation/diffusion_runner.py --input data/derived/prompts/ --output data/derived/generated_images/`
- **Evaluation**: `python code/evaluation/detector.py --images data/derived/generated_images/ --constraints data/derived/physics_constraints/ --output data/derived/evaluation_results/`
- **Analysis**: `python code/analysis/statistics.py --input data/derived/evaluation_results/ --output data/processed/final_analysis.csv`

## 4. Verification
- **Check Schemas**: `pytest tests/contract/test_schemas.py`
- **Check Results**: View `data/processed/final_analysis.csv` for p-value and violation rates.

## 5. Troubleshooting
- **Out of Memory**: Reduce batch size to 1 (default) or reduce N.
- **GPU Error**: Ensure `torch` is CPU-only. Remove any `cuda` flags.
- **Slow Generation**: If > 2 mins/image, reduce N to 80.