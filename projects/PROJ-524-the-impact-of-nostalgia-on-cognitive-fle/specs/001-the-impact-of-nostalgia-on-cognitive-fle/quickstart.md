# Quickstart: The Impact of Nostalgia on Cognitive Flexibility in Aging Adults

## Prerequisites

- Python 3.11+
- pip
- Git

## Setup

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-524-the-impact-of-nostalgia-on-cognitive-fle
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Prepare data**:
   - Place raw WCST data in `data/raw/` (CSV format with columns: `participant_id`, `age`, `stimulus_type`, `perseverative_errors`, `categories_completed`)
   - Place nostalgia/control stimuli in `data/stimuli/` (audio/visual files)
   - Run checksum generation:
     ```bash
     python code/utils.py --generate-checksums
     ```

4. **Run the pipeline**:
   ```bash
   python code/main.py
   ```

5. **View results**:
   - Processed data: `data/processed/`
   - Statistical results: `data/results/`
   - Final report: `paper/report.md`

## Testing

- **Unit tests**:
  ```bash
  pytest tests/unit/
  ```
- **Integration tests**:
  ```bash
  pytest tests/integration/
  ```
- **Contract tests** (schema validation):
  ```bash
  pytest tests/contract/
  ```

## Troubleshooting

- **Missing age field**: Records excluded with `ERR_MISSING_AGE_FIELD` logged.
- **Corrupted stimuli**: Pipeline halts with error listing missing files.
- **Runtime > 6 hours**: Warning logged; pipeline continues.
