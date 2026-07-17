# Secrets Management for llmXive Pipeline

This document describes how to configure and manage API keys and sensitive configuration for the llmXive pipeline.

## Overview

The pipeline requires access to external services that need API keys:
- **HuggingFace**: For dataset downloads and model inference
- **Prolific**: For rater recruitment (optional)

## Configuration

### 1. Create Environment File

Copy the example environment file:

```bash
cp.env.example.env
```

### 2. Add Your API Keys

Edit `.env` and add your actual API keys:

```env
HF_TOKEN=your_huggingface_token_here
PROLIFIC_API_KEY=your_prolific_api_key_here
```

**Important**:
- Never commit `.env` to version control
- The `.env` file is in `.gitignore`
- Use `.env.example` as a template for other developers

### 3. HuggingFace Token

Get your HuggingFace token from:
https://huggingface.co/settings/tokens

Make sure the token has at least `read` permissions for public datasets.

### 4. Prolific API Key (Optional)

Get your Prolific API key from:
https://app.prolific.com/api

This is only needed if you plan to use Prolific for rater recruitment.

## Usage in Code

### Automatic Loading

The secrets are automatically loaded when you import the secrets manager:

```python
from code.secrets_manager import SecretsManager

# Initialize and validate
with SecretsManager() as sm:
 hf_token = sm.hf_token
 prolific_key = sm.prolific_api_key
```

### Direct Access

For simple cases, you can access secrets directly:

```python
from code.secrets_manager import get_hf_token, get_prolific_api_key

hf_token = get_hf_token() # Raises if missing
prolific_key = get_prolific_api_key() # Returns None if missing
```

### Validation

The pipeline validates required secrets at startup. If any required secret is missing, the pipeline will fail with a clear error message:

```python
from code.secrets_manager import validate_secrets

try:
 validate_secrets()
except ValueError as e:
 print(f"Configuration error: {e}")
 exit(1)
```

## Error Handling

- **Missing Required Secrets**: The pipeline will raise a `ValueError` with a clear message indicating which secrets are missing and where to get them.
- **Missing Optional Secrets**: Optional secrets (like Prolific API key) will return `None` and the pipeline will continue, possibly with reduced functionality.
- **Invalid Token Format**: The pipeline does not validate token format, but downstream services will reject invalid tokens.

## Security Best Practices

1. **Never commit secrets**: Always keep `.env` out of version control
2. **Use different tokens for different environments**: Development, staging, and production should use different API keys
3. **Rotate tokens regularly**: Update your tokens periodically
4. **Limit token permissions**: Use the minimum permissions necessary
5. **Monitor usage**: Keep an eye on API usage and set up alerts

## Troubleshooting

### "Missing required secret: HF_TOKEN"

This error means your HuggingFace token is not configured. To fix:

1. Create or update your `.env` file
2. Add your HuggingFace token: `HF_TOKEN=your_token_here`
3. Ensure the file is in the project root directory

### "Secrets not validated"

This error occurs when you try to access a required secret without validating first. Use the context manager or call `validate_secrets()` before accessing secrets.

### Token not working

If you're getting authentication errors from HuggingFace:

1. Verify your token is correct (no extra spaces)
2. Check that the token has the required permissions
3. Try regenerating the token from HuggingFace settings

## Integration with Other Components

### Ingestion Pipeline

The ingestion pipeline uses `HF_TOKEN` to access HuggingFace datasets:

```python
from code.ingestion import run_ingestion_pipeline
from code.secrets_manager import get_hf_token

# Token is automatically available via environment
run_ingestion_pipeline()
```

### Model Inference

The inference module uses `HF_TOKEN` to download models:

```python
from code.inference import run_inference
# Token is automatically available via environment
run_inference()
```

### Annotation

If using Prolific for rater recruitment, the annotation module uses `PROLIFIC_API_KEY`:

```python
from code.annotation import recruit_raters
from code.secrets_manager import get_prolific_api_key

api_key = get_prolific_api_key()
if api_key:
 recruit_raters(api_key=api_key)
else:
 print("Prolific API key not configured. Using manual recruitment.")
```