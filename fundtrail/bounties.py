"""Diff the Immunefi public program listing against a saved snapshot.

Lesson from the earlier prototype: Immunefi re-issues internal row ids
(e.g. reward ids) without changing anything meaningful, so the comparison
uses a normalised view that drops volatile ids and keeps amounts, scope
size and status.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import requests

TRACKED = ("project", "maxBounty", "isPaused", "inviteOnly", "kyc",
           "launchDate", "endDate", "rewardsToken")


def _reward_rows(program: dict[str, Any]) -> list[tuple[Any, ...]]:
    rows = []
    for r in program.get("rewards") or []:
        rows.append((r.get("assetType"), r.get("severity"),
                     r.get("minReward"), r.get("maxReward"), r.get("rewardModel")))
    return sorted(rows, key=lambda t: tuple(str(x) for x in t))


def normalise(program: dict[str, Any]) -> dict[str, Any]:
    out = {k: program.get(k) for k in TRACKED}
    out["rewards"] = [list(r) for r in _reward_rows(program)]
    out["asset_count"] = len(program.get("assets") or [])
    out["audit_count"] = len(program.get("audits") or [])
    return out


def snapshot(programs: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {p["slug"]: normalise(p) for p in programs if p.get("slug")}


def diff(old: dict[str, dict[str, Any]], new: dict[str, dict[str, Any]]) -> dict[str, Any]:
    added = sorted(set(new) - set(old))
    removed = sorted(set(old) - set(new))
    changed = []
    for slug in sorted(set(old) & set(new)):
        fields = {k: {"old": old[slug].get(k), "new": new[slug].get(k)}
                  for k in new[slug] if old[slug].get(k) != new[slug].get(k)}
        if fields:
            changed.append({"slug": slug, "project": new[slug].get("project"),
                            "changes": fields})
    return {
        "programs": len(new),
        "new": [{"slug": s, "project": new[s].get("project"),
                 "maxBounty": new[s].get("maxBounty")} for s in added],
        "removed": removed,
        "changed": changed,
    }


def fetch_listing(url: str, timeout: float = 30) -> list[dict[str, Any]]:
    resp = requests.get(url, timeout=timeout, headers={"User-Agent": "fundtrail/0.1"})
    resp.raise_for_status()
    data = resp.json()
    if not isinstance(data, list):
        raise ValueError("unexpected listing format (expected a JSON list)")
    return data


def load_listing_or_snapshot(path: str | Path) -> dict[str, dict[str, Any]]:
    """Accept either a raw listing (list) or a saved normalised snapshot (dict)."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return snapshot(data) if isinstance(data, list) else data


def run_bounties(listing: list[dict[str, Any]], snapshot_path: str | Path,
                 update: bool = True) -> dict[str, Any]:
    new = snapshot(listing)
    path = Path(snapshot_path)
    if path.exists():
        result = diff(load_listing_or_snapshot(path), new)
        result["baseline"] = False
    else:
        result = {"programs": len(new), "new": [], "removed": [], "changed": [],
                  "baseline": True}
    if update:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(new, indent=1, sort_keys=True), encoding="utf-8")
    return result
