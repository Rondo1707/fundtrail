# Contributing

Thanks for helping. fundtrail is an early prototype, so small, focused pull
requests are easiest to review.

## Setup

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
pytest -q
```

## Ground rules

- Tests must not touch the network. Use recorded or reconstructed fixtures in
  `tests/fixtures/` and say in `tests/fixtures/README.md` how each was made.
- Keep dependencies light (currently `requests` and `PyYAML`).
- Type hints on public functions.
- **Labels:** every new entry in `fundtrail/data/labels.yaml` needs a `source:` URL
  field (official docs, a sanctions list, or a reproducible on-chain
  reference). Unsourced labels will not be merged.
- fundtrail is read-only. It must never sign or send transactions, and pull
  requests that add key handling will not be accepted.
- Do not include private data about individuals in fixtures or examples beyond
  public on-chain addresses and transactions.
