with leads as (

    select * from {{ ref('stg_leads') }}

),

funnel_counts as (

    select
        segment,
        count(*) as total_leads,
        count(case when status in ('MQL', 'SQL', 'Opportunity') then 1 end) as mql_count,
        count(case when status in ('SQL', 'Opportunity') then 1 end) as sql_count,
        count(case when status = 'Opportunity' then 1 end) as opportunity_count

    from leads

    group by segment

)

select * from funnel_counts