"""Convert a hand-built evidence file (the 79thVault example) into a trace graph.

The 79thVault investigation predates this tool: it was done with ad-hoc
scripts against an archive BSC RPC. This adapter turns an evidence file of that shape into
the same ``fundtrail.trace/v1`` graph so the report renderer and tests can use
it as a worked example.
"""

from __future__ import annotations

from typing import Any

from .labels import Labels, lookup
from .trace import Edge, Node, build_graph

# evidence key -> sender role (roles resolve via evidence["addresses"])
FLOW_KEYS = {
    "collection_outflows": "collection_0x629B",
    "holding_outflows": "holding_0xa953",
    "secondary_outflows": "secondary",
}


def _addr(evidence: dict[str, Any], role: str) -> str:
    entry = evidence["addresses"][role]
    return (entry["a"] if isinstance(entry, dict) else entry).lower()


def graph_from_evidence(evidence: dict[str, Any], labels: Labels,
                        chain: str = "bsc") -> dict[str, Any]:
    roles = {(_addr(evidence, r)): r for r, v in evidence["addresses"].items()
             if isinstance(v, dict) and str(v.get("a", "")).startswith("0x")}
    start = _addr(evidence, "seller_A_exploiter")
    nodes: dict[str, Node] = {}
    edges: list[Edge] = []
    seen: set[str] = set()

    def node(addr: str, hop: int, block: int) -> None:
        if addr not in nodes:
            info = lookup(labels, chain, addr)
            n = Node(addr, hop, block, info.get("name") if info else None,
                     info.get("kind") if info else None)
            if addr in roles and not n.label:
                n.label = roles[addr]
            nodes[addr] = n

    def add(src: str, tx: dict[str, Any], hop: int) -> None:
        if tx["hash"] in seen or not tx.get("bnb"):
            return
        seen.add(tx["hash"])
        dst = tx["to"].lower()
        node(src, hop - 1, tx["block"])
        node(dst, hop, tx["block"])
        edges.append(Edge(src, dst, "native", int(round(tx["bnb"] * 10**6)) * 10**12,
                          tx["hash"], tx["block"], hop, 18, "BNB"))

    seed = evidence["seed_consolidation_tx"]
    add(start, seed, 1)
    hops = {"collection_outflows": 2, "secondary_outflows": 3, "holding_outflows": 3}
    for key, role in FLOW_KEYS.items():
        for tx in evidence.get(key, []):
            add(_addr(evidence, role), tx, hops[key])
    for n in nodes.values():
        n.expanded = n.address in {_addr(evidence, r) for r in FLOW_KEYS.values()} | {start}
        if n.kind:
            n.stop_reason = f"labelled {n.kind}"
    warnings = [
        "Converted from a hand-built evidence file, not produced by `fundtrail trace`.",
        "Seller B's 238 Tornado deposits (2,283.7 BNB) are summarised, not included as edges.",
        str(evidence.get("unresolved_relays_nonce0_bal0", "")),
    ]
    graph = build_graph(chain, start, nodes, edges,
                        {"source": "evidence file"}, [w for w in warnings if w])
    graph["summary_extra"] = {
        "seller_B_tornado": {k: v for k, v in evidence.get("seller_B_tornado", {}).items()
                             if k != "txs"},
        "onchain_messages": evidence.get("onchain_messages", {}),
    }
    return graph
