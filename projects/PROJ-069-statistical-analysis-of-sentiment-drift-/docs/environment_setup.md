# Environment Configuration Guide

This project uses environment variables to manage sensitive API keys and tokens.
Follow the steps below to configure your local environment.

## 1. Create the Environment File

1. Locate the `code/.env.example` file in the project root.
2. Copy it to a new file named `.env` in the same directory:
 ```bash
 cp code/.env.example.env
 ```
 *Note: Depending on your project structure, the example might be in the root. Adjust the path if necessary.*

3. Open `.env` in a text editor and replace the placeholder values with your actual API keys.

## 2. Required Variables

### FRED API Key (Required)
The Federal Reserve Economic Data (FRED) API key is required to fetch macroeconomic data.

- **Variable Name**: `FRED_API_KEY`
- **How to get it**:
 1. Visit [https://fred.stlouisfed.org/docs/api/api_key.html](https://fred.stlouisfed.org/docs/api/api_key.html).
 2. Register for a free account if you don't have one.
 3. Generate an API key.
- **Usage**: Paste the key into the `.env` file.

## 3. Optional Variables

### HuggingFace Token (Optional)
Required if you plan to download specific models or datasets from HuggingFace that require authentication.

- **Variable Name**: `HF_TOKEN`
- **How to get it**:
 1. Visit [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens).
 2. Create a new token with read permissions.
- **Usage**: Paste the token into the `.env` file.

### GDELT API Key (Optional)
Required for accessing GDELT data if the specific endpoint used requires authentication (though many GDELT endpoints are open).

- **Variable Name**: `GDELT_API_KEY`
- **How to get it**: Check the [GDELT Documentation](http://api.gdeltproject.org/api/v2/doc/doc) for current requirements.
- **Usage**: Paste the key into the `.env` file.

## 4. Verification

After setting up your `.env` file, you can verify the configuration by running the configuration script:

```bash
cd code
python config.py
```

Expected output:
```text
Checking environment configuration...
✓.env file loaded successfully.
✓ FRED_API_KEY is configured.
✓ Environment validation complete.
```

## 5. Security Note

The `.env` file contains sensitive credentials. **Never commit this file to version control.**
The project includes a `.gitignore` rule to prevent accidental commits of `.env`.
Always use `code/.env.example` as the template for new environments.
