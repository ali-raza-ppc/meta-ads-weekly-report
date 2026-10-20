#!/usr/bin/env python3
"""
Meta Ads Weekly Report: week-over-week campaign analysis from Ads Manager exports.
Author: Ali Raza (github.com/ali-raza-ppc)

Usage:
    python weekly_report.py this_week.csv last_week.csv [-o report.md] [--target-roas 3] [--target-cpa 25]

Export each week from Meta Ads Manager at campaign level (Reports > Export table
data > .csv). Column names are matched flexibly, so the default "Performance"
column set plus "Purchases" and "Purchases conversion value" works out of the box.
Only the Python standard library is used.
"""
import argparse
import csv
import sys

# Column aliases as they appear in Meta Ads Manager exports.
ALIASES = {
    "campaign":    ["Campaign name", "Campaign Name", "Campaign"],
    "spend":       ["Amount spent (USD)", "Amount spent (EUR)", "Amount spent (GBP)", "Amount spent (DKK)",
                    "Amount spent (SEK)", "Amount spent (AED)", "Amount spent (PKR)", "Amount spent", "Spend"],
    "impressions": ["Impressions"],
    "clicks":      ["Link clicks", "Clicks (all)", "Clicks"],
    "purchases":   ["Purchases", "Website purchases", "Results"],
    "revenue":     ["Purchases conversion value", "Website purchases conversion value", "Purchase conversion value"],
}


def find_col(header, key):
    for name in ALIASES[key]:
        if name in header:
            return name
    for h in header:  # loose match, e.g. "Amount spent (NOK)"
        if any(h.lower().startswith(a.lower().split(" (")[0]) for a in ALIASES[key]):
            return h
    return None


def num(v):
    try:
        return float(str(v).replace(",", "").strip() or 0)
    except ValueError:
        return 0.0


def load(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        sys.exit(f"{path} is empty")
    header = rows[0].keys()
    cols = {k: find_col(header, k) for k in ALIASES}
    if not cols["campaign"] or not cols["spend"]:
        sys.exit(f"{path}: could not find campaign name / amount spent columns")
    out = {}
    for r in rows:
        name = (r.get(cols["campaign"]) or "").strip()
        if not name:
            continue  # skip totals / blank rows
        m = out.setdefault(name, {k: 0.0 for k in ALIASES if k != "campaign"})
        for k in m:
            if cols[k]:
                m[k] += num(r.get(cols[k]))
    return out


def kpis(m):
    s, i, c, p, rev = m["spend"], m["impressions"], m["clicks"], m["purchases"], m["revenue"]
    return {
        "Spend": s,
        "Purchases": p,
        "Revenue": rev,
        "ROAS": rev / s if s else 0,
        "CPA": s / p if p else 0,
        "CTR %": c / i * 100 if i else 0,
        "CPC": s / c if c else 0,
        "CPM": s / i * 1000 if i else 0,
        "CVR %": p / c * 100 if c else 0,
    }


def total(data):
    t = {k: 0.0 for k in ALIASES if k != "campaign"}
    for m in data.values():
        for k in t:
            t[k] += m[k]
    return t


def pct(new, old):
    if not old:
        return "n/a"
    return f"{(new - old) / old * 100:+.1f}%"


FMT = {"Spend": "{:,.2f}", "Revenue": "{:,.2f}", "Purchases": "{:,.0f}", "ROAS": "{:.2f}x",
       "CPA": "{:,.2f}", "CTR %": "{:.2f}%", "CPC": "{:,.2f}", "CPM": "{:,.2f}", "CVR %": "{:.2f}%"}
LOWER_IS_BETTER = {"CPA", "CPC", "CPM"}


def build_report(this, last, target_roas, target_cpa):
    lines = ["# Meta Ads Weekly Report", ""]
    tk, lk = kpis(total(this)), kpis(total(last))

    lines += ["## Account summary (week over week)", "", "| Metric | This week | Last week | Change |", "|---|---|---|---|"]
    for k in FMT:
        change = pct(tk[k], lk[k])
        if change != "n/a" and k != "Spend":
            better = (tk[k] < lk[k]) if k in LOWER_IS_BETTER else (tk[k] > lk[k])
            change += " ✅" if better else (" ⚠️" if tk[k] != lk[k] else "")
        lines.append(f"| {k} | {FMT[k].format(tk[k])} | {FMT[k].format(lk[k])} | {change} |")

    lines += ["", "## Campaigns", "",
              "| Campaign | Spend | WoW spend | Purchases | ROAS | WoW ROAS | CPA | CTR |",
              "|---|---|---|---|---|---|---|---|"]
    ranked = sorted(this.items(), key=lambda kv: kv[1]["spend"], reverse=True)
    for name, m in ranked:
        k = kpis(m)
        safe = name.replace("|", "\\|")
        prev = kpis(last[name]) if name in last else None
        lines.append(
            f"| {safe} | {k['Spend']:,.2f} | {pct(k['Spend'], prev['Spend']) if prev else 'new'} | "
            f"{k['Purchases']:,.0f} | {k['ROAS']:.2f}x | {pct(k['ROAS'], prev['ROAS']) if prev else 'new'} | "
            f"{k['CPA']:,.2f} | {k['CTR %']:.2f}% |")

    # Action list
    actions = []
    for name, m in ranked:
        k = kpis(m)
        if k["Spend"] > 0 and k["Purchases"] == 0:
            actions.append(f"**{name}**: spent {k['Spend']:,.2f} with no purchases. Check tracking and creative, then pause or cut budget.")
            continue
        if target_roas and k["ROAS"] >= target_roas * 1.2:
            actions.append(f"**{name}**: ROAS {k['ROAS']:.2f}x is well above target ({target_roas}x). Scale budget 15–20% if frequency allows.")
        elif target_roas and k["ROAS"] < target_roas * 0.8:
            actions.append(f"**{name}**: ROAS {k['ROAS']:.2f}x is below target ({target_roas}x). Refresh creative or reduce budget.")
        if target_cpa and k["CPA"] > target_cpa * 1.2:
            actions.append(f"**{name}**: CPA {k['CPA']:,.2f} is above target ({target_cpa}). Review audiences and landing page.")
        if name in last:
            p = kpis(last[name])
            if p["CTR %"] and k["CTR %"] < p["CTR %"] * 0.8:
                actions.append(f"**{name}**: CTR fell {pct(k['CTR %'], p['CTR %'])} WoW. Possible creative fatigue; test new hooks.")
    for name in last:
        if name not in this:
            actions.append(f"**{name}**: ran last week but not this week. Confirm it was paused on purpose.")

    lines += ["", "## Action plan", ""]
    lines += [f"{i}. {a}" for i, a in enumerate(actions, 1)] or ["No issues flagged. Keep current structure and keep testing creative."]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("this_week")
    ap.add_argument("last_week")
    ap.add_argument("-o", "--output", help="write Markdown report to this file")
    ap.add_argument("--target-roas", type=float, default=0)
    ap.add_argument("--target-cpa", type=float, default=0)
    a = ap.parse_args()
    report = build_report(load(a.this_week), load(a.last_week), a.target_roas, a.target_cpa)
    if a.output:
        with open(a.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Report written to {a.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
