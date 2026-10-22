# DAX reference - Indian Startup Funding Analytics

All 30 measures live in the `_Measures` table and already exist in the open Power BI model. This file is the copy-paste reference. Rules followed: totals use `SUM` on **disclosed** amounts only; averages/medians ignore blanks; `DIVIDE` everywhere a denominator can be zero; records, startups and investors are separate measures; YoY uses the marked `Dim_Date` table.

## Dim_Date (calculated table)

After creating it: **Table tools > Mark as date table** on `Dim_Date[Date]`; sort `Month Name`/`Month Short` by `Month Number` and `Quarter` by `Quarter Number`.

```dax
Dim_Date =
VAR _MinDate = MIN ( Fact_Funding[Funding_Date] )
VAR _MaxDate = MAX ( Fact_Funding[Funding_Date] )
VAR _Start = IF ( ISBLANK ( _MinDate ), DATE ( 2015, 1, 1 ), DATE ( YEAR ( _MinDate ), 1, 1 ) )
VAR _End = IF ( ISBLANK ( _MaxDate ), DATE ( 2020, 12, 31 ), DATE ( YEAR ( _MaxDate ), 12, 31 ) )
VAR _DataEnd = IF ( ISBLANK ( _MaxDate ), DATE ( 2020, 12, 31 ), _MaxDate )
RETURN
    ADDCOLUMNS (
        CALENDAR ( _Start, _End ),
        "Year", YEAR ( [Date] ),
        "Year Status", IF ( DATE ( YEAR ( [Date] ), 12, 31 ) > _DataEnd, "Partial year", "Full year" ),
        "Quarter Number", QUARTER ( [Date] ),
        "Quarter", "Q" & QUARTER ( [Date] ),
        "Year-Quarter", YEAR ( [Date] ) & "-Q" & QUARTER ( [Date] ),
        "Month Number", MONTH ( [Date] ),
        "Month Name", FORMAT ( [Date], "mmmm" ),
        "Month Short", FORMAT ( [Date], "mmm" ),
        "Year-Month", FORMAT ( [Date], "yyyy-mm" )
    )
```

## Dynamic currency format

Measures marked **money** use this *format string expression* (Measure tools > Format > Dynamic) so cards show `$38.1B`, `$1.8M`, `$350.0K`. It needs compatibility level 1601+ (already set). Without it, use the static format `$#,0`.

```dax
SWITCH (
    TRUE (),
    ISBLANK ( SELECTEDMEASURE () ), "$#,0",
    ABS ( SELECTEDMEASURE () ) >= 1000000000, "$#,0.0,,,\B",
    ABS ( SELECTEDMEASURE () ) >= 1000000, "$#,0.0,,\M",
    ABS ( SELECTEDMEASURE () ) >= 1000, "$#,0.0,\K",
    "$#,0"
)
```

## Measures

### 1 Funding

**1. Total Funding (USD)**  - format: dynamic currency format (money)
*Disclosed amounts only. Blank (not 0) if nothing is disclosed.*

```dax
Total Funding (USD) =
SUM ( Fact_Funding[Amount_USD] )
```

**2. Average Disclosed Funding (USD)**  - format: dynamic currency format (money)
*AVERAGE ignores blanks, so only disclosed amounts count. Skewed by mega-deals - read with the median.*

```dax
Average Disclosed Funding (USD) =
AVERAGE ( Fact_Funding[Amount_USD] )
```

**3. Median Disclosed Funding (USD)**  - format: dynamic currency format (money)
*Best 'typical deal' measure for this skewed data.*

```dax
Median Disclosed Funding (USD) =
MEDIAN ( Fact_Funding[Amount_USD] )
```

**4. Largest Single Record (USD)**  - format: dynamic currency format (money)

```dax
Largest Single Record (USD) =
MAX ( Fact_Funding[Amount_USD] )
```

**5. Average Funding per Recorded Event (USD)**  - format: dynamic currency format (money)
*Diluted by undisclosed records in the denominator. NOT a typical deal size.*

```dax
Average Funding per Recorded Event (USD) =
DIVIDE ( [Total Funding (USD)], [Funding Records] )
```

**6. Total Funding excl. Extreme Records (USD)**  - format: dynamic currency format (money)
*Sensitivity view without the 9 records above about $534M (includes the unverified $3.9B record).*

```dax
Total Funding excl. Extreme Records (USD) =
CALCULATE ( [Total Funding (USD)], Fact_Funding[Is_Extreme_Amount] = 0 )
```

