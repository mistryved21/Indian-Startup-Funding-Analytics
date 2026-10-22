# Business insights and recommendations - Indian Startup Funding

Every figure comes from `startup_funding.csv` (3,044 records, 2 Jan 2015 - 13 Jan 2020) and was calculated in `notebooks/startup_funding_eda.ipynb` or from `data/startup_funding_cleaned.csv`.
**Definitions:** a *record* is one row, not a verified funding round. *Funding* = disclosed amounts only. *Investor appearances* = times a name is recorded, not investments or performance.
**Status note:** the Power BI dashboard visuals and the in-dashboard validation are **not** part of this report; the numbers below are validated against the data files, not against a finished dashboard.

## Key findings

### 1. A few very large deals drive disclosed funding
- **Data shows:** $38.1B is disclosed across 2,073 of 3,044 records. The median record is $1.75M; the mean is $18.4M (10.5x). The top 10% of disclosed records hold 80.4% of the money, the bottom 50% hold 1.5%. Nine records above about $534M hold $12.8B (33.5%).
- **Why it matters:** averages and totals describe a handful of mega-rounds, not the typical startup.
- **Limitation:** the largest record - Rapido Bike Taxi, $3.9B labelled Series B (Aug 2019) - is 10.2% of everything and is **unverified**. Without it, 2019's total falls about 40% ($9.7B to $5.8B) while the median is unchanged.

### 2. Industry comparisons are only reliable for 2016-2020
- **Data shows:** 98.1% of 2015 records (918 of 936) have no usable industry (blank or free text) and no sub-vertical. In the cleaned data, 925 records (30.4%) and 22.4% of disclosed funding are "Unclassified".
- **Why it matters:** an all-years industry ranking under-represents 2015, the year with the most records.
- **Limitation:** 2019 is also 39.6% unclassified in the EDA's stricter definition.

### 3. eCommerce and Consumer Internet lead among classifiable industries
- **Data shows:** eCommerce $8.3B (21.7% of disclosed funding), Consumer Internet $6.3B (16.4%), Transportation $4.1B, Technology $2.2B, Finance $2.0B. By record count: Consumer Internet 943, Technology 478, eCommerce 300.
- **Why it matters:** eCommerce attracts larger tickets (mean $40.1M vs median $3.0M); Consumer Internet and Technology are broad, frequent labels.
- **Limitation:** 96% of Transportation's total is the single Rapido record. Finance/FinTech and Healthcare/Health and Wellness are separate labels. FinTech has the highest mean ($80.5M) but a median of only $5.0M.

### 4. Funding is geographically concentrated, led by Bengaluru
- **Data shows:** Bengaluru holds 49.2% of disclosed funding ($18.8B; 43.4% without Rapido) and 844 records. Mumbai 13.0%, Gurugram 10.2%, New Delhi 7.9%, Noida 3.4%; the top three cities hold 72.4%.
- **Why it matters:** Delhi, New Delhi, Gurugram, Noida and Faridabad are listed separately; combined they have 896 records and $8.7B, which would rank Delhi-NCR a clear second.
- **Limitation:** 230 records have no usable city (missing, multi-city or region-only); about 20 are outside India.

### 5. Seed deals dominate by count, private-equity-labelled deals by money
- **Data shows:** Seed Funding and Private Equity are 90.7% of records (45.9% and 44.7%). Private Equity carries 71.4% of disclosed funding, Seed 2.2%. Seed amounts are missing far more often (46.2% vs 20.9%).
- **Why it matters:** record counts and dollar totals tell opposite stories about which round types matter.
- **Limitation:** "Private Equity" is a catch-all; the stage (Series A, B...) is in Remarks for only 330 of its 1,362 records.

### 6. The yearly trend cannot be read as market growth
- **Data shows:** records per year: 936, 993, 687, 310, 111 (2015-2019); 2020 has 7 records covering 13 days. Disclosed totals: $8.7B, $3.8B, $10.4B, $5.1B, $9.7B. Disclosure coverage rises from 70% to 95% while the median rises from $1.5M to $12.0M.
- **Why it matters:** the record mix changes sharply (Seed Funding is 59% of 2016 records and 1.9% of 2018), so totals and medians are not like-for-like across years.
- **Limitation:** within a type the median does rise (Seed $350K to $1.4M; Private Equity $6.55M to $11.5M), but 2019 has only 4 disclosed Private Equity records. Month-to-month seasonality is within noise.

### 7. Investor names are fragmented and mostly appear once
- **Data shows:** 5,885 investor appearances across 3,071 names; 77% of names appear on one record only; 45.6% of records list two or more investors. Most frequently recorded: Sequoia Capital 122 appearances (87 startups), Accel 96 (68), Blume Ventures 61, Kalaari Capital 59, SAIF Partners 56. The top 10 names account for 9.6% of appearances.
- **Why it matters:** a "unique investors" KPI would be inflated by spelling variants (Accel has 8 spellings, Sequoia 6).
- **Limitation:** appearances are not verified investments and say nothing about performance. Only three firms were aliased beyond case/punctuation variants.

### 8. Startup counts are estimates and funding per startup is concentrated
- **Data shows:** about 2,244 distinct startups after name normalization (2,459 raw); 78% have one record. Flipkart (6 records, $4.8B) leads on summed amounts; the top 10 startups hold 45.8% of disclosed funding.
- **Why it matters:** "Ola" and "Ola Cabs" are listed separately ($2.1B combined); similar pairs likely exist (55 candidate pairs are in `reports/startup_name_review.csv`).
- **Limitation:** summing a startup's records can double-count a round listed twice.

## Opportunities (hypotheses for further research, not conclusions)
1. **Under-documented stage information:** most Private Equity rows lack a stage. Enriching them from a second source would turn the largest funding category into something analyzable.
2. **Seed-stage disclosure gap:** nearly half of seed records have no amount. A researcher covering early-stage activity should treat seed totals as a lower bound.
3. **Delhi-NCR as one market:** if the five NCR cities are treated as one, it is the clear second hub; investment research on "second hubs" should define geography explicitly.
4. **Investor mapping:** a curated investor master list (aliases, firm vs fund) would make co-investment and activity analysis meaningful.

## Recommendations for stakeholders
1. **Lead with median deal size, record counts and disclosure coverage;** never rank startups, industries or years on raw totals alone.
2. **Verify the Rapido $3.9B record** (and other records above about $534M) at source before publishing any headline figure; show a with/without-largest-deals view.
3. **Restrict industry comparisons to 2016-2020** or show the unclassified share beside every industry chart.
4. **Label investor views "recorded appearances"** and avoid performance language.
5. **Treat year-over-year charts as descriptions of this dataset,** not of the market, until record coverage by year is understood (records fall 88% between 2015 and 2019).
6. **Decide Delhi/NCR and Ola/Ola Cabs-type groupings explicitly** and document them; they change rankings.
7. **Extend the data** (more recent years, a stage field, a country column, a verified investor list) before using it for investment decisions.

## What this analysis cannot say
It cannot establish market size, growth, investor skill, or causes. It describes a records file with uneven coverage, 31.9% undisclosed amounts and no verification of individual deals.
