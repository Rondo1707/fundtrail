# Set Protocol V1 "ETHMACOAPY" rebalancing set, 8.11 WETH drained in two transactions (Ethereum), 6 Oct 2026

_Traced with fundtrail (early prototype) and checked against transaction receipts on 13 Oct 2026.
Check every finding against a block explorer before acting on it._

**Status as of 13 Oct 2026, 08:15 UTC (Ethereum block 26182293):** neither attacker address still holds the
proceeds as a separate balance. Both are long-running, high-volume accounts (nonces 649 and 1835), and the
WETH/ETH they took was mixed with their other activity within minutes. There is no clean trail to an end
point, and this report does not claim one.

This report was written 7 days after the incident. It is not a live alert. It adds a verified transaction list,
receipt-level amounts, and the vault balance change.

## Summary

- **Chain:** Ethereum
- **Loss:** 8.109980 WETH left the Set Protocol V1 Vault across two transactions two blocks apart
  (4.047988 + 4.061992 WETH). The Vault's WETH balance fell from 486.027135 to 477.917155 WETH over those blocks.
  This matches the "about 8.11 WETH" reported by ExVul (via Foresight News) and by Tozvan citing SunWeb3Sec.
- **Product:** the ETHMACOAPY rebalancing set [`0xb647a1d7633c6c4d434e22ee9756b36f2b219525`](https://etherscan.io/address/0xb647a1d7633c6c4d434e22ee9756b36f2b219525),
  which returns `name()` "ETH 20 MA Crossover Yield II" and `symbol()` "ETHMACOAPY". Its base set
  [`0x10c9acd6e7b65abaf04118198553b375dc2b0ad4`](https://etherscan.io/address/0x10c9acd6e7b65abaf04118198553b375dc2b0ad4)
  returns `name()` "BaseAssetCollateral" and `symbol()` "BACOL". Set Protocol V1 has been deprecated since 6 April 2021
  (per Set's deprecation notice, as cited by Tozvan).
- **Mechanism (from ExVul and SunWeb3Sec as reported, not re-derived here):** `actualizeFee()` on the rebalancing
  set needs no role, and it recalculates `unitShares` with division rounded up even when no fee is due. The attacker
  issues rebalancing-set tokens, donates base-set collateral to the set's vault balance, calls `actualizeFee()`,
  then redeems the same number of tokens for more collateral than was deposited. The extra comes out of collateral
  held for other holders.
- **What the receipts confirm:** in each transaction the attacker contract mints and burns ETHMACOAPY within the
  same transaction, the BACOL supply drops (0.612600 → 0.552280 → 0.491752), and the Set Vault sends back more WETH
  than it received. ETHMACOAPY's total supply is unchanged (16.126317) before and after.
- **Two senders:** the transactions came from two different EOAs, each using a contract deployed in that moment.
  The second came 24 seconds (two blocks) after the first, on the same set. Whether they are related was not determined.
- **Related:** SlowMist (as reported by DefiEdge) describes a separate Set Protocol `actualizeFee` rounding loss of
  about 5.08 ETH. That incident was not traced here.

## Addresses

| Role | Address |
|---|---|
| Set Protocol V1 Vault (holds the WETH) | [`0x5b67871c3a857de81a1ca0f9f7945e5670d986dc`](https://etherscan.io/address/0x5b67871c3a857de81a1ca0f9f7945e5670d986dc) |
| ETHMACOAPY rebalancing set | [`0xb647a1d7633c6c4d434e22ee9756b36f2b219525`](https://etherscan.io/address/0xb647a1d7633c6c4d434e22ee9756b36f2b219525) |
| BACOL base set | [`0x10c9acd6e7b65abaf04118198553b375dc2b0ad4`](https://etherscan.io/address/0x10c9acd6e7b65abaf04118198553b375dc2b0ad4) |
| Attacker 1 EOA | [`0x3a15cf422307e922645d671cb247e76e8b1ec50d`](https://etherscan.io/address/0x3a15cf422307e922645d671cb247e76e8b1ec50d) |
| Attacker 1 contract (made the Set calls) | [`0xa0f52c688345d05859a94499e0809577b28f4e6d`](https://etherscan.io/address/0xa0f52c688345d05859a94499e0809577b28f4e6d) |
| Attacker 2 EOA | [`0xfc3facd67138966ab0c841e905b0c4bca1abe92f`](https://etherscan.io/address/0xfc3facd67138966ab0c841e905b0c4bca1abe92f) |
| Attacker 2 contract (deployed in block 26132516) | [`0x9308ec8254dad4fc81eae8dedcfb2863136a8ac1`](https://etherscan.io/address/0x9308ec8254dad4fc81eae8dedcfb2863136a8ac1) |
| Flash liquidity, tx 1: Spark WETH (`name()` "Spark WETH", `symbol()` "spWETH") | [`0x59cd1c87501baa753d0b5b5ab5d8416a45cd71db`](https://etherscan.io/address/0x59cd1c87501baa753d0b5b5ab5d8416a45cd71db) |
| Flash liquidity, tx 2: Morpho Blue and Uniswap v4 PoolManager (published deployment addresses), plus Aave v3 (`aEthWETH`, `aEthwstETH`, `aEthweETH`, `variableDebtEthWETH`) | `0xbbbbbbbbbb9cc5e90e3b3af64bdaf62c37eeffcb`, `0x000000000004444c5dc75cb358380d2e3de08a90`, `0x4d5f47fa6a74757f35c14fd3a6ef8e3c9bc514e8` |

## Timeline (UTC, both transactions succeeded, checked by receipt)

| Time | Block | What | Amount | Tx |
|---|---|---|---|---|
| 6 Oct 09:42:59 | 26132514 | Attacker 1 deploys a contract (nonce 325). Inside the same transaction, `0xa0f5…4e6d` borrows 116,000 WETH from Spark spWETH, mints 1,728.53 BACOL and 140,948.71 ETHMACOAPY, sends 1.490116 BACOL to the Vault (the donation), burns the ETHMACOAPY, redeems 1,728.60 BACOL, receives 116,004.047988 WETH from the Vault, repays 116,000 WETH and unwraps the rest | **4.047988 WETH** | [0xb54c77…8fc2](https://etherscan.io/tx/0xb54c77dae4c5ff8664779bacfb56d75242f39005b0b7778109d2f9033b9e8fc2) |
| 6 Oct 09:43:23 | 26132516 | Attacker 2 deploys `0x9308…8ac1` (nonce 1756) | | [0xfba982…2090](https://etherscan.io/tx/0xfba982e33350c15813445cd1123115123bf03f258ea3eeb9ce8d8d5486682090) |
| 6 Oct 09:43:23 | 26132516 | Attacker 2 calls it (nonce 1757). It flash-borrows wstETH, weETH and WETH from Morpho Blue and Uniswap v4, supplies wstETH/weETH to Aave v3 and borrows 285,617.51 WETH, sends 162,781.088502 WETH to the Vault, mints 2,425.63 BACOL and 197,773.16 ETHMACOAPY, donates 0.137245 BACOL, burns, redeems, and receives 162,785.150494 WETH back. After repaying, 4.059992 WETH goes to the EOA (plus 0.002 WETH spent on two dust swaps) | **4.061992 WETH** out of the Vault | [0x1dc6b9…e08a](https://etherscan.io/tx/0x1dc6b9f18c362192397e8483088f7957622a9323fd93ed2a22073bf309c8e08a) |

Vault WETH balance (`balanceOf` at block): 486.027135 (block 26132513) → 477.917155 (block 26132516).
Difference 8.109980 WETH = 4.047988 + 4.061992.

## Where the funds went (read on 13 Oct 2026, 08:15 UTC)

| Address | ETH before (block 26132513) | ETH after (block 26132516) | ETH now | WETH now | Nonce then → now |
|---|---|---|---|---|---|
| Attacker 1 `0x3a15…c50d` | 0.023716 | 4.070134 | 0.000095 | 0 | 325 → 649 |
| Attacker 2 `0xfc3f…e92f` | 0.088200 | 0.084569 | 0.110671 | 0 | 1756 → 1835 |

- **Attacker 1** received the proceeds as ETH. The balance rose by 4.046418 ETH in the attack transaction (4.047988
  less gas). The address has since sent 323 more transactions, and its outgoing token transfers include flash-sized
  USDC and DAI movements (20M each in blocks 26142103 and 26142122). The 4.05 ETH cannot be separated from that activity.
- **Attacker 2** received the proceeds as WETH and, 4 blocks later, sent 4.310831 WETH (the proceeds plus WETH it
  already held) to EOA [`0xedac2d8905bf2bf0033872d420c4ec6ef1ddd0c8`](https://etherscan.io/address/0xedac2d8905bf2bf0033872d420c4ec6ef1ddd0c8)
  in [0x5ab1c4…1ba0](https://etherscan.io/tx/0x5ab1c4dcb22646d857596a18042635d400589ed737433226ecf6f905bac81ba0).
  That address (nonce 30) now holds 0.047 WETH and 0.037 ETH, so it has moved the funds on. It was not traced further.
- Both attacker addresses also show address-poisoning spam after the incident: fake `Transfer` logs of look-alike
  tokens, such as `WĖTḨ` copying Attacker 2's real 4.310831 WETH amount and `ЕΤН`-style symbols on Attacker 1.
  These are not movements of the proceeds.
- This is plain ETH/WETH in EOAs. There is no issuer freeze. The amount is small and the accounts are busy, so
  attribution through an exchange deposit is unlikely to be clean.

## How this was produced

```bash
# Outgoing token transfers from each attacker EOA since the attack block, one hop
fundtrail trace 0x3a15cf422307e922645d671cb247e76e8b1ec50d --chain ethereum \
  --rpc https://rpc.mevblocker.io --from-block 26132514 --to-block 26182293 --hops 1 --no-native
fundtrail trace 0xfc3facd67138966ab0c841e905b0c4bca1abe92f --chain ethereum \
  --rpc https://rpc.mevblocker.io --from-block 26132514 --to-block 26182293 --hops 1 --no-native
```

- fundtrail kept the 25 largest outgoing transfers per address (`max_fanout`). For Attacker 1 these are dominated
  by flash-sized USDC/DAI and memecoin transfers. For Attacker 2 they include the WETH transfer above.
- The first run crashed on a token whose `Transfer` log has empty data (`0x`). A one-line fix (treat `0x` as zero)
  is on a separate branch, `fix/empty-hex-data`.
- Both attack transactions were found by scanning the full blocks for the sender prefixes given in the public
  write-ups, then decoded with `eth_getTransactionReceipt` (`Transfer` and WETH `Withdrawal` logs).
- Balances, nonces, `totalSupply()`, `name()` and `symbol()` were read with `eth_call` at the listed blocks.

## Limits

- The root cause is taken from ExVul and SunWeb3Sec as reported by Foresight News, Gate and Tozvan. This report
  did not read the ETHMACOAPY source, decode the calldata, or replay the attack.
- Native ETH movements out of Attacker 1 were not indexed (fundtrail cannot see them without a trace API).
- The Vault's WETH balance has fallen a further ~97 WETH since the incident (to 380.56 WETH at block 26182293).
  That may be ordinary redemptions or the separate ~5.08 ETH incident. It was not investigated.
- The default publicnode endpoint refuses blocks this old ("archive requests require a personal token") and the
  drpc free tier also limits `eth_getLogs`, so this report used `rpc.mevblocker.io` for reads.
- No project statement was found. Set Protocol V1 has been deprecated since 2021.

## Sources

- Gate News (citing Foresight News and ExVul), 6 Oct 2026: https://www.gate.com/news/detail/set-protocol-legacy-product-ethmacoapy-loses-811-weth-due-to-actualizefee-24781177
- Tozvan (citing SunWeb3Sec), 12 Oct 2026: https://tozvan.com/hacks/set-protocol-ethmacoapy-exploit
- DefiEdge (citing SlowMist) on the separate ~5.08 ETH Set Protocol loss: https://defiedge.com/security/setprotocol-lost-5-08-eth-to-rounding-error-in-actualize-fef0229d

This report names no person as responsible. It lists transactions between addresses as recorded on chain.