**7. Extreme Records Share of Funding %**  - format: `0.0%`

```dax
Extreme Records Share of Funding % =
DIVIDE (
    CALCULATE ( [Total Funding (USD)], Fact_Funding[Is_Extreme_Amount] = 1 ),
    [Total Funding (USD)]
)
```

**8. Share of Disclosed Funding %**  - format: `0.0%`
*Contribution within the visual, respecting slicers.*

```dax
Share of Disclosed Funding % =
DIVIDE (
    [Total Funding (USD)],
    CALCULATE ( [Total Funding (USD)], ALLSELECTED ( Fact_Funding ) )
)
```

### 2 Records and Coverage

**9. Funding Records**  - format: `#,0`
*A record is not a verified round.*

```dax
Funding Records =
COUNTROWS ( Fact_Funding )
```

**10. Funding Records with Disclosed Amounts**  - format: `#,0`
*COUNT ignores blanks.*

```dax
Funding Records with Disclosed Amounts =
COUNT ( Fact_Funding[Amount_USD] )
```

**11. Funding Amount Missing Count**  - format: `#,0`

```dax
Funding Amount Missing Count =
[Funding Records] - [Funding Records with Disclosed Amounts]
```

**12. Funding Amount Missing %**  - format: `0.0%`

```dax
Funding Amount Missing % =
DIVIDE ( [Funding Amount Missing Count], [Funding Records] )
```

**13. Disclosed Amount Coverage %**  - format: `0.0%`
*Show beside every funding total.*

```dax
Disclosed Amount Coverage % =
DIVIDE ( [Funding Records with Disclosed Amounts], [Funding Records] )
```

**14. Unique Startups**  - format: `#,0`
*Estimate by normalized name; Ola / Ola Cabs not merged.*

```dax
Unique Startups =
DISTINCTCOUNT ( Fact_Funding[Startup_Key] )
```

**15. Records per Startup**  - format: `0.00`

```dax
Records per Startup =
DIVIDE ( [Funding Records], [Unique Startups] )
```

### 3 Investors

**16. Unique Investors (Named)**  - format: `#,0`
*Distinct NAMES, not verified investors. Placeholders (Others, Undisclosed) excluded.*

```dax
Unique Investors (Named) =
DISTINCTCOUNT ( Bridge_Investor[Investor] )
```

**17. Investor Appearances**  - format: `#,0`
*Recorded appearances; one record with 3 investors adds 3. Not investments or performance.*

```dax
Investor Appearances =
COUNTROWS ( Bridge_Investor )
```

**18. Records with Named Investors**  - format: `#,0`

```dax
Records with Named Investors =
CALCULATE ( [Funding Records], Fact_Funding[Investor_Count] > 0 )
```

**19. Multi-Investor Records %**  - format: `0.0%`

```dax
Multi-Investor Records % =
DIVIDE (
    CALCULATE ( [Funding Records], Fact_Funding[Investor_Count] >= 2 ),
    [Funding Records]
)
```

### 4 Time Intelligence

**20. Funding by Year (USD)**  - format: dynamic currency format (money)
*Whole-year total even when a quarter or month is selected.*

```dax
Funding by Year (USD) =
CALCULATE ( [Total Funding (USD)], ALLEXCEPT ( Dim_Date, Dim_Date[Year] ) )
```

**21. Previous-Year Funding (USD)**  - format: dynamic currency format (money)
*Needs the marked Dim_Date table.*

```dax
Previous-Year Funding (USD) =
CALCULATE ( [Total Funding (USD)], SAMEPERIODLASTYEAR ( Dim_Date[Date] ) )
```

**22. YoY Funding Growth %**  - format: `+0.0%;-0.0%;0.0%`
*Blank when there is no prior year or the period runs past the last data date (2020 = 13 days). Not like-for-like across years.*

```dax
YoY Funding Growth % =
VAR _DataEnd =
    CALCULATE ( MAX ( Fact_Funding[Funding_Date] ), ALL ( Fact_Funding ), ALL ( Dim_Date ) )
VAR _SelectedEnd = MAX ( Dim_Date[Date] )
VAR _Current = [Total Funding (USD)]
VAR _Previous = [Previous-Year Funding (USD)]
RETURN
    IF (
        _SelectedEnd > _DataEnd || ISBLANK ( _Current ) || ISBLANK ( _Previous ),
        BLANK (),
        DIVIDE ( _Current - _Previous, _Previous )
    )
```

**23. Previous-Year Funding Records**  - format: `#,0`

