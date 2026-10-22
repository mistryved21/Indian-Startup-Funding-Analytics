# Dashboard build guide - INDIAN STARTUP FUNDING ANALYTICS

**Status:** the data model and all 30 measures already exist in the open Power BI Desktop file. **No report pages or visuals have been created** - Power BI visuals must be built by hand in Desktop. This guide gives exact steps, fields, filters and formatting. No `.pbix` is included because none has been created and validated.

**Do first:** load the data (`data_model.md`, section 4) and run `validation_queries.dax`. Do not build visuals until the headline numbers match.

Five pages are justified for this dataset: 3,044 records, five distinct analytical questions (overview, industry, investors/startups, geography, record-level lookup). Plus two hidden helper pages (tooltip, drill-through).

---
## 0. Setup (once)

1. **Import the theme:** View > Themes > Browse for themes > `theme.json`. It sets colors, Segoe UI fonts, white rounded cards on a light-grey page background.
2. **Page size:** View > Page view > Fit to page; Format page > Canvas settings > Type **Custom 1280 x 720** (px).
3. **Rename pages:** `1 Overview`, `2 Industry`, `3 Investors & Startups`, `4 Geography`, `5 Funding Explorer`, `Tooltip - Deal` (hidden), `Startup Detail` (hidden).
4. **Layout grid (all pages):** margins 24 px, gutter 16 px, content width 1,232 px.
   Header band y = 0-56 | slicer band y = 64-104 | content y = 116-696 | footnote y = 700-716.
