from __future__ import annotations

import copy
import json

from conftest import load
from fundtrail.bounties import diff, run_bounties, snapshot


def test_baseline_then_no_changes(tmp_path) -> None:
    listing = load("immunefi_listing.json")
    snap = tmp_path / "snap.json"
    first = run_bounties(listing, snap)
    assert first["baseline"] is True and first["programs"] == 3
    second = run_bounties(listing, snap)
    assert second["new"] == [] and second["changed"] == [] and not second["baseline"]


def test_reissued_reward_ids_are_not_a_change() -> None:
    # The earlier prototype flagged ENS when Immunefi reissued reward row ids.
    listing = load("immunefi_listing.json")
    after = copy.deepcopy(listing)
    for r in after[0]["rewards"]:
        r["id"] += 1000
    after[0]["updatedDate"] = "2026-10-09T00:00:00Z"
    assert diff(snapshot(listing), snapshot(after))["changed"] == []


def test_new_changed_removed() -> None:
    listing = load("immunefi_listing.json")
    after = copy.deepcopy(listing)
    after[0]["maxBounty"] = 500000
    after[1]["audits"].append({"id": "x", "url": "u"})
    removed = after.pop(2)
    after.append({"slug": "newproto", "project": "NewProto", "maxBounty": 50000,
                  "rewards": [], "assets": []})
    d = diff(snapshot(listing), snapshot(after))
    assert [n["slug"] for n in d["new"]] == ["newproto"]
    assert d["removed"] == [removed["slug"]]
    ch = {c["slug"]: c["changes"] for c in d["changed"]}
    assert ch["ens"]["maxBounty"] == {"old": 250000, "new": 500000}
    assert "audit_count" in ch[listing[1]["slug"]]


def test_accepts_raw_listing_as_old_snapshot(tmp_path) -> None:
    listing = load("immunefi_listing.json")
    old = tmp_path / "imm.json"
    old.write_text(json.dumps(listing))
    res = run_bounties(listing, old, update=False)
    assert res["changed"] == [] and res["programs"] == 3
