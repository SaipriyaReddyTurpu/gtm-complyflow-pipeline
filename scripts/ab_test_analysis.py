"""
ComplyFlow Retention A/B Test — Statistical Analysis
------------------------------------------------------
Pulls the churn A/B test results from Snowflake (built by dbt) and runs:
  1. A power analysis (was our sample size big enough?)
  2. A two-proportion z-test (is the churn rate difference statistically significant?)
  3. A confidence interval for the true difference in churn rates
"""

import os
import snowflake.connector
from dotenv import load_dotenv

load_dotenv()

SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT")
SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER")
SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD")
SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE")
SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE")


def get_connection():
    return snowflake.connector.connect(
        account=SNOWFLAKE_ACCOUNT,
        user=SNOWFLAKE_USER,
        password=SNOWFLAKE_PASSWORD,
        warehouse=SNOWFLAKE_WAREHOUSE,
        database=SNOWFLAKE_DATABASE,
        schema="MART",
    )

import pandas as pd


def fetch_ab_test_data():
    conn = get_connection()
    query = """
        SELECT
            variant,
            risk_tier_at_assignment,
            total_accounts,
            churned_count,
            renewed_count,
            churn_rate_pct,
            total_pre_experiment_mrr,
            total_retained_mrr
        FROM fct_churn_ab_test_results
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df


from statsmodels.stats.proportion import proportions_ztest, proportion_confint


def run_two_proportion_ztest(churned_a, total_a, churned_b, total_b, label_a="control", label_b="treatment"):
    count = [churned_a, churned_b]
    nobs = [total_a, total_b]

    z_stat, p_value = proportions_ztest(count, nobs)

    rate_a = churned_a / total_a
    rate_b = churned_b / total_b
    diff = rate_a - rate_b

    ci_a_low, ci_a_high = proportion_confint(churned_a, total_a, alpha=0.05, method='wilson')
    ci_b_low, ci_b_high = proportion_confint(churned_b, total_b, alpha=0.05, method='wilson')

    print(f"\n--- {label_a} vs {label_b} ---")
    print(f"{label_a} churn rate: {rate_a:.2%}  (95% CI: {ci_a_low:.2%} - {ci_a_high:.2%})")
    print(f"{label_b} churn rate: {rate_b:.2%}  (95% CI: {ci_b_low:.2%} - {ci_b_high:.2%})")
    print(f"Absolute difference: {diff:.2%}")
    print(f"z-statistic: {z_stat:.3f}")
    print(f"p-value: {p_value:.4f}")

    if p_value < 0.05:
        print("Result: statistically significant at the 95% confidence level.")
    else:
        print("Result: NOT statistically significant at the 95% confidence level.")



from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize


def run_power_analysis(rate_control, rate_treatment, alpha=0.05, power=0.80):
    effect_size = proportion_effectsize(rate_control, rate_treatment)

    analysis = NormalIndPower()
    required_n = analysis.solve_power(
        effect_size=abs(effect_size),
        alpha=alpha,
        power=power,
        ratio=1.0,
    )

    print(f"\nAssumed control rate: {rate_control:.2%}, treatment rate: {rate_treatment:.2%}")
    print(f"Effect size (Cohen's h): {effect_size:.3f}")
    print(f"Required sample size per group (80% power, alpha=0.05): {required_n:.0f}")


if __name__ == "__main__":
    data = fetch_ab_test_data()
    print("Raw A/B test results from Snowflake:\n")
    print(data)

    print("\n" + "=" * 60)
    print("STATISTICAL SIGNIFICANCE TESTS")
    print("=" * 60)

    for tier in data["RISK_TIER_AT_ASSIGNMENT"].unique():
        tier_data = data[data["RISK_TIER_AT_ASSIGNMENT"] == tier]

        control_row = tier_data[tier_data["VARIANT"] == "control"].iloc[0]
        treatment_row = tier_data[tier_data["VARIANT"] == "treatment"].iloc[0]

        print(f"\n### Risk tier: {tier} ###")
        run_two_proportion_ztest(
            churned_a=control_row["CHURNED_COUNT"],
            total_a=control_row["TOTAL_ACCOUNTS"],
            churned_b=treatment_row["CHURNED_COUNT"],
            total_b=treatment_row["TOTAL_ACCOUNTS"],
        )

    print("\n### Overall (both risk tiers combined) ###")
    overall = data.groupby("VARIANT")[["CHURNED_COUNT", "TOTAL_ACCOUNTS"]].sum()
    run_two_proportion_ztest(
        churned_a=overall.loc["control", "CHURNED_COUNT"],
        total_a=overall.loc["control", "TOTAL_ACCOUNTS"],
        churned_b=overall.loc["treatment", "CHURNED_COUNT"],
        total_b=overall.loc["treatment", "TOTAL_ACCOUNTS"],
    )
    print("\n" + "=" * 60)
    print("POWER ANALYSIS — was the high_risk sample big enough?")
    print("=" * 60)

    hr_control = data[(data["RISK_TIER_AT_ASSIGNMENT"] == "high_risk") & (data["VARIANT"] == "control")].iloc[0]
    hr_treatment = data[(data["RISK_TIER_AT_ASSIGNMENT"] == "high_risk") & (data["VARIANT"] == "treatment")].iloc[0]

    observed_control_rate = hr_control["CHURNED_COUNT"] / hr_control["TOTAL_ACCOUNTS"]
    observed_treatment_rate = hr_treatment["CHURNED_COUNT"] / hr_treatment["TOTAL_ACCOUNTS"]

    run_power_analysis(observed_control_rate, observed_treatment_rate)

    print(f"\nActual sample sizes: control={hr_control['TOTAL_ACCOUNTS']}, treatment={hr_treatment['TOTAL_ACCOUNTS']}")
