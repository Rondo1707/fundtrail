from __future__ import annotations

import json
from pathlib import Path

from fundtrail.cli import main
from fundtrail.evidence import graph_from_evidence
from fundtrail.labels import load_labels, lookup
from fundtrail.report import render_report

EVIDENCE = Path(__file__).parent / "fixtures" / "79thvault_flows.json"


def graph() -> dict:
    return graph_from_evidence(json.loads(EVIDENCE.read_text("utf-8")), load_labels())


def test_labels_bundle() -> None:
    labels = load_labels()
    assert lookup(labels, "bsc", "0x0D5550d52428E7e3175bfc9550207e4ad3859b17")["kind"] == "mixer"
    assert lookup(labels, "ethereum", "0x910Cbd523D972eb0a6f4cAe4618aD62622b39DbF")
    assert lookup(labels, "ethereum", "0x" + "00" * 20) is None


def test_evidence_graph_totals() -> None:
    g = graph()
    assert g["schema"] == "fundtrail.trace/v1"
    tornado = "0x0d5550d52428e7e3175bfc9550207e4ad3859b17"
    to_mixer = sum(e["amount"] for e in g["edges"] if e["dst"] == tornado)
    assert to_mixer > 0
    assert any(e["amount"] == 15000 for e in g["edges"])  # the return to the team
    assert len({e["tx"] for e in g["edges"]}) == len(g["edges"])  # deduplicated


def test_report_markdown() -> None:
    md = render_report(graph(), title="79thVault")
    assert md.startswith("# 79thVault")
    assert "Tornado Cash Proxy (BSC)" in md
    assert "https://bscscan.com/tx/0xee0e4416" in md
    assert "## Caveats" in md


def test_cli_report_from_evidence(tmp_path, capsys) -> None:
    out = tmp_path / "r.md"
    gout = tmp_path / "g.json"
    assert main(["report", str(EVIDENCE), "--evidence", "-o", str(out),
                 "--graph-out", str(gout)]) == 0
    assert "mixer" in out.read_text() and json.loads(gout.read_text())["chain"] == "bsc"
