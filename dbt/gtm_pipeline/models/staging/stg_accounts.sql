with source as (

    select * from {{ source('raw', 'accounts') }}

),

renamed as (

    select
        account_id,
        company_name,
        segment,
        industry,
        region,
        arr,
        signup_date

    from source

)

select * from renamed