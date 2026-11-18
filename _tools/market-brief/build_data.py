#!/usr/bin/env python3
"""Build market-brief/data.json from a USA Trade Online CSV export.

Usage (from the repo root):

    python3 _tools/market-brief/build_data.py _tools/market-brief/source/<export>.csv

Several CSV files can be passed if the export was split; they are merged and
any cell that disagrees between files stops the build.

The page (market-brief/index.html) computes every figure it shows from the raw
values written here: weight, customs value, CIF value and calculated duty.
Nothing on the page is typed by hand, so updating this file updates the brief.

Standard library only. No installs needed.
"""
import argparse
import csv
import datetime
import json
import os
import re
import sys

LB_PER_KG = 2.20462262185

# 10-digit tariff code -> (product id, line label). A product can have several lines;
# the page sums them and also lists them separately in the data table.
LINES = {
    "0910990500": ("thyme", "Unprocessed (code also covers bay leaves)"),
    "0910990600": ("thyme", "Processed"),
    "0909610000": ("seeds", "Whole seed"),
    "0910995000": ("dill", "Weed and seed"),
    "0909210000": ("coriander", "Whole seed"),
}

# Display order, names and the one-line reading note shown under each product.
PRODUCTS = [
    {
        "id": "thyme",
        "name": "Thyme",
        "note": "Two tariff codes combined. The unprocessed code also covers bay leaves, "
                "a major Turkish export, so Turkey is not a like-for-like thyme comparison.",
        # optional: a short caution shown under an origin's name for this product
        "originNotes": {"TR": "incl. bay leaves"},
    },
    {
        "id": "seeds",
        "name": "Anise, fennel & caraway",
        "note": "One tariff code covers anise, fennel, caraway, star anise and juniper. "
                "Origins ship different mixes, so compare prices with care.",
    },
    {
        "id": "dill",
        "name": "Dill",
        "note": "Dill weed and dill seed share one tariff code. Seed is cheaper than weed, "
                "so an origin's average depends on its mix.",
    },
    {
        "id": "coriander",
        "name": "Coriander seed",
        "note": "Whole seed only (not crushed or ground).",
    },
]

ORIGINS = {"Egypt": "EG", "India": "IN", "Turkey": "TR", "World Total": "WORLD"}
ORIGIN_NAMES = {"EG": "Egypt", "IN": "India", "TR": "Turkey", "WORLD": "All origins"}

MEASURES = {
    "Customs Value (Gen) ($US) (Default Member)": "value",
    "Customs Value (Gen) ($US)": "value",
    "CIF Value (Gen) ($US)": "cif",
    "Calculated Duty($US)": "duty",
    "Calculated Duty ($US)": "duty",
    "Quantity 1 (Gen)": "kg",
}
UNIT_VALUE = "Customs Unit Value (Gen)"

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]


def fail(msg):
    sys.exit("ERROR: " + msg)


def parse_period(text):
    """Return (key, label, months) for a USA Trade Online time label."""
    t = text.strip()
    m = re.fullmatch(r"(\d{4})", t)
    if m:
        return "prev", m.group(1), 12
    m = re.fullmatch(r"(\d{4}) through (\w+)", t)
    if m and m.group(2) in MONTHS:
        n = MONTHS.index(m.group(2)) + 1
        label = ("Jan %s" % m.group(1)) if n == 1 else "Jan–%s %s" % (m.group(2)[:3], m.group(1))
        return "ytd", label, n
    m = re.fullmatch(r"(\w+) (\d{4})", t)
    if m and m.group(1) in MONTHS:
        return "latest", "%s %s" % (m.group(1)[:3], m.group(2)), 1
    fail("unrecognised time label: %r" % text)


