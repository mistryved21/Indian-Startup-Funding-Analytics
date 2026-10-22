# EDA summary - Indian Startup Funding

Source: `startup_funding.csv` - 3,044 records, 10 columns, 2 Jan 2015 to 13 Jan 2020. Full evidence, code and charts: `notebooks/startup_funding_eda.ipynb` (charts in `reports/figures/`).
A *record* is one row, not a verified funding round. Funding figures use **disclosed amounts only**.

## Data quality at a glance
| Issue | Measured |
|---|---|
| Amount missing / undisclosed | 971 records (31.9%); 2,073 disclosed |
| Amounts needing repair | 8 (escape artifacts, trailing `+`); Indian and Western comma grouping both present |
| Dates | 3,036 in clean `dd/mm/yyyy`; 8 malformed (repaired, flagged); day-first confirmed |
| Escape-text artifacts (`\xc2\xa0`, `\n`) | 232 cells in 9 columns |
| Exact duplicates | 0 |
| Label inconsistency (raw distinct) | startups 2,459; industries 822; cities 115; investment types 57 |
| Industry unusable | 2015 rows: 98.1% have blank or free-text industry; SubVertical empty for all of 2015 |
| Multi-investor cells | 45.6% of records list 2+ investors |

## Key findings
1. **Funding is dominated by a few deals.** $38.1B disclosed; median record $1.75M vs mean $18.4M (10.5x). Top 10% of disclosed records hold 80.4%; bottom 50% hold 1.5%.
2. **One unverified record:** Rapido Bike Taxi, $3.9B "Series B" (Aug 2019) = 10.2% of all disclosed funding. Without it, 2019's total falls about 40% ($9.7B to $5.8B); the median is unaffected.
3. **Industry (2016-2020 only is reliable).** eCommerce $8.3B (21.7%) and Consumer Internet $6.3B (16.4%) lead on funding; Consumer Internet (943), Technology (478) and eCommerce (300) lead on records. Transportation's $4.1B is 96% the Rapido record.
4. **Geography.** Bengaluru holds 49.2% of disclosed funding (43.4% without Rapido); top 3 cities 72.4%. Delhi, New Delhi, Gurugram, Noida and Faridabad combined (illustrative) = 896 records and $8.7B, second to Bengaluru.
5. **Round types.** Seed Funding and Private Equity are 90.7% of records, but Private Equity carries 71.4% of disclosed funding and Seed 2.2%. Seed amounts are missing far more often (46.2% vs 20.9%).
6. **Trend caution.** Records per year: 936, 993, 687, 310, 111 (2015-2019; 2020 = 7 records in 13 days). Totals swing $8.7B / $3.8B / $10.4B / $5.1B / $9.7B. The mix of investment types changes sharply by year, so totals and medians are not like-for-like; no firm seasonality (4.3-point gap vs 3.0 points of normal noise).
7. **Investors.** 5,885 appearances across 3,071 names after splitting; 77% of names appear once. Most frequent: Sequoia Capital 122 appearances, Accel 96, Blume Ventures 61, Kalaari Capital 59, SAIF Partners 56 (recorded appearances, not verified investments).
8. **Startups.** About 2,244 distinct names after normalization; 78% have a single record. Flipkart (6 records, $4.8B) leads on summed amounts; "Ola" and "Ola Cabs" are listed separately ($2.1B combined).

## Main limitations
Heavy skew; uneven missing amounts; coverage that collapses after 2016; unusable industry for 2015; record counts that may repeat a round; fragmented investor and startup names.

## Implications for the dashboard
Lead with median deal size, record counts and disclosure coverage; provide a with/without-largest-deal view; label investor visuals "recorded appearances"; show the unclassified share on industry and city views; treat year-over-year charts as descriptions of this dataset, not the market.

## Cleaning plan (implemented in Stage 3)
See `reports/cleaning_log.md` and `scripts/clean_startup_funding.py`.
