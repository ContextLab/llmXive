# Environment Configuration Setup

This document describes how to configure environment variables for the Statistical Analysis of Sentiment Drift project.

## Prerequisites

- Python 3.11+
- Virtual environment activated (see `T003` setup instructions)

## API Keys Required

### FRED API Key (Required)

The Federal Reserve Economic Data (FRED) API is used to fetch macroeconomic indicators.

1. Go to [FRED API Registration](https://fred.stlouisfed.org/docs/api/api_key.html)
2. Register with your email address
3. Copy your API key

### HuggingFace Token (Optional)

Used for accessing HuggingFace datasets and models.

1. Go to [HuggingFace Settings](https://huggingface.co/settings/tokens)
2. Create a new token with `read` permissions
3. Copy your token

### GDELT API Key (Optional)

GDELT typically doesn't require an API key for basic access, but some advanced features may require one.

## Configuration Steps

1. **Copy the example environment file**:
 ```bash
 cp.env.example.env
 ```

2. **Edit the `.env` file** with your actual API keys:
 ```bash
 nano.env
 # or
 vim.env
 ```

 Replace the placeholder values:
 ```
 FRED_API_KEY=your_actual_fred_key
 HF_TOKEN=your_actual_hf_token
 GDELT_API_KEY=your_actual_gdelt_key
 ```

3. **Verify the configuration**:
 ```bash
 python code/config.py
 ```

 Expected output if successful:
 ```
 Loading environment configuration...
 ✓ Loaded environment from /path/to/project/.env
 ✓ Environment validation passed
 FRED_API_KEY: ********** (set)
 HF_TOKEN: ********** (set)
 GDELT_API_KEY: not set (optional)
 ```

## Security Notes

- **Never commit `.env` files to version control**
- The `.env` file is already listed in `.gitignore`
- Use environment variables for sensitive data, never hardcode credentials
- If you accidentally commit a `.env` file, remove it immediately from git history

## Troubleshooting

### "Required environment variables are missing"

This error occurs when `FRED_API_KEY` is not set. Create or update your `.env` file with a valid FRED API key.

### "No.env file found"

Ensure you copied `.env.example` to `.env` in the project root directory.

### API rate limits

If you encounter rate limit errors, consider:
- Reducing the frequency of API calls
- Implementing caching for frequently accessed data
- Contacting the service providers for higher rate limits

## Related Tasks

- `T007`: Setup environment configuration management
- `T008`: Create data ingestion skeleton with FRED and HuggingFace clients
- `T016`: Implement FRED data fetcher
- `T017`: Implement GDELT sentiment fetcher
