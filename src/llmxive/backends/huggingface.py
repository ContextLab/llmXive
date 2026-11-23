"""Hugging Face Inference Providers backend (spec 027): one OpenAI-compatible chat call.

This module is only the transport. Which model to call, how much it may cost and
whether the monthly budget allows it are decided elsewhere (model selection and the
execute path); here a request is sent to the Hugging Face router and every outcome
is mapped to the shared backend error taxonomy.

Model ids are pinned ``repo:provider`` strings (for example ``acme/alpha-large:prov-a``);
the router routes to exactly that provider. Every request carries the ``X-HF-Bill-To``
header naming the resource group that pays (read from ``LLMXIVE_HF_BILL_TO``); without
it the router answers HTTP 402, so a missing value fails closed before any request.

Exactly one HTTP attempt is made per :meth:`HuggingFaceBackend.chat`; retries and
fallback belong to the router layer. Neither the token nor the bill-to value is ever
placed in an exception message.
"""

from __future__ import annotations

import os
from collections.abc import Iterable
from typing import Any

import httpx

from llmxive.backends.base import (
    BackendCredentialError,
    BackendUnavailable,
    BaseBackend,
    ChatMessage,
    ChatResponse,
    CircuitBreaker,
    EmptyReplyError,
    PermanentBackendError,
    TransientBackendError,
    invoke_with_deadline,
    openai_content,
)
from llmxive.credentials import load_hf_token

ROUTER_BASE_URL = "https://router.huggingface.co/v1"
BILL_TO_ENV = "LLMXIVE_HF_BILL_TO"
BILL_TO_HEADER = "X-HF-Bill-To"

#: Reasoning-model deadline applied to every model: the catalog cannot say which
#: models reason (spec 5.9.4), so none gets the shorter non-reasoning deadline.
_DEFAULT_DEADLINE_S = 360.0
_MAX_ERROR_CHARS = 300


class PreInferenceRejection(Exception):
    """Marker: the provider rejected the request before inference, or it was never sent.

    No tokens were generated and no inference cost was incurred, so a caller may
    release the budget it reserved for the call.
    """


class HFPaymentRequired(PreInferenceRejection, BackendUnavailable):
    """HTTP 402: the bill-to group has no credit (or the bill-to header was missing)."""


class HFCredentialRejected(PreInferenceRejection, BackendCredentialError):
    """The credential cannot serve any request.

    ``http_status`` is 401/403 when the router refused it, or ``None`` when the
    request was never sent because the token or the bill-to value is missing.
    """

    def __init__(self, message: str, *, http_status: int | None = None) -> None:
        super().__init__(message)
        self.http_status = http_status


def request_was_sent(exc: BaseException) -> bool:
    """Whether the request that raised ``exc`` may have reached the provider.

    ``False`` only when :meth:`HuggingFaceBackend.chat` recorded that no request was
    or will be sent; an exception without that record (from another backend, or one
    that refused the attribute) reads as sent — the safe answer for budget accounting."""
    return getattr(exc, "request_sent", True) is not False


def _deadline_s() -> float:
    return float(os.environ.get("LLMXIVE_HF_DEADLINE_S", str(_DEFAULT_DEADLINE_S)))


def fetch_router_catalog(*, base_url: str = ROUTER_BASE_URL, timeout: float = 30.0) -> dict:
    """GET ``/models`` from the router (keyless: the catalog is public)."""
    try:
        resp = httpx.get(f"{base_url.rstrip('/')}/models", timeout=timeout)
    except httpx.HTTPError as exc:
        raise TransientBackendError(f"Hugging Face catalog fetch failed: {type(exc).__name__}") from exc
    if resp.status_code != 200:
        raise TransientBackendError(f"Hugging Face catalog fetch returned HTTP {resp.status_code}")
    try:
        body = resp.json()
    except ValueError as exc:
        raise TransientBackendError("Hugging Face catalog was not JSON") from exc
    if not isinstance(body, dict):
        raise TransientBackendError("Hugging Face catalog had an unexpected shape")
    return body


def _error_text(resp: httpx.Response, secrets: Iterable[str]) -> str:
    """Extract a short, secret-free message from an error body (string or object form)."""
    try:
        body: Any = resp.json()
    except ValueError:
        body = resp.text
    err = body.get("error", body) if isinstance(body, dict) else body
    if isinstance(err, dict):
        err = err.get("message") or err.get("type") or ""
    text = str(err)[:_MAX_ERROR_CHARS]
    for secret in secrets:
        if secret:
            text = text.replace(secret, "<redacted>")
    return text