```dax
Previous-Year Funding Records =
CALCULATE ( [Funding Records], SAMEPERIODLASTYEAR ( Dim_Date[Date] ) )
```

**24. YoY Records Growth %**  - format: `+0.0%;-0.0%;0.0%`
*Falling record counts may reflect data collection, not the market.*

```dax
YoY Records Growth % =
VAR _DataEnd =
    CALCULATE ( MAX ( Fact_Funding[Funding_Date] ), ALL ( Fact_Funding ), ALL ( Dim_Date ) )
VAR _SelectedEnd = MAX ( Dim_Date[Date] )
VAR _Current = [Funding Records]
VAR _Previous = [Previous-Year Funding Records]
RETURN
    IF (
        _SelectedEnd > _DataEnd || ISBLANK ( _Previous ),
        BLANK (),
        DIVIDE ( _Current - _Previous, _Previous )
    )
```

### 5 Rankings

**25. Top Industry by Funding**  - format: text
*Excludes 'Unclassified'. Show Unclassified Industry Share of Funding % beside it.*

```dax
Top Industry by Funding =
VAR _T =
    FILTER (
        ADDCOLUMNS ( VALUES ( Fact_Funding[Industry] ), "@Funding", [Total Funding (USD)] ),
        NOT ISBLANK ( [@Funding] ) && Fact_Funding[Industry] <> "Unclassified"
    )
RETURN
    IF ( COUNTROWS ( _T ) = 0, BLANK (), MAXX ( TOPN ( 1, _T, [@Funding], DESC ), Fact_Funding[Industry] ) )
```

**26. Top Industry Share of Funding %**  - format: `0.0%`

```dax
Top Industry Share of Funding % =
VAR _T =
    FILTER (
        ADDCOLUMNS ( VALUES ( Fact_Funding[Industry] ), "@Funding", [Total Funding (USD)] ),
        NOT ISBLANK ( [@Funding] ) && Fact_Funding[Industry] <> "Unclassified"
    )
RETURN
    DIVIDE ( MAXX ( _T, [@Funding] ), [Total Funding (USD)] )
```

**27. Top City by Funding**  - format: text
*Excludes Unknown / Multiple locations / Region-country only. Delhi, New Delhi and Gurugram are separate here; use City_Group for Delhi-NCR.*

```dax
Top City by Funding =
VAR _T =
    FILTER (
        ADDCOLUMNS ( VALUES ( Fact_Funding[City] ), "@Funding", [Total Funding (USD)] ),
        NOT ISBLANK ( [@Funding] )
            && NOT ( Fact_Funding[City] IN { "Unknown", "Multiple locations", "Region/country only" } )
    )
RETURN
    IF ( COUNTROWS ( _T ) = 0, BLANK (), MAXX ( TOPN ( 1, _T, [@Funding], DESC ), Fact_Funding[City] ) )
```

**28. Top City Share of Funding %**  - format: `0.0%`

```dax
Top City Share of Funding % =
VAR _T =
    FILTER (
        ADDCOLUMNS ( VALUES ( Fact_Funding[City] ), "@Funding", [Total Funding (USD)] ),
        NOT ISBLANK ( [@Funding] )
            && NOT ( Fact_Funding[City] IN { "Unknown", "Multiple locations", "Region/country only" } )
    )
RETURN
    DIVIDE ( MAXX ( _T, [@Funding] ), [Total Funding (USD)] )
```

### 6 Data Quality

**29. Unclassified Industry Share of Funding %**  - format: `0.0%`

```dax
Unclassified Industry Share of Funding % =
DIVIDE (
    CALCULATE ( [Total Funding (USD)], Fact_Funding[Industry] = "Unclassified" ),
    [Total Funding (USD)]
)
```

**30. Unclassified Industry Share of Records %**  - format: `0.0%`
*2015 records carry free text or blanks instead of an industry.*

```dax
Unclassified Industry Share of Records % =
DIVIDE (
    CALCULATE ( [Funding Records], Fact_Funding[Industry] = "Unclassified" ),
    [Funding Records]
)
```

## Notes on the requested measure list

* **Median / average** use only disclosed amounts. The average expressed in millions is a *display format*, not a different calculation.
* **Unique Investors** is counted on distinct *names* in the bridge; names are only partly standardized, so treat it as an upper-bound estimate.
* **Top Industry / Top City** exclude unclassified buckets by design and ignore ties beyond the alphabetical maximum.
* **Funding by Year** ignores quarter/month filters; use `Total Funding (USD)` on a Year axis for the normal view.
