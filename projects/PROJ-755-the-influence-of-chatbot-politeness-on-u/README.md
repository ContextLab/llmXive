# The Influence of Chatbot Politeness on User-Perceived Quality

This project investigates the relationship between chatbot politeness and user-perceived quality using mixed-effects modeling and robustness analysis.

## Project Structure

- `code/`: Source code for data processing, modeling, and analysis
- `data/`: Data storage (raw, processed, models)
- `tests/`: Unit, integration, and contract tests
- `docs/`: Documentation
- `specs/`: Feature specifications and design documents
- `contracts/`: Schema contracts for data validation
- `state/`: Project state and artifact tracking

## Environment Configuration

### Local Development

1. Copy the environment template:
 ```bash
 cp code/.env.example code/.env
 ```

2. Edit `code/.env` and add your Hugging Face token:
 ```
 HF_TOKEN=your_hf_token_here
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

### CI/CD (GitHub Actions)

**Do NOT use.env files in CI/CD.** Secrets must be injected via GitHub Actions environment variables:

1. Go to your repository Settings > Secrets and variables > Actions
2. Create a new secret named `HF_TOKEN` with your Hugging Face token value
3. Reference in workflows:
 ```yaml
 env:
 HF_TOKEN: ${{ secrets.HF_TOKEN }}
 ```

This approach ensures:
- Reproducibility on fresh runners
- No secret leakage in logs or version control
- Compliance with Constitution Principle I (secrets management)

## Running the Pipeline

See `docs/quickstart.md` for step-by-step instructions.

## Testing

Run tests with:
```bash
pytest tests/
```

## License

This project is for research purposes only.
