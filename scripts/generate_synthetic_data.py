"""
ComplyFlow Synthetic CRM & Retention Data Generator
-----------------------------------------------------
Generates a realistic B2B SaaS (compliance automation) dataset simulating
the full lead-to-revenue lifecycle PLUS a customer health scoring layer
and a retention-offer A/B test layer.
"""

import csv
import random
from datetime import date, timedelta
from pathlib import Path

from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)

OUT_DIR = Path(__file__).resolve().parent.parent / "data"
OUT_DIR.mkdir(exist_ok=True)



# ----------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------
N_SALES_REPS = 40
N_ACCOUNTS = 1800
N_LEADS = 6500
START_DATE = date(2024, 1, 1)
END_DATE = date(2026, 6, 30)

SEGMENTS = ["SMB", "Mid-Market", "Enterprise"]
SEGMENT_WEIGHTS = [0.55, 0.32, 0.13]

INDUSTRIES = [
    "FinTech", "HealthTech", "Cybersecurity", "HR Tech", "Legal Tech",
    "E-commerce", "EdTech", "Logistics", "InsurTech", "Data Infrastructure",
]

REGIONS = ["West", "Midwest", "Northeast", "South", "EMEA"]

LEAD_SOURCES = [
    "Paid Search", "Organic Search", "Content Download", "Partner Referral",
    "Compliance Webinar", "Outbound Prospecting", "G2/Capterra Review",
    "Security Conference",
]

# Compliance frameworks drive plan tier in this vertical
PLANS = {
    "SOC2 Starter": 1200,
    "SOC2 + ISO 27001": 2800,
    "Enterprise Multi-Framework": 6500,
}

RETENTION_TREATMENTS = [
    "csm_strategic_call",
    "audit_prep_discount_10pct",
    "free_extra_framework_addon",
]


def random_date(start: date, end: date) -> date:
    delta_days = (end - start).days
    return start + timedelta(days=random.randint(0, max(delta_days, 0)))



# ----------------------------------------------------------------------
# 1. SALES REPS (no dependencies)
# ----------------------------------------------------------------------
def gen_sales_reps():
    rows = []
    for i in range(1, N_SALES_REPS + 1):
        rows.append({
            "rep_id": f"REP-{i:04d}",
            "name": fake.name(),
            "region": random.choice(REGIONS),
            "quota_quarterly": random.choice([150000, 200000, 300000, 450000]),
            "hire_date": random_date(date(2022, 1, 1), date(2026, 1, 1)).isoformat(),
        })
    return rows




# ----------------------------------------------------------------------
# 2. ACCOUNTS (depends on: nothing, but referenced by everything downstream)
# ----------------------------------------------------------------------
def gen_accounts():
    rows = []
    for i in range(1, N_ACCOUNTS + 1):
        segment = random.choices(SEGMENTS, weights=SEGMENT_WEIGHTS)[0]
        arr_ranges = {
            "SMB": (8000, 25000),
            "Mid-Market": (25000, 90000),
            "Enterprise": (90000, 400000),
        }
        lo, hi = arr_ranges[segment]
        rows.append({
            "account_id": f"ACC-{i:05d}",
            "company_name": fake.company(),
            "segment": segment,
            "industry": random.choice(INDUSTRIES),
            "region": random.choice(REGIONS),
            "arr": round(random.uniform(lo, hi), 2),
            "signup_date": random_date(START_DATE, END_DATE - timedelta(days=30)).isoformat(),
        })
    return rows


# ----------------------------------------------------------------------
# 3. LEADS (depends on: nothing directly, but segment/source drive downstream)
# ----------------------------------------------------------------------
def gen_leads():
    rows = []
    for i in range(1, N_LEADS + 1):
        segment = random.choices(SEGMENTS, weights=SEGMENT_WEIGHTS)[0]
        source = random.choice(LEAD_SOURCES)

        # Compliance conferences & partner referrals convert better (industry-realistic)
        mql_boost = 1.25 if source in ("Security Conference", "Partner Referral") else 1.0
        # Enterprise segment realistically converts less often but at higher value
        segment_factor = {"SMB": 1.0, "Mid-Market": 0.9, "Enterprise": 0.75}[segment]

        roll = random.random() * mql_boost * segment_factor
        if roll > 0.82:
            status = "Opportunity"
        elif roll > 0.55:
            status = "SQL"
        elif roll > 0.30:
            status = "MQL"
        elif roll > 0.05:
            status = "New"
        else:
            status = "Disqualified"

        rows.append({
            "lead_id": f"LEAD-{i:06d}",
            "segment": segment,
            "lead_source": source if random.random() > 0.03 else "",
            "status": status,
            "created_at": random_date(START_DATE, END_DATE - timedelta(days=15)).isoformat(),
        })
    return rows


