# Quickstart: Statistical Analysis of OpenStreetMap Data for Urban Heat Island Effects

## Prerequisites

- Python 3.11+
- Git
- (Optional) Google Earth Engine API key (for satellite data, but not required if data is successfully downloaded via Hugging Face)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-125-statistical-analysis-of-openstreetmap-da
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Configuration

1. **Set up environment variables** (if using Earth Engine):
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/credentials.json"
   ```

2. **Configure `code/config.py`**:
   - Set `MAX_MEMORY_GB = 6`
   - Set `MAX_SAMPLES = 500000`
   - Set `RANDOM_SEED = 42`

## Running the Pipeline

1. **Download Data** (if not already present):
   ```bash
   python code/main.py --task download --city "New York"
   ```

2. **Run Analysis**:
   ```bash
   python code/main.py --task run --city "New York"
   ```

3. **View Results**:
   - Metrics: `data/results/metrics.csv`
   - Plots: `data/results/plots/`
   - Reports: `data/results/reports/`

## Troubleshooting

- **Memory Error**: The pipeline will halt execution if memory exceeds 6GB.
- **Data Download Failure**: Ensure Earth Engine API key is set or that the Hugging Face dataset download succeeds.
