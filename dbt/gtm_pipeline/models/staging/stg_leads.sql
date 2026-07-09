with source as (

    select * from {{ source('raw', 'leads') }}

),

renamed as (

    select
        lead_id,
        segment,
        lead_source,
        status,
        created_at

    from source

)

select * from renamed