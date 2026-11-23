"""Versioned capability policy (spec 026, slice 2).

The **capability policy** is the reviewed canonical artifact that attributes
*competence* to models. Eligibility in ``select`` is the INTERSECTION of this
policy and the live snapshot (FR-006): the catalog proves a model's
presence / identifier / pricing (and possibly context limits), but it MUST NOT
be read as proof of competence — a model absent from this policy is INELIGIBLE
regardless of how it appears in the catalog.

Keyed by ``model_family`` (not raw ``model_id``): the family is the drift-
resistant identity the snapshot already derives (``snapshot._family_of`` strips
date/size suffixes), so a dated catalog id like
``anthropic.claude-haiku-4-5-20251001`` still resolves to the reviewed
``claude-haiku-4-5`` entry, and independence's ``family`` dimension lines up
with the same key.

``selection_policy_version`` (``SELECTION_POLICY_VERSION``) is part of
``select``'s pure input: bumping it is how a policy change becomes a NEW,
distinguishable decision (SC-001). Changes to this table are ordinary reviewed
human PRs (Constitution I), never autonomous.

The v1 table encodes the maintainer-approved consolidated free chain
``qwen.qwen3.5-122b`` → ``google.gemma-4-31B-it`` → ``openai.gpt-oss-120b`` →
guarded paid ``anthropic.claude-haiku-4-5`` (gemma-3 is DELIBERATELY absent —
the approved gemma-3→gemma-4 correction makes gemma-3 ineligible), plus the
vision peer ``qwen.qwen3-vl`` and the local ``Qwen/Qwen2.5-3B-Instruct``
fallback. The qwen→gemma-4→gpt-oss order is produced by ``select``'s tie-breaks
(quality tier, then stable model id), matching the legacy ``MODEL_FALLBACKS``.

v2 (spec 026 slice 7, 2026-07-19) attributes ``qwen3.5`` the ``vision``
capability + feature. This is NOT a guess: a real call gave
``qwen.qwen3.5-122b`` a pure-red 256x256 PNG (as
:class:`~llmxive.backends.base.ImagePart` content, routed through
``route_chat(profile="vision")``) and it correctly answered "Red" — genuine
image UNDERSTANDING, not merely payload acceptance (Constitution II; see
``tests/real_call/test_vision_real.py``,
``test_qwen35_actually_understands_images``). A second real call routed the
same image to ``qwen.qwen3-vl:32b`` via
``RequirementOverrides(exclude_leader=True)``
(``test_qwen3_vl_serves_the_canonical_multimodal_representation``), which
also correctly answered "Red", confirming that peer independently consumes
the new ``ContentPart`` representation (SC-008). ``qwen3-vl`` remains the
dedicated vision peer (its own attribution is unchanged) so the paper
figure-review call (``paper_reprocess.preprint_figures``) can still reach it
via ``RequirementOverrides(exclude_leader=True)`` when it needs a second
opinion independent of qwen3.5.

v3 (2026-11-23, merge of ``main`` into the spec-026 branch) adds the
``glm-5.3`` family (``zai-org.glm-5.3``) as the TEXT leader. ``main`` had made
it the registry-wide default model and the head of its fallback table
(``glm-5.3`` → ``gpt-oss`` → ``gemma-4`` → guarded paid haiku); under this
policy that intent is expressed as the highest quality tier, so ``select``
ranks it first for ``cheap`` / ``standard`` / ``deep`` and the free text chain
becomes ``zai-org.glm-5.3`` → ``qwen.qwen3.5-122b`` → ``google.gemma-4-31B-it``
→ ``openai.gpt-oss-120b`` → guarded paid ``anthropic.claude-haiku-4-5``. Two
differences from ``main``'s table follow from keeping ONE policy rather than a
per-primary table: qwen3.5 stays in the chain (second), and gemma-4 precedes
gpt-oss (the existing tier-2 tie-break on model id).

What is attributed to ``glm-5.3``, and on what evidence in this repository:

- ``reasoning``: ``backends.dartmouth._REASONING_MODELS`` lists ``"glm-5"``
  (it gets the reasoning deadline), and ``main`` ran every reasoning agent on it.
- ``structured``: ``main`` ran the structured-output agents (reviewers,
  revisers, verifiers) on it as their default model.
- NOT ``vision``: nothing in the repository shows it understanding an image, so
  it is not attributed the capability (Constitution II). The ``vision`` chain is
  unchanged (``qwen3.5`` → ``qwen3-vl``).
- ``max_context_tokens=128_000`` is an ASSUMPTION, not a verified fact: the
  repository states no context window for this model, so it takes the smallest
  window among its Dartmouth-hosted text peers (gemma-4 / gpt-oss). Raise it
  only with a verified figure.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from llmxive.model_selection.types import Capability

#: Bump when the table below changes in a way that can alter a decision. Part of
#: ``select``'s pure input so the same snapshot+requirement under a different
#: policy version is a DIFFERENT (distinguishable) decision.
SELECTION_POLICY_VERSION = 3


@dataclass(frozen=True)
class PolicyEntry:
    """A model family's reviewed capability attribution.

    - ``capabilities``: the requirement ``capability`` values this family is
      trusted to serve (``{"cheap","standard","deep","vision"}``).
    - ``features``: named features the family provides (matched against a
      requirement's ``required_features``).
    - ``quality_tier``: higher = preferred among same-cost candidates (the
      "preferred quality tier" tie-break, FR-008 rung 4). Comparable ONLY within
      this policy; not an absolute benchmark.
    - ``max_context_tokens``: the family's usable context window, used to honor a
      requirement's ``min_context_tokens`` (the catalog does not surface this).
    """

    capabilities: frozenset[Capability]
    features: frozenset[str]
    quality_tier: int
    max_context_tokens: int


@dataclass(frozen=True)
class CapabilityPolicy:
    """A versioned, immutable ``family -> PolicyEntry`` table + its version.

    Injectable into ``select`` for tests; the module-level ``CAPABILITY_POLICY``
    is the production default.
    """

    version: int
    entries: Mapping[str, PolicyEntry]

    def __post_init__(self) -> None:
        object.__setattr__(self, "entries", MappingProxyType(dict(self.entries)))

    def entry(self, family: str) -> PolicyEntry | None:
        """The reviewed attribution for ``family``, or ``None`` if the family is
        not in the policy (→ ineligible)."""
        return self.entries.get(family)

    def has_capability(self, family: str, capability: Capability) -> bool:
        e = self.entries.get(family)
        return e is not None and capability in e.capabilities

    def has_features(self, family: str, required: frozenset[str]) -> bool:
        e = self.entries.get(family)
        return e is not None and required <= e.features

    def quality_tier(self, family: str) -> int:
        e = self.entries.get(family)
        return e.quality_tier if e is not None else 0

    def max_context_tokens(self, family: str) -> int | None:
        e = self.entries.get(family)
        return e.max_context_tokens if e is not None else None


# --------------------------------------------------------------------------- #
# The canonical policy. Context windows are the maintainer-verified usable
# limits (router notes: qwen3.5 256K, gpt-oss/gemma-4 128K, claude-haiku ~200K).
# qwen3.5 is ALSO attributed ``vision`` as of v2 (real-call verified — see the
# module docstring); ``qwen3-vl`` is attributed ONLY ``vision`` so it never
# intrudes on the text chains (behavior-preserving vs the legacy
# MODEL_FALLBACKS, which never routed text through a VL model); the paid
# ``claude-haiku-4-5`` stays a TEXT fallback (no vision) — its role in the
# legacy chain. glm-5.3 (v3) is the text leader — the top quality tier; its
# 128K window is an assumed conservative value (see the module docstring).
# --------------------------------------------------------------------------- #
CAPABILITY_POLICY = CapabilityPolicy(
    version=SELECTION_POLICY_VERSION,
    entries={
        "glm-5.3": PolicyEntry(
            capabilities=frozenset({"cheap", "standard", "deep"}),
            features=frozenset({"reasoning", "structured"}),
            quality_tier=4,
            max_context_tokens=128_000,
        ),
        "qwen3.5": PolicyEntry(
            capabilities=frozenset({"cheap", "standard", "deep", "vision"}),
            features=frozenset({"reasoning", "structured", "vision"}),
            quality_tier=3,
            max_context_tokens=256_000,
        ),
        "gemma-4": PolicyEntry(
            capabilities=frozenset({"cheap", "standard", "deep"}),
            features=frozenset({"structured"}),
            quality_tier=2,
            max_context_tokens=128_000,
        ),
        "gpt-oss": PolicyEntry(
            capabilities=frozenset({"cheap", "standard", "deep"}),
            features=frozenset({"reasoning", "structured"}),
            quality_tier=2,
            max_context_tokens=128_000,
        ),
        "claude-haiku-4-5": PolicyEntry(
            capabilities=frozenset({"cheap", "standard", "deep"}),
            features=frozenset({"reasoning", "structured"}),
            quality_tier=3,
            max_context_tokens=200_000,
        ),
        "qwen3-vl": PolicyEntry(
            capabilities=frozenset({"vision"}),
            features=frozenset({"vision", "structured"}),
            quality_tier=2,
            max_context_tokens=128_000,
        ),
        "qwen2.5": PolicyEntry(
            capabilities=frozenset({"cheap", "standard"}),
            features=frozenset({"structured"}),
            quality_tier=1,
            max_context_tokens=32_768,
        ),
    },
)
