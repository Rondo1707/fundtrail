# Test fixtures

- `tip_ethereum.json`, `tip_base.json`: real `eth_getBlockByNumber("latest")` responses
  from publicnode, captured 11 Oct 2026, trimmed to the fields fundtrail reads.
- `immunefi_listing.json`: three programs from the Immunefi public listing saved on
  8 Oct 2026 (`immunefi.com/public-api/bounties.json`), trimmed.
- `rekt_feed.xml`: the rekt.news RSS feed captured 11 Oct 2026, trimmed to three items.
- `bsc_79thvault_rpc.json`: JSON-RPC responses for a subset of the 79thVault flows.
  Tx hashes, blocks, senders, recipients and amounts come from
  `79thvault_flows.json` (gathered over public RPC). The block bodies are reconstructed from that data and include
  only the relevant transactions; they are not byte-for-byte captures.
- Token `Transfer` log tests use obviously fake addresses (0x1111…, 0x2222…) built inline in `tests/test_trace.py`.
- `79thvault_flows.json`: public on-chain 79thVault flows (tx hashes, blocks, recipients,
  amounts) in the evidence-file shape read by `fundtrail report --evidence`.
