"""
Regex‑based rule engine for the Gatekeeper component.

This module provides data structures and helper functions to:
* Parse role definitions and deletion logs (both from JSON structures or raw text lines).
* Determine whether a target has been securely deleted.
* Authorise a role for a given domain and action.
* Combine the above checks into a single access‑policy decision.

The implementation follows the contracts exercised in
`tests/unit/test_rules.py`.
"""
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, List, Dict, Optional, Tuple

# Toolkit helper for consistent project‑wide paths
from llmxive_toolkit import paths

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Data classes
# ----------------------------------------------------------------------


@dataclass
class DeletionLog:
    """A single deletion‑log entry."""
    target_id: str
    timestamp: datetime
    status: str  # e.g. "success", "failed", "completed"


@dataclass
class RoleDefinition:
    """Definition of a role and its permissions."""
    role_name: str
    allowed_domains: List[str] = field(default_factory=list)
    allowed_actions: List[str] = field(default_factory=list)
    priority: int = 0
    is_default: bool = False


# ----------------------------------------------------------------------
# Helper / internal utilities
# ----------------------------------------------------------------------


def _log_anomaly_to_file(line: str, line_num: int, error_reason: str) -> None:
    """
    Log a malformed line from a deletion‑log text source.

    The log is appended to ``logs/deletion_errors.log`` inside the project
    directory.  Each entry is a single line for easy grepping.

    Parameters
    ----------
    line: str
        The raw line that could not be parsed.
    line_num: int
        1‑based line number in the source file.
    error_reason: str
        Short description of why parsing failed.
    """
    log_path: Path = paths.logs("deletion_errors.log")
    # Ensure the parent directory exists (paths.logs creates it)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(
            f"[line {line_num}] {error_reason}: {line.rstrip()}\n"
        )
    logger.debug(
        "Logged deletion‑log anomaly (line %d): %s – %s",
        line_num,
        error_reason,
        line.rstrip(),
    )


# ----------------------------------------------------------------------
# Parsing functions
# ----------------------------------------------------------------------


def parse_role_definitions(raw_roles: List[Dict[str, Any]]) -> List[RoleDefinition]:
    """
    Convert a list of role dictionaries (as loaded from JSON) into
    ``RoleDefinition`` objects.

    The function is tolerant: missing keys are replaced with sensible
    defaults and malformed entries are ignored rather than raising.

    Parameters
    ----------
    raw_roles: List[Dict[str, Any]]
        Each dict should contain at least ``role_name``.  Optional keys are
        ``allowed_domains``, ``allowed_actions``, ``priority`` and
        ``is_default``.

    Returns
    -------
    List[RoleDefinition]
    """
    roles: List[RoleDefinition] = []
    for idx, entry in enumerate(raw_roles):
        if not isinstance(entry, dict):
            logger.warning("Skipping non‑dict role entry at index %d", idx)
            continue
        role_name = entry.get("role_name")
        if not role_name:
            logger.warning(
                "Role entry missing 'role_name' at index %d – skipping",
                idx,
            )
            continue
        allowed_domains = entry.get("allowed_domains") or []
        allowed_actions = entry.get("allowed_actions") or []
        priority = entry.get("priority", 0)
        is_default = entry.get("is_default", False)

        # Ensure we have proper list types
        if not isinstance(allowed_domains, list):
            allowed_domains = list(allowed_domains)
        if not isinstance(allowed_actions, list):
            allowed_actions = list(allowed_actions)

        roles.append(
            RoleDefinition(
                role_name=role_name,
                allowed_domains=allowed_domains,
                allowed_actions=allowed_actions,
                priority=int(priority),
                is_default=bool(is_default),
            )
        )
    return roles


