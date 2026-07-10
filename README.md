# ComplyFlow GTM Analytics Pipeline

An end-to-end GTM (Go-To-Market) analytics project built on a synthetic B2B SaaS compliance automation company — designed to demonstrate hands-on RevOps/analytics engineering skills across the modern data stack: **Python → Snowflake → dbt → Looker Studio**.

🔗 **Live Dashboard:** [Looker Studio Report](https://datastudio.google.com/reporting/784e609a-78b7-4f5d-a756-6fa2f0234329)
📊 **Repo:** [github.com/SaipriyaReddyTurpu/gtm-complyflow-pipeline](https://github.com/SaipriyaReddyTurpu/gtm-complyflow-pipeline)

---

## Why this project

Most GTM/RevOps analytics portfolio projects stop at "funnel + revenue dashboard." This one goes further by adding two things real GTM teams actually care about but rarely see in portfolio work:

1. **A customer health scoring layer** — turning raw account activity into a risk signal, not just a lagging churn number
2. **A statistically rigorous A/B test** on a retention offer — including a two-proportion z-test, confidence intervals, and a power analysis, not just "treatment did better"

The goal was to build something that looks and behaves like a real internal analytics stack a Data/RevOps Analyst would maintain — including the messy debugging that comes with it (see Challenges & Debugging below).

---

## Architecture
generate_synthetic_data.py         (Python)
│
▼
Snowflake RAW schema               (8 tables, referential integrity)
│
▼
dbt: staging models (8)            GTM_DB.STAGING
│
▼
dbt: mart models (6)               GTM_DB.MART
│
▼
┌────────────┴────────────┐
▼                         ▼
Looker Studio          ab_test_analysis.py
(3-page dashboard)     (statsmodels/scipy —
z-test, CI, power analysis)

---

## Dataset

A synthetic B2B SaaS company ("ComplyFlow") with 8 interdependent CSVs generated in Python, preserving referential integrity end to end:

- Sales reps
- Accounts
- Leads
- Opportunities
- Subscriptions
- Revenue events
- Customer health scores
- Retention experiment (A/B test) assignments

A ~9 percentage point churn reduction effect was deliberately baked into the treatment group at generation time, so the downstream statistical tests have a real, known signal to detect — and the pipeline could be validated end to end against ground truth.

---

## Dashboard

**Page 1 — Overview**
KPI scorecards (Total Leads, Opportunity Count, Data Quality Score, Missing Lead Source Count), a lead-to-opportunity funnel, and win rate by segment/source.

**Page 2 — Revenue**
MRR waterfall combo chart (New MRR, Expansion MRR, Churned MRR as bars, Net MRR Change as an overlaid line) across the full historical period.

**Page 3 — Retention A/B Test** *(the differentiator)*
Control vs. treatment churn rate comparison, backed by a full statistical writeup:

- **Overall effect:** Treatment reduced churn by **12.72 percentage points** (38.12% → 25.41%), **p = 0.0003** — statistically significant at 95% confidence
- **By risk tier:** The effect was strongest in the "watch" risk tier (p < 0.0001, 16.29pt reduction). The "high_risk" tier showed a directionally similar effect (6.16pt reduction) but was **not** statistically significant (p = 0.3836) due to limited sample size
- **Power analysis:** ~1,015 accounts per group would be needed to reliably detect an effect of this size at 80% power in the high-risk tier — a deliberate inclusion to show statistical maturity, not just "eyeballing the percentages"
---

## Tech stack

| Layer | Tools |
|---|---|
| Data generation | Python, pandas |
| Data warehouse | Snowflake (AWS US East, Ohio) |
| Transformation | dbt (custom schema macro, staging + mart layers) |
| Statistical analysis | statsmodels, scipy (two-proportion z-test, confidence intervals, power analysis) |
| Credential management | `.env` + python-dotenv |
| BI / Visualization | Looker Studio |
| Version control | GitHub |

---

## Challenges & Debugging

Real bugs encountered and resolved during the build — included here deliberately, since debugging experience is as relevant as the finished product:

- Missing `return rows` in a data-loading function causing silent `NoneType` errors
- `zsh: no matches found` errors requiring quoted glob patterns
- Git credential conflicts between two GitHub accounts, resolved by embedding the username directly in the remote URL
- Missing pandas extras for the Snowflake connector, requiring `pip install "snowflake-connector-python[pandas]"`
- Network timeouts during package installs (e.g. `scipy`), typically resolved by retrying
- A silent-output issue in the A/B test analysis script during a work-in-progress phase, later resolved

---

## Project status

✅ Phase 1 — Synthetic data generation
✅ Phase 2 — Snowflake RAW schema + load pipeline
✅ Phase 3 — dbt staging + mart models
✅ Phase 4 — A/B test statistical analysis (z-test, CI, power analysis)
✅ Looker Studio dashboard (3 pages)

---

## Setup

```bash
# 1. Generate synthetic data
python generate_synthetic_data.py

# 2. Load into Snowflake (requires .env with credentials)
python load_to_snowflake.py

# 3. Run dbt transformations
cd gtm_pipeline
dbt run

# 4. Run the A/B test statistical analysis
python ab_test_analysis.py
```

Requires a `.env` file (not committed) with:
SNOWFLAKE_ACCOUNT=
SNOWFLAKE_USER=
SNOWFLAKE_PASSWORD=
SNOWFLAKE_WAREHOUSE=
SNOWFLAKE_DATABASE=

---

## Author

**Saipriya Reddy Turpu**
[GitHub](https://github.com/SaipriyaReddyTurpu) · [LinkedIn](https://www.linkedin.com/in/saipriyareddyturpu/)
