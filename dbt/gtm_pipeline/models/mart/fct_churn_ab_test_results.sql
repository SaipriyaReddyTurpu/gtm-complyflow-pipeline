with experiments as (

    select * from {{ ref('stg_retention_experiments') }}

),

results_by_variant as (

    select
        variant,
        risk_tier_at_assignment,
        count(*) as total_accounts,
        count(case when outcome = 'churned' then 1 end) as churned_count,
        count(case when outcome = 'renewed' then 1 end) as renewed_count,
        round(
            count(case when outcome = 'churned' then 1 end) * 100.0 / nullif(count(*), 0),
            2
        ) as churn_rate_pct,
        sum(pre_experiment_mrr) as total_pre_experiment_mrr,
        sum(renewal_mrr) as total_retained_mrr

    from experiments

    group by variant, risk_tier_at_assignment

)

select * from results_by_variant
order by risk_tier_at_assignment, variant