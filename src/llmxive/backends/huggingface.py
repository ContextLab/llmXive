"""Hugging Face Inference Providers backend (spec 027): one OpenAI-compatible chat call.

This module is only the transport. Which model to call, how much it may cost and
whether the monthly budget allows it are decided elsewhere (model selection and the
execute path); here a request is sent to the Hugging Face router and every outcome
is mapped to the shared backend error taxonomy.

Model ids are pinned ``repo:provider`` strings (for example ``acme/alpha-large:prov-a``);
the router routes to exactly that provider. Every request carries the ``X-HF-Bill-To``
header naming the resource group that pays (read from ``LLMXIVE_HF_BILL_TO``); without
it the router answers HTTP 402, so a missing value fails closed before any request.

Replies are requested as a server-sent-events stream (``stream: true`` with
``stream_options.include_usage``) and assembled here. A non-streamed request kept the
connection silent until the whole reply was generated: long code-writing replies
then outlasted the fixed 360 s client deadline, or the provider gateway answered
HTTP 504 after 120 s (both seen on 2026-11-24; the same request, streamed,
completed). Streaming keeps data flowing, so the deadline (``LLMXIVE_HF_DEADLINE_S``, default 360 s) now bounds
silence, and ``LLMXIVE_HF_TOTAL_DEADLINE_S`` (default 1800 s) bounds a reply that is
still arriving. The usage chunk the stream ends with is reported as the reply's
token counts; when a provider omits it the counts stay ``None`` and the funded
ledger charges the full reservation. A provider that answers with a plain JSON body
instead of a stream is parsed as before.

Exactly one HTTP attempt is made per :meth:`HuggingFaceBackend.chat`; retries and
fallback belong to the router layer. Neither the token nor the bill-to value is ever
placed in an exception message.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Iterable
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
    invoke_with_idle_deadline,
    openai_content,
)
from llmxive.credentials import load_hf_token

ROUTER_BASE_URL = "https://router.huggingface.co/v1"
BILL_TO_ENV = "LLMXIVE_HF_BILL_TO"
BILL_TO_HEADER = "X-HF-Bill-To"

#: Reasoning-model deadline applied to every model: the catalog cannot say which
#: models reason (spec 5.9.4), so none gets the shorter non-reasoning deadline.
#: Replies are streamed, so this bounds SILENCE: the wait for the first data and
#: every gap between data after it (``LLMXIVE_HF_DEADLINE_S``).
_DEFAULT_DEADLINE_S = 360.0
#: Upper bound on one streamed reply that keeps arriving (``LLMXIVE_HF_TOTAL_DEADLINE_S``).
_DEFAULT_TOTAL_DEADLINE_S = 1800.0
_SOCKET_SLACK_S = 5.0
_MAX_ERROR_CHARS = 300


class PreInferenceRejection(Exception):
    """Marker: the provider rejected the request before inference, or it was never sent.

    No tokens were generated and no inference cost was incurred, so a caller may
    release the budget it reserved for the call.
    """


class HFPaymentRequired(PreInferenceRejection, BackendUnavailable):
    """HTTP 402: the bill-to group has no credit (or the bill-to header was missing)."""


class HFRouteUnavailable(BackendUnavailable):
    """HTTP 404, or HTTP 400 with code ``model_not_supported``: the router has no
    provider it may use for this model and request (for example "No allowed
    providers are available for the selected model" when the pinned provider
    serves the model's text calls but not image input, or "not supported by
    provider" when the pinned provider has stopped serving the model).

    Another candidate may serve the request, so the chain advances
    (``disposition_of`` treats every :class:`BackendUnavailable` that way). It is
    NOT a :class:`PreInferenceRejection`: the funded hold is charged in full, as for
    any rejection other than 401/402/403. Being a permanent error it does not count
    toward the model's circuit breaker, so the pair's text calls are unaffected.
    """


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


def _total_deadline_s() -> float:
    return float(os.environ.get("LLMXIVE_HF_TOTAL_DEADLINE_S", str(_DEFAULT_TOTAL_DEADLINE_S)))


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
    return _safe_error_text(err, secrets)


# The router's error code when the pinned provider does not serve the model (a
# provider can drop a model after the catalog snapshot that listed the pair).
_MODEL_NOT_SUPPORTED = "model_not_supported"


def _error_code(resp: httpx.Response) -> str:
    """The machine-readable ``error.code`` of an error body, or ``""``."""
    try:
        body: Any = resp.json()
    except ValueError:
        return ""
    err = body.get("error") if isinstance(body, dict) else None
    code = err.get("code") if isinstance(err, dict) else None
    return code if isinstance(code, str) else ""


def _safe_error_text(err: Any, secrets: Iterable[str]) -> str:
    """``err`` (string or ``{"message"|"type"}`` object) as a short message with
    every secret removed. Secrets are removed from the WHOLE text before it is
    shortened: shortening first could cut a secret in two and leave its first
    part in the message."""
    if isinstance(err, dict):
        err = err.get("message") or err.get("type") or ""
    text = str(err)
    for secret in secrets:
        if secret:
            text = text.replace(secret, "<redacted>")
    return text[:_MAX_ERROR_CHARS]


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
        """The per-model breaker. ``dict.setdefault`` is atomic, so threads that
        race on a model's first call all get the SAME breaker (a check-then-set
        could hand two threads different breakers and lose a recorded failure)."""
        br = self._breakers.get(model)
        if br is None:
            br = self._breakers.setdefault(
                model, CircuitBreaker(max_consecutive=3, window_s=1800.0, label="Hugging Face")
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
                "stream": True,
                "stream_options": {"include_usage": True},
            }
            if max_tokens is not None:
                payload["max_tokens"] = max_tokens
            if temperature is not None:
                payload["temperature"] = temperature
            headers = {"Authorization": f"Bearer {token}", BILL_TO_HEADER: bill_to}
            idle = deadline_s if deadline_s is not None else _deadline_s()
            total = max(_total_deadline_s(), idle)
            secrets = (token, bill_to)

            def _attempt(progress: Callable[[], None]) -> ChatResponse:
                try:
                    with httpx.stream(
                        "POST",
                        f"{self._base_url}/chat/completions",
                        json=payload,
                        headers=headers,
                        # The idle watchdog below decides; the socket timeout is only a
                        # backstop that ends an abandoned worker blocked on a read.
                        timeout=httpx.Timeout(idle + _SOCKET_SLACK_S),
                    ) as resp:
                        progress()  # the status line and headers arrived
                        if resp.status_code != 200:
                            resp.read()
                            return self._parse(resp, model, secrets=secrets)
                        ctype = resp.headers.get("content-type", "")
                        if not ctype.startswith("text/event-stream"):
                            resp.read()  # the provider answered without streaming
                            return self._parse(resp, model, secrets=secrets)
                        return self._parse_stream(resp, model, progress, secrets=secrets)
                except httpx.HTTPError as exc:
                    raise TransientBackendError(
                        f"Hugging Face model {model!r}: {type(exc).__name__}"
                    ) from exc

            def _dispatch() -> ChatResponse:
                nonlocal started
                started = True  # from here on a request may leave, whatever happens next
                return invoke_with_idle_deadline(
                    _attempt,
                    idle_timeout=idle,
                    total_timeout=total,
                    description=f"Hugging Face model {model!r}",
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
            if status == 404 or (status == 400 and _error_code(resp) == _MODEL_NOT_SUPPORTED):
                raise HFRouteUnavailable(msg)  # this pair cannot serve this request; try the next
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
        return self._reply(content, choice.get("finish_reason"), body.get("usage"), model)

    def _parse_stream(
        self,
        resp: httpx.Response,
        model: str,
        progress: Callable[[], None],
        *,
        secrets: tuple[str, ...],
    ) -> ChatResponse:
        """Assemble a server-sent-events reply: ``data:`` lines carrying
        ``chat.completion.chunk`` objects, then ``data: [DONE]``. Text is the
        concatenated ``delta.content``; the usage is read from the chunk that
        reports it (``stream_options.include_usage``: an extra chunk with empty
        ``choices`` just before ``[DONE]``). ``progress()`` is called for every
        line received, reasoning deltas and keep-alive comments included, so the
        idle deadline measures silence rather than total length.

        A stream that closes with neither a ``finish_reason`` nor ``[DONE]`` was
        cut off and is a :class:`TransientBackendError`, never a partial reply; an
        ``error`` object inside the stream is one too."""
        pieces: list[str] = []
        finish: str | None = None
        usage: Any = None
        done = False
        for line in resp.iter_lines():
            progress()
            if not line.startswith("data:"):
                continue  # blank separators, ``:`` comments, ``event:``/``id:`` fields
            data = line[5:].strip()
            if data == "[DONE]":
                done = True
                break
            try:
                chunk = json.loads(data)
                if not isinstance(chunk, dict):
                    raise TypeError("chunk is not an object")
                if chunk.get("error") is not None:
                    text = _safe_error_text(chunk["error"], secrets)
                    raise TransientBackendError(f"Hugging Face model {model!r}: error in stream: {text}")
                if chunk.get("usage") is not None:
                    usage = chunk["usage"]
                for choice in chunk.get("choices") or []:
                    delta = choice.get("delta") or {}
                    content = delta.get("content")
                    if isinstance(content, str):
                        pieces.append(content)
                    elif content is not None:
                        raise TypeError("delta content is not text")
                    if choice.get("finish_reason"):
                        finish = choice["finish_reason"]
            except (ValueError, TypeError, AttributeError) as exc:
                raise TransientBackendError(
                    f"Hugging Face model {model!r}: malformed stream chunk"
                ) from exc
        if not done and finish is None:
            raise TransientBackendError(
                f"Hugging Face model {model!r}: stream ended before the reply was complete"
            )
        return self._reply("".join(pieces), finish, usage, model)

    def _reply(self, content: str | None, finish: Any, usage: Any, model: str) -> ChatResponse:
        """The shared tail of both reply forms: empty-reply classes, then usage.
        A count the provider did not report stays ``None`` (the funded ledger then
        charges the full reservation)."""
        if not (content or "").strip():
            if finish == "length":
                raise TransientBackendError(
                    f"Hugging Face model {model!r}: reasoning budget exhausted "
                    "(empty content, finish_reason=length)"
                )
            raise EmptyReplyError(f"Hugging Face model {model!r}: empty reply")
        usage = usage if isinstance(usage, dict) else {}
        return ChatResponse(
            text=content,  # type: ignore[arg-type]
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
    "HFRouteUnavailable",
    "HuggingFaceBackend",
    "PreInferenceRejection",
    "fetch_router_catalog",
    "request_was_sent",
]
