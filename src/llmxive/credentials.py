"""Local credential store for the Dartmouth Chat API key (T030 / FR-019..023).

Resolution order for DARTMOUTH_CHAT_API_KEY:

  1. Environment variable (highest priority — CI / GitHub Actions path).
  2. ~/.config/llmxive/credentials.toml (POSIX) or
     %APPDATA%/llmxive/credentials.toml (Windows). Written with mode 0600
     on POSIX. Refused if perms are world- or group-readable (FR-023).
  3. Interactive prompt (`getpass`); offers to persist.

The CLI exposes `python -m llmxive auth {set|show|rotate|clear}` for
managing the stored key.
"""

from __future__ import annotations

import getpass
import os
import stat
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DARTMOUTH_KEY_NAME = "DARTMOUTH_CHAT_API_KEY"
SEMANTIC_SCHOLAR_KEY_NAME = "SEMANTIC_SCHOLAR_API_KEY"
ZENODO_TOKEN_NAME = "ZENODO_API_TOKEN"
ZENODO_SANDBOX_TOKEN_NAME = "ZENODO_SANDBOX_API_TOKEN"


def credentials_path() -> Path:
    """Return the canonical credentials file path for the current OS."""
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming")))
        return base / "llmxive" / "credentials.toml"
    base = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
    return base / "llmxive" / "credentials.toml"


@dataclass(frozen=True)
class CredentialsCheck:
    ok: bool
    reason: str | None
    path: Path
    exists: bool


def check_permissions(path: Path | None = None) -> CredentialsCheck:
    """Verify that the credentials file is safe to read.

    Returns ok=True if the file does not exist (caller will create it).
    On POSIX, requires mode 0600 (no group / other bits).
    """
    p = path or credentials_path()
    if not p.exists():
        return CredentialsCheck(ok=True, reason=None, path=p, exists=False)
    if os.name == "nt":
        # ACL enforcement on Windows is non-trivial; trust user $APPDATA.
        return CredentialsCheck(ok=True, reason=None, path=p, exists=True)
    mode = p.stat().st_mode & 0o777
    bad_bits = mode & 0o077  # any group/other read|write|exec
    if bad_bits:
        return CredentialsCheck(
            ok=False,
            reason=(
                f"credentials file {p} has unsafe permissions "
                f"({oct(mode)}); chmod 600 it"
            ),
            path=p,
            exists=True,
        )
    return CredentialsCheck(ok=True, reason=None, path=p, exists=True)


def _read_file(path: Path) -> dict[str, Any]:
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return {}