# ----------------------------------------------------------------------
# 4. OPPORTUNITIES (depends on: leads, accounts, sales_reps)
# ----------------------------------------------------------------------
def gen_opportunities(leads, accounts, sales_reps):
    rows = []
    qualifying_leads = [l for l in leads if l["status"] in ("SQL", "Opportunity")]
    opp_counter = 1
    for lead in qualifying_leads:
        account = random.choice(accounts)
        rep = random.choice(sales_reps)
        created = date.fromisoformat(lead["created_at"])

        segment = lead["segment"]
        cycle_days = {
            "SMB": random.randint(7, 30),
            "Mid-Market": random.randint(20, 75),
            "Enterprise": random.randint(60, 180),
        }[segment]
        close_date = created + timedelta(days=cycle_days)
        if close_date > END_DATE:
            close_date = END_DATE

        win_prob = {"SMB": 0.30, "Mid-Market": 0.27, "Enterprise": 0.22}[segment]
        if lead["lead_source"] == "Paid Search" and segment == "Enterprise":
            win_prob = 0.45

        if close_date >= END_DATE - timedelta(days=5):
            stage = random.choice(["Negotiation", "Proposal", "Discovery"])
        elif random.random() < win_prob:
            stage = "Closed Won"
        else:
            stage = "Closed Lost"

        plan = random.choice(list(PLANS.keys())) if segment != "SMB" else "SOC2 Starter"
        amount = PLANS[plan] * random.uniform(0.85, 1.3)

        rows.append({
            "opp_id": f"OPP-{opp_counter:06d}",
            "lead_id": lead["lead_id"],
            "account_id": account["account_id"],
            "rep_id": rep["rep_id"],
            "segment": segment,
            "lead_source": lead["lead_source"],
            "plan": plan,
            "stage": stage,
            "amount": round(amount, 2),
            "created_date": lead["created_at"],
            "close_date": close_date.isoformat(),
        })
        opp_counter += 1
    return rows



# ----------------------------------------------------------------------
# 5. SUBSCRIPTIONS (depends on: opportunities that closed won, accounts)
# ----------------------------------------------------------------------
def gen_subscriptions(opportunities):
    rows = []
    sub_counter = 1
    for opp in opportunities:
        if opp["stage"] != "Closed Won":
            continue
        start = date.fromisoformat(opp["close_date"])
        mrr = round(opp["amount"] / 12, 2)

        churn_roll = random.random()
        segment_churn = {"SMB": 0.22, "Mid-Market": 0.14, "Enterprise": 0.08}[opp["segment"]]
        is_churned = churn_roll < segment_churn
        end_date = ""
        status = "active"
        if is_churned:
            tenure_months = random.randint(3, 20)
            end = start + timedelta(days=tenure_months * 30)
            if end < END_DATE:
                end_date = end.isoformat()
                status = "churned"

        rows.append({
            "sub_id": f"SUB-{sub_counter:06d}",
            "account_id": opp["account_id"],
            "opp_id": opp["opp_id"],
            "plan": opp["plan"],
            "mrr": mrr,
            "start_date": start.isoformat(),
            "end_date": end_date,
            "status": status,
        })
        sub_counter += 1
    return rows



# ----------------------------------------------------------------------
# 6. REVENUE EVENTS (depends on: subscriptions)
# ----------------------------------------------------------------------
def gen_revenue_events(subscriptions):
    rows = []
    event_counter = 1
    for sub in subscriptions:
        start = date.fromisoformat(sub["start_date"])
        rows.append({
            "event_id": f"EVT-{event_counter:06d}",
            "account_id": sub["account_id"],
            "sub_id": sub["sub_id"],
            "type": "new",
            "amount": sub["mrr"],
            "event_date": start.isoformat(),
        })
        event_counter += 1

        if sub["status"] == "active" and random.random() < 0.18:
            expansion_date = start + timedelta(days=random.randint(60, 400))
            if expansion_date < END_DATE:
                rows.append({
                    "event_id": f"EVT-{event_counter:06d}",
                    "account_id": sub["account_id"],
                    "sub_id": sub["sub_id"],
                    "type": "expansion",
                    "amount": round(sub["mrr"] * random.uniform(0.1, 0.4), 2),
                    "event_date": expansion_date.isoformat(),
                })
                event_counter += 1

        if sub["status"] == "churned":
            rows.append({
                "event_id": f"EVT-{event_counter:06d}",
                "account_id": sub["account_id"],
                "sub_id": sub["sub_id"],
                "type": "churn",
                "amount": -sub["mrr"],
                "event_date": sub["end_date"],
            })
            event_counter += 1
    return rows




