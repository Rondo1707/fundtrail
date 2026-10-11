from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


def load(name: str) -> Any:
    return json.loads((FIXTURES / name).read_text("utf-8"))


class FakeTransport:
    """Answers JSON-RPC calls from a handler; records every call. No network."""

    def __init__(self, handler: Callable[[str, str, list[Any]], Any]) -> None:
        self.handler = handler
        self.calls: list[tuple[str, str, list[Any]]] = []

    def __call__(self, url: str, payload: dict[str, Any], timeout: float) -> Any:
        self.calls.append((url, payload["method"], payload["params"]))
        result = self.handler(url, payload["method"], payload["params"])
        if isinstance(result, dict) and "__error__" in result:
            return {"jsonrpc": "2.0", "id": payload["id"], "error": result["__error__"]}
        return {"jsonrpc": "2.0", "id": payload["id"], "result": result}


@pytest.fixture(autouse=True)
def no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    import requests

    def blocked(*a: Any, **k: Any) -> None:
        raise AssertionError("live network access in tests")

    monkeypatch.setattr(requests, "post", blocked)
    monkeypatch.setattr(requests, "get", blocked)
