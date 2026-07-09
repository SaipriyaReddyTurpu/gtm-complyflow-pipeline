with source as (

    select * from {{ source('raw', 'opportunities') }}

),

renamed as (

    select
        opp_id,
        lead_id,
        account_id,
        rep_id,
        segment,
        lead_source,
        plan,
        stage,
        amount,
        created_date,
        close_date

    from source

)

select * from renamed