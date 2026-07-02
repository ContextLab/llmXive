# Quickstart: Evaluating Automated Code Review Tools Effectiveness

## Prerequisites

- Python 3.11+
- Docker (for tool execution)
- GitHub Personal Access Token (with `public_repo` scope)
- Sufficient RAM, 14 GB disk, 6-hour runtime budget
- CPU-optimized `sentence-transformers` model (auto-downloaded)

## Setup

1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-180-evaluating-the-effectiveness-of-automate
   ```

2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r code/requirements.txt
   ```

3. Set environment variables:
   ```bash
   export GITHUB_TOKEN=<your-token>
   ```

4. Run the pipeline:
   ```bash
   python code/01_data_acquisition.py
   python code/02_human_baseline.py
   python code/03_alignment.py
   python code/04_metrics.py
   ```

5. View results:
   ```bash
   ls results/
   ```

## Testing

Run unit tests:
```bash
pytest code/tests/
```

Run contract tests:
```bash
pytest tests/contract/
```

## Troubleshooting

- **Tool execution fails**: Check Docker is running; verify tool versions in `code/versions.yaml`.
- **GitHub API rate limit**: Use authenticated token; reduce repo count if needed.
- **Memory error**: Reduce concurrent repo analysis; check `data/raw` size.
- **Semantic search slow**: The `all-MiniLM-L6-v2` model is CPU-optimized; ensure sufficient RAM (≥4GB) for embedding generation.
- **Alignment failure**: If AST/semantic confidence < 0.85, the pair is marked 'unmatched'. This is expected behavior to avoid false positives. Line tolerance is not used for matching.
