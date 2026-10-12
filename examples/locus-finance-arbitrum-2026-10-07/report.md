# Locus Finance cross-chain vault, 8,010.99 USDC.e drained (Arbitrum → Ethereum), 7 Oct 2026

_Traced with fundtrail (early prototype) and checked against transaction receipts on 12 Oct 2026.
Check every finding against a block explorer before acting on it._

**Status as of 12 Oct 2026, 09:33 UTC (Ethereum block 26175516, Arbitrum block 514074887):**
the proceeds, now **3.3096 ETH**, sit unmoved at `0x7dA487…637A66` on Ethereum. That address has
never sent a transaction on Ethereum (nonce 0).

This report was written 5 days after the incident. It is not a live alert. It adds a verified
transaction list and the current location of the funds.

## Summary

- **Chains:** Arbitrum (the drain), Ethereum (where the funds went)
- **Loss:** 8,010.985591 USDC.e paid out by the vault to the attacker in one transaction. DeFiLlama lists about $18K
  for the protocol's Arbitrum deposits that day (as reported by Blackpaper).
- **Vault:** [`0x6318938f825f57d439b3a9e25c38f04ef97987d8`](https://arbiscan.io/address/0x6318938f825f57d439b3a9e25c38f04ef97987d8) (Arbitrum, proxy).
  Its share token [`0x95611dcbffc93b97baa9c65a23aafdec088b7f32`](https://arbiscan.io/address/0x95611dcbffc93b97baa9c65a23aafdec088b7f32)
  returns `name()` "Locus Yield USD" and `symbol()` "xUSD" (6 decimals).
- **Mechanism (from Blackpaper, not re-derived here):** the vault prices its shares from debt it believes is
  deployed to strategies on other chains. That debt is updated from signed strategy reports whose signature
  does not cover the amounts, so the recorded debt could be inflated without assets arriving. The attacker
  deposited a small amount and redeemed against the inflated valuation.
- **What fundtrail and the RPC reads confirm:** a 1 USDC.e deposit, then 11 seconds later a redemption that paid
  out 8,010.985591 USDC.e. Today the vault holds **0 USDC.e** while `totalAssets()` still returns
  **200,008,788.58** (6 decimals), consistent with Blackpaper's "about $200M recorded against a near-zero balance".
- **Exit:** about 22 hours later the attacker sent all of the USDC.e through Relay (a cross-chain intent bridge),
  which swapped it to ETH and delivered 3.3033 ETH to the same address on Ethereum.
- **Project response:** Blackpaper found no project statement. None was found for this report either.

## Addresses

| Role | Address | Chain |
|---|---|---|
| Vault (victim, holds the USDC.e) | [`0x6318938f825f57d439b3a9e25c38f04ef97987d8`](https://arbiscan.io/address/0x6318938f825f57d439b3a9e25c38f04ef97987d8) | Arbitrum |
| Vault share token (xUSD) | [`0x95611dcbffc93b97baa9c65a23aafdec088b7f32`](https://arbiscan.io/address/0x95611dcbffc93b97baa9c65a23aafdec088b7f32) | Arbitrum |
| Contract called by the redemption transaction | [`0xc66534d9f18a9ab1b092861590495f6e4b4cfe14`](https://arbiscan.io/address/0xc66534d9f18a9ab1b092861590495f6e4b4cfe14) | Arbitrum |
| Attacker EOA (same address on both chains) | `0x7dA487bAd95E5c4240B265B978DeD73546637A66` ([Arbitrum](https://arbiscan.io/address/0x7dA487bAd95E5c4240B265B978DeD73546637A66), [Ethereum](https://etherscan.io/address/0x7dA487bAd95E5c4240B265B978DeD73546637A66)) | Arbitrum, Ethereum |
| Relay Approval Proxy V3 / Router V3 / Depository (explorer name tags) | `0xCcC88a9d…315bE`, `0xb92fe925…fFf4f`, `0x4cD00E38…8BC31` | Arbitrum |

## Timeline (UTC, all transactions succeeded, checked by receipt)

| Time | What | Amount | Tx |
|---|---|---|---|
| 7 Oct 13:00:04 | Attacker swaps a little ETH for USDC.e through Relay on Arbitrum (Relay request `0x179137…11b0`) | 0.000779 ETH → 2.005289 USDC.e | [0x5f9387…5d38](https://arbiscan.io/tx/0x5f9387006dd2e3daa7e7f6c93ade465c9200c47cffac977e83db1cf3c5095d38) |
| 7 Oct 18:47:54 | Attacker deposits into the vault and receives shares | 1.000000 USDC.e in, 0.949053 xUSD minted | [0x8f76e0…eb0c](https://arbiscan.io/tx/0x8f76e0ea6df644331ca1687653f98ab095cfaf12bb8b01b31c65fc767c03eb0c) |
| 7 Oct 18:48:05 | Redemption: the attacker calls `0xc66534…fe14` (selector `0x72408ab6`). The vault burns 0.949053 xUSD and pays out USDC.e. In the same transaction the vault also sends 37.551665 USDC.e to `0x70f1bd…9a63` (an EIP-7702 delegated account; its role was not determined) and burns a further 0.003 xUSD. | **8,010.985591 USDC.e** to the attacker | [0xf8e6a0…9500](https://arbiscan.io/tx/0xf8e6a0c26ede17e671ce97e9d4de28ae433a9b0af460e4f04e7831e643829500) |
| 8 Oct 16:54:49 | Attacker sends all USDC.e to Relay (`transferAndMulticall` on Approval Proxy V3). Relay's router swaps it through an unlabelled USDC.e/USDC pool, a Uniswap V3 pool, Curve 2pool and WOOFi into 3.307040 WETH, unwraps it and deposits the ETH into the Relay Depository (`RelayNativeDeposit`, id `0x2b676b…9442`) | 8,011.99088 USDC.e | [0x4ee513…815b](https://arbiscan.io/tx/0x4ee513f5bc84e3f8ca2cdd4637ab2c7a2f09acef08b8c00a05398850698f815b) |
| 8 Oct 16:54:59 | Relay fill on Ethereum to the same address (sent by `0xf70da9…dbef`, the solver address named as `refundTo` in the Arbitrum call) | 3.303318 ETH | [0xc84d59…8789](https://etherscan.io/tx/0xc84d59db27a0e6e54476d2ae98adde105af825a888c4ff62eaab32958bf88789) |
| 8 Oct 16:55:47 | A second, small Relay transfer of leftover ETH from Arbitrum (in [0xf0b3e7…e32c](https://arbiscan.io/tx/0xf0b3e75fa5fb4c604282e6332a3a9a19366ee53856b9be13b636e1b8b975e32c)) | 0.006364 ETH in, 0.006275 ETH out | [0x58f7eb…aff5](https://etherscan.io/tx/0x58f7eb36a8128ac894ec527dfc31263c2312c96e754181d269394ed4d55baff5) |

The attacker held about 1 USDC.e before the drain (2.005289 from the 7 Oct swap, minus the 1 USDC.e deposit),
which is why 8,011.99 USDC.e left on 8 Oct against 8,010.99 USDC.e taken.

## Where the funds are now (read on 12 Oct 2026, 09:33 UTC)

| Address | Chain | USDC.e | ETH | Nonce |
|---|---|---|---|---|
| `0x7dA487…637A66` | Ethereum | | **3.309593** | 0 |
| `0x7dA487…637A66` | Arbitrum | 0 | 0.000086 | 10 |
| Vault `0x631893…87d8` | Arbitrum | **0** | | |

- The Ethereum balance equals the two Relay fills exactly (3.303318 + 0.006275 ETH), so the address has received
  nothing else on Ethereum and has sent nothing.
- The funds are plain ETH in an EOA. There is no issuer freeze. Points of control are exchanges and services
  where the ETH may later be deposited, and Relay, which keeps an off-chain record of the request.

## How this was produced

```bash
# Arbitrum: outgoing token transfers from the attacker since the drain block
fundtrail trace 0x7da487bad95e5c4240b265b978ded73546637a66 --chain arbitrum \
  --rpc https://arb1.arbitrum.io/rpc --from-block 512650243 --hops 2 --no-native
```

fundtrail found one outgoing transfer (8,011.99088 USDC.e to Relay Router V3 on 8 Oct) and stopped at the
contract, as designed. The steps after that were done by hand:

- Every transaction in the timeline was checked with `eth_getTransactionReceipt` (status, sender, target, `Transfer` logs).
- Incoming token transfers to the attacker on Arbitrum (blocks 511,900,000 to 514,075,000) were listed with `eth_getLogs`.
- Relay's public API (`/requests/v2?user=…`) listed three requests for the attacker. It names the Ethereum fill
  transactions, and both fills were checked on Ethereum by `eth_getTransactionByHash`.
- Balances, nonces, `totalAssets()`, and the share token's `name()`, `symbol()` and `decimals()` were read with `eth_call`.

## Limits

- The root cause comes from Blackpaper's review of the deployed source. This report did not re-read the vault source
  or decode the redemption call.
- The attacker's original gas funding on Arbitrum was not found. It arrived as native ETH, which fundtrail cannot
  index without a trace API or an explorer.
- The 37.551665 USDC.e sent to `0x70f1bd…9a63` in the drain transaction may be a fee or a strategy payment. It was
  not investigated.
- fundtrail stops at contracts. Bridges that are not in its label list, such as Relay, have to be followed by hand.
  Adding Relay's contracts to `labels.yaml` (after an on-chain check) would let the tool flag this exit automatically.
- The default publicnode Arbitrum endpoint refuses old blocks ("archive requests require a personal token"), so this
  report used the official `arb1.arbitrum.io` endpoint, which allows 30,000 blocks per `eth_getLogs` call.

## Sources

- Blackpaper BP-1325: https://blackpaper.wiki/incident/BP-1325/
- Arbiscan transaction page for the Relay exit (name tags for the Relay contracts, Uniswap V3, Curve and WOOFi):
  https://arbiscan.io/tx/0x4ee513f5bc84e3f8ca2cdd4637ab2c7a2f09acef08b8c00a05398850698f815b
- Relay public API: https://api.relay.link/requests/v2?user=0x7da487bad95e5c4240b265b978ded73546637a66

This report names no person as responsible. It lists transactions between addresses as recorded on chain.
