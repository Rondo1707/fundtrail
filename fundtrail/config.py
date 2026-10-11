"""YAML config loading with built-in defaults."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

DEFAULT_CHAINS: dict[str, dict[str, Any]] = {
    "ethereum": {"chain_id": 1, "symbol": "ETH",
                 "rpcs": ["https://ethereum-rpc.publicnode.com", "https://eth.llamarpc.com"]},
    "arbitrum": {"chain_id": 42161, "symbol": "ETH",
                 "rpcs": ["https://arbitrum-one-rpc.publicnode.com", "https://arb1.arbitrum.io/rpc"]},
    "optimism": {"chain_id": 10, "symbol": "ETH",
                 "rpcs": ["https://optimism-rpc.publicnode.com", "https://mainnet.optimism.io"]},
    "base": {"chain_id": 8453, "symbol": "ETH",
             "rpcs": ["https://base-rpc.publicnode.com", "https://mainnet.base.org"]},
    "bsc": {"chain_id": 56, "symbol": "BNB", "optional": True,
            "rpcs": ["https://bsc-rpc.publicnode.com", "https://bsc-dataseed.bnbchain.org"]},
    "polygon": {"chain_id": 137, "symbol": "POL", "optional": True,
                "rpcs": ["https://polygon-bor-rpc.publicnode.com", "https://polygon-rpc.com"]},
}

DEFAULTS: dict[str, Any] = {
    "chains": DEFAULT_CHAINS,
    "tips": {"include_optional": False, "max_lag_seconds": 120},
    "bounties": {"url": "https://immunefi.com/public-api/bounties.json",
                 "snapshot": "state/immunefi-snapshot.json"},
    "trace": {"max_hops": 2, "max_blocks": 500, "log_chunk": 2000,
              "max_fanout": 25, "min_interval": 0.1},
    "alerts": {"sources": [], "state": "state/alerts-seen.json"},
}


def _merge(base: dict[str, Any], over: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    if path is None:
        return _merge(DEFAULTS, {})
    with open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top level must be a mapping")
    return _merge(DEFAULTS, data)