def parse_deletion_log(line: str) -> Optional[DeletionLog]:
    """
    Parse a single text line describing a deletion log entry.

    Expected format (case‑insensitive, commas separating fields):
        "target_id: <id>, status: <status>, timestamp: <ISO‑8601>"

    Returns ``None`` if the line cannot be parsed; the caller may log the
    anomaly using ``_log_anomaly_to_file`` if desired.

    Parameters
    ----------
    line: str
        Raw line from a deletion‑log file.

    Returns
    -------
    DeletionLog | None
    """
    # Normalise whitespace and split on commas
    parts = [p.strip() for p in line.split(",") if p.strip()]
    kv: Dict[str, str] = {}
    for part in parts:
        if ":" not in part:
            # malformed piece – abort parsing for this line
            return None
        key, value = part.split(":", 1)
        kv[key.strip().lower()] = value.strip()

    required_keys = {"target_id", "status", "timestamp"}
    if not required_keys.issubset(kv.keys()):
        return None

    try:
        # Accept both "Z" and offset‑aware ISO strings
        ts_raw = kv["timestamp"]
        if ts_raw.endswith("Z"):
            ts_raw = ts_raw[:-1] + "+00:00"
        timestamp = datetime.fromisoformat(ts_raw)
    except Exception:  # pylint: disable=broad-except
        return None

    return DeletionLog(
        target_id=kv["target_id"],
        status=kv["status"].lower(),
        timestamp=timestamp,
    )


# ----------------------------------------------------------------------
# Core rule checks
# ----------------------------------------------------------------------


def is_target_deleted(target_id: str, deletion_logs: List[DeletionLog]) -> bool:
    """
    Determine whether a target has a *successful* deletion entry.

    Success is indicated by a ``status`` of ``"success"`` or
    ``"completed"`` (case‑insensitive).

    Parameters
    ----------
    target_id: str
    deletion_logs: List[DeletionLog]

    Returns
    -------
    bool
    """
    target_id = target_id.strip()
    for log in deletion_logs:
        if log.target_id == target_id and log.status in {"success", "completed"}:
            return True
    return False


def is_target_deleted_secure(
    target_id: str,
    deletion_logs: List[DeletionLog],
    current_time: datetime,
    freshness_hours: int = 24,
) -> bool:
    """
    Determine whether a target has been securely deleted, i.e. a successful
    deletion entry exists **and** it is recent enough to satisfy the
    security policy.

    The default policy requires the deletion to be within the last
    ``freshness_hours`` (24 h).

    Parameters
    ----------
    target_id: str
    deletion_logs: List[DeletionLog]
    current_time: datetime
        Reference time (usually ``datetime.now()``).
    freshness_hours: int, optional
        Maximum age of a deletion log to be considered secure.

    Returns
    -------
    bool
    """
    for log in deletion_logs:
        if log.target_id != target_id:
            continue
        if log.status not in {"success", "completed"}:
            continue
        age = current_time - log.timestamp
        if age <= timedelta(hours=freshness_hours):
            return True
    return False


def is_role_authorized(
    role_name: str,
    domain: str,
    action: str,
    roles: List[RoleDefinition],
) -> bool:
    """
    Check whether ``role_name`` is permitted to perform ``action`` in
    ``domain`` according to the supplied role definitions.

    If the role is not found, the function returns ``False`` (fail‑safe).
    The default role (``is_default=True``) is also treated as a deny‑all
    placeholder unless it explicitly lists permissions.

    Parameters
    ----------
    role_name: str
    domain: str
    action: str
    roles: List[RoleDefinition]

    Returns
    -------
    bool
    """
    role_name = role_name.strip()
    domain = domain.strip()
    action = action.strip()

    for role in roles:
        if role.role_name != role_name:
            continue
        # If the role explicitly lists allowed domains/actions, enforce them.
        # An empty list means “no permission” (except for a default role that
        # deliberately denies everything).
        if domain not in role.allowed_domains:
            return False
        if action not in role.allowed_actions:
            return False
        return True

    # Role not found – deny by default
    return False


