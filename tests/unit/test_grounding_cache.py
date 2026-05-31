from llmxive.grounding import cache


def test_fulltext_roundtrip(tmp_path):
    cache.put_fulltext(tmp_path, "arxiv", "1706.03762",
                       {"tier": "arxiv", "full_text": "body", "abstract": None, "title": "T"})
    got = cache.get_fulltext(tmp_path, "arxiv", "1706.03762")
    assert got["full_text"] == "body" and got["tier"] == "arxiv"
    assert cache.get_fulltext(tmp_path, "arxiv", "nope") is None


def test_verdict_roundtrip_and_key_includes_number(tmp_path):
    cache.put_verdict(tmp_path, source_id="doi:10.x/y", claim="c", number="42",
                      verdict={"status": "grounded", "ok": True, "reason": ""})
    assert cache.get_verdict(tmp_path, source_id="doi:10.x/y", claim="c", number="42")["ok"] is True
    # different number -> different key -> miss
    assert cache.get_verdict(tmp_path, source_id="doi:10.x/y", claim="c", number="43") is None


def test_expired_entry_ignored(tmp_path):
    cache.put_verdict(tmp_path, source_id="s", claim="c", number=None,
                      verdict={"status": "grounded", "ok": True, "reason": ""})
    assert cache.get_verdict(tmp_path, source_id="s", claim="c", number=None,
                             max_age_s=-1) is None  # negative TTL => always expired
