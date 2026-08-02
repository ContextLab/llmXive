# PROJ-055: Investigating the Impact of Telomere Length on Lifespan Variation in Wild Bird Populations

## Security Hardening (Task T043)

This project implements security best practices to prevent hardcoded API keys and secrets.

### Security Features

1. **No Hardcoded Credentials**: All API keys must be provided via environment variables or `.env` files.
2. **Automatic Security Scanning**: Run `python code/security_scanner.py` to scan for hardcoded secrets.
3. **Environment Variable Configuration**: Use `config.py` to load credentials safely.
4. **Git Ignore Protection**: `.env` files and sensitive data are excluded from version control.

### Setup Instructions

1. **Install Dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

2. **Create Environment File**:
 ```bash
 # Create a.env file in the project root
 echo "DRYAD_API_KEY=your_key_here" >.env
 echo "ANAGE_API_KEY=your_key_here" >>.env
 echo "RANDOM_SEED=42" >>.env
 ```

3. **Run Security Scan** (Recommended before committing):
 ```bash
 python code/security_scanner.py
 ```

4. **Execute Pipeline**:
 ```bash
./run_pipeline.sh
 ```

### Security Best Practices

- Never commit `.env` files or hardcoded credentials
- Use environment variables for all sensitive data
- Run the security scanner before each commit
- Rotate API keys regularly
- Use separate keys for development and production

### Configuration

The `config.py` module handles all configuration loading:

```python
from config import get_config

config = get_config()
dryad_key = config['dryad_api_key'] # Loaded from environment
```

### Testing

Run security tests:
```bash
pytest tests/test_security_scanner.py -v
```

### Files

- `code/security_scanner.py`: Security scanning tool
- `code/config.py`: Configuration management (no hardcoded secrets)
- `tests/test_security_scanner.py`: Security scanner tests
- `.env`: Environment variables (gitignored)
- `requirements.txt`: Project dependencies

## Original Project Description

[Original project content would follow...]