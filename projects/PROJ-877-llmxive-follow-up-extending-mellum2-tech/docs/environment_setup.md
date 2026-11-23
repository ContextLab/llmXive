# Environment Configuration Setup

## Overview

This document describes how to configure the environment for the llmXive pipeline,
specifically focusing on Hugging Face token management.

## Prerequisites

- A Hugging Face account (free at https://huggingface.co)
- Generated API token with read permissions

## Setup Instructions

### 1. Generate a Hugging Face Token

1. Log in to [Hugging Face](https://huggingface.co)
2. Go to **Settings** → **Access Tokens**
3. Click **New token**
4. Give it a descriptive name (e.g., "llmXive-pipeline")
5. Select **Read** permissions
6. Copy the generated token (starts with `hf_`)

### 2. Create `.env` File

Create a `.env` file in the project root directory:

```bash
cp.env.example.env
```

Edit `.env` and replace `hf_your_token_here` with your actual token:

```env
HuggingfaceToken=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

> **Security Note**: The `.env` file is listed in `.gitignore` and should never be committed to version control.

### 3. Alternative: System Environment Variables

If you prefer not to use a `.env` file, you can set the token as a system environment variable:

**Linux/macOS:**
```bash
export HUGGING_FACE_TOKEN="hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

**Windows (PowerShell):**
```powershell
$env:HUGGING_FACE_TOKEN="hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

**Windows (Command Prompt):**
```cmd
set HUGGING_FACE_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Verification

Run the environment configuration check:

```bash
python code/utils/env_config.py
```

Expected output:
```
INFO: Successfully loaded 1 variables from.env
INFO: Environment Summary: {...}
INFO: Hugging Face token: VALID (masked)
```

## Troubleshooting

### Error: "Hugging Face token not found"

- Ensure your token is correctly set in `.env` or as an environment variable.
- Verify the token starts with `hf_`.
- Check that the `.env` file is in the project root directory.

### Error: "Token does not appear to be a valid Hugging Face token"

- Double-check that you copied the entire token without extra characters.
- Regenerate the token if it may have been compromised.

## Security Best Practices

1. **Never commit `.env` files** to version control.
2. **Rotate tokens periodically** by generating new ones.
3. **Use minimal permissions** (Read-only for dataset access).
4. **Store tokens securely** using a password manager if needed.
