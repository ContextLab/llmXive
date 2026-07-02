"""Shared external memory buffer with <MEMORY_ACTION> token handling.

This module provides a thread‑safe ``MemoryBuffer`` that stores
:class:`MemoryAction` objects.  In addition to the original ``add``/``clear``
API, the buffer now understands a textual token syntax used throughout the
code base:

    <MEMORY_ACTION type=ACTION_TYPE payload={...}>

The token is parsed into a :class:`MemoryAction` instance and stored in the
buffer.  This satisfies FR‑003 which requires handling of the
``<MEMORY_ACTION>`` token.

The implementation is deliberately tolerant:
* ``add`` accepts either a ``MemoryAction`` object **or** a token string.
* Unknown attributes accessed on a ``MemoryBuffer`` instance resolve to a
  no‑op callable (via ``__getattr__``) so that future log‑style calls do not
  raise ``AttributeError``.
* ``reset`` is provided for legacy test code and simply clears the buffer.
"""
from __future__ import annotations

import ast
import json
import re
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Union

@dataclass
class MemoryAction:
    """A single action that can be stored in the external memory buffer.

    Attributes
    ----------
    action_type: str
        Identifier of the action (e.g. ``store``, ``retrieve``).
    payload: dict
        Arbitrary JSON‑serialisable data associated with the action.
    """
    action_type: str
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain‑dictionary representation (useful for logging)."""
        return {"action_type": self.action_type, "payload": self.payload}

class MemoryBuffer:
    """Thread‑safe buffer for storing ``MemoryAction`` objects.

    The buffer is deliberately permissive: any unknown method name accessed
    on an instance returns a no‑op callable, making it compatible with
    legacy callers that expect logger‑style methods (e.g. ``info()``,
    ``debug()``).
    """

    _TOKEN_REGEX = re.compile(
        r"""
        ^<MEMORY_ACTION                # opening token
        \s+type=(?P<type>\w+)         # mandatory ``type`` field
        (?:\s+payload=(?P<payload>.+))? # optional ``payload`` field
        >$                             # closing token
        """,
        re.VERBOSE,
    )

    def __init__(self) -> None:
        self._actions: List[MemoryAction] = []
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------
    def add(self, action: Union[MemoryAction, str]) -> None:
        """Add an action to the buffer.

        Parameters
        ----------
        action : MemoryAction | str
            Either a ready‑made :class:`MemoryAction` instance or a textual
            ``<MEMORY_ACTION>`` token.  If a string token is supplied it is
            parsed into a :class:`MemoryAction` before being stored.
        """
        if isinstance(action, str):
            action = self._parse_token(action)
        if not isinstance(action, MemoryAction):
            raise TypeError(
                "MemoryBuffer.add expects a MemoryAction or a valid token string"
            )
        with self._lock:
            self._actions.append(action)

    def get_all(self) -> List[MemoryAction]:
        """Return a shallow copy of all stored actions."""
        with self._lock:
            return list(self._actions)

    def clear(self) -> None:
        """Remove all stored actions."""
        with self._lock:
            self._actions.clear()

    # ------------------------------------------------------------------
    # Compatibility helpers
    # ------------------------------------------------------------------
    def reset(self) -> None:
        """Legacy compatibility method – clears the buffer."""
        self.clear()

    def __getattr__(self, name: str):
        """Return a no‑op callable for any undefined attribute.

        This makes the buffer tolerant of calls like ``info()``,
        ``debug()`` or any future method names without raising
        ``AttributeError``.
        """
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop

    # ------------------------------------------------------------------
    # Token handling
    # ------------------------------------------------------------------
    @classmethod
    def _parse_token(cls, token: str) -> MemoryAction:
        """Parse a ``<MEMORY_ACTION>`` token into a :class:`MemoryAction`.

        The expected token format is::

            <MEMORY_ACTION type=TYPE payload={...}>

        * ``TYPE`` is a word consisting of alphanumerics and underscores.
        * ``payload`` is optional; when present it must be a JSON‑compatible
          literal (e.g. ``{"key": 1}``) or a Python literal that can be parsed
          with :func:`ast.literal_eval`.

        Raises
        ------
        ValueError
            If the token does not match the expected pattern.
        """
        match = cls._TOKEN_REGEX.match(token.strip())
        if not match:
            raise ValueError(f"Invalid MEMORY_ACTION token: {token!r}")

        action_type = match.group("type")
        payload_str = match.group("payload")

        if payload_str is None:
            payload = {}
        else:
            # Try JSON first; fall back to Python literal evaluation.
            try:
                payload = json.loads(payload_str)
            except json.JSONDecodeError:
                try:
                    payload = ast.literal_eval(payload_str)
                except (SyntaxError, ValueError) as exc:
                    raise ValueError(
                        f"Could not parse payload in MEMORY_ACTION token: {payload_str!r}"
                    ) from exc
            if not isinstance(payload, dict):
                raise ValueError(
                    "Payload of MEMORY_ACTION token must be a mapping/dict"
                )
        return MemoryAction(action_type=action_type, payload=payload)