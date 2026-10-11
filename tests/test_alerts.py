from __future__ import annotations

from conftest import FIXTURES
from fundtrail.alerts import FeedSource, build_sources, run_alerts

RSS = (FIXTURES / "rekt_feed.xml").read_text("utf-8")
ATOM = """<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Bridge exploit drains $5M</title>
<id>urn:1</id><link href="https://example.org/a"/><updated>2026-10-10T00:00:00Z</updated>
<summary>details</summary></entry></feed>"""


def test_rss_parse_all_items() -> None:
    items = FeedSource("rekt", "u", fetcher=lambda u: RSS).fetch()
    assert len(items) == 3 and items[0].link.startswith("https://www.rekt.news/")


def test_keyword_filter_and_atom() -> None:
    src = FeedSource("x", "u", keywords=["exploit"], fetcher=lambda u: ATOM)
    items = src.fetch()
    assert len(items) == 1 and items[0].matched == ["exploit"]
    assert items[0].link == "https://example.org/a"


def test_dedupe_with_state(tmp_path) -> None:
    state = tmp_path / "seen.json"
    srcs = [FeedSource("rekt", "u", fetcher=lambda u: RSS)]
    assert len(run_alerts(srcs, state)["new"]) == 3
    assert run_alerts(srcs, state)["new"] == []


def test_build_sources_from_config() -> None:
    srcs = build_sources([{"type": "feed", "name": "a", "url": "https://x", "keywords": ["k"]}])
    assert srcs[0].name == "a"