def load_dartmouth_key(*, prompt_if_missing: bool = False) -> str | None:
    """Load the Dartmouth Chat API key.

    Resolution order:
        1. env var
        2. credentials file
        3. (optional) interactive prompt

    Returns None if not found and prompt_if_missing=False.
    Raises PermissionError if the credentials file has unsafe perms.
    """
    env = os.environ.get(DARTMOUTH_KEY_NAME)
    if env:
        return env.strip()

    chk = check_permissions()
    if not chk.ok:
        raise PermissionError(chk.reason)
    if chk.exists:
        data = _read_file(chk.path)
        key = (data or {}).get("dartmouth_chat_api_key")
        if isinstance(key, str) and key.strip():
            return key.strip()

    if not prompt_if_missing:
        return None

    if not sys.stdin.isatty():
        return None
    try:
        key = getpass.getpass("Enter Dartmouth Chat API key (sk-…): ")
    except (EOFError, KeyboardInterrupt):
        return None
    key = key.strip()
    if not key:
        return None
    try:
        ans = input("Save this key for future runs? [y/N] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        ans = "n"
    if ans in ("y", "yes"):
        save_dartmouth_key(key)
    return key


def _save_key(toml_field: str, key: str, *, path: Path | None = None) -> Path:
    """Persist a credential under ``toml_field`` with safe permissions,
    merging with any existing keys in the file.

    Creates parent directories with 0700 and writes the file with 0600
    on POSIX. Returns the written path.
    """
    p = path or credentials_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    if os.name != "nt":
        try:
            os.chmod(p.parent, stat.S_IRWXU)  # 0700
        except OSError:
            pass
    # Merge with any existing keys so saving one doesn't clobber the other.
    existing: dict[str, Any] = _read_file(p) if p.exists() else {}
    existing[toml_field] = key.strip()
    lines = [f'{k} = "{_toml_escape(v)}"' for k, v in existing.items() if isinstance(v, str)]
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if os.name != "nt":
        os.chmod(p, stat.S_IRUSR | stat.S_IWUSR)  # 0600
    return p


def save_dartmouth_key(key: str, *, path: Path | None = None) -> Path:
    """Persist the Dartmouth Chat API key (merges with existing keys)."""
    return _save_key("dartmouth_chat_api_key", key, path=path)


def save_semantic_scholar_key(key: str, *, path: Path | None = None) -> Path:
    """Persist the Semantic Scholar API key (merges with existing keys).

    Per spec 005 / FR-001: librarian agent uses Semantic Scholar Graph
    API as one of two backends. Free key obtained via
    https://www.semanticscholar.org/product/api#api-key-form.
    """
    return _save_key("semantic_scholar_api_key", key, path=path)


def load_semantic_scholar_key(*, prompt_if_missing: bool = False) -> str | None:
    """Load the Semantic Scholar API key.

    Resolution order mirrors load_dartmouth_key:
        1. env var SEMANTIC_SCHOLAR_API_KEY
        2. credentials file (semantic_scholar_api_key field)
        3. (optional) interactive prompt

    Returns None if not found and prompt_if_missing=False.
    Raises PermissionError if the credentials file has unsafe perms.
    """
    env = os.environ.get(SEMANTIC_SCHOLAR_KEY_NAME)
    if env:
        return env.strip()

    chk = check_permissions()
    if not chk.ok:
        raise PermissionError(chk.reason)
    if chk.exists:
        data = _read_file(chk.path)
        key = (data or {}).get("semantic_scholar_api_key")
        if isinstance(key, str) and key.strip():
            return key.strip()

    if not prompt_if_missing:
        return None
    if not sys.stdin.isatty():
        return None
    try:
        key = getpass.getpass("Enter Semantic Scholar API key: ")
    except (EOFError, KeyboardInterrupt):
        return None
    key = key.strip()
    if not key:
        return None
    try:
        ans = input("Save this key for future runs? [y/N] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        ans = "n"
    if ans in ("y", "yes"):
        save_semantic_scholar_key(key)
    return key


def clear_dartmouth_key(*, path: Path | None = None) -> bool:
    """Delete the credentials file (if any). Returns True if a file was removed."""
    p = path or credentials_path()
    if p.exists():
        p.unlink()
        return True
    return False


def mask_key(key: str | None) -> str:
    """Mask all but the last 4 characters of a key for display."""
    if not key:
        return "(unset)"
    if len(key) <= 8:
        return "****"
    return f"{key[:3]}…{key[-4:]}"


def _toml_escape(s: str) -> str:
    """Minimal TOML basic-string escape for double quotes + backslash."""
    return s.replace("\\", "\\\\").replace('"', '\\"')


class MissingCredentialError(RuntimeError):
    """Raised when a required credential is absent from both env and
    the credentials file. Used by fail-fast paths per Constitution V."""


def load_zenodo_token(*, sandbox: bool = False) -> str:
    """Load the Zenodo API token (FR-031, spec 013).

    Resolution order matches `load_dartmouth_key`:

      1. Env var (``ZENODO_API_TOKEN`` for production; ``ZENODO_SANDBOX_API_TOKEN`` when sandbox=True).
      2. ``~/.config/llmxive/credentials.toml``: ``[zenodo].api_token`` or
         ``[zenodo_sandbox].api_token`` respectively.

    Raises :class:`MissingCredentialError` when the requested token is
    not configured — the publisher's fail-fast precondition (FR-030).
    """
    env_name = ZENODO_SANDBOX_TOKEN_NAME if sandbox else ZENODO_TOKEN_NAME
    env = os.environ.get(env_name)
    if env and env.strip():
        return env.strip()

    chk = check_permissions()
    if not chk.ok:
        raise PermissionError(chk.reason)
    if chk.exists:
        data = _read_file(chk.path) or {}
        section = "zenodo_sandbox" if sandbox else "zenodo"
        token = (data.get(section) or {}).get("api_token")
        if isinstance(token, str) and token.strip():
            return token.strip()

    env_hint = env_name
    section_hint = "[zenodo_sandbox]" if sandbox else "[zenodo]"
    raise MissingCredentialError(
        f"Zenodo {'sandbox' if sandbox else 'production'} token not found. "
        f"Set ${env_hint} or add a {section_hint} section with "
        f"`api_token = \"...\"` to {chk.path}."
    )


__all__ = [
    "DARTMOUTH_KEY_NAME",
    "SEMANTIC_SCHOLAR_KEY_NAME",
    "ZENODO_SANDBOX_TOKEN_NAME",
    "ZENODO_TOKEN_NAME",
    "CredentialsCheck",
    "MissingCredentialError",
    "check_permissions",
    "clear_dartmouth_key",
    "credentials_path",
    "load_dartmouth_key",
    "load_semantic_scholar_key",
    "load_zenodo_token",
    "mask_key",
    "save_dartmouth_key",
    "save_semantic_scholar_key",
]