5. **Header (every page):** text box at x 24, y 12: **INDIAN STARTUP FUNDING ANALYTICS** (Segoe UI Semibold 20, color #1F4E79), and under it a 10 pt grey sub-line (page name). Right side: **Insert > Buttons > Navigator > Page navigator** (x 880, y 12, w 376, h 36); style: selected = #1F4E79 fill + white text, default = white + #1F4E79 text. Hide the two helper pages from the navigator (they are hidden pages).
6. **Footnote (every page, 9 pt grey):** *"A record is one row in the source file, not a verified funding round. Funding = disclosed amounts only. Investor figures count recorded name appearances."*
7. **Sync slicers:** View > Sync slicers. Sync `Year`, `Industry`, `City`, `Investment Type` across the pages that show them (marked below). Do **not** sync the Startup/Investor search slicers.
8. **Model view check:** keep `Fact_Funding[Record_ID]`, `Startup_Key`, `Is_Amount_Disclosed` hidden; use only fields named in this guide.

### Common recipes (used below)
| Task | How |
|---|---|
| **Top N filter** | Select the visual > Filters pane > drag the category field (e.g. `Industry`) to *Filters on this visual* > Filter type **Top N** > Show items **Top 10** > By value: drag the measure (e.g. `Total Funding (USD)`) > **Apply filter** |
| **Exclude values** | Filters pane > category field > Filter type **Basic filtering** > tick all, untick `Unclassified` (or the listed values) |
| **Minimum-data filter** | Drag a measure (e.g. `Funding Records with Disclosed Amounts`) into *Filters on this visual* > **is greater than or equal to** 10 |
| **Data bars / color scale** | Format pane > Cell elements (table/matrix) > select the field > turn on **Data bars** or **Background color > fx > Gradient** (Minimum #E8F0F8, Maximum #1F4E79) |
| **Alt text** | Format pane > General > **Alt text**: one sentence stating what the visual shows |
| **Number display** | Measures already carry a dynamic currency format (`$38.1B`, `$1.8M`). On axes: Format > Y axis > **Display units: Auto**, **Value decimal places 1** |

### Number formats
| Quantity | Format | Where set |
|---|---|---|
| USD funding | `$38.1B` / `$1.8M` / `$350.0K` (dynamic) | already in the measure |
| Record / startup / investor counts | `#,0` | already in the measure |
| Percentages | `0.0%` ; growth `+0.0%;-0.0%` | already in the measure |
| Record-level amount (`Amount_USD`) | `$#,0` | column format already set |

---
## Page 1 - Executive Overview

```
y=0    [ title ........................................ page navigator ]
y=64   [Year v] [Industry v] [City v] [Investment type v]
y=116  [KPI][KPI][KPI][KPI][KPI][KPI]                     (6 x 192 w, 80 h)
y=208  [ Funding & records by year  608w ][ Top 10 industries 296w ][ Top 10 cities 296w ]   (h 212)
y=432  [ Investment type 400w ][ Records: industry x year heat-matrix 816w ]                (h 264)
```

**Slicers** (x 24 / 264 / 504 / 744, y 64, w 224, h 40, style **Dropdown**, search on, **synced**):
`Dim_Date[Year]` (title "Year") | `Fact_Funding[Industry]` | `Fact_Funding[City]` | `Fact_Funding[Investment_Type]`.

**KPI cards** - use the **Card (new)** visual, y 116, h 80, w 192, x = 24 + n x 208. Callout font 26 Semibold #1F4E79, label 10 pt grey.
| # | Title | Field | Reference label (add via *Reference labels > +*) |
|---|---|---|---|
| 1 | Total disclosed funding | `Total Funding (USD)` | `Disclosed Amount Coverage %` - "of records disclosed" |
| 2 | Funding records | `Funding Records` | `Funding Amount Missing Count` - "without an amount" |
| 3 | Unique startups (estimate) | `Unique Startups` | `Records per Startup` |
| 4 | Unique investor names | `Unique Investors (Named)` | `Multi-Investor Records %` - "list 2+ investors" |
| 5 | Average disclosed funding | `Average Disclosed Funding (USD)` | *(none)* |
| 6 | Median disclosed funding | `Median Disclosed Funding (USD)` | `Total Funding excl. Extreme Records (USD)` - "total w/o 9 extreme records" |

**Chart 1 - Funding and records by year** (x 24, y 208, w 608, h 212): **Line and clustered column chart**. X-axis `Dim_Date[Year]`; Column y `Total Funding (USD)`; Line y `Funding Records` (secondary axis). Title: *"Disclosed funding and record count by year (2020 = 13 days only)"*. Column color #1F4E79, line #E07B39. Data labels on columns. Tooltip page: `Tooltip - Deal` (see below).
**Chart 2 - Top 10 industries** (x 648, w 296): **Clustered bar chart**. Y `Fact_Funding[Industry]`; X `Total Funding (USD)`. Filters: Top N 10 by `Total Funding (USD)`; exclude `Unclassified`. Title *"Top 10 industries by disclosed funding"*. Data labels on, sort descending by value, bars #1F4E79.
**Chart 3 - Top 10 cities** (x 960, w 296): same as chart 2 with Y `Fact_Funding[City]`; exclude `Unknown`, `Multiple locations`, `Region/country only`. Title *"Top 10 cities by disclosed funding"*.
**Chart 4 - Investment type** (x 24, y 432, w 400, h 264): **Clustered bar chart**. Y `Investment_Type`; X `Funding Records`. Top N 8 by `Funding Records`. Title *"Funding records by investment type"*. Tooltip: add `Total Funding (USD)` and `Median Disclosed Funding (USD)` to *Tooltips* well so counts and dollars are both visible. Reason for a bar over a donut: 30+ categories and a long tail.
**Chart 5 - Activity by year and industry** (x 440, y 432, w 816, h 264): **Matrix** (heat-map). Rows `Industry`, Columns `Dim_Date[Year]`, Values `Funding Records`. Filters on Industry: Top N 8 by `Funding Records`, exclude `Unclassified`. Cell elements > Background color > Gradient (#E8F0F8 -> #1F4E79); font auto-contrast. Title *"Funding records by industry and year (2015 industries are mostly unclassified)"*. (Counts are used instead of dollars because yearly dollar totals are dominated by a few deals.)


---
## Page 2 - Industry Analysis

```
y=64   [Year v][Investment type v]                     [Unclassified % of funding card  256w]
y=116  [ Funding by industry 400w ][ Records by industry 400w ][ Avg vs median 400w ]   (h 256)
y=384  [ Top sub-verticals 400w ][ Contribution treemap 400w ][ Industry trend 400w ]   (h 312)
```
Slicers: `Year`, `Investment_Type` (synced). Right of them (x 1000, y 64, w 256, h 40) a **Card (new)**: `Unclassified Industry Share of Funding %`, label *"of disclosed funding is in unclassified industries"*.

| Visual | Type | Fields | Filters | Title |
|---|---|---|---|---|
| Funding by industry | Clustered bar | Y: hierarchy **Industry Drill** (Industry > Sub-Vertical); X: `Total Funding (USD)` | Top N 15 by funding; exclude `Unclassified` | *Total disclosed funding by industry (drill down for sub-verticals)* |
| Records by industry | Clustered bar | Y: `Industry`; X: `Funding Records` | Top N 15 by records; exclude `Unclassified` | *Funding records by industry* |
| Average vs median | Clustered bar | Y: `Industry`; X: `Average Disclosed Funding (USD)`, `Median Disclosed Funding (USD)` | `Funding Records with Disclosed Amounts` >= 10; exclude `Unclassified` | *Average vs median disclosed funding (industries with 10+ disclosed records)* |
| Top sub-verticals | Clustered bar | Y: `Sub_Vertical`; X: `Total Funding (USD)` | Top N 10; exclude `Unknown` | *Top sub-verticals by disclosed funding* |
| Contribution | Treemap | Group `Industry`; Values `Total Funding (USD)`; Tooltips `Share of Disclosed Funding %` | exclude `Unclassified` | *Industry share of classified funding* |
| Trend | Line chart | X `Dim_Date[Year]`; Y `Total Funding (USD)`; Legend `Industry` | Industry: Top N 5 by funding, exclude `Unclassified` | *Disclosed funding by year - top 5 industries* |

**Drill-down (how to):** select the first bar chart > turn on **Drill mode** (the down-arrow icon on the visual header) > click a bar to drill to its sub-verticals; use the up-arrow to return. In the Y-axis well the hierarchy shows both levels.
**Reading notes to add as a 9 pt text box (x 24, y 700):** "Mean is pulled up by a few mega-deals - compare with the median. 2015 records carry free-text sub-verticals and almost no industry labels, so use the Year slicer (2016-2020) for industry comparisons."

---
## Page 3 - Investor & Startup Analysis

```
y=64   [Year v][Industry v][Investment type v][Investor search]
y=116  [ Top investors 400w ][ Top startups by funding 400w ][ Startup record count 400w ]   (h 290)
y=418  [ Investment type table 400w ][ Investor & startup detail table 816w ]               (h 278)
```
Slicers: Year, Industry, Investment Type (synced) + **Investor search**: `Dim_Investor[Investor]`, style **List** with *Search* on (not synced).

| Visual | Type | Fields | Filters | Title |
|---|---|---|---|---|
| Top investors | Clustered bar | Y `Dim_Investor[Investor]`; X `Investor Appearances` | Top N 15 by `Investor Appearances` | **Most frequently recorded investors (appearances, not verified investments)** |
| Top startups by funding | Clustered bar | Y `Fact_Funding[Startup_Name]`; X `Total Funding (USD)` | Top N 15 | *Startups with the highest summed disclosed funding* |
| Startup record count | Clustered bar | Y `Startup_Name`; X `Funding Records` | Top N 10 | *Startups with the most funding records (a record is not a verified round)* |
| Investment type table | Table | `Investment_Type`, `Funding Records`, `Funding Records with Disclosed Amounts`, `Median Disclosed Funding (USD)`, `Total Funding (USD)` | none | *Investment type analysis* (data bars on `Total Funding (USD)`) |
| Detail table | Table | `Dim_Investor[Investor]`, `Fact_Funding[Startup_Name]`, `Industry`, `Investment_Type`, `Funding Records`, `Total Funding (USD)` | none | *Investor and startup detail (one row per investor-startup pair)* |

**What the investor ranking means:** each time a name is recorded on a funding record counts once; a record with three investors adds one to each. It does **not** measure money invested, success or verified deals. Put this sentence in a 9 pt text box under the chart. Placeholders ("Others", "Undisclosed") are excluded in the model.
**Drill-through:** right-click a startup bar > *Drill through* > `Startup Detail` (see the hidden pages).

---
## Page 4 - Geographic Analysis

```
y=64   [Year v][Industry v][Investment type v]
y=116  [ Funding by city 400w ][ Activity by city 400w ][ Top 10 cities table 400w ]   (h 290)
y=418  [ Industry mix in leading cities 816w ][ Delhi-NCR grouped view 400w ]          (h 278)
```
| Visual | Type | Fields | Filters | Title |
|---|---|---|---|---|
| Funding by city | Clustered bar | Y `City`; X `Total Funding (USD)` | Top N 12; exclude `Unknown`, `Multiple locations`, `Region/country only` | *Disclosed funding by city* |
| Activity by city | Clustered bar | Y `City`; X `Funding Records` | same exclusions; Top N 12 | *Funding records by city* |
| Top 10 cities | Table | `City`, `Funding Records`, `Median Disclosed Funding (USD)`, `Total Funding (USD)`, `Share of Disclosed Funding %` | Top N 10 by funding; same exclusions | *Top 10 cities* (data bars on Total) |
| Industry mix | 100% stacked bar | Y `City` (Top N 6 by records, same exclusions); X `Funding Records`; Legend `Industry` (Top N 6 by records, exclude `Unclassified`) | | *Industry mix (share of records) in the six most active cities* |
| Delhi-NCR view | Clustered bar | Y hierarchy **Geography Drill** (City Group > City); X `Total Funding (USD)` | Top N 8 City Group; same exclusions | *Cities with Delhi-NCR grouped (drill into the cities)* |

**Why no map:** the data has city names only (no coordinates or country), some values are multi-city or region-only, and Bing geocoding of short city names can misplace points. Ranked bars communicate the ranking more accurately. If you still want a map: add a **Map** visual with `City` in Location, Data category = *City*, `Total Funding (USD)` in Size, and visually check that all bubbles are in India before using it.
**Reading note:** "Delhi and New Delhi are separate in the left charts; the Delhi-NCR view groups Delhi, New Delhi, Gurugram, Noida and Faridabad. 230 records have no usable city and are excluded from city rankings."

---
## Page 5 - Detailed Funding Explorer

```
y=64   [Year v][Industry v][City v][Investment type v][Amount status (buttons)][Startup search]
y=116  [ Records table  1232w x 580h ]
```
Slicers: Year, Industry, City, Investment Type (synced) | **Amount status**: `Fact_Funding[Amount_Status]`, style **Tile** (values Disclosed / Repaired / Missing) | **Startup search**: `Fact_Funding[Startup_Name]`, style List, Search on (not synced).

**Table** (x 24, y 116, w 1232, h 580): columns in this order, all **not summarized**:
`Funding_Date` (format dd mmm yyyy, default sort **descending**), `Startup_Name`, `Industry`, `Sub_Vertical`, `City`, `Investors`, `Investment_Type`, `Amount_USD`, `Amount_Status`.
Format: Style preset *Minimal*, row padding 4, font 10, text wrap on for `Investors`, column header bold. Turn on **Search** in the visual header options.

**Conditional formatting - tell "missing" from "zero":** the file contains **no zero amounts**, undisclosed amounts are blank.
1. Format pane > Cell elements > select `Amount_USD` > **Background color** > fx > Format style **Rules**:
   Rule 1: *If value* **is blank** -> background `#FBE3D3`, font `#9A3F10`.
   Rule 2 (optional): *If value* **is greater than or equal to** 534,000,000 -> background `#D6E4F0` (extreme records).
2. Select `Amount_USD` > **Data bars** (positive #1F4E79).
3. Select `Amount_Status` > Background color > Rules: `Missing` -> `#FBE3D3`; `Repaired` -> `#FFF3CD`.
4. Add a text box above the table: *"Blank amount = not disclosed (never zero). Orange = undisclosed. Light blue = extreme record (about $534M or more)."*
**Drill-through:** right-click a row > *Drill through* > `Startup Detail`.

---
## Hidden helper pages

### Tooltip - Deal (report-page tooltip)
1. New page > Format page > Canvas settings > **Type: Tooltip** (320 x 240); Page information > **Allow use as tooltip: On**; hide the page.
2. Add four **Card (new)** visuals in a 2 x 2 grid: `Funding Records`, `Median Disclosed Funding (USD)`, `Disclosed Amount Coverage %`, `YoY Funding Growth %`. Page background #FFFFFF, no border.
3. On Page 1's year chart: Format > General > Tooltips > Type **Report page** > Page `Tooltip - Deal`. (Also useful on the industry bar charts: it shows the median and coverage next to every total.)

### Startup Detail (drill-through)
1. New page, hide it. In the Filters pane drag `Fact_Funding[Startup_Name]` into **Drill through** (Keep all filters: Off, Cross-report: Off).
2. Title text box: *"Startup detail"*; **Card (new)** with `Startup_Name` (First); cards `Total Funding (USD)`, `Funding Records`, `Funding Records with Disclosed Amounts`.
3. **Table:** `Funding_Date`, `Investment_Type`, `Funding_Stage`, `Investors`, `Amount_USD`, `Amount_Status`, `Remarks`.
4. A back button (Insert > Buttons > Back) at top left.

---
## Interactions, bookmarks, accessibility

**Interactions (Format > Edit interactions):**
- Page 1: keep the default cross-filtering between charts, with one change: select the *Investment type* chart (chart 4), then in Edit interactions set the **heat-matrix** (chart 5) to **None**, so choosing a type does not blank the matrix.
- KPI cards: leave default (they must respond to every slicer).
- Pages 2 and 4: set the *trend* and *treemap* visuals to **highlight**, not filter.

**Navigation:** keep the page navigator; also add a **Reset** button: View > Bookmarks > Add (with all slicers cleared, *Data* on, *Display* off) then Insert > Buttons > Bookmark, label "Reset filters".

**Accessibility and readability checklist**
- Minimum font 9 pt for notes, 10 pt for labels, 12 pt for titles.
- Colors: #1F4E79 on white contrast is 8.6:1; do **not** use the orange #E07B39 for small text (3:1) - only for bars, lines and fills.
- Never rely on color alone: heat-matrix cells show numbers; missing amounts show a rule color *and* the `Missing` text status.
- Alt text on every visual; set **Tab order** (Selection pane > Tab order) top-left to bottom-right; title every visual.
- Check View > **Show as table** works on charts; test the report with **Alt+Shift+F10** keyboard navigation.
- Avoid dual axes except Chart 1; label both axes.

---
## Final QA (Stage 6 preview)
1. Reconcile card 1 to $38.1B (38,143,914,864.22) and card 2 to 3,044 with no filters.
2. Hover the 2020 and 2019 columns of chart 1: the tooltip's YoY card must be **blank** for 2020 (partial year) and **+89.4%** for 2019.
3. Slice Industry = eCommerce: Funding Records 300; investor ranking changes accordingly.
4. Confirm no visual shows `Unclassified`, `Unknown`, `Multiple locations` in a ranking unless intended.
5. Save as `Indian_Startup_Funding_Analytics.pbix` and tell me; I can then validate every measure against the real data.
