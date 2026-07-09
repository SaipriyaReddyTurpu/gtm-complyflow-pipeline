with source as (

    select * from {{ source('raw', 'sales_reps') }}

),

renamed as (

    select
        rep_id,
        name as rep_name,
        region,
        quota_quarterly,
        hire_date

    from source

)

select * from renamed