def read_export(path):
    """Return (accessed-date string or None, {(code, origin, period_text): {field: number}})."""
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rows = [r for r in csv.reader(fh) if r]
    accessed = None
    m = re.search(r"accessed on (\w+ \d{1,2}, \d{4})", rows[0][0])
    if m:
        accessed = datetime.datetime.strptime(m.group(1), "%B %d, %Y").date().isoformat()
    head, data, in_measures = {}, {}, False
    for r in rows[1:]:
        if r[0] == "Measures":
            in_measures = True
            continue
        (data if in_measures else head)[r[0]] = r[1:]
    for need in ("Commodity", "Country", "Time", "District", "RateProvision"):
        if need not in head:
            fail("%s: header row %r is missing" % (path, need))
    cells, unit_values = {}, {}
    for i, commodity in enumerate(head["Commodity"]):
        code = commodity.split(" ", 1)[0]
        if code not in LINES:
            continue  # 6-digit roll-ups and anything not used by the brief
        if head["District"][i] != "All Districts" or head["RateProvision"][i] != "All Rate Provisions":
            fail("%s: column %d is not 'All Districts' / 'All Rate Provisions'" % (path, i + 2))
        country = head["Country"][i]
        if country not in ORIGINS:
            continue
        key = (code, ORIGINS[country], head["Time"][i])
        rec = {}
        for measure, field in MEASURES.items():
            if measure in data and i < len(data[measure]):
                raw = data[measure][i].strip()
                rec[field] = float(raw) if raw else 0.0
        for field in ("value", "cif", "duty", "kg"):
            if field not in rec:
                fail("%s: measure for %r is missing (need customs value, CIF value, "
                     "calculated duty and quantity 1)" % (path, field))
        if key in cells and cells[key] != rec:
            fail("%s: %r appears twice with different values" % (path, key))
        cells[key] = rec
        if UNIT_VALUE in data and i < len(data[UNIT_VALUE]) and data[UNIT_VALUE][i].strip():
            unit_values[key] = float(data[UNIT_VALUE][i])
    return accessed, cells, unit_values


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv", nargs="+", help="USA Trade Online CSV export(s)")
    ap.add_argument("--out", default=os.path.join("market-brief", "data.json"))
    ap.add_argument("--updated", default=datetime.date.today().isoformat(),
                    help="date shown on the page as 'Updated' (YYYY-MM-DD, default today)")
    args = ap.parse_args()

    cells, unit_values, accessed = {}, {}, None
    for path in args.csv:
        acc, c, u = read_export(path)
        accessed = max(filter(None, [accessed, acc]), default=None)
        for key, rec in c.items():
            if key in cells and cells[key] != rec:
                fail("files disagree on %r: %r vs %r" % (key, cells[key], rec))
            cells[key] = rec
        unit_values.update(u)
    if not cells:
        fail("no usable columns found. Check the export layout (see README.md).")

    # periods
    periods, by_text = {}, {}
    for text in sorted({k[2] for k in cells}):
        key, label, months = parse_period(text)
        if key in periods:
            fail("two time columns map to %r: %r and %r" % (key, periods[key]["source"], text))
        periods[key] = {"label": label, "months": months, "source": text}
        by_text[text] = key
    for need in ("prev", "ytd", "latest"):
        if need not in periods:
            fail("the export needs three time columns: a full prior year (e.g. 2025), "
                 "year to date (e.g. '2026 through September') and the latest month. Missing: %s" % need)

    # completeness + sanity checks
    problems = []
    for code in LINES:
        for okey in ORIGIN_NAMES:
            for text, pkey in by_text.items():
                if (code, okey, text) not in cells:
                    problems.append("missing %s / %s / %s" % (code, ORIGIN_NAMES[okey], text))
    if problems:
        fail("incomplete export:\n  " + "\n  ".join(problems))
    for (code, okey, text), rec in sorted(cells.items()):
        tag = "%s %s %s" % (code, okey, text)
        if min(rec.values()) < 0:
            problems.append("negative value in " + tag)
        if rec["cif"] + 1 < rec["value"]:
            problems.append("CIF below customs value in " + tag)
        if rec["value"] > 0 and rec["duty"] > rec["value"]:
            problems.append("duty above customs value in " + tag)
        if key_uv := unit_values.get((code, okey, text)):
            if rec["kg"] and abs(rec["value"] / rec["kg"] - key_uv) > 0.006:
                problems.append("unit value differs from Census's own figure in " + tag)
    for code in LINES:
        for text in by_text:
            world = cells[(code, "WORLD", text)]
            for field in ("kg", "value", "cif", "duty"):
                part = sum(cells[(code, o, text)][field] for o in ("EG", "IN", "TR"))
                if part > world[field] + 1:
                    problems.append("named origins exceed the world total: %s %s %s" % (code, text, field))
    if problems:
        fail("sanity checks failed:\n  " + "\n  ".join(problems))

    # assemble
    def num(x):
        return int(x) if float(x).is_integer() else round(x, 2)

    products = []
    for p in PRODUCTS:
        lines = []
        for code, (pid, label) in LINES.items():
            if pid != p["id"]:
                continue
            d = {}
            for text, pkey in by_text.items():
                d[pkey] = {o: {f: num(cells[(code, o, text)][f]) for f in ("kg", "value", "cif", "duty")}
                           for o in ORIGIN_NAMES}
            lines.append({"hts": "%s.%s.%s" % (code[:4], code[4:6], code[6:]), "label": label,
                          "data": {k: d[k] for k in ("prev", "ytd", "latest")}})
        entry = {"id": p["id"], "name": p["name"], "note": p["note"]}
        if p.get("originNotes"):
            entry["originNotes"] = p["originNotes"]
        entry["lines"] = lines
        products.append(entry)

    out = {
        "meta": {
            "updated": args.updated,
            "accessed": accessed,
            "source": "U.S. Census Bureau, USA Trade Online",
            "sourceUrl": "https://usatrade.census.gov/",
            "basis": "General imports, all U.S. customs districts",
            "focusOrigin": "EG",
            "minShare": 0.02,
            "periods": {k: {"label": periods[k]["label"], "months": periods[k]["months"]}
                        for k in ("prev", "ytd", "latest")},
        },
        "origins": ORIGIN_NAMES,
        "products": products,
    }
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    # audit print: the figures the page will show for the focus origin
    def tot(p, pkey, okey):
        t = {"kg": 0.0, "value": 0.0, "cif": 0.0, "duty": 0.0}
        for ln in p["lines"]:
            for f in t:
                t[f] += ln["data"][pkey][okey][f]
        return t

    print("Wrote %s  (data: %s vs %s; latest month %s; accessed %s)" % (
        args.out, periods["ytd"]["label"], periods["prev"]["label"], periods["latest"]["label"], accessed))
    print("\nEgypt, landed at a US port (customs value + freight & insurance + duty):")
    print("  %-26s %10s %10s %8s %8s %8s" % ("", "$/lb now", "$/lb prev", "change", "share", "duty"))
    for p in products:
        a, b = tot(p, "ytd", "EG"), tot(p, "prev", "EG")
        w = tot(p, "ytd", "WORLD")
        la = (a["cif"] + a["duty"]) / a["kg"] / LB_PER_KG
        lb_ = (b["cif"] + b["duty"]) / b["kg"] / LB_PER_KG
        print("  %-26s %10.3f %10.3f %+7.1f%% %7.1f%% %7.2f%%" % (
            p["name"], la, lb_, 100 * (la / lb_ - 1), 100 * a["kg"] / w["kg"], 100 * a["duty"] / a["value"]))
    print("\nAll checks passed. Open market-brief/ in a browser to review, then commit.")


if __name__ == "__main__":
    main()