def extract_role_from_context(context: str) -> Optional[str]:
    """
    Extract a role identifier from a free‑form text context.

    The function looks for the pattern ``role: <role_name>`` (case‑insensitive).
    If no such pattern is present, ``None`` is returned.

    Parameters
    ----------
    context: str

    Returns
    -------
    str | None
    """
    match = re.search(r"role\s*:\s*([A-Za-z0-9_]+)", context, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def check_access_policy(
    target_id: str,
    context: str,
    target_domain: str,
    action: str,
    deletion_logs: List[DeletionLog],
    roles: List[RoleDefinition],
) -> Tuple[bool, str]:
    """
    Core policy decision used by the Gatekeeper pipeline.

    The decision order mirrors the security‑first principle:
    1. If the target has been *securely* deleted (recent successful log), deny.
    2. Otherwise, verify that the role extracted from ``context`` is authorised
       for the requested ``domain`` and ``action``.
    3. If either check fails, deny with an explanatory reason; otherwise grant.

    Parameters
    ----------
    target_id: str
    context: str
        Free‑form user context that should contain a ``role: <name>`` token.
    target_domain: str
    action: str
    deletion_logs: List[DeletionLog]
    roles: List[RoleDefinition]

    Returns
    -------
    Tuple[bool, str]
        (allowed, reason) where ``allowed`` is ``True`` for grant.
    """
    # 1️⃣ Deletion check (secure)
    now = datetime.now()
    if is_target_deleted_secure(target_id, deletion_logs, now):
        return False, "Access denied: target has been securely deleted."

    # 2️⃣ Role extraction
    role = extract_role_from_context(context)
    if not role:
        return False, "Access denied: role not found in context."

    # 3️⃣ Role authorisation
    if is_role_authorized(role, target_domain, action, roles):
        return True, "Access granted."

    return False, "Access denied: role not authorized for this domain/action."


# ----------------------------------------------------------------------
# Loading helpers (JSON files)
# ----------------------------------------------------------------------


def load_role_definitions(file_path: str) -> List[RoleDefinition]:
    """
    Load role definitions from a JSON file and parse them.

    The JSON file should contain an array of role dictionaries compatible
    with ``parse_role_definitions``.

    Parameters
    ----------
    file_path: str

    Returns
    -------
    List[RoleDefinition]
    """
    try:
        with open(file_path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Failed to load role definitions from %s: %s", file_path, exc)
        return []
    if not isinstance(raw, list):
        logger.error("Role definitions JSON must be a list – got %s", type(raw))
        return []
    return parse_role_definitions(raw)


def load_deletion_logs(file_path: str) -> List[DeletionLog]:
    """
    Load deletion logs from a JSON file.

    Expected JSON format: a list of objects each with ``target_id``,
    ``timestamp`` (ISO‑8601 string) and ``status`` fields.

    Parameters
    ----------
    file_path: str

    Returns
    -------
    List[DeletionLog]
    """
    try:
        with open(file_path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Failed to load deletion logs from %s: %s", file_path, exc)
        return []

    logs: List[DeletionLog] = []
    for idx, entry in enumerate(raw):
        if not isinstance(entry, dict):
            logger.warning("Skipping non‑dict deletion entry at index %d", idx)
            continue
        try:
            target_id = entry["target_id"]
            status = entry["status"]
            ts_raw = entry["timestamp"]
            if ts_raw.endswith("Z"):
                ts_raw = ts_raw[:-1] + "+00:00"
            timestamp = datetime.fromisoformat(ts_raw)
            logs.append(
                DeletionLog(
                    target_id=target_id,
                    status=status.lower(),
                    timestamp=timestamp,
                )
            )
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning(
                "Malformed deletion‑log entry at index %d: %s – %s", idx, entry, exc
            )
    return logs


# ----------------------------------------------------------------------
# CLI entry‑point (optional convenience)
# ----------------------------------------------------------------------


def main() -> None:
    """
    Simple demonstration CLI that reads role and deletion JSON files,
    then evaluates a hard‑coded example access request.  This is **not**
    used by the test‑suite but can aid manual debugging.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Gatekeeper rule engine demo")
    parser.add_argument(
        "--roles",
        type=str,
        required=True,
        help="Path to JSON file containing role definitions",
    )
    parser.add_argument(
        "--deletions",
        type=str,
        required=True,
        help="Path to JSON file containing deletion logs",
    )
    args = parser.parse_args()

    roles = load_role_definitions(args.roles)
    deletions = load_deletion_logs(args.deletions)

    # Example request
    allowed, reason = check_access_policy(
        target_id="mem_123",
        context="User performed action with role: admin",
        target_domain="medical",
        action="read",
        deletion_logs=deletions,
        roles=roles,
    )
    print(f"Decision: {'ALLOW' if allowed else 'DENY'} – {reason}")


if __name__ == "__main__":
    main()