class HuggingFaceBackend(BaseBackend):
    """OpenAI-compatible chat against the Hugging Face router, billed to a resource group."""

    name = "huggingface"
    is_paid = False  # funding is governed by the budget layer, not this flag

    def __init__(
        self,
        *,
        token: str | None = None,
        bill_to: str | None = None,
        base_url: str = ROUTER_BASE_URL,
    ) -> None:
        self._token = token
        self._bill_to = bill_to
        self._base_url = base_url.rstrip("/")
        self._breakers: dict[str, CircuitBreaker] = {}

    # ---- credentials -------------------------------------------------
    def _credentials(self) -> tuple[str, str]:
        token = (self._token or load_hf_token() or "").strip()
        bill_to = (self._bill_to or os.environ.get(BILL_TO_ENV, "")).strip()
        missing = []
        if not token:
            missing.append("HF_TOKEN (or the llmxive-huggingface Keychain item)")
        if not bill_to:
            missing.append(BILL_TO_ENV)
        if missing:
            raise HFCredentialRejected(
                "Hugging Face request not sent; missing " + " and ".join(missing), http_status=None
            )
        return token, bill_to  # type: ignore[return-value]

    def _breaker(self, model: str) -> CircuitBreaker:
        br = self._breakers.get(model)
        if br is None:
            br = self._breakers[model] = CircuitBreaker(
                max_consecutive=3, window_s=1800.0, label="Hugging Face"
            )
        return br

    # ---- BaseBackend -------------------------------------------------
    def list_models(self) -> list[str]:
        data = fetch_router_catalog(base_url=self._base_url).get("data") or []
        return [m["id"] for m in data if isinstance(m, dict) and isinstance(m.get("id"), str)]

    def chat(
        self,
        messages: Iterable[ChatMessage],
        *,
        model: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
        deadline_s: float | None = None,
    ) -> ChatResponse:
        """One chat request. Any exception leaving this method carries
        ``request_sent`` (read it with :func:`request_was_sent`): ``False`` only when it
        is certain no HTTP request was or will be sent — missing credentials, or the
        circuit breaker refusing before the request thread starts. Once that thread
        starts it is ``True``, even if the request has not reached the network yet (a
        deadline can abandon the thread before it sends, and the thread may still send)."""
        started = False
        try:
            token, bill_to = self._credentials()
            payload: dict[str, Any] = {
                "model": model,
                "messages": [{"role": m.role, "content": openai_content(m.content)} for m in messages],
                "stream": False,
            }
            if max_tokens is not None:
                payload["max_tokens"] = max_tokens
            if temperature is not None:
                payload["temperature"] = temperature
            headers = {"Authorization": f"Bearer {token}", BILL_TO_HEADER: bill_to}
            deadline = deadline_s if deadline_s is not None else _deadline_s()

            def _attempt() -> ChatResponse:
                try:
                    resp = httpx.post(
                        f"{self._base_url}/chat/completions",
                        json=payload,
                        headers=headers,
                        timeout=deadline,
                    )
                except httpx.HTTPError as exc:
                    raise TransientBackendError(
                        f"Hugging Face model {model!r}: {type(exc).__name__}"
                    ) from exc
                return self._parse(resp, model, secrets=(token, bill_to))

            def _dispatch() -> ChatResponse:
                nonlocal started
                started = True  # from here on a request may leave, whatever happens next
                return invoke_with_deadline(
                    _attempt, timeout=deadline, description=f"Hugging Face model {model!r}"
                )

            return self._breaker(model).call(_dispatch)
        except Exception as exc:
            try:
                exc.request_sent = started  # type: ignore[attr-defined]
            except AttributeError:  # refuses attributes → request_was_sent() reads "sent"
                pass
            raise

    def healthcheck(self) -> bool:
        try:
            fetch_router_catalog(base_url=self._base_url, timeout=10.0)
        except TransientBackendError:
            return False
        return True

    # ---- response mapping --------------------------------------------
    def _parse(self, resp: httpx.Response, model: str, *, secrets: tuple[str, ...]) -> ChatResponse:
        status = resp.status_code
        if status != 200:
            detail = _error_text(resp, secrets)
            msg = f"Hugging Face model {model!r}: HTTP {status}: {detail}"
            if status == 402:
                raise HFPaymentRequired(msg)
            if status in (401, 403):
                raise HFCredentialRejected(msg, http_status=status)
            if status in (408, 429) or status >= 500:
                raise TransientBackendError(msg)
            raise PermanentBackendError(msg)
        try:
            body = resp.json()
            choice = body["choices"][0]
            if not isinstance(choice, dict):
                raise TypeError("choice is not an object")
            content = choice["message"].get("content")
            if isinstance(content, list):  # OpenAI content parts: keep the text parts
                content = "".join(
                    p["text"]
                    for p in content
                    if isinstance(p, dict) and p.get("type", "text") == "text" and isinstance(p.get("text"), str)
                )
            elif content is not None and not isinstance(content, str):
                raise TypeError("content is not text")
        except (ValueError, KeyError, IndexError, TypeError, AttributeError) as exc:
            raise TransientBackendError(
                f"Hugging Face model {model!r}: malformed 200 response"
            ) from exc
        if not (content or "").strip():
            if choice.get("finish_reason") == "length":
                raise TransientBackendError(
                    f"Hugging Face model {model!r}: reasoning budget exhausted "
                    "(empty content, finish_reason=length)"
                )
            raise EmptyReplyError(f"Hugging Face model {model!r}: empty reply")
        usage = body.get("usage") or {}
        return ChatResponse(
            text=content,
            model=model,
            backend=self.name,
            input_tokens=usage.get("prompt_tokens"),
            output_tokens=usage.get("completion_tokens"),
        )


__all__ = [
    "BILL_TO_ENV",
    "BILL_TO_HEADER",
    "ROUTER_BASE_URL",
    "HFCredentialRejected",
    "HFPaymentRequired",
    "HuggingFaceBackend",
    "PreInferenceRejection",
    "fetch_router_catalog",
    "request_was_sent",
]
