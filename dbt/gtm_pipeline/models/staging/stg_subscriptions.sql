with source as (

    select * from {{ source('raw', 'subscriptions') }}

),

renamed as (

    select
        sub_id,
        account_id,
        opp_id,
        plan,
        mrr,
        start_date,
        end_date,
        status

    from source

)

select * from renamed