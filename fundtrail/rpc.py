"""Minimal JSON-RPC client with fallback endpoints, retries and rate limiting."""

from __future__ import annotations

import time
from typing import Any, Callable, Protocol, Sequence

import requests


class RPCError(Exception):
    """Raised when every endpoint failed or the node returned an error."""

    def __init__(self, message: str, code: int | None = None) -> None:
        super().__init__(message)
        self.code = code


class Transport(Protocol):
    def __call__(self, url: str, payload: dict[str, Any], timeout: float) -> Any: ...


def http_transport(url: str, payload: dict[str, Any], timeout: float) -> Any:
    resp = requests.post(url, json=payload, timeout=timeout,
                         headers={"User-Agent": "fundtrail/0.1"})
    if resp.status_code == 429:
        raise RPCError("rate limited (HTTP 429)", code=429)
    resp.raise_for_status()
    return resp.json()


class RPCClient:
    """Calls endpoints in order; moves to the next one on failure.

    ``min_interval`` spaces out requests (simple client-side rate limit).
    """

    def __init__(
        self,
        endpoints: Sequence[str],
        timeout: float = 10.0,
        retries: int = 2,
        min_interval: float = 0.0,
        transport: Transport = http_transport,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if not endpoints:
            raise ValueError("at least one endpoint is required")
        self.endpoints = list(endpoints)
        self.timeout = timeout
        self.retries = retries
        self.min_interval = min_interval
        self.transport = transport
        self.sleep = sleep
        self._last = 0.0
        self._id = 0
        self.last_endpoint: str | None = None
        self.calls = 0

    def _throttle(self) -> None:
        if self.min_interval <= 0:
            return
        wait = self._last + self.min_interval - time.monotonic()
        if wait > 0:
            self.sleep(wait)
        self._last = time.monotonic()

    def call(self, method: str, params: list[Any] | None = None) -> Any:
        errors: list[str] = []
        for url in self.endpoints:
            for attempt in range(self.retries + 1):
                self._throttle()
                self._id += 1
                payload = {"jsonrpc": "2.0", "id": self._id, "method": method,
                           "params": params or []}
                try:
                    self.calls += 1
                    data = self.transport(url, payload, self.timeout)
                except RPCError as exc:  # rate limited: back off and retry
                    errors.append(f"{url}: {exc}")
                    self.sleep(min(2 ** attempt, 8))
                    continue
                except (requests.RequestException, ValueError) as exc:
                    errors.append(f"{url}: {exc.__class__.__name__}: {exc}")
                    break  # transport failure: try next endpoint
                if "error" in data and data["error"]:
                    err = data["error"]
                    # Node-level errors (e.g. range too large) are surfaced to the
                    # caller, which may know how to adapt.
                    raise RPCError(str(err.get("message", err)), code=err.get("code"))
                self.last_endpoint = url
                return data.get("result")
        raise RPCError("all endpoints failed: " + "; ".join(errors[-4:]))


def hex_to_int(value: str | None) -> int:
    return int(value, 16) if value else 0