# ----------------------------------------------------------------------
# 7. CUSTOMER HEALTH SCORES (depends on: subscriptions, accounts)
#    One snapshot per active/at-risk subscription, taken ~90 days before
#    either their churn date or END_DATE (i.e. "current" snapshot).
# ----------------------------------------------------------------------
def gen_health_scores(subscriptions):
    rows = []
    hs_counter = 1
    for sub in subscriptions:
        start = date.fromisoformat(sub["start_date"])
        if sub["status"] == "churned":
            snapshot_date = date.fromisoformat(sub["end_date"]) - timedelta(days=90)
            usage_score = random.randint(10, 45)
            login_frequency = random.randint(0, 4)
            support_tickets_30d = random.randint(2, 9)
            days_to_renewal = random.randint(60, 120)
        else:
            snapshot_date = END_DATE - timedelta(days=random.randint(30, 300))
            usage_score = random.randint(40, 95)
            login_frequency = random.randint(3, 25)
            support_tickets_30d = random.randint(0, 4)
            days_to_renewal = random.randint(20, 300)

        if snapshot_date < start:
            snapshot_date = start + timedelta(days=15)

        health_score = round(
            (usage_score * 0.5)
            + (min(login_frequency, 20) / 20 * 30)
            + (max(0, 10 - support_tickets_30d) / 10 * 20),
            1,
        )
        risk_tier = "high_risk" if health_score < 45 else ("watch" if health_score < 65 else "healthy")

        rows.append({
            "health_id": f"HS-{hs_counter:06d}",
            "account_id": sub["account_id"],
            "sub_id": sub["sub_id"],
            "snapshot_date": snapshot_date.isoformat(),
            "usage_score": usage_score,
            "login_frequency_30d": login_frequency,
            "support_tickets_30d": support_tickets_30d,
            "days_to_renewal": days_to_renewal,
            "health_score": health_score,
            "risk_tier": risk_tier,
        })
        hs_counter += 1
    return rows




# ----------------------------------------------------------------------
# 8. RETENTION EXPERIMENTS (depends on: health_scores, subscriptions)
#    Only accounts flagged high_risk or watch are eligible -> randomized
#    into control / treatment. This is the core A/B test dataset.
# ----------------------------------------------------------------------
def gen_retention_experiments(health_scores, subscriptions):
    sub_by_id = {s["sub_id"]: s for s in subscriptions}
    eligible = [h for h in health_scores if h["risk_tier"] in ("high_risk", "watch")]

    rows = []
    exp_counter = 1
    for h in eligible:
        sub = sub_by_id[h["sub_id"]]
        variant = random.choice(["control", "treatment"])
        assigned_date = date.fromisoformat(h["snapshot_date"]) + timedelta(days=5)

        base_churn_prob = 0.55 if h["risk_tier"] == "high_risk" else 0.30
        if variant == "treatment":
            churn_prob = max(0.03, base_churn_prob - 0.09)
            treatment_type = random.choice(RETENTION_TREATMENTS)
        else:
            churn_prob = base_churn_prob
            treatment_type = "none"

        outcome = "churned" if random.random() < churn_prob else "renewed"
        renewal_mrr = 0.0 if outcome == "churned" else sub["mrr"]

        rows.append({
            "experiment_id": f"EXP-{exp_counter:05d}",
            "account_id": h["account_id"],
            "sub_id": h["sub_id"],
            "risk_tier_at_assignment": h["risk_tier"],
            "variant": variant,
            "treatment_type": treatment_type,
            "assigned_date": assigned_date.isoformat(),
            "pre_experiment_mrr": sub["mrr"],
            "outcome": outcome,
            "renewal_mrr": renewal_mrr,
        })
        exp_counter += 1
    return rows



# ----------------------------------------------------------------------
# WRITE CSVs
# ----------------------------------------------------------------------
def write_csv(rows, filename):
    if not rows:
        print(f"WARNING: no rows generated for {filename}")
        return
    path = OUT_DIR / filename
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows):>6} rows -> {path.relative_to(OUT_DIR.parent)}")


def main():
    print("Generating ComplyFlow synthetic GTM + retention dataset...\n")

    sales_reps = gen_sales_reps()
    write_csv(sales_reps, "sales_reps.csv")

    accounts = gen_accounts()
    write_csv(accounts, "accounts.csv")

    leads = gen_leads()
    write_csv(leads, "leads.csv")

    opportunities = gen_opportunities(leads, accounts, sales_reps)
    write_csv(opportunities, "opportunities.csv")

    subscriptions = gen_subscriptions(opportunities)
    write_csv(subscriptions, "subscriptions.csv")

    revenue_events = gen_revenue_events(subscriptions)
    write_csv(revenue_events, "revenue_events.csv")

    health_scores = gen_health_scores(subscriptions)
    write_csv(health_scores, "customer_health_scores.csv")

    retention_experiments = gen_retention_experiments(health_scores, subscriptions)
    write_csv(retention_experiments, "retention_experiments.csv")

    print("\nDone. All 8 CSVs written to /data with referential integrity preserved.")


if __name__ == "__main__":
    main()


