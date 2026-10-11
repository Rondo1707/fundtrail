"""Follow-the-funds tracer over plain JSON-RPC.

Native transfers have no index in JSON-RPC, so they are found by scanning
full blocks in a bounded window (``max_blocks``). ERC-20 ``Transfer`` logs are
found with ``eth_getLogs`` filtered on the sender topic, in chunks that shrink
when a node rejects the range. Internal (contract-initiated) native transfers
are NOT seen; that needs trace APIs (see README limitations).
"""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass, field
from typing import Any

from .labels import Labels, lookup
from .rpc import RPCClient, RPCError, hex_to_int

TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
EIP7702_PREFIX = "0xef0100"


@dataclass
class Edge:
    src: str
    dst: str
    asset: str  # "native" or token contract address
    amount_raw: int
    tx: str
    block: int
    hop: int
    decimals: int = 18
    symbol: str | None = None

    @property
    def amount(self) -> float:
        return self.amount_raw / (10 ** self.decimals)

    def to_json(self) -> dict[str, Any]:
        d = asdict(self)
        d["amount_raw"] = str(self.amount_raw)
        d["amount"] = round(self.amount, 8)
        return d


@dataclass
class Node:
    address: str
    hop: int
    first_block: int
    label: str | None = None
    kind: str | None = None
    is_contract: bool | None = None
    expanded: bool = False
    stop_reason: str | None = None
    notes: list[str] = field(default_factory=list)


def _pad_topic(address: str) -> str:
    return "0x" + address.lower()[2:].rjust(64, "0")


def _topic_to_address(topic: str) -> str:
    return "0x" + topic[-40:].lower()


