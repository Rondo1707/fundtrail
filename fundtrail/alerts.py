"""Pluggable alert sources. Ships with an RSS/Atom feed source."""

from __future__ import annotations

import hashlib
import json
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Protocol

import requests

ATOM = "{http://www.w3.org/2005/Atom}"


@dataclass
class Alert:
    source: str
    id: str
    title: str
    link: str | None
    published: str | None
    matched: list[str]


class AlertSource(Protocol):
    name: str

    def fetch(self) -> list[Alert]: ...


def _fetch_text(url: str) -> str:
    resp = requests.get(url, timeout=20, headers={"User-Agent": "fundtrail/0.1"})
    resp.raise_for_status()
    return resp.text


class FeedSource:
    """RSS 2.0 or Atom feed, optionally filtered by keywords (case-insensitive)."""

    def __init__(self, name: str, url: str, keywords: Iterable[str] = (),
                 fetcher: Callable[[str], str] = _fetch_text) -> None:
        self.name = name
        self.url = url
        self.keywords = [k.lower() for k in keywords]
        self.fetcher = fetcher

    def fetch(self) -> list[Alert]:
        return self.parse(self.fetcher(self.url))

    def parse(self, text: str) -> list[Alert]:
        root = ET.fromstring(text)
        items = root.findall(".//item") or root.findall(f".//{ATOM}entry")
        out = []
        for it in items:
            title = _text(it, "title") or _text(it, f"{ATOM}title") or ""
            desc = (_text(it, "description") or _text(it, f"{ATOM}summary") or "")
            link = _text(it, "link")
            if not link:
                el = it.find(f"{ATOM}link")
                link = el.get("href") if el is not None else None
            published = (_text(it, "pubDate") or _text(it, f"{ATOM}updated")
                         or _text(it, f"{ATOM}published"))
            guid = _text(it, "guid") or _text(it, f"{ATOM}id") or link or title
            hay = f"{title} {desc}".lower()
            matched = [k for k in self.keywords if k in hay]
            if self.keywords and not matched:
                continue
            aid = hashlib.sha256(f"{self.name}|{guid}".encode()).hexdigest()[:16]
            out.append(Alert(self.name, aid, title.strip(), link, published, matched))
        return out


def _text(el: ET.Element, tag: str) -> str | None:
    child = el.find(tag)
    return child.text.strip() if child is not None and child.text else None


SOURCE_TYPES: dict[str, Callable[..., AlertSource]] = {"feed": FeedSource, "rss": FeedSource}


def build_sources(cfg: list[dict[str, Any]]) -> list[AlertSource]:
    sources = []
    for entry in cfg:
        entry = dict(entry)
        kind = entry.pop("type", "feed")
        if kind not in SOURCE_TYPES:
            raise ValueError(f"unknown alert source type: {kind}")
        sources.append(SOURCE_TYPES[kind](**entry))
    return sources


def run_alerts(sources: list[AlertSource], state_path: str | Path | None) -> dict[str, Any]:
    seen: set[str] = set()
    path = Path(state_path) if state_path else None
    if path and path.exists():
        seen = set(json.loads(path.read_text("utf-8")))
    new, errors = [], []
    for src in sources:
        try:
            for a in src.fetch():
                if a.id not in seen:
                    seen.add(a.id)
                    new.append(asdict(a))
        except (requests.RequestException, ET.ParseError) as exc:
            errors.append({"source": src.name, "error": str(exc)})
    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(sorted(seen)), "utf-8")
    return {"new": new, "errors": errors}
