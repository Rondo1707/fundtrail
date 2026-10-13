from __future__ import annotations

import requests

from conftest import FakeTransport, load
from fundtrail.config import load_config
from fundtrail.rpc import RPCClient, RPCError
from fundtrail.tips import run_tips


def test_fallback_to_second_endpoint() -> None:
    def handler(url, method, params):
        if "bad" in url:
            raise requests.ConnectionError("down")
        return "0x10"

    t = FakeTransport(handler)
    c = RPCClient(["https://bad.example", "https://good.example"], transport=t)
    assert c.call("eth_blockNumber") == "0x10"
    assert c.last_endpoint == "https://good.example"


def test_rate_limit_retries_then_succeeds() -> None:
    state = {"n": 0}

    def handler(url, method, params):
        state["n"] += 1
        if state["n"] == 1:
            raise RPCError("429", code=429)
        return "0x1"

    sleeps: list[float] = []
    c = RPCClient(["https://x"], transport=FakeTransport(handler), sleep=sleeps.append)
    assert c.call("eth_blockNumber") == "0x1"
    assert sleeps == [1]


def test_all_endpoints_fail() -> None:
    def handler(url, method, params):
        raise requests.Timeout("slow")

    c = RPCClient(["https://a", "https://b"], transport=FakeTransport(handler))
    try:
        c.call("eth_blockNumber")
    except RPCError as exc:
        assert "all endpoints failed" in str(exc)
    else:
        raise AssertionError("expected RPCError")


def test_tips_with_recorded_responses() -> None:
    eth = load("tip_ethereum.json")["result"]
    base = load("tip_base.json")["result"]
    now = int(eth["timestamp"], 16) + 5
    cfg = load_config()

    def factory(rpcs):
        def handler(url, method, params):
            if "ethereum" in url:
                return eth
            if "base" in url:
                return base
            if "arbitrum-one-rpc" in url:  # primary down -> fallback answers
                raise requests.ConnectionError("down")
            if "optimism" in url:
                return {"number": "0x1", "timestamp": hex(now - 9999)}  # stale
            return {"number": "0x2", "timestamp": hex(now)}
        return RPCClient(rpcs, transport=FakeTransport(handler), retries=0)

    res = run_tips(cfg, factory=factory, now=lambda: now)
    by = {r["chain"]: r for r in res["chains"]}
    assert set(by) == {"ethereum", "arbitrum", "optimism", "base"}
    assert by["ethereum"]["ok"] and by["ethereum"]["block"] == int(eth["number"], 16)
    assert by["arbitrum"]["fallback_used"] is True
    assert by["optimism"]["ok"] is False and "old" in by["optimism"]["error"]
    assert res["all_ok"] is False
    res_all = run_tips(cfg, include_optional=True, factory=factory, now=lambda: now)
    assert {r["chain"] for r in res_all["chains"]} >= {"bsc", "polygon"}


def test_hex_to_int_empty_data():
    from fundtrail.rpc import hex_to_int
    assert hex_to_int("0x") == 0
    assert hex_to_int(None) == 0
    assert hex_to_int("") == 0
    assert hex_to_int("0x10") == 16
