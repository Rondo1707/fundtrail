# Unclaimed Base vault, 1,783.067 wstETH drained (Base → Ethereum), 4 Oct 2026

_Traced with fundtrail (early prototype) and checked against transaction receipts on 12 Oct 2026.
Check every finding against a block explorer before acting on it._

**Status as of 12 Oct 2026, 08:10 UTC (Ethereum block 26175091, Base block 52501567):**
1,001 wstETH sits unmoved at `0xC73448…297f8D` on Ethereum. The other 782.067 wstETH has left Base
through the Lido wstETH bridge and has not yet been claimed on Ethereum.

This report was written 8 days after the incident. It is not a live alert. It adds a verified
transaction list and the current location of the funds.

## Summary

- **Chains:** Base (the drain), Ethereum (where the funds are being bridged to)
- **Loss:** 1,783.067 aBaswstETH, redeemed on Aave V3 for 1,783.067 wstETH. PeckShield put it at about $6M.
- **Vault:** [`0xD1895f2019c2152FC2b9022D57f19198c4CFCABC`](https://basescan.org/address/0xD1895f2019c2152FC2b9022D57f19198c4CFCABC) (Base, unverified proxy). No protocol has claimed it publicly.
- **Vault owner:** `owner()` returns the Safe [`0x6b27512a5943Ed327f6cb6C3EC1f0398229f42C4`](https://basescan.org/address/0x6b27512a5943Ed327f6cb6C3EC1f0398229f42C4) (Safe 1.4.1, 7 owners, threshold 3). All read on-chain.
- **Mechanism:** the Safe executed a call to the vault with three signatures. That call added the
  attacker's contract to an allowlist, and the contract then pulled the vault's Aave position. The
  vault's code is unverified, so the function name is not confirmed. On-chain data does not show
  whether keys were stolen, signers were phished, or something else happened. No Aave or Base core
  contract is involved.
- **First public alerts:** Blockaid (about 09:20 UTC, 4 Oct), PeckShield (about 09:56 UTC), followed by CertiK and ExVul.

## Addresses

| Role | Address | Chain |
|---|---|---|
| Vault (victim) | [`0xD1895f2019c2152FC2b9022D57f19198c4CFCABC`](https://basescan.org/address/0xD1895f2019c2152FC2b9022D57f19198c4CFCABC) | Base |
| Vault owner (3-of-7 Safe) | [`0x6b27512a5943Ed327f6cb6C3EC1f0398229f42C4`](https://basescan.org/address/0x6b27512a5943Ed327f6cb6C3EC1f0398229f42C4) | Base |
| Attacker EOA (deployed and called the contract) | [`0x0B5126e1bc27C0de77e02e97945760A674EdB034`](https://basescan.org/address/0x0B5126e1bc27C0de77e02e97945760A674EdB034) | Base |
| Attacker contract (allowlisted) | [`0xcdFE91301356da873562EF513828a60dba1F569d`](https://basescan.org/address/0xcdFE91301356da873562EF513828a60dba1F569d) | Base |
| Bridging and holding address | `0xC73448432a05deeA5Ea18a07D3b5d9ccf6297f8D` ([Base](https://basescan.org/address/0xC73448432a05deeA5Ea18a07D3b5d9ccf6297f8D), [Ethereum](https://etherscan.io/address/0xC73448432a05deeA5Ea18a07D3b5d9ccf6297f8D)) | Base, Ethereum |
| Ethereum gas funder (reported by PublicAML, not re-checked here) | [`0x707877cE44282896E417EbBDc5e7d4620A3366EF`](https://etherscan.io/address/0x707877cE44282896E417EbBDc5e7d4620A3366EF) | Ethereum |

Blockaid also listed `0x5D7a38144b4D17F47a22e3d0987523CD68B43310` as an exploiter address. It is a
contract on Base. fundtrail did not trace it, because no flow in this report touches it.

## Timeline (UTC, all transactions succeeded, checked by receipt)

| Time (4 Oct unless noted) | What | Amount | Tx |
|---|---|---|---|
| 08:53:51 | The Safe calls the vault with the attacker contract address and `true` (selector `0x38edc837`, 3 signatures). The transaction was relayed by `0x4ff634…c104`. | | [0xed265f…2810](https://basescan.org/tx/0xed265fc80e4abe42d72d6bfd1623c89dd2d12f544d53d4ca2c9c3d0fefbf2810) |
| 08:55:01 | Pull 1: vault to attacker contract | 1 aBaswstETH | [0x0ec75c…f491](https://basescan.org/tx/0x0ec75c3be1f55bb08a92421796675e051993cdb6cbc38d5e33cc2b7f6ef2f491) |
| 09:08:13 | Pull 2 | 100 aBaswstETH | [0xa08b02…459b](https://basescan.org/tx/0xa08b02678971f1dd3ada15721fd760ceb2846270e5b23a5bc6aa983bab7b459b) |
| 09:09:21 | Pull 3 | 500 aBaswstETH | [0x083270…a154](https://basescan.org/tx/0x0832709749dbeddabcee648a936cac1d8456b8e0f0c45f3f0516e4ac66c0a154) |
| 09:10:19 | Pull 4 | 500 aBaswstETH | [0x212dc5…80ac](https://basescan.org/tx/0x212dc5e03214abe70b5e37ffcb22c8dd8710e82397badf8f687d9164eaec80ac) |
| 09:11:11 | Pull 5 | 500 aBaswstETH | [0x327e47…543f](https://basescan.org/tx/0x327e47ad60274fc3bde84ddbb054fde45b97a571fa4931be5d19a5ba5806543f) |
| 09:12:37 | Pull 6 | 182.067 aBaswstETH | [0xf1c944…cd7e](https://basescan.org/tx/0xf1c9448c615122423c5f21aad2f690e76dfe7b9e9bfc320b1d36ef79a7a9cd7e) |
| 08:56–09:15 | The contract passes the aTokens to the attacker EOA in separate transactions (1, 100, 500, 500, 500, 182, 0.067), for example | 1 / 182 / 0.067 aBaswstETH | [0x6001ea…ae29](https://basescan.org/tx/0x6001ea94e6a4e7ca6426066d8f10e6a2f4db5b8a471580710f81d9325082ae29), [0xfc4bba…cfb2](https://basescan.org/tx/0xfc4bba1eb305270e6e137fb3e9e02706c088c025d80ade224fd72d37f9e0cfb2), [0x57a491…d375](https://basescan.org/tx/0x57a49136a5a5dbbb06ba03a3d76c85d59f6f6ae5547445e7d0ee4cbf3053d375) |
| 09:23:13 | The EOA withdraws all of it from Aave V3 (aTokens burned, wstETH paid out) | 1,783.067 wstETH | [0x557bfd…e8c](https://basescan.org/tx/0x557bfd0e8530fd3e089748ccaabaa7837877f7578b13a377008474f2e367ee8c) |
| 09:24:15 | EOA to `0xC73448…` (test) | 1 wstETH | [0xe824b2…85d2](https://basescan.org/tx/0xe824b27ca120908d145fd071e27f43f05aff541296d76c7772c3829398cf85d2) |
| 09:27:29 | `0xC73448…` withdraws through the Lido L2 bridge `0xac9D11…87AB` to Ethereum | 1 wstETH | [0x9c55ee…81bc](https://basescan.org/tx/0x9c55eed4b982de648578a463f889c49d2abeec501249629becb538e4a77281bc) |
| 10:47:23 | EOA to `0xC73448…` | 1,782.067 wstETH | [0x20fb64…e145](https://basescan.org/tx/0x20fb64ee4adceee8fb3c36b2441a32b830917afc56fe7064b46f82a58f6be145) |
| 12:10:59 | `0xC73448…` withdraws through the Lido L2 bridge to Ethereum | 1,000 wstETH | [0x7b8560…3e14](https://basescan.org/tx/0x7b8560996d362fe1f3f0edec72ca3d84286163643172b135e485b184e3723e14) |
| 9 Oct 11:06:59 | Claimed on Ethereum through the Base OptimismPortal `0x490480…E97e`, paid out by the Lido L1 bridge `0x9de443…1e72` | 1 wstETH | [0xf33030…b088](https://etherscan.io/tx/0xf33030416a2123f449b7f0f98a636b4bd80678fbbfdd7d5b5f725949decbb088) |
| 9 Oct 13:53:59 | Claimed on Ethereum, same route | 1,000 wstETH | [0xd17830…b681](https://etherscan.io/tx/0xd17830a8579772a20889632b3921a761f56de5c136e3c7aff2a8f26dfd7fb681) |
| 9 Oct 13:55:53 | `0xC73448…` withdraws the rest through the Lido L2 bridge to Ethereum | 782.067 wstETH | [0xb59dbb…e669](https://basescan.org/tx/0xb59dbbcc0107e5e504f8127f50175f45633f33decbd4a4f17dca6ab651f9e669) |

## Where the funds are now (read on 12 Oct 2026, about 08:10 UTC)

| Address | Chain | wstETH | ETH | Nonce |
|---|---|---|---|---|
| `0xC73448…297f8D` | Ethereum | **1,001.0** | 0.0070 | 5 |
| `0xC73448…297f8D` | Base | 0 | 0.0226 | 4 |
| `0x0B5126…EdB034` (attacker EOA) | Base | 0 | 0.0200 | 22 |

- fundtrail found **no outgoing ERC-20 transfers** from `0xC73448…` on Ethereum between block
  26115000 and block 26175101. The 1,001 wstETH claimed on 9 Oct has not moved.
- **782.067 wstETH is in the Base to Ethereum withdrawal process.** It was burned on Base on 9 Oct
  and has not been paid out on Ethereum. PublicAML reports that this withdrawal was proved on Ethereum
  at 18:56 UTC on 9 Oct. fundtrail did not find that proof transaction itself. The address's
  Ethereum nonce of 5 is consistent with three proofs and two claims. Going by the first two
  withdrawals (proved on 4 Oct, claimed on 9 Oct), it could become claimable from about **14 Oct**.
  That date is an estimate.
- When it is claimed, all 1,783.067 wstETH will sit on one Ethereum EOA. wstETH has no issuer freeze
  function, so the main points of control are exchanges and other services where the funds may be deposited.

## Noise in the trace: address poisoning, not attacker flows

The fundtrail trace of the attacker EOA on Base also returned these, and they are **not** attacker activity:

- Two "0.03 ETH" transfers of fake tokens with look-alike symbols (`EṬH` at `0x90e283…`, and a second
  token at `0xbcafed…`). They went to addresses that share the first and last characters of `0xC73448…7f8d`
  (`0xc73494…7f8d`, `0xc73a06…7f8d`). Unrelated senders submitted these transactions, for example
  [0x5c8b9b…5fb5](https://basescan.org/tx/0x5c8b9b192ac246e079f37288dfc2c9e296441ac56a45ae70af9e1bf0513e5fb5),
  which was sent by `0x43b2f0…04bd` and emits dozens of similar fake transfers.
- Five zero-value wstETH `Transfer` events to `0xc7343a…7f8d` and `0xc73482…0f8d`, sent by unrelated
  batch transactions (for example [0xc106b2…671a](https://basescan.org/tx/0xc106b21cf35a854afaf28dfb24eec22099d24658c2eb7d8def5a97c9f1cf671a), sent by `0x3959e4…f1f6`).

This is the usual address-poisoning spam aimed at a newly active wallet.

## How this was produced

```bash
# Ethereum: outgoing token transfers from the holding address since about 3 Oct
fundtrail trace 0xC73448432a05deeA5Ea18a07D3b5d9ccf6297f8D --chain ethereum \
  --rpc https://mainnet.gateway.tenderly.co --from-block 26115000 --hops 2 --no-native
# Base: one hop from the attacker EOA and from the holding address
fundtrail trace 0x0B5126e1bc27C0de77e02e97945760A674EdB034 --chain base \
  --rpc https://base.gateway.tenderly.co --from-block 52150000 --hops 1 --no-native
fundtrail trace 0xC73448432a05deeA5Ea18a07D3b5d9ccf6297f8D --chain base \
  --rpc https://base.gateway.tenderly.co --from-block 52158200 --hops 1 --no-native
```

Each transaction in the timeline was then checked with `eth_getTransactionReceipt` (status, sender,
target, `Transfer` logs). The vault owner, Safe threshold and owner count were read with `eth_call`.

## Limits

- The 08:52 UTC whitelist removal that ExVul and PublicAML describe was not re-checked here.
- The Tornado Cash gas funding on Ethereum, also reported by PublicAML, was not re-checked here.
  It is an internal transfer, which fundtrail cannot see without a trace API.
- The vault and the attacker contract are unverified, so the function names are not known.
- The default publicnode endpoints now refuse `eth_getLogs` for blocks more than a few days old
  ("archive requests require a personal token"). This report used the Tenderly public gateways,
  which allow at most 1,000 blocks per call on Base.
- The tracer does not yet skip the zero address or zero-value and fake-token transfers. A 2-hop run
  on Base expanded `0x0` (every mint on the chain) and ran out of memory, which is why Base used `--hops 1`.

## Sources

- Blockaid, PeckShield, CertiK and ExVul alerts on X, 4 Oct 2026
- Blackpaper BP-1315: https://blackpaper.wiki/incident/BP-1315/
- PublicAML: https://publicaml.org/base-vault-hack/ (updated 10 Oct)
- SigIntZero: https://sigintzero.com/blog/base-wsteth-vault-6m-signed-whitelist-drain
- Lido Base bridge addresses: https://research.lido.fi/t/wsteth-deployment-to-base-and-ownership-acceptance-by-lido-dao/5668

This report names no person as responsible. It lists transactions between addresses as recorded on chain.
