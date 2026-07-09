with leads as (

    select * from {{ ref('stg_leads') }}

),

quality_checks as (

    select
        count(*) as total_leads,
        count(case when lead_source is null or lead_source = '' then 1 end) as missing_lead_source_count,
        count(case when segment is null or segment = '' then 1 end) as missing_segment_count,
        count(case when created_at is null then 1 end) as missing_created_at_count

    from leads

),

summary as (

    select
        total_leads,
        missing_lead_source_count,
        missing_segment_count,
        missing_created_at_count,
        (missing_lead_source_count + missing_segment_count + missing_created_at_count) as total_issues,
        round(
            (missing_lead_source_count + missing_segment_count + missing_created_at_count) * 100.0
            / nullif(total_leads * 3, 0),
            2
        ) as issue_rate_pct,
        round(
            100.0 - (
                (missing_lead_source_count + missing_segment_count + missing_created_at_count) * 100.0
                / nullif(total_leads * 3, 0)
            ),
            2
        ) as data_quality_score_pct

    from quality_checks

)

select * from summary