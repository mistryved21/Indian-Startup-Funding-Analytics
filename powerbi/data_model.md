# Power BI data model - Indian Startup Funding Analytics

Built in the open Power BI Desktop file (model name: *Untitled*) through the Power BI modeling tools, then logic-tested with a small inline dataset (see "Validation"). **Data is not loaded yet**: the CSV files live on your PC, so Power Query reads them through a `DataFolder` parameter that you set once (steps below).

## 1. Star schema

```
                    Dim_Date (calculated)
                    Date [1] ----------------+
                                              | 1:*  single direction
                                              v
Dim_Investor [1] --1:*--> Bridge_Investor [*] --*:1 (both directions)--> Fact_Funding [1]
 Investor        single    Record_ID, Investor                           Record_ID (grain: 1 row per record)
```

| Table | Type | Grain | Rows (expected) |
|---|---|---|---|
| `Fact_Funding` | Import (Power Query, CSV) | One **funding record** (not a verified round) | 3,044 |
| `Dim_Date` | Calculated table (DAX), marked as date table | One calendar day, full years 2015-2020 | 2,192 |
| `Bridge_Investor` | Import (CSV) | One record x one named investor | 5,885 |
| `Dim_Investor` | Import (distinct names from the bridge) | One investor name | 3,071 |
| `_Measures` | Calculated table (hidden dummy column) | Holds the 30 measures | - |

### Why not more dimensions?
Industry, City, Investment Type and Startup are single-attribute labels with no extra descriptive columns, so separate dimension tables would only add relationships. They stay in `Fact_Funding` with two drill hierarchies (`Industry Drill`: Industry > Sub-Vertical, `Geography Drill`: City Group > City). Investors need their own tables because one record can list several investors (many-to-many).

## 2. Relationships

| From (many) | To (one) | Cardinality | Filter direction | Why |
|---|---|---|---|---|
| `Fact_Funding[Funding_Date]` | `Dim_Date[Date]` | Many-to-one | Single (Dim_Date -> Fact) | Standard date relationship; enables time intelligence |
| `Bridge_Investor[Record_ID]` | `Fact_Funding[Record_ID]` | Many-to-one | **Both** | Lets an investor selection filter the funding facts (and fact slicers filter investors). Safe: the model has no other path between these tables |
| `Bridge_Investor[Investor]` | `Dim_Investor[Investor]` | Many-to-one | Single (Dim_Investor -> Bridge) | Investor slicer / axis |

No relationship is based on similar names; each key was checked for uniqueness on the "one" side (Record_ID unique 1-3,044; Dim_Date[Date] unique; Dim_Investor[Investor] distinct).

## 3. Python vs Power Query vs DAX

| Where | What | Why |
|---|---|---|
| **Python** (`scripts/clean_startup_funding.py`) | Text/escape cleaning, placeholder handling, amount and date parsing, category standardization, investor splitting, flags | Heavy, documented, testable cleaning that must reconcile to the raw file |
| **Power Query** | Read CSV, promote headers, set data types, drop columns the report does not need, blank-amount-to-null | Only type-safe loading; **no business logic repeated** |
| **DAX** | `Dim_Date`, all measures, ranking logic, YoY | Calculations that must respond to slicers |

Columns deliberately **not** loaded into `Fact_Funding`: `Year/Quarter/Year_Quarter/Month_Number/Month_Name` (they live in `Dim_Date`) and the `*_Original` / `Amount_Original` audit columns (still in the CSV).

Hidden columns: `Startup_Key`, `Is_Amount_Disclosed` (fact); `Record_ID`, `Investor` (bridge); `Quarter Number`, `Month Number` (date); `Dummy` (measures table). Sort-by: `Month Name` and `Month Short` by `Month Number`; `Quarter` by `Quarter Number`.

## 4. Load the data (manual - about 2 minutes)