class Tracer:
    def __init__(self, client: RPCClient, chain: str, labels: Labels,
                 from_block: int, to_block: int, max_hops: int = 2,
                 max_blocks: int = 500, log_chunk: int = 2000, max_fanout: int = 25,
                 native_symbol: str = "ETH", include_tokens: bool = True,
                 include_native: bool = True) -> None:
        if to_block < from_block:
            raise ValueError("to_block must be >= from_block")
        self.client = client
        self.chain = chain
        self.labels = labels
        self.from_block = from_block
        self.to_block = to_block
        self.native_end = min(to_block, from_block + max_blocks - 1)
        self.max_hops = max_hops
        self.log_chunk = max(1, log_chunk)
        self.max_fanout = max_fanout
        self.native_symbol = native_symbol
        self.include_tokens = include_tokens
        self.include_native = include_native
        self._native_index: dict[str, list[tuple[str, int, str, int]]] | None = None
        self._token_meta: dict[str, tuple[int, str | None]] = {}
        self.warnings: list[str] = []

    # -- data access -------------------------------------------------------
    def _scan_native(self) -> dict[str, list[tuple[str, int, str, int]]]:
        """Index value-bearing txs by sender over the bounded native window."""
        if self._native_index is not None:
            return self._native_index
        index: dict[str, list[tuple[str, int, str, int]]] = {}
        for n in range(self.from_block, self.native_end + 1):
            block = self.client.call("eth_getBlockByNumber", [hex(n), True])
            if not block:
                self.warnings.append(f"block {n} unavailable")
                continue
            for tx in block.get("transactions", []):
                value = hex_to_int(tx.get("value"))
                if value == 0 or not tx.get("to"):
                    continue
                index.setdefault(tx["from"].lower(), []).append(
                    (tx["to"].lower(), value, tx["hash"], n))
        if self.native_end < self.to_block:
            self.warnings.append(
                f"native transfers scanned only for blocks {self.from_block}-"
                f"{self.native_end} (max_blocks cap); token logs cover up to {self.to_block}")
        self._native_index = index
        return index

    def _get_logs(self, sender: str, start: int) -> list[dict[str, Any]]:
        logs: list[dict[str, Any]] = []
        lo, chunk = start, self.log_chunk
        while lo <= self.to_block:
            hi = min(self.to_block, lo + chunk - 1)
            try:
                part = self.client.call("eth_getLogs", [{
                    "fromBlock": hex(lo), "toBlock": hex(hi),
                    "topics": [TRANSFER_TOPIC, _pad_topic(sender)]}])
            except RPCError as exc:
                if chunk > 1 and exc.code is not None:
                    chunk = max(1, chunk // 2)  # node rejected range: shrink and retry
                    continue
                raise
            logs.extend(part or [])
            lo = hi + 1
        return logs

    def _token_info(self, token: str) -> tuple[int, str | None]:
        if token in self._token_meta:
            return self._token_meta[token]
        decimals, symbol = 18, None
        try:
            raw = self.client.call("eth_call", [{"to": token, "data": "0x313ce567"}, "latest"])
            if raw and raw != "0x":
                decimals = hex_to_int(raw)
        except RPCError:
            self.warnings.append(f"decimals() failed for {token}; assuming 18")
        try:
            raw = self.client.call("eth_call", [{"to": token, "data": "0x95d89b41"}, "latest"])
            symbol = _decode_string(raw)
        except RPCError:
            pass
        self._token_meta[token] = (decimals, symbol)
        return decimals, symbol

    def _is_contract(self, address: str) -> bool:
        code = self.client.call("eth_getCode", [address, "latest"]) or "0x"
        # EIP-7702 delegated EOAs carry 0xef0100<delegate>; treat them as EOAs.
        return code not in ("0x", "0x0") and not code.lower().startswith(EIP7702_PREFIX)

    # -- traversal ---------------------------------------------------------
    def outgoing(self, address: str, since_block: int, hop: int) -> list[Edge]:
        edges: list[Edge] = []
        if self.include_native:
            for dst, value, tx, block in self._scan_native().get(address, []):
                if block >= since_block:
                    edges.append(Edge(address, dst, "native", value, tx, block, hop,
                                      18, self.native_symbol))
        if self.include_tokens:
            for log in self._get_logs(address, since_block):
                topics = log.get("topics", [])
                if len(topics) < 3:
                    continue  # ERC-721 style or malformed
                token = log["address"].lower()
                decimals, symbol = self._token_info(token)
                edges.append(Edge(address, _topic_to_address(topics[2]), token,
                                  hex_to_int(log.get("data") or "0x0"),
                                  log["transactionHash"], hex_to_int(log["blockNumber"]),
                                  hop, decimals, symbol))
        edges.sort(key=lambda e: (e.block, e.tx))
        return edges

    def run(self, start: str) -> dict[str, Any]:
        start = start.lower()
        nodes: dict[str, Node] = {start: self._make_node(start, 0, self.from_block)}
        edges: list[Edge] = []
        queue: deque[str] = deque([start])
        while queue:
            addr = queue.popleft()
            node = nodes[addr]
            if node.hop >= self.max_hops:
                node.stop_reason = node.stop_reason or "max hops"
                continue
            if node.kind:
                node.stop_reason = f"labelled {node.kind}"
                continue
            if node.hop > 0:
                node.is_contract = self._is_contract(addr)
                if node.is_contract:
                    node.stop_reason = "contract (not expanded)"
                    continue
            node.expanded = True
            out = self.outgoing(addr, node.first_block, node.hop + 1)
            # Keep the largest transfers when fan-out is huge (e.g. dust sprays).
            if len(out) > self.max_fanout:
                node.notes.append(f"{len(out)} transfers; kept top {self.max_fanout} by amount")
                out = sorted(out, key=lambda e: e.amount, reverse=True)[: self.max_fanout]
            for e in out:
                edges.append(e)
                if e.dst not in nodes:
                    nodes[e.dst] = self._make_node(e.dst, node.hop + 1, e.block)
                    queue.append(e.dst)
        return build_graph(self.chain, start, nodes, edges, {
            "from_block": self.from_block, "to_block": self.to_block,
            "native_scanned_to": self.native_end if self.include_native else None,
            "max_hops": self.max_hops, "rpc_calls": self.client.calls,
        }, self.warnings)

    def _make_node(self, addr: str, hop: int, block: int) -> Node:
        info = lookup(self.labels, self.chain, addr)
        return Node(addr, hop, block, info.get("name") if info else None,
                    info.get("kind") if info else None)


def build_graph(chain: str, start: str, nodes: dict[str, Node], edges: list[Edge],
                params: dict[str, Any], warnings: list[str]) -> dict[str, Any]:
    flagged = [asdict(n) for n in nodes.values() if n.kind in ("mixer", "bridge", "exchange")]
    return {
        "schema": "fundtrail.trace/v1",
        "chain": chain,
        "start": start,
        "params": params,
        "nodes": [asdict(n) for n in nodes.values()],
        "edges": [e.to_json() for e in edges],
        "flagged": flagged,
        "warnings": warnings,
    }


def _decode_string(raw: str | None) -> str | None:
    if not raw or raw == "0x":
        return None
    data = bytes.fromhex(raw[2:])
    try:
        if len(data) >= 96:
            length = int.from_bytes(data[32:64], "big")
            return data[64:64 + length].decode("utf-8", "replace") or None
        return data.rstrip(b"\x00").decode("utf-8", "replace") or None
    except (ValueError, UnicodeDecodeError):
        return None
