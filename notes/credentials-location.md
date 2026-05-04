# Credentials Location

**File**: `~/.config/llmxive/credentials.toml` (POSIX) or `%APPDATA%/llmxive/credentials.toml` (Windows)
**Permissions**: 0600 (owner read/write only) — verified by `src/llmxive/credentials.py::ensure_safe_permissions()`
**Format**: TOML key-value pairs, e.g.:

```toml
dartmouth_chat_api_key = "<key value>"
```

## Resolution order (per `src/llmxive/credentials.py`)

1. Environment variable `DARTMOUTH_CHAT_API_KEY` — if set, takes precedence
2. Credentials file at the canonical path above

So **the orchestrator will work with just the credentials file** — exporting the env var is only needed if you want to override or temporarily run with a different key (e.g., the deliberately-invalid key for the FR-015 induced-failure test).

## Useful commands

- View / set the key via the orchestrator's CLI helpers:
  - `python -m llmxive auth show` — show whether the credential is configured (does NOT print the key)
  - `python -m llmxive auth set --key <KEY>` — write a new credentials file
  - `python -m llmxive auth rotate --key <NEW_KEY>` — clear + write
  - `python -m llmxive auth clear` — delete the credentials file

## Key acquisition

The Dartmouth Chat API key comes from <https://rc.dartmouth.edu/ai/online-resources/>. It is also stored as the `DARTMOUTH_CHAT_API_KEY` GitHub repository secret on `ContextLab/llmXive` for use by GitHub Actions workflows.
