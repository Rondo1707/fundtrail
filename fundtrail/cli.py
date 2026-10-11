"""Command-line interface: fundtrail {tips,bounties,trace,alerts,report}."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import __version__
from .alerts import build_sources, run_alerts
from .bounties import fetch_listing, run_bounties
from .config import load_config
from .evidence import graph_from_evidence
from .labels import load_labels
from .report import render_report
from .rpc import RPCClient, hex_to_int
from .tips import run_tips
from .trace import Tracer


def _out(data: Any, path: str | None) -> None:
    text = json.dumps(data, indent=2)
    if path:
        Path(path).write_text(text + "\n", "utf-8")
    else:
        print(text)


def _block_arg(value: str, latest: int) -> int:
    if value == "latest":
        return latest
    if value.startswith("latest-"):
        return latest - int(value.split("-", 1)[1])
    return int(value, 0)


def cmd_tips(args: argparse.Namespace, cfg: dict[str, Any]) -> int:
    res = run_tips(cfg, include_optional=args.all or None)
    _out(res, args.output)
    return 0 if res["all_ok"] else 1


def cmd_bounties(args: argparse.Namespace, cfg: dict[str, Any]) -> int:
    bcfg = cfg["bounties"]
    if args.listing:
        listing = json.loads(Path(args.listing).read_text("utf-8"))
    else:
        listing = fetch_listing(bcfg["url"])
    res = run_bounties(listing, args.snapshot or bcfg["snapshot"], update=not args.no_update)
    _out(res, args.output)
    return 0


def cmd_trace(args: argparse.Namespace, cfg: dict[str, Any]) -> int:
    tcfg = cfg["trace"]
    chain = cfg["chains"].get(args.chain, {})
    rpcs = args.rpc or chain.get("rpcs")
    if not rpcs:
        print(f"no RPC for chain {args.chain!r}; pass --rpc", file=sys.stderr)
        return 2
    client = RPCClient(rpcs, min_interval=float(tcfg["min_interval"]))
    latest = hex_to_int(client.call("eth_blockNumber"))
    frm = _block_arg(args.from_block, latest)
    to = _block_arg(args.to_block, latest)
    tracer = Tracer(client, args.chain, load_labels(args.labels),
                    frm, to, max_hops=args.hops if args.hops is not None else tcfg["max_hops"],
                    max_blocks=args.max_blocks or tcfg["max_blocks"],
                    log_chunk=tcfg["log_chunk"], max_fanout=tcfg["max_fanout"],
                    native_symbol=chain.get("symbol", "ETH"),
                    include_tokens=not args.no_tokens, include_native=not args.no_native)
    graph = tracer.run(args.address)
    _out(graph, args.output)
    if args.report:
        Path(args.report).write_text(render_report(graph), "utf-8")
    return 0


def cmd_report(args: argparse.Namespace, cfg: dict[str, Any]) -> int:
    data = json.loads(Path(args.graph).read_text("utf-8"))
    if args.evidence:
        data = graph_from_evidence(data, load_labels(args.labels), chain=args.chain)
        if args.graph_out:
            _out(data, args.graph_out)
    md = render_report(data, title=args.title)
    if args.output:
        Path(args.output).write_text(md, "utf-8")
    else:
        print(md)
    return 0


def cmd_alerts(args: argparse.Namespace, cfg: dict[str, Any]) -> int:
    acfg = cfg["alerts"]
    res = run_alerts(build_sources(acfg.get("sources", [])), acfg.get("state"))
    _out(res, args.output)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="fundtrail", description=__doc__)
    p.add_argument("--version", action="version", version=__version__)
    p.add_argument("-c", "--config", help="YAML config file")
    sub = p.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("tips", help="block-tip health check")
    t.add_argument("--all", action="store_true", help="include optional chains (BSC, Polygon)")
    t.add_argument("-o", "--output")
    t.set_defaults(func=cmd_tips)

    b = sub.add_parser("bounties", help="diff Immunefi listing vs snapshot")
    b.add_argument("--listing", help="use a saved listing JSON instead of fetching")
    b.add_argument("--snapshot", help="snapshot path (overrides config)")
    b.add_argument("--no-update", action="store_true", help="do not overwrite the snapshot")
    b.add_argument("-o", "--output")
    b.set_defaults(func=cmd_bounties)

    tr = sub.add_parser("trace", help="follow funds from an address")
    tr.add_argument("address")
    tr.add_argument("--chain", default="ethereum")
    tr.add_argument("--rpc", action="append", help="RPC URL (repeat for fallbacks)")
    tr.add_argument("--from-block", default="latest-100")
    tr.add_argument("--to-block", default="latest")
    tr.add_argument("--hops", type=int)
    tr.add_argument("--max-blocks", type=int, help="native-transfer block scan cap")
    tr.add_argument("--labels", action="append", help="extra labels YAML")
    tr.add_argument("--no-tokens", action="store_true")
    tr.add_argument("--no-native", action="store_true")
    tr.add_argument("-o", "--output", help="graph JSON path")
    tr.add_argument("--report", help="also write a markdown report here")
    tr.set_defaults(func=cmd_trace)

    r = sub.add_parser("report", help="render markdown from a trace graph")
    r.add_argument("graph", help="trace graph JSON (or evidence JSON with --evidence)")
    r.add_argument("--evidence", action="store_true",
                   help="input is a 79thVault-style evidence file")
    r.add_argument("--chain", default="bsc", help="chain for --evidence input")
    r.add_argument("--graph-out", help="with --evidence, also save the converted graph")
    r.add_argument("--labels", action="append")
    r.add_argument("--title")
    r.add_argument("-o", "--output")
    r.set_defaults(func=cmd_report)

    a = sub.add_parser("alerts", help="poll configured RSS/Atom feeds")
    a.add_argument("-o", "--output")
    a.set_defaults(func=cmd_alerts)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args, load_config(args.config)))


if __name__ == "__main__":
    sys.exit(main())
