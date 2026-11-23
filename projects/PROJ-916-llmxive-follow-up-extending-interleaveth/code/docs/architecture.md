# Architecture

## High-Level Design

The llmXive pipeline is structured into several key components:

### 1. Simulator (`src/simulator/`)
- `parser.py`: Converts text captions into structured JSON scene descriptions
- `noise_injector.py`: Simulates semantic uncertainty by injecting noise
- `validator.py`: Detects ambiguous spatial relationships
- `simulator.py`: Orchestrates Perfect/Noisy mode switching

### 2. Agents (`src/agents/`)
- `planner.py`: Generates intent and next steps
- `generator.py`: Reconstructs SceneDescription JSON using a lightweight LLM
- `critic.py`: Evaluates generated JSON against prompts and ground truth
- `interfaces.py`: Defines contracts for agent inputs/outputs

### 3. Pipeline (`src/pipeline/`)
- `orchestrator.py`: Manages the agentic loop with memory and timeout constraints
- `logger.py`: Records intermediate states and critiques

### 4. Data (`src/data/`)
- `loader.py`: Streams Visual Genome, GQA, WISE, and RISE datasets

### 5. Stats (`src/stats/`)
- `simulator_metrics.py`: Calculates Graph Edit Distance and error rates
- `generator_metrics.py`: Evaluates generator performance
- `analyzer.py`: Performs statistical tests (t-test, Wilcoxon)
- `report_generator.py`: Generates statistical significance reports

## Data Flow

1. **Data Loading**: Real datasets (WISE, RISE) are streamed
2. **Simulation**: Text-based scene graphs are generated (Perfect/Noisy)
3. **Agentic Loop**: Planner → Generator → Critic loop executes
4. **Metrics**: Error rates and reasoning scores are calculated
5. **Analysis**: Statistical tests compare baselines and ablations

## Constraints

- CPU-only execution (max 7GB RAM)
- 6-hour runtime budget
- Real data only (no synthetic fallbacks for core datasets)
