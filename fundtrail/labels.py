"""Address labels (mixers, bridges, exchanges) from bundled or user YAML."""

from __future__ import annotations

from importlib import resources
from pathlib import Path
from typing import Any

import yaml

Labels = dict[str, dict[str, dict[str, Any]]]


def load_labels(extra: list[str | Path] | None = None) -> Labels:
    text = resources.files("fundtrail").joinpath("data/labels.yaml").read_text("utf-8")
    labels: Labels = _normalise(yaml.safe_load(text) or {})
    for path in extra or []:
        with open(path, encoding="utf-8") as fh:
            for chain, entries in _normalise(yaml.safe_load(fh) or {}).items():
                labels.setdefault(chain, {}).update(entries)
    return labels


def _normalise(raw: dict[str, Any]) -> Labels:
    return {chain: {addr.lower(): dict(info) for addr, info in (entries or {}).items()}
            for chain, entries in raw.items()}


def lookup(labels: Labels, chain: str, address: str) -> dict[str, Any] | None:
    return labels.get(chain, {}).get(address.lower())
