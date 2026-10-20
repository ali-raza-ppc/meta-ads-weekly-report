# Meta Ads Weekly Report Generator

Turns two Meta Ads Manager CSV exports (this week and last week) into a clean **week-over-week report with an action plan**, in seconds. This is the same structure I use for weekly client reporting: account summary, campaign breakdown, then prioritised next steps.

## What you get

- **Account summary:** Spend, Revenue, Purchases, ROAS, CPA, CTR, CPC, CPM and CVR, with WoW change and ✅/⚠️ flags.
- **Campaign table:** ranked by spend, with WoW spend and ROAS movement.
- **Automatic action plan**, flagging:
  - campaigns spending with zero purchases,
  - campaigns well above target ROAS (scale candidates),
  - campaigns below target ROAS or above target CPA,
  - CTR drops over 20% WoW (creative fatigue),
  - campaigns that stopped running.

See [`sample_report.md`](sample_report.md) for the output from the included sample data.

## Usage

```bash
# 1. In Ads Manager: campaign level, set the date range, then Reports > Export table data > CSV
# 2. Run (Python 3, no extra packages needed):
python weekly_report.py this_week.csv last_week.csv --target-roas 3 --target-cpa 30 -o report.md
```

Column names are matched flexibly (`Amount spent (USD/EUR/GBP/DKK/SEK/AED/PKR)`, `Link clicks`, `Purchases`, `Purchases conversion value`, …), so standard exports work without editing.

## Files

| File | Purpose |
|---|---|
| [`weekly_report.py`](weekly_report.py) | The report generator |
| [`sample_this_week.csv`](sample_this_week.csv), [`sample_last_week.csv`](sample_last_week.csv) | Example exports (made-up numbers) |
| [`sample_report.md`](sample_report.md) | Example output |

## Reporting principles behind it

1. Lead with the business result (revenue, ROAS, CPA), not vanity metrics.
2. Always compare against last week **and** against target.
3. Every report ends in actions: scale, fix, pause or test.

---

Built by **[Ali Raza](https://ali-raza-ppc.github.io)**, Performance Marketing Specialist · [LinkedIn](https://www.linkedin.com/in/ali-raza-ads-manager/)