1. Save the project folder somewhere on your PC, e.g. `C:\Users\<you>\Documents\Indian_Startup_Funding_Analytics\`.
2. In Power BI Desktop: **Home > Transform data > Transform data**. Select the parameter **DataFolder** and set **Current Value** to the full path of the `data` folder **ending with a backslash**, e.g. `C:\Users\<you>\Documents\Indian_Startup_Funding_Analytics\data\`.
3. **Close & Apply**, then **Home > Refresh**. All four tables load; `Dim_Date` recalculates from the data.
4. Run the queries in `validation_queries.dax` (DAX query view) and compare with the expected values in that file.
5. **File > Save** (suggested name: `Indian_Startup_Funding_Analytics.pbix`).

If a table fails to load, check the path ends with `\data\` and that `startup_funding_cleaned.csv` and `investor_bridge.csv` are inside.

## 5. Power Query (M) - for rebuilding manually

Parameter `DataFolder` (Text, required):
```powerquery
"C:\Indian_Startup_Funding_Analytics\data\" meta [IsParameterQuery = true, Type = "Text", IsParameterQueryRequired = true]
```

`Fact_Funding`:
```powerquery
let
    Source = Csv.Document(File.Contents(DataFolder & "startup_funding_cleaned.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    BlankAmountToNull = Table.TransformColumns(Promoted, {{"Amount_USD", each if _ = "" then null else _, type nullable text}}),
    Typed = Table.TransformColumnTypes(BlankAmountToNull, {{"Record_ID", Int64.Type}, {"Funding_Date", type date}, {"Is_Outside_India", Int64.Type}, {"Investor_Count", Int64.Type}, {"Amount_USD", Currency.Type}, {"Is_Amount_Disclosed", Int64.Type}, {"Is_Extreme_Amount", Int64.Type}}, "en-US"),
    Kept = Table.SelectColumns(Typed, {"Record_ID", "Funding_Date", "Date_Quality", "Startup_Name", "Startup_Key", "Industry", "Industry_Status", "Sub_Vertical", "City", "City_Group", "Is_Outside_India", "Investors", "Investor_Count", "Investment_Type", "Funding_Stage", "Amount_USD", "Amount_Status", "Is_Amount_Disclosed", "Is_Extreme_Amount", "Remarks"})
in
    Kept
```

`Bridge_Investor`:
```powerquery
let
    Source = Csv.Document(File.Contents(DataFolder & "investor_bridge.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed = Table.TransformColumnTypes(Promoted, {{"Record_ID", Int64.Type}}, "en-US"),
    Kept = Table.SelectColumns(Typed, {"Record_ID", "Investor", "Investor_As_Listed"})
in
    Kept
```

`Dim_Investor`:
```powerquery
let
    Source = Csv.Document(File.Contents(DataFolder & "investor_bridge.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Names = Table.Distinct(Table.SelectColumns(Promoted, {"Investor"}))
in
    Names
```

`Dim_Date` (calculated table, DAX) is in `dax_measures.md`.

## 6. Modeling notes and limitations

* **Amounts:** `Amount_USD` is blank (not zero) for the 971 undisclosed records; measures use only disclosed amounts and report coverage separately.
* **Unclassified industry:** in the model, `Industry = "Unclassified"` means blank, 2015 free-text description or "Others" - 925 records (30.4%) and about 22.4% of disclosed funding. (The EDA notebook's 30.7% figure also counted rare but genuine labels such as "Hospitality" in a long tail; here they stay as their own industries.)
* **Investor counts** are distinct *names*, not verified investors; only case/punctuation variants and Sequoia, Accel and SAIF were unified.
* **YoY:** 2020 holds 7 records (1-13 Jan), so every YoY measure returns blank for it instead of comparing against a full 2019. 2015 has no prior year.
* **Compatibility level** was raised from 1600 to 1601, which the dynamic currency format (`$38.1B`, `$1.8M`, `$350.0K`) needs. Any current Power BI Desktop opens it.
* **Bidirectional bridge:** an investor filter also narrows other visuals through `Fact_Funding`. This is intended; avoid adding further relationships between `Fact_Funding` and the investor tables.

## 7. Validation performed

Because the real CSV could not be loaded from this environment, the DAX was tested on 7 inline test records with known answers, then the real Power Query sources were restored and the test rows cleared. All 30 measures compiled and matched hand-calculated values, including: total $4,061,000,000, median $4,000,000 (ignores the blank amount), 6 unique startups, Top City = Mumbai (the 'Multiple locations' record with the largest amount is excluded), Top Industry = FinTech, YoY 2019 = +7,311% and **blank** YoY for 2018 (no prior year) and for the partial year 2020, and investor drill-through (X: 2 records, $4M; Z: 1 record, $4B).
**Still to confirm after you load the real data:** the expected totals listed in `validation_queries.dax`.
