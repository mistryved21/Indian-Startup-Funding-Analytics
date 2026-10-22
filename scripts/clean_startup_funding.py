#!/usr/bin/env python3
"""
Stage 3 - reproducible cleaning pipeline for startup_funding.csv

Run from anywhere:   python scripts/clean_startup_funding.py

Reads   data/startup_funding.csv              (never modified)
Writes  data/startup_funding_cleaned.csv      (one row per raw record, typed, Power BI ready)
        data/investor_bridge.csv              (record <-> investor, many-to-many)
        reports/data_quality_report.csv       (before / after validation)
        reports/cleaning_log.md               (every decision, with measured counts)
        reports/category_mappings.csv         (raw -> clean value for city, industry, investment type)
        reports/investor_alias_map.csv        (investor spellings that were unified)
        reports/startup_name_review.csv       (name pairs flagged for HUMAN review, NOT merged)

Principles: preserve the raw data, never fill missing amounts with zero, never merge categories
without a documented rule, flag (do not delete) outliers, and keep every raw record.
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "startup_funding.csv"
CLEAN_PATH = ROOT / "data" / "startup_funding_cleaned.csv"
BRIDGE_PATH = ROOT / "data" / "investor_bridge.csv"
REPORTS = ROOT / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------------------------
RENAME = {  # exact original names (note the DOUBLE space in 'City  Location')
    "Sr No": "Record_ID",
    "Date dd/mm/yyyy": "Funding_Date",
    "Startup Name": "Startup_Name",
    "Industry Vertical": "Industry",
    "SubVertical": "Sub_Vertical",
    "City  Location": "City",
    "Investors Name": "Investors",
    "InvestmentnType": "Investment_Type",
    "Amount in USD": "Amount_USD",
    "Remarks": "Remarks",
}
PLACEHOLDERS = {"", "nan", "n/a", "na", "null", "none", "-", "--", "undisclosed", "unknown"}
UNKNOWN = "Unknown"

IND_CANON = {  # same label after case/punctuation removal, or an unambiguous synonym / typo
    "ecommerce": "eCommerce", "ecommece": "eCommerce",
    "fintech": "FinTech", "financialtech": "FinTech",
    "edtech": "EdTech", "healthcare": "Healthcare",
    "foodbeverage": "Food & Beverage", "foodandbeverage": "Food & Beverage",
    "foodbeverages": "Food & Beverage", "foodandbeverages": "Food & Beverage",
    "transportation": "Transportation", "transport": "Transportation",
    "informationtechnology": "Information Technology", "it": "Information Technology",
    "consumerinternet": "Consumer Internet", "consumerinterne": "Consumer Internet",
    "saas": "SaaS",
}
IND_MIN_RECORDS = 5          # a label used at least this often is treated as a real industry label
IND_PLACEHOLDER_LABELS = {"others"}

CITY_MAP = {"bangalore": "Bengaluru", "gurgaon": "Gurugram", "ahemadabad": "Ahmedabad", "ahemdabad": "Ahmedabad",
            "kolkatta": "Kolkata", "nw delhi": "New Delhi", "bhubneswar": "Bhubaneswar",
            "kormangala": "Bengaluru", "andheri": "Mumbai", "chembur": "Mumbai", "taramani": "Chennai"}
REGION_ONLY = {"us", "usa", "india", "california", "karnataka", "haryana", "uttar pradesh", "kerala", "missourie"}
NCR = {"Delhi", "New Delhi", "Gurugram", "Noida", "Faridabad"}
OUTSIDE_INDIA = {"singapore", "san francisco", "menlo park", "palo alto", "santa monica", "burnsville", "nairobi",
                 "new york", "london", "seattle", "boston", "san jose", "tulangan", "us", "usa", "california", "missourie"}

INV_PLACEHOLDERS = {"others", "other", "undisclosed", "undisclosed investors", "undisclosed investor",
                    "n/a", "nan", "unknown", ""}
INV_ALIASES = [(re.compile(r"^sequoia\b"), "Sequoia Capital (all variants)"),
               (re.compile(r"^accel\b"), "Accel (all variants)"),
               (re.compile(r"^saif partners"), "SAIF Partners")]

STAGE_RE = re.compile(r"\b(pre[- ]?series a|series [a-j])\b", re.I)
LOG = []   # (step, action, affected, note)


def log(step, action, affected, note=""):
    LOG.append((step, action, affected, note))


# ----------------------------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------------------------
def clean_text(x):
    """Strip literal escape artifacts (\\xc2\\xa0, \\n) found in this file, collapse whitespace."""
    if pd.isna(x):
        return ""
    s = str(x)
    s = re.sub(r"\\+xe2\\+x80\\+x93", "-", s)      # escaped en dash
    s = re.sub(r"\\+x[0-9a-fA-F]{2}", "", s)        # escaped bytes such as \xc2\xa0
    s = re.sub(r"\\+n", " ", s)                      # literal \n
    return re.sub(r"\s+", " ", s).strip()


def is_placeholder(s):
    return s.strip().lower() in PLACEHOLDERS


ARTIFACT_RE = re.compile(r"\\+x[0-9a-fA-F]{2}|\\+n")


def parse_amount(x):
    s0 = "" if pd.isna(x) else str(x)
    s = clean_text(s0)
    if is_placeholder(s):
        return np.nan, "Missing"
    t = s.rstrip("+").replace(",", "").strip()
    try:
        v = float(t)
    except ValueError:
        return np.nan, "Unparseable"
    return v, ("Disclosed" if re.fullmatch(r"\d[\d,]*(\.\d+)?", s0) else "Repaired")


def parse_date(x):
    s0 = "" if pd.isna(x) else str(x)
    s = clean_text(s0)
    d = pd.to_datetime(s, format="%d/%m/%Y", errors="coerce")
    if pd.notna(d) and s == s0:
        return d, "Valid"
    t = s.replace("//", "/").replace(".", "/")
    t = re.sub(r"^(\d{1,2})/(\d{2})(\d{4})$", r"\1/\2/\3", t)        # 05/072018 -> 05/07/2018
    t = re.sub(r"/(\d{3})$", lambda m: "/2" + m.group(1), t)         # 01/07/015 -> 01/07/2015
    d = pd.to_datetime(t, format="%d/%m/%Y", errors="coerce")
    return d, ("Repaired" if pd.notna(d) else "Invalid")


def startup_key(s):
    k = s.lower()
    k = re.sub(r"^https?://(www\.)?", "", k)
    k = re.sub(r"/.*$", "", k)
    k = re.sub(r"\.(com|in|co|org|net|io)(\.in)?$", "", k)
    return re.sub(r"[^a-z0-9]", "", k) or s.lower()


def key_text(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def std_city(x):
    s = clean_text(x).rstrip(", ").strip()
    if is_placeholder(s):
        return np.nan
    if re.search(r"[/&,]| and ", s):
        return "Multiple locations"
    if s.lower() in REGION_ONLY:
        return "Region/country only"
    return CITY_MAP.get(s.lower(), s)


def std_invtype(x):
    """Return a standardized label, or None when no documented rule applies (caller keeps the cleaned text)."""
    s = clean_text(x)
    if is_placeholder(s):
        return np.nan
    k = re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s.lower())).strip()
    if re.search(r"seed.*(angel|angle)|(angel|angle).*seed", k):
        return "Seed / Angel Funding"
    if re.fullmatch(r"seed( funding)?( round)?", k):
        return "Seed Funding"
    if re.fullmatch(r"angel( funding| round)?", k):
        return "Angel Funding"
    if re.fullmatch(r"private ?equity( round)?", k):
        return "Private Equity"
    if re.fullmatch(r"pre ?series a", k):
        return "Pre-Series A"
    m = re.fullmatch(r"series ([a-j])( extension)?", k)
    if m:
        return f"Series {m.group(1).upper()}"
    if re.fullmatch(r"debt( funding)?|structured debt|term loan", k):
        return "Debt Funding"
    if re.fullmatch(r"crowd funding", k):
        return "Crowd Funding"
    return None


def stage_from_text(x):
    m = STAGE_RE.search(clean_text(x))
    if not m:
        return np.nan
    g = re.sub(r"[- ]+", " ", m.group(1).lower())
    return "Pre-Series A" if g.startswith("pre") else "Series " + g.split()[-1].upper()


def split_investors(x):
    s = clean_text(x)
    if is_placeholder(s):
        return []
    out, seen = [], set()
    for p in re.split(r",|;|\s&\s|\sand\s|/", s):
        p = re.sub(r"\s+", " ", p).strip().rstrip(".").strip()
        k = p.lower()
        if k in INV_PLACEHOLDERS or len(k) < 2 or k in seen:
            continue
        seen.add(k)
        out.append(p)
    return out


def investor_canonical_key(p):
    for rx, lab in INV_ALIASES:
        if rx.match(p.lower()):
            return lab.lower(), lab
    return re.sub(r"\s+", " ", p.lower().rstrip(".")).strip(), None


def md_table(rows, headers):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c).replace("|", "/") for c in r) + " |")
    return "\n".join(out)


# ----------------------------------------------------------------------------------------------
# Pipeline
# ----------------------------------------------------------------------------------------------
def main():
    # ---- 0. read (as text; nothing converted silently) --------------------------------------
    raw = pd.read_csv(RAW_PATH, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    assert set(raw.columns) == set(RENAME), f"Column mismatch: {set(raw.columns) ^ set(RENAME)}"
    n = len(raw)
    log("0", "Read raw file as text (UTF-8 with BOM)", f"{n:,} rows x {raw.shape[1]} cols", "Raw file is never modified.")

    # ---- 1. rename --------------------------------------------------------------------------
    r = raw.rename(columns=RENAME)
    assert list(r.columns) == list(RENAME.values())
    log("1", "Renamed 10 columns using the exact original names", "10 columns",
        "Original `City  Location` has a double space; the mapping uses the exact string and was asserted.")

    # ---- 2. text artifacts + whitespace -----------------------------------------------------
    art = {c: int(r[c].str.contains(ARTIFACT_RE).sum()) for c in r.columns if r[c].str.contains(ARTIFACT_RE).any()}
    log("2", "Removed literal escape artifacts (e.g. `\\xc2\\xa0`, `\\n`) and collapsed whitespace",
        f"{sum(art.values()):,} cells",
        "By column: " + ", ".join(f"{k}={v}" for k, v in art.items()))
    amount_original = r["Amount_USD"].copy()
    text = r.drop(columns=["Record_ID"]).apply(lambda s: s.map(clean_text))

    # ---- 3. placeholders -> missing (counted per column) ------------------------------------
    ph = {c: int(text[c].map(is_placeholder).sum()) for c in text.columns}
    log("3", "Identified placeholders (`nan`, `N/A`, `Undisclosed`, `unknown`, empty) as missing values",
        f"{sum(ph.values()):,} cells", "By column: " + ", ".join(f"{k}={v}" for k, v in ph.items()))

    c = pd.DataFrame({"Record_ID": r["Record_ID"].astype(int)})

    # ---- 4. dates ---------------------------------------------------------------------------
    dd = r["Funding_Date"].map(parse_date)
    c["Funding_Date"] = pd.to_datetime(dd.map(lambda t: t[0]))
    c["Date_Quality"] = dd.map(lambda t: t[1])
    assert c["Funding_Date"].notna().all(), "unparseable dates remain"
    c["Year"] = c["Funding_Date"].dt.year.astype(int)
    c["Quarter"] = "Q" + c["Funding_Date"].dt.quarter.astype(str)
    c["Year_Quarter"] = c["Year"].astype(str) + "-" + c["Quarter"]
    c["Month_Number"] = c["Funding_Date"].dt.month.astype(int)
    c["Month_Name"] = c["Funding_Date"].dt.month_name()
    rep = c[c["Date_Quality"] != "Valid"]
    log("4", "Parsed dates as day/month/year with an explicit format; repaired malformed separators only",
        f"{len(rep)} repaired, 0 invalid",
        "Day-first is supported: 1,744 dates have a first part >12 and none has a second part >12. "
        "`01/07/015` was read as 2015 because its record sits in the 2015 block. Repaired rows: "
        + "; ".join(f"#{i} `{r.loc[i-1,'Funding_Date']}`->{d:%Y-%m-%d}" for i, d in zip(rep["Record_ID"], rep["Funding_Date"])))

    # ---- 5. amounts -------------------------------------------------------------------------
    aa = r["Amount_USD"].map(parse_amount)
    c["Amount_USD"] = aa.map(lambda t: t[0]).astype(float)
    c["Amount_Status"] = aa.map(lambda t: t[1])
    c["Is_Amount_Disclosed"] = c["Amount_USD"].notna().astype(int)
    c["Amount_Original"] = amount_original
    assert (c["Amount_Status"] != "Unparseable").all()
    assert (c["Amount_USD"].dropna() > 0).all()
    vc = c["Amount_Status"].value_counts()
    log("5", "Converted Amount to numeric USD (commas removed - Indian and Western grouping give identical integers; trailing `+` dropped)",
        f"{int(vc.get('Disclosed',0)):,} clean + {int(vc.get('Repaired',0))} repaired",
        "No currency/unit conversion. `Amount_Original` keeps the raw text for traceability.")
    log("5b", "Left missing amounts EMPTY (never 0)", f"{int(vc.get('Missing',0)):,} records ({vc.get('Missing',0)/n*100:.1f}%)",
        "No confirmed zero-dollar funding exists in the file; `Amount_Status` = Missing marks them.")

    # ---- 6. outlier flag --------------------------------------------------------------------
    lx = np.log10(c["Amount_USD"].dropna())
    q1, q3 = lx.quantile([.25, .75])
    fence = 10 ** (q3 + 1.5 * (q3 - q1))
    c["Is_Extreme_Amount"] = (c["Amount_USD"] > fence).astype(int)
    top = c.loc[c["Amount_USD"].idxmax()]
    log("6", f"Flagged extreme amounts (log10 IQR rule, fence = ${fence:,.0f}); NOT removed",
        f"{int(c['Is_Extreme_Amount'].sum())} records",
        f"Largest record: Record_ID {int(top['Record_ID'])}, ${top['Amount_USD']:,.0f}, "
        f"{(top['Amount_USD']/c['Amount_USD'].sum())*100:.1f}% of all disclosed funding - needs source verification.")

    # ---- 7. startup names ------------------------------------------------------------------
    sn = text["Startup_Name"].map(lambda s: re.sub(r"^https?://(www\.)?|/+$", "", s))
    n_url = int((sn != text["Startup_Name"]).sum())
    c["Startup_Name_Original"] = text["Startup_Name"]
    c["Startup_Key"] = sn.map(startup_key)
    disp = pd.DataFrame({"k": c["Startup_Key"], "s": sn}).groupby("k")["s"].agg(lambda x: x.value_counts().index[0])
    c["Startup_Name"] = c["Startup_Key"].map(disp)
    changed = int((c["Startup_Name"] != c["Startup_Name_Original"]).sum())
    log("7", "Unified startup spellings that are identical after ignoring case, spaces, punctuation and a trailing .com/.in/.co",
        f"{text['Startup_Name'].nunique():,} -> {c['Startup_Name'].nunique():,} distinct names; {changed:,} records relabelled",
        f"Original kept in `Startup_Name_Original`; {n_url} URL-style name stripped of scheme/www. "
        "Different names (e.g. Ola vs Ola Cabs) are NOT merged - see startup_name_review.csv.")

    # ---- 8. city ---------------------------------------------------------------------------
    city_std = r["City"].map(std_city)
    c["City"] = city_std.fillna(UNKNOWN)
    c["City_Group"] = c["City"].map(lambda v: "Delhi-NCR" if v in NCR else v)
    low = city_std.fillna("").str.lower()
    c["Is_Outside_India"] = low.isin(OUTSIDE_INDIA).astype(int)
    log("8", "Standardized city: official renames (Bangalore->Bengaluru, Gurgaon->Gurugram), typos, well-known localities; "
             "multi-city cells = `Multiple locations`; state/country-only = `Region/country only`; missing = `Unknown`",
        f"{raw['City  Location'].nunique()} raw -> {c['City'].nunique()} distinct values",
        "Delhi and New Delhi stay SEPARATE in `City`; `City_Group` adds a Delhi-NCR grouping "
        f"({', '.join(sorted(NCR))}). `Is_Outside_India`=1 for {int(c['Is_Outside_India'].sum())} records identified from the city name "
        "(0 does not prove the location is in India).")

    # ---- 9. industry / sub-vertical ---------------------------------------------------------
    ind_text = text["Industry"]
    sub_text = text["Sub_Vertical"]
    ind_key = ind_text.map(lambda s: np.nan if is_placeholder(s) else key_text(s))
    key_count = ind_key.value_counts()
    label_disp = pd.DataFrame({"k": ind_key, "s": ind_text}).dropna().groupby("k")["s"].agg(lambda x: x.value_counts().index[0])
    canon = ind_key.map(lambda k: IND_CANON.get(k, label_disp.get(k)) if pd.notna(k) else np.nan)
    sub_missing = sub_text.map(is_placeholder)

    industry, status, moved = [], [], []
    for k, lab, txt, sm in zip(ind_key, canon, ind_text, sub_missing):
        if pd.isna(k):
            industry.append("Unclassified"); status.append("Missing"); moved.append(False)
        elif k in IND_PLACEHOLDER_LABELS:
            industry.append("Unclassified"); status.append("Placeholder label (Others)"); moved.append(False)
        elif key_count[k] >= IND_MIN_RECORDS:
            industry.append(lab); status.append("Standard label"); moved.append(False)
        elif sm:                                    # 2015 layout: description sits in the Industry column
            industry.append("Unclassified"); status.append("Free-text description"); moved.append(True)
        else:
            industry.append(lab); status.append("Rare label"); moved.append(False)
    c["Industry"] = industry
    c["Industry_Status"] = status
    c["Industry_Original"] = ind_text.where(~ind_text.map(is_placeholder), "")
    moved = pd.Series(moved)
    sub = sub_text.where(~sub_missing, UNKNOWN)
    sub = sub.where(~moved, ind_text)
    c["Sub_Vertical"] = sub
    c["Sub_Vertical_Source"] = np.where(moved, "Moved from Industry column",
                                        np.where(sub_missing, "Missing", "Original"))
    sc = c["Industry_Status"].value_counts()
    log("9", "Standardized industry: same-label variants unified (eCommerce/E-Commerce/ECommerce...), labels used >= "
             f"{IND_MIN_RECORDS} times kept, `Others` and blanks -> `Unclassified`",
        f"{raw['Industry Vertical'].nunique()} raw -> {c['Industry'].nunique()} distinct values",
        "Status counts: " + ", ".join(f"{k}={int(v)}" for k, v in sc.items()))
    log("9b", "2015 records keep a free-text description in the Industry column and have an empty SubVertical; the text was "
              "MOVED to `Sub_Vertical` and Industry set to `Unclassified`",
        f"{int(moved.sum())} records",
        "Reversible: `Industry_Original` keeps the text, `Sub_Vertical_Source` marks moved rows. "
        "Finance/FinTech and Healthcare/Health and Wellness remain separate labels.")

    # ---- 10. investment type + stage --------------------------------------------------------
    it_std = r["Investment_Type"].map(std_invtype)
    it_orig = text["Investment_Type"]
    it_final = it_std.copy()
    unmatched = it_std.isna() & ~it_orig.map(is_placeholder)
    it_final[unmatched] = it_orig[unmatched]
    c["Investment_Type"] = it_final.fillna(UNKNOWN)
    c["Investment_Type_Original"] = it_orig.where(~it_orig.map(is_placeholder), "")
    log("10", "Standardized investment type spellings (Seed/Angel variants, Private Equity Round, Pre-Series A, Debt...)",
        f"{raw['InvestmentnType'].nunique()} raw -> {c['Investment_Type'].nunique()} distinct values",
        f"{int(unmatched.sum())} records with no documented rule keep their cleaned original text (e.g. Corporate Round); "
        f"{int((c['Investment_Type'] == UNKNOWN).sum())} missing -> Unknown.")

    stage_type = c["Investment_Type"].where(c["Investment_Type"].str.match(r"^(Series [A-J]|Pre-Series A)$"), np.nan)
    stage_rem = text["Remarks"].map(stage_from_text)
    conflict = int((stage_type.notna() & stage_rem.notna() & (stage_type != stage_rem)).sum())
    c["Funding_Stage"] = stage_type.fillna(stage_rem).fillna("Not specified")
    log("11", "Derived `Funding_Stage` from Investment_Type (when it names a stage) else from Remarks",
        f"{int((c['Funding_Stage'] != 'Not specified').sum()):,} records with a stage",
        f"Stage found only in Remarks for {int((stage_type.isna() & stage_rem.notna()).sum())} records; "
        f"{conflict} records name a different stage in both fields (Investment_Type wins).")

    # ---- 12. investors + bridge -------------------------------------------------------------
    inv_text = text["Investors"]
    parts = inv_text.map(split_investors)
    rows = []
    for rid, plist in zip(c["Record_ID"], parts):
        seen = set()
        for p in plist:
            key, alias = investor_canonical_key(p)
            if key in seen:
                continue
            seen.add(key)
            rows.append((rid, p, key, alias))
    br = pd.DataFrame(rows, columns=["Record_ID", "Investor_As_Listed", "key", "alias"])
    disp_inv = br.groupby("key").apply(lambda g: g["alias"].dropna().iloc[0] if g["alias"].notna().any()
                                       else g["Investor_As_Listed"].value_counts().index[0], include_groups=False)
    br["Investor"] = br["key"].map(disp_inv)
    bridge = br[["Record_ID", "Investor", "Investor_As_Listed"]].reset_index(drop=True)
    c["Investors"] = inv_text.where(~inv_text.map(is_placeholder), UNKNOWN)
    cnt = bridge.groupby("Record_ID").size()
    c["Investor_Count"] = c["Record_ID"].map(cnt).fillna(0).astype(int)
    alias_map = (bridge[bridge["Investor"] != bridge["Investor_As_Listed"]]
                 .groupby(["Investor_As_Listed", "Investor"]).size().reset_index(name="Appearances")
                 .sort_values("Appearances", ascending=False))
    alias_map.to_csv(REPORTS / "investor_alias_map.csv", index=False, encoding="utf-8-sig")
    log("12", "Kept the original investor text in `Investors`; built `investor_bridge.csv` (one row per record x investor) by splitting on "
              "`,` `;` ` & ` ` and ` `/`, trimming, dropping placeholders (Others, Undisclosed), unifying case/trailing-dot variants "
              "and three major firms (Sequoia, Accel, SAIF)",
        f"{len(bridge):,} bridge rows; {bridge['Investor'].nunique():,} distinct investor names",
        f"{int((c['Investor_Count'] >= 2).sum()):,} records list 2+ investors. Investor figures are recorded APPEARANCES, not verified investments. "
        "Names containing `&` or `and` may be split incorrectly; `investor_alias_map.csv` lists every unified spelling.")

    # ---- 13. remarks ------------------------------------------------------------------------
    c["Remarks"] = text["Remarks"].where(~text["Remarks"].map(is_placeholder), "")
    log("13", "Kept Remarks (cleaned text; placeholders -> empty)", f"{int((c['Remarks'] != '').sum())} non-empty",
        "86% empty, but it holds the funding stage and strategic-deal notes for some records.")

    # ---- 14. duplicates (investigate, do not remove) -----------------------------------------
    k1 = ["Funding_Date", "Startup_Key", "Amount_USD", "Investors"]
    exact = int(c.drop(columns="Record_ID").duplicated().sum())
    biz = int(c.assign(a=c["Amount_USD"].fillna(-1)).duplicated(["Funding_Date", "Startup_Key", "a", "Investors"]).sum())
    same_day = c[c.duplicated(["Funding_Date", "Startup_Key"], keep=False)].sort_values(["Startup_Key", "Funding_Date"])
    log("14", "Checked duplicates on the CLEANED data", f"exact={exact}, same date+startup+amount+investors={biz}, same date+startup={len(same_day)} rows",
        "No record was removed. All 3,044 raw records are kept." + ("" if same_day.empty else
        " Same-day same-startup records for review: " + ", ".join(f"#{i}" for i in same_day['Record_ID'])))

    # ---- assemble ---------------------------------------------------------------------------
    cols = ["Record_ID", "Funding_Date", "Date_Quality", "Year", "Quarter", "Year_Quarter", "Month_Number", "Month_Name",
            "Startup_Name", "Startup_Name_Original", "Startup_Key",
            "Industry", "Industry_Status", "Industry_Original", "Sub_Vertical", "Sub_Vertical_Source",
            "City", "City_Group", "Is_Outside_India",
            "Investors", "Investor_Count", "Investment_Type", "Investment_Type_Original", "Funding_Stage",
            "Amount_USD", "Amount_Status", "Is_Amount_Disclosed", "Amount_Original", "Is_Extreme_Amount", "Remarks"]
    out = c[cols].sort_values("Record_ID").reset_index(drop=True)
    assert len(out) == n, "row count changed"
    out.to_csv(CLEAN_PATH, index=False, encoding="utf-8-sig", date_format="%Y-%m-%d", float_format="%.2f")
    bridge.to_csv(BRIDGE_PATH, index=False, encoding="utf-8-sig")
    log("15", "Wrote cleaned dataset and investor bridge", f"{len(out):,} rows, {len(cols)} columns",
        "UTF-8 with BOM, dates as yyyy-mm-dd, amounts with 2 decimals (blank when missing).")

    # ---- mapping tables for traceability ---------------------------------------------------
    maps = []
    for col, rawcol, newser in [("City", "City  Location", out["City"]), ("Industry", "Industry Vertical", out["Industry"]),
                                ("Investment_Type", "InvestmentnType", out["Investment_Type"])]:
        m = pd.DataFrame({"Column": col, "Raw_Value": raw[rawcol].values, "Clean_Value": newser.values})
        m = m.groupby(["Column", "Raw_Value", "Clean_Value"]).size().reset_index(name="Records")
        maps.append(m.sort_values(["Column", "Records"], ascending=[True, False]))
    pd.concat(maps).to_csv(REPORTS / "category_mappings.csv", index=False, encoding="utf-8-sig")

    # ---- startup names flagged for human review (NOT merged) ---------------------------------
    keys = out.groupby("Startup_Key").agg(name=("Startup_Name", "first"), records=("Record_ID", "count"))
    kl = sorted(keys.index, key=len)
    pairs = []
    for i, a in enumerate(kl):
        if len(a) < 4:
            continue
        for b in kl[i + 1:]:
            if b.startswith(a) and 0 < len(b) - len(a) <= 8:
                pairs.append((keys.loc[a, "name"], keys.loc[b, "name"], int(keys.loc[a, "records"]), int(keys.loc[b, "records"])))
    rev = pd.DataFrame(pairs, columns=["Name_A", "Name_B", "Records_A", "Records_B"])
    rev["Reason"] = "One normalized name starts with the other - possibly the same company; NOT merged"
    rev.sort_values(["Records_A", "Records_B"], ascending=False).to_csv(REPORTS / "startup_name_review.csv", index=False, encoding="utf-8-sig")
    log("16", "Listed possibly-related startup names for human review (not merged)", f"{len(rev)} pairs", "See reports/startup_name_review.csv (e.g. Ola / Ola Cabs).")

    # ---- validation against the cleaned FILE (re-read from disk) -----------------------------
    chk = pd.read_csv(CLEAN_PATH, encoding="utf-8-sig", parse_dates=["Funding_Date"])
    obj_cols = [col for col in chk.columns if chk[col].dtype == object or str(chk[col].dtype).startswith("str")]
    leftover_art = int(sum(chk[col].astype(str).str.contains(ARTIFACT_RE).sum() for col in obj_cols if col != "Amount_Original"))
    ws = int(sum((chk[col].dropna().astype(str) != chk[col].dropna().astype(str).str.strip()).sum() for col in obj_cols))
    cat_cols = ["Industry", "Sub_Vertical", "City", "Investors", "Investment_Type", "Startup_Name"]
    stray_ph = int(sum(chk[col].astype(str).str.strip().str.lower().isin({"nan", "n/a", "na", "none", "null", "undisclosed"}).sum() for col in cat_cols))
    raw_amt = pd.to_numeric(raw["Amount in USD"].map(clean_text).str.replace(",", "", regex=False).str.rstrip("+"), errors="coerce")
    checks = [
        ("Row count preserved", f"{n:,}", f"{len(chk):,}", len(chk) == n),
        ("Record_ID unique and complete", "unique 1-3,044", f"unique={chk['Record_ID'].is_unique}, min={chk['Record_ID'].min()}, max={chk['Record_ID'].max()}", chk["Record_ID"].is_unique and chk["Record_ID"].min() == 1 and chk["Record_ID"].max() == n),
        ("Funding_Date is a date type", "text (dd/mm/yyyy)", str(chk["Funding_Date"].dtype), str(chk["Funding_Date"].dtype).startswith("datetime")),
        ("Dates parsed", f"{int(raw['Date dd/mm/yyyy'].map(clean_text).str.fullmatch(r'\d{2}/\d{2}/\d{4}').sum()):,} in strict format", f"{int(chk['Funding_Date'].notna().sum()):,} valid dates", chk["Funding_Date"].notna().all()),
        ("Date range", "2 Jan 2015 - 13 Jan 2020 (after repair)", f"{chk['Funding_Date'].min():%Y-%m-%d} to {chk['Funding_Date'].max():%Y-%m-%d}", (chk['Funding_Date'].min().strftime('%Y-%m-%d'), chk['Funding_Date'].max().strftime('%Y-%m-%d')) == ("2015-01-02", "2020-01-13")),
        ("Amount_USD is numeric", "text", str(chk["Amount_USD"].dtype), pd.api.types.is_float_dtype(chk["Amount_USD"])),
        ("Disclosed amounts", f"{int(raw_amt.notna().sum()):,} parseable", f"{int(chk['Amount_USD'].notna().sum()):,}", int(raw_amt.notna().sum()) == int(chk["Amount_USD"].notna().sum())),
        ("Total disclosed USD reconciles to raw text", f"{raw_amt.sum():,.2f}", f"{chk['Amount_USD'].sum():,.2f}", bool(np.isclose(raw_amt.sum(), chk["Amount_USD"].sum()))),
        ("No zero or negative amounts", "n/a", f"min={chk['Amount_USD'].min():,.0f}", bool((chk["Amount_USD"].dropna() > 0).all())),
        ("Missing amounts left empty (not zero)", f"{int((raw_amt.isna()).sum()):,}", f"{int(chk['Amount_USD'].isna().sum()):,}", int(raw_amt.isna().sum()) == int(chk["Amount_USD"].isna().sum())),
        ("Escape artifacts left in text columns", f"{sum(art.values()):,} cells", f"{leftover_art}", leftover_art == 0),
        ("Leading/trailing spaces", "0", f"{ws}", ws == 0),
        ("Placeholder strings left in category columns", f"{sum(ph[k] for k in ['Industry','Sub_Vertical','City','Investors','Investment_Type']):,} cells", f"{stray_ph}", stray_ph == 0),
        ("Exact duplicate rows", "0", f"{exact}", exact == 0),
        ("Flagged extreme amounts retained", "n/a", f"{int(chk['Is_Extreme_Amount'].sum())} flagged, all still present", int(chk["Is_Extreme_Amount"].sum()) == int(out["Is_Extreme_Amount"].sum())),
        ("Investor bridge references valid records", "n/a", f"{bridge['Record_ID'].isin(chk['Record_ID']).all()}", bool(bridge["Record_ID"].isin(chk["Record_ID"]).all())),
    ]
    rows = [("Validation", name, before, after, "PASS" if ok else "FAIL") for name, before, after, ok in checks]
    # distinct values and missingness before/after
    def dist(rawcol, newcol): return (raw[rawcol].nunique(), chk[newcol].nunique())
    for label, rc, nc in [("Distinct startup names", "Startup Name", "Startup_Name"), ("Distinct industry labels", "Industry Vertical", "Industry"),
                          ("Distinct city labels", "City  Location", "City"), ("Distinct investment types", "InvestmentnType", "Investment_Type")]:
        b, a = dist(rc, nc)
        rows.append(("Consistency", label, f"{b:,}", f"{a:,}", "Reduced" if a < b else "Unchanged"))
    miss_rows = [("Amount", "Amount in USD", lambda s: s.map(lambda v: is_placeholder(clean_text(v))).sum(), chk["Amount_USD"].isna().sum()),
                 ("Industry", "Industry Vertical", lambda s: s.map(lambda v: is_placeholder(clean_text(v))).sum(), (chk["Industry_Status"] == "Missing").sum()),
                 ("Sub_Vertical", "SubVertical", lambda s: s.map(lambda v: is_placeholder(clean_text(v))).sum(), (chk["Sub_Vertical"] == UNKNOWN).sum()),
                 ("City", "City  Location", lambda s: s.map(lambda v: is_placeholder(clean_text(v))).sum(), (chk["City"] == UNKNOWN).sum()),
                 ("Investors", "Investors Name", lambda s: s.map(lambda v: is_placeholder(clean_text(v))).sum(), (chk["Investors"] == UNKNOWN).sum()),
                 ("Investment_Type", "InvestmentnType", lambda s: s.map(lambda v: is_placeholder(clean_text(v))).sum(), (chk["Investment_Type"] == UNKNOWN).sum()),
                 ("Remarks", "Remarks", lambda s: s.map(lambda v: is_placeholder(clean_text(v))).sum(), (chk["Remarks"].isna()).sum())]
    for label, rc, f, after_n in miss_rows:
        b = int(f(raw[rc]))
        note = "Blank (not zero)" if label == "Amount" else ("Empty" if label == "Remarks" else "Explicit 'Unknown' category" if label != "Industry" else "Industry_Status=Missing (value 'Unclassified')")
        rows.append(("Missing values", f"{label} - missing/placeholder cells", f"{b:,} ({b/n*100:.1f}%)", f"{int(after_n):,} ({after_n/n*100:.1f}%)", note))
    rows += [
        ("Flags", "Repaired dates", "8 malformed", f"{int((chk['Date_Quality']=='Repaired').sum())} repaired", "Date_Quality=Repaired"),
        ("Flags", "Repaired amounts", "8 with artifacts or '+'", f"{int((chk['Amount_Status']=='Repaired').sum())} repaired", "Amount_Status=Repaired"),
        ("Flags", "Extreme amounts", "outliers uninvestigated", f"{int(chk['Is_Extreme_Amount'].sum())} flagged (>= ${fence:,.0f})", "Kept; verify at source"),
        ("Flags", "Industry free text moved to Sub_Vertical", "2015 layout issue", f"{int((chk['Sub_Vertical_Source']=='Moved from Industry column').sum())} records", "Reversible via Industry_Original"),
        ("Flags", "Records outside India identified", "not identified", f"{int(chk['Is_Outside_India'].sum())} records", "From city name only"),
        ("Flags", "Records with 2+ investors", "multi-investor text", f"{int((chk['Investor_Count']>=2).sum()):,} records", "Use investor_bridge.csv"),
    ]
    dq = pd.DataFrame(rows, columns=["Section", "Check", "Before (raw)", "After (cleaned)", "Result / Note"])
    dq.to_csv(REPORTS / "data_quality_report.csv", index=False, encoding="utf-8-sig")
    fails = dq[dq["Result / Note"] == "FAIL"]

    # ---- cleaning_log.md ---------------------------------------------------------------------
    lines = ["# Cleaning log - Indian Startup Funding Analytics", "",
             f"Generated by `scripts/clean_startup_funding.py` from `data/startup_funding.csv` ({n:,} rows).", "",
             "The raw file is never modified. Every raw record is kept (**3,044 in, 3,044 out; 0 rows removed**).", "",
             "## Steps", "", md_table([(a, b, c_, d) for a, b, c_, d in LOG], ["Step", "Action", "Affected", "Notes"]), "",
             "## Validation (re-read from the cleaned file)", "",
             md_table([(r_[1], r_[2], r_[3], r_[4]) for r_ in rows[:len(checks)]], ["Check", "Before", "After", "Result"]), "",
             "## Decisions taken (defaults agreed after EDA)", "",
             "* **Largest record** (Record_ID %d, $%s): kept and flagged `Is_Extreme_Amount`; not verified against an external source." % (int(top['Record_ID']), f"{top['Amount_USD']:,.0f}"),
             "* **Delhi / New Delhi / Gurugram / Noida / Faridabad:** `City` keeps them separate; `City_Group` = `Delhi-NCR` for dashboards that need the grouping.",
             "* **Ola / Ola Cabs and similar pairs:** not merged without evidence; listed in `reports/startup_name_review.csv`.",
             "* **Finance / FinTech, Healthcare / Health and Wellness:** not merged.",
             "* **Missing amounts:** left blank. Averages and medians must use disclosed amounts only.", "",
             "## Not done (deliberately)", "",
             "* No amount was imputed, scaled or converted.",
             "* No record was deleted.",
             "* No investor was merged beyond case/punctuation variants and three major firms.",
             "* Startup display names use the most frequent spelling per normalized key (e.g. `Byjus`); the original text is in `Startup_Name_Original`.",
             "", "## Output files", "",
             "| File | Purpose |", "|---|---|",
             "| `data/startup_funding_cleaned.csv` | Analysis-ready fact table (one row per raw record) |",
             "| `data/investor_bridge.csv` | Record-to-investor many-to-many table |",
             "| `reports/data_quality_report.csv` | Before/after checks and counts |",
             "| `reports/category_mappings.csv` | Raw -> clean value for city, industry, investment type |",
             "| `reports/investor_alias_map.csv` | Investor spellings that were unified |",
             "| `reports/startup_name_review.csv` | Possibly-related startup names (not merged) |"]
    (REPORTS / "cleaning_log.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"Rows in/out: {n:,} / {len(out):,}")
    print(dq[dq["Section"] == "Validation"][["Check", "Before (raw)", "After (cleaned)", "Result / Note"]].to_string(index=False))
    if len(fails):
        print("\nFAILED CHECKS:\n", fails.to_string(index=False))
        sys.exit(1)
    print("\nAll validation checks passed.")


if __name__ == "__main__":
    main()
