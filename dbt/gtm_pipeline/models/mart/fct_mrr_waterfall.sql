with revenue_events as (

    select * from {{ ref('stg_revenue_events') }}

),

monthly_events as (

    select
        date_trunc('month', event_date) as event_month,
        event_type,
        sum(amount) as total_amount

    from revenue_events

    group by date_trunc('month', event_date), event_type

),

pivoted as (

    select
        event_month,
        sum(case when event_type = 'new' then total_amount else 0 end) as new_mrr,
        sum(case when event_type = 'expansion' then total_amount else 0 end) as expansion_mrr,
        sum(case when event_type = 'churn' then total_amount else 0 end) as churned_mrr

    from monthly_events

    group by event_month

),

with_net_change as (

    select
        event_month,
        new_mrr,
        expansion_mrr,
        churned_mrr,
        (new_mrr + expansion_mrr + churned_mrr) as net_mrr_change

    from pivoted

)

select * from with_net_change
order by event_month