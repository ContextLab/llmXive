"""Unit tests for the STRUCTURED-vs-PROSE channel classifier (spec 019, C1).

A STRUCTURED channel (constants / oeis / wikidata) carries an inherent
subject<->value link, so literal presence substantiates a fill. A PROSE channel
(wikipedia / theorem / paper, plus any unknown channel — fail-closed) is free
text where a value can appear coincidentally and must clear the semantic gate.
"""

from __future__ import annotations

import pytest

from llmxive.fill.channels import (
    AUTHORITY,
    STRUCTURED_CHANNELS,
    is_prose,
    is_structured,
)


@pytest.mark.parametrize("channel", ["constants", "oeis", "wikidata"])
def test_structured_channels(channel: str) -> None:
    assert is_structured(channel) is True
    assert is_prose(channel) is False


@pytest.mark.parametrize("channel", ["wikipedia", "theorem", "paper"])
def test_prose_channels(channel: str) -> None:
    assert is_prose(channel) is True
    assert is_structured(channel) is False


@pytest.mark.parametrize(
    "channel", ["", "unknown-xyz", "Wikipedia", "OEIS", "arxiv", "blog"]
)
def test_unknown_channel_is_prose_fail_closed(channel: str) -> None:
    """An unrecognized or differently-cased channel MUST default to PROSE so it
    gets the stricter gate (fail-closed, FR-001)."""
    assert is_prose(channel) is True
    assert is_structured(channel) is False


def test_structured_and_prose_are_complementary() -> None:
    """For every known channel and a few unknowns, exactly one of the predicates
    holds."""
    for channel in [*AUTHORITY, "", "mystery", "WIKIDATA"]:
        assert is_structured(channel) != is_prose(channel)


def test_structured_set_matches_documented_membership() -> None:
    assert STRUCTURED_CHANNELS == frozenset({"constants", "oeis", "wikidata"})
    # Every STRUCTURED channel is a real, ranked channel.
    assert STRUCTURED_CHANNELS <= set(AUTHORITY)
