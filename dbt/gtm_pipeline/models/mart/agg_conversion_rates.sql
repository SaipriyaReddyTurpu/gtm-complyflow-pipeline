with leads as (

    select * from {{ ref('stg_leads') }}

),

by_segment_source as (

    select
        segment,
        lead_source,
        count(*) as total_leads,
        count(case when status in ('MQL', 'SQL', 'Opportunity') then 1 end) as mql_count,
        count(case when status in ('SQL', 'Opportunity') then 1 end) as sql_count,
        count(case when status = 'Opportunity' then 1 end) as opportunity_count

    from leads

    group by segment, lead_source

),

conversion_rates as (

    select
        segment,
        lead_source,
        total_leads,
        mql_count,
        sql_count,
        opportunity_count,
        round(mql_count * 100.0 / nullif(total_leads, 0), 2) as lead_to_mql_pct,
        round(sql_count * 100.0 / nullif(mql_count, 0), 2) as mql_to_sql_pct,
        round(opportunity_count * 100.0 / nullif(sql_count, 0), 2) as sql_to_opp_pct

    from by_segment_source

)

select * from conversion_rates