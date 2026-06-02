# Trailhead Gear Co. — Synthetic Dataset

This is the **seed dataset** for the capstone (see [../Projectoutline.md](../Projectoutline.md),
Section 5). Everything here is fictional. Extend it freely to make your demo feel real.

## Reference date — read this first

For **reproducible return-eligibility logic**, the dataset is anchored to a fixed
"today":

```
REFERENCE_DATE = 2026-06-02
```

All order dates were chosen relative to this date. Your **Order & Returns** agent should
treat `2026-06-02` as "now" (hardcode it as `REFERENCE_DATE`) rather than calling the
system clock — otherwise eligibility answers will drift as real time passes and the sample
scenarios will stop reproducing. If you prefer live dates, re-date the orders in
`orders.json` accordingly.

## The return window (cross-component rule)

`policies/returns-policy.txt` Section 1 is the **single source of truth**:

> Returns are accepted within **60 days of the delivery date**.

So an item is return-eligible when:

```
delivery_date is not null
AND status in {delivered}          # not yet delivered → can't start a return
AND (REFERENCE_DATE - delivery_date) <= 60 days
```

With `REFERENCE_DATE = 2026-06-02`, the cutoff delivery date is **2026-04-03**: orders
delivered on/after that date are inside the window, earlier ones are outside.

## Files

| Path | What it is | Used by |
|------|-----------|---------|
| `catalog/*.md` | 25 products, one Markdown file each | Product Advisor (RAG) |
| `policies/*.txt` | 5 policy documents, numbered ALL-CAPS sections | Policy & Support (RAG/FileSearch) |
| `orders.json` | 24 synthetic orders | Order & Returns (function tools) |

## Scenario coverage (Section 6 of the outline)

| Scenario | Data that supports it |
|----------|-----------------------|
| 1 — lightest 2P/3-season tent < $400 | `catalog/` has 5 tents; **Summit Ridge 2** ($379, 3.2 lb) is the correct answer. Featherlite UL 2 is lighter (2.4 lb) but $449 (over budget); Alpine Stormbreaker 2 is 4-season; Basecamp 4 is 4-person. |
| 2 — Glacier 15 temp rating + material | `catalog/glacier-15.md` — 15°F, 800-fill goose down. |
| 3 — status of order TGC-10293 | `orders.json` → TGC-10293, status `delivered`. |
| 4 — return boots from TGC-10293, in window? | TGC-10293 contains **Cascade Trail Boot** (TGC-FOOT-004), delivered 2026-04-24 → **inside** the 60-day window (≈21 days left). |
| 5 — return window + price-match REI | `returns-policy.txt` (60 days) + `price-match-policy.txt` (REI listed). |
| 6 — Summit Club membership | `membership-program.txt`. |
| 7 — TGC-10311 not arrived + membership | TGC-10311 status `shipped`, `delivery_date: null` (in transit) + `membership-program.txt`. |
| 8 — live bait (out of scope) | No such product/category anywhere → graceful fallback. |

**Also useful for testing the refusal path:** order **TGC-10250** (Stormshell Jacket,
delivered 2026-02-10) is **outside** the window — a correct system refuses that return.
