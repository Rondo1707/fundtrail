from __future__ import annotations

from typing import Any

from conftest import FakeTransport, load
from fundtrail.labels import load_labels
from fundtrail.rpc import RPCClient
from fundtrail.trace import TRANSFER_TOPIC, Tracer, _pad_topic

FX = load("bsc_79thvault_rpc.json")


def bsc_handler(url: str, method: str, params: list[Any]) -> Any:
    if method == "eth_getBlockByNumber":
        n = int(params[0], 16)
        return FX["blocks"].get(str(n), {"number": params[0], "transactions": []})
    if method == "eth_getLogs":
        return []
    if method == "eth_getCode":
        return FX["code"].get(params[0].lower(), "0x")
    raise AssertionError(method)


def make_tracer(hops: int) -> Tracer:
    client = RPCClient(["https://fixture"], transport=FakeTransport(bsc_handler))
    return Tracer(client, "bsc", load_labels(), FX["from_block"], FX["to_block"],
                  max_hops=hops, max_blocks=50_000, native_symbol="BNB")


def test_79thvault_flow_reaches_tornado() -> None:
    g = make_tracer(hops=3).run(FX["start"])
    exp = FX["expect"]
    pairs = {(e["src"], e["dst"]) for e in g["edges"]}
    assert (FX["start"], exp["collection"]) in pairs
    assert (exp["collection"], exp["secondary"]) in pairs
    assert (exp["collection"], exp["tornado"]) in pairs
    assert (exp["secondary"], exp["relay"]) in pairs
    flagged = {n["address"]: n for n in g["flagged"]}
    assert flagged[exp["tornado"]]["kind"] == "mixer"
    seed = next(e for e in g["edges"] if e["dst"] == exp["collection"])
    assert abs(seed["amount"] - 16249.117811) < 1e-3


def test_hop_limit_and_eip7702_eoa() -> None:
    g = make_tracer(hops=1).run(FX["start"])
    assert len(g["edges"]) == 1  # only the seed consolidation
    g3 = make_tracer(hops=3).run(FX["start"])
    relay = next(n for n in g3["nodes"] if n["address"] == FX["expect"]["relay"])
    # 7702-delegated code must not be mistaken for a contract
    assert relay["hop"] == 3 and relay["stop_reason"] == "max hops"


def test_transfers_before_entry_block_are_ignored() -> None:
    # The secondary wallet is funded at a later block than the trace start. A
    # transfer it made *before* it was funded is outside the flow and must be skipped.
    early_block = FX["from_block"] + 5
    junk = "0x" + "33" * 20
    early = {"number": hex(early_block), "transactions": [{
        "hash": "0x" + "ab" * 32, "from": FX["expect"]["secondary"], "to": junk,
        "value": hex(10**18), "blockNumber": hex(early_block)}]}

    def handler(url, method, params):
        if method == "eth_getBlockByNumber" and int(params[0], 16) == early_block:
            return early
        return bsc_handler(url, method, params)

    client = RPCClient(["https://fixture"], transport=FakeTransport(handler))
    g = Tracer(client, "bsc", load_labels(), FX["from_block"], FX["to_block"],
               max_hops=3, max_blocks=50_000).run(FX["start"])
    dsts = {e["dst"] for e in g["edges"]}
    assert junk not in dsts and FX["expect"]["relay"] in dsts


A, B, TOKEN = "0x" + "11" * 20, "0x" + "22" * 20, "0x" + "99" * 20


def token_handler(fail_over: int) -> Any:
    def handler(url, method, params):
        if method == "eth_getBlockByNumber":
            return {"transactions": []}
        if method == "eth_getCode":
            return "0x"
        if method == "eth_call":
            return "0x" + "6".rjust(64, "0") if params[0]["data"] == "0x313ce567" else "0x"
        if method == "eth_getLogs":
            f = params[0]
            lo, hi = int(f["fromBlock"], 16), int(f["toBlock"], 16)
            if hi - lo + 1 > fail_over:
                return {"__error__": {"code": -32005, "message": "range too large"}}
            if f["topics"][1] == _pad_topic(A) and lo <= 150 <= hi:
                return [{"address": TOKEN, "topics": [TRANSFER_TOPIC, _pad_topic(A), _pad_topic(B)],
                         "data": hex(2_500_000), "transactionHash": "0x" + "cd" * 32,
                         "blockNumber": hex(150)}]
            return []
        raise AssertionError(method)
    return handler


def test_token_logs_with_range_shrinking() -> None:
    t = FakeTransport(token_handler(fail_over=100))
    client = RPCClient(["https://fixture"], transport=t)
    tr = Tracer(client, "ethereum", load_labels(), 0, 999, max_hops=1,
                max_blocks=1, log_chunk=1000, include_native=False)
    g = tr.run(A)
    assert len(g["edges"]) == 1
    e = g["edges"][0]
    assert e["dst"] == B and e["amount"] == 2.5 and e["decimals"] == 6
    sizes = [int(p[0]["toBlock"], 16) - int(p[0]["fromBlock"], 16) + 1
             for _, m, p in t.calls if m == "eth_getLogs"]
    assert max(s for s in sizes) == 1000 and all(s <= 125 for s in sizes[4:])


def test_fanout_cap() -> None:
    txs = [{"hash": f"0x{i:064x}", "from": A, "to": f"0x{i + 1:040x}",
            "value": hex((i + 1) * 10**18), "blockNumber": "0x1"} for i in range(40)]

    def handler(url, method, params):
        if method == "eth_getBlockByNumber":
            return {"transactions": txs if params[0] == "0x1" else []}
        if method == "eth_getLogs":
            return []
        return "0x"

    tr = Tracer(RPCClient(["https://f"], transport=FakeTransport(handler)), "ethereum",
                load_labels(), 1, 1, max_hops=1, max_fanout=5)
    g = tr.run(A)
    assert len(g["edges"]) == 5 and min(e["amount"] for e in g["edges"]) == 36
