with source as (

    select * from {{ source('raw', 'retention_experiments') }}

),

renamed as (

    select
        experiment_id,
        account_id,
        sub_id,
        risk_tier_at_assignment,
        variant,
        treatment_type,
        assigned_date,
        pre_experiment_mrr,
        outcome,
        renewal_mrr

    from source

)

select * from renamed