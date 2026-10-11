"""Multi-chain block-tip health check."""

from __future__ import annotations

import time
from typing import Any, Callable

from .rpc import RPCClient, RPCError, hex_to_int

ClientFactory = Callable[[list[str]], RPCClient]


def check_chain(name: str, chain: dict[str, Any], client: RPCClient,
                max_lag_seconds: int, now: float) -> dict[str, Any]:
    result: dict[str, Any] = {"chain": name, "ok": False}
    try:
        block = client.call("eth_getBlockByNumber", ["latest", False])
        if not block:
            raise RPCError("empty block response")
        number = hex_to_int(block["number"])
        ts = hex_to_int(block["timestamp"])
        lag = int(now - ts)
        result.update({
            "block": number,
            "timestamp": ts,
            "lag_seconds": lag,
            "endpoint": client.last_endpoint,
            "fallback_used": client.last_endpoint != chain["rpcs"][0],
            "ok": lag <= max_lag_seconds,
        })
        if lag > max_lag_seconds:
            result["error"] = f"tip is {lag}s old (limit {max_lag_seconds}s)"
    except RPCError as exc:
        result["error"] = str(exc)
    return result


def run_tips(config: dict[str, Any], include_optional: bool | None = None,
             factory: ClientFactory | None = None,
             now: Callable[[], float] = time.time) -> dict[str, Any]:
    tcfg = config["tips"]
    if include_optional is None:
        include_optional = bool(tcfg.get("include_optional"))
    factory = factory or (lambda rpcs: RPCClient(rpcs, timeout=8, retries=1))
    results = []
    for name, chain in config["chains"].items():
        if chain.get("optional") and not include_optional:
            continue
        results.append(check_chain(name, chain, factory(chain["rpcs"]),
                                   int(tcfg.get("max_lag_seconds", 120)), now()))
    return {"checked_at": int(now()), "all_ok": all(r["ok"] for r in results),
            "chains": results}
