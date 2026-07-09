with source as (

    select * from {{ source('raw', 'customer_health_scores') }}

),

renamed as (

    select
        health_id,
        account_id,
        sub_id,
        snapshot_date,
        usage_score,
        login_frequency_30d,
        support_tickets_30d,
        days_to_renewal,
        health_score,
        risk_tier

    from source

)

select * from renamed