with source as (

    select * from {{ source('raw', 'revenue_events') }}

),

renamed as (

    select
        event_id,
        account_id,
        sub_id,
        type as event_type,
        amount,
        event_date

    from source

)

select * from renamed