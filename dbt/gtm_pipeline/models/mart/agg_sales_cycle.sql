with opportunities as (

    select * from {{ ref('stg_opportunities') }}

),

closed_deals as (

    select
        segment,
        stage,
        datediff('day', created_date, close_date) as sales_cycle_days

    from opportunities

    where stage in ('Closed Won', 'Closed Lost')

),

cycle_by_segment as (

    select
        segment,
        count(*) as total_closed_deals,
        round(avg(sales_cycle_days), 1) as avg_sales_cycle_days,
        min(sales_cycle_days) as min_sales_cycle_days,
        max(sales_cycle_days) as max_sales_cycle_days

    from closed_deals

    group by segment

)

select * from cycle_by_segment