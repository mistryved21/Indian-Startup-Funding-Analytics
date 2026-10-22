# Indian Startup Funding Analytics

End-to-end analytics project on India's startup funding records (2 Jan 2015 - 13 Jan 2020): data audit, exploratory analysis, reproducible cleaning, a Power BI data model with 30 validated DAX measures, a dashboard build guide, and evidence-based business insights.

## Project status (please read)
| Deliverable | Status |
|---|---|
| Data-quality audit, EDA notebook (executed, 14 charts) | Done |
| Reproducible cleaning pipeline, cleaned CSV, investor bridge, reports | Done - 16 validation checks pass |
| Power BI model (tables, relationships, hierarchies, 30 measures) | Built in Power BI Desktop; DAX logic **tested on a 7-record inline dataset** |
| Power BI data load and validation against the real data | **Pending** - the CSVs must be loaded on your PC (see "Power BI setup") |
| Dashboard pages and visuals | **Not built** - step-by-step guide provided; visuals must be created in Power BI Desktop |
| `.pbix` file | **Not included** (none created or validated) |
| Business insights report | Done - validated against the data files, not against a finished dashboard |

## Objective
Understand India's startup funding ecosystem - funding trends, industries, cities, investors and data reliability - and turn a messy records file into a trustworthy analytical dataset and an executive dashboard design.

## Dataset
`data/startup_funding.csv`: 3,044 records x 10 columns (Sr No, Date dd/mm/yyyy, Startup Name, Industry Vertical, SubVertical, City  Location [two spaces], Investors Name, InvestmentnType, Amount in USD, Remarks).
Key facts: 31.9% of amounts are undisclosed (971 records); 2015 rows have no usable industry; 45.6% of records list several investors; a record is **not** a verified funding round.

## Tools
Python 3.12+ (pandas, numpy, matplotlib), Jupyter, Power BI Desktop (Power Query M, DAX). See `requirements.txt`.

## Workflow
1. **Audit** - types, missing values, duplicates, date and amount formats, category consistency, outliers.
2. **EDA** - `notebooks/startup_funding_eda.ipynb` (univariate, bivariate, time series, statistics, ten business questions).
3. **Cleaning** - `scripts/clean_startup_funding.py`: escape-text removal, placeholders to missing (never zero), amount and date parsing, category standardization, investor bridge, flags; nothing deleted (3,044 rows in, 3,044 out).
4. **Model and DAX** - `powerbi/data_model.md`, `powerbi/dax_measures.md`.
5. **Dashboard** - `powerbi/dashboard_build_guide.md`, `powerbi/theme.json`.
6. **Insights** - `reports/business_insights.md`.

## Key findings (details and limitations in `reports/business_insights.md`)
- $38.1B disclosed across 2,073 records; median $1.75M vs mean $18.4M; top 10% of records hold 80.4% of the money.
- One unverified $3.9B record (Rapido, Series B, 2019) is 10.2% of all disclosed funding.
- eCommerce ($8.3B) and Consumer Internet ($6.3B) lead among classifiable industries; Bengaluru holds 49.2% of disclosed funding.
- Seed Funding is 45.9% of records but 2.2% of the money; Private Equity is 44.7% of records and 71.4% of the money.
- Yearly record counts fall from 936 (2015) to 111 (2019) while the record mix changes - the trend is not market growth.
- Investor rankings are recorded appearances only (3,071 names; 77% appear once).

## Folder structure
```
Indian_Startup_Funding_Analytics/
|-- README.md, requirements.txt
|-- data/
|   |-- startup_funding.csv            raw file (never modified)
|   |-- startup_funding_cleaned.csv    analysis-ready, 30 columns
|   `-- investor_bridge.csv            record x investor (5,885 rows)
|-- notebooks/startup_funding_eda.ipynb
|-- scripts/clean_startup_funding.py
|-- reports/
|   |-- data_quality_report.csv, cleaning_log.md, eda_summary.md, business_insights.md
|   |-- category_mappings.csv, investor_alias_map.csv, startup_name_review.csv
|   `-- figures/                       14 EDA charts (PNG)
`-- powerbi/
    |-- data_model.md, dax_measures.md, dashboard_build_guide.md
    |-- validation_queries.dax, theme.json
```

## Reproduce the analysis
```bash
pip install -r requirements.txt
python scripts/clean_startup_funding.py          # rebuilds cleaned CSV, bridge and reports; exits non-zero if any validation fails
jupyter notebook notebooks/startup_funding_eda.ipynb
```
The notebook reads `../data/startup_funding.csv` and writes charts to `../reports/figures/`.

## Power BI setup
1. In Power BI Desktop, set the `DataFolder` parameter (Home > Transform data) to the full path of the `data` folder, ending with a backslash; Close & Apply; Refresh.
2. Run `powerbi/validation_queries.dax` and compare with the expected values in that file.
3. Build the pages with `powerbi/dashboard_build_guide.md`; import `powerbi/theme.json`.
Details: `powerbi/data_model.md`.

## Assumptions and decisions
- Amounts are USD as labelled; no conversion. Dates are day/month/year (confirmed: no second part exceeds 12).
- Missing amounts stay blank; averages and medians use disclosed amounts only.
- Delhi, New Delhi, Gurugram, Noida and Faridabad stay separate in `City`; `City_Group` adds a Delhi-NCR grouping.
- Similar names (Ola / Ola Cabs, Finance / FinTech) are not merged without evidence; candidates are listed for review.
- Extreme amounts (9 records above about $534M) are flagged, not removed.

## Limitations
Uneven coverage by year, undisclosed amounts, unusable 2015 industry data, partly standardized investor names, startup-name variants, and an unverified largest record. See `reports/business_insights.md`.
