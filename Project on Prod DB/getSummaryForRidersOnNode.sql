select
    t.rider_id as "riderId",
    r.rider_name as "riderName",
    r.rider_profile_url as "riderProfileUrl",
    r.phone as "riderPhoneNumber",
    string_agg(distinct t.tour_type, ',') as "tourTypes",
    max(t.start_time) as "timestamp",
    max(t.end_time) as "endTime",
    count(distinct case
        when ((t.tour_type = 'FORWARD' and t2.is_drop_task) 
            or (t.tour_type = 'REVERSE' and t2.is_drop_task is false)) 
        then t.tour_id
    end) as "countOfTours",
    cast(
        round(avg(
            case 
            when t2.trip_rating is null 
            then 0 else t2.trip_rating 
            end)::numeric, 2) 
        as double precision
    ) as "rating",
    sum(t2.cod_amount) as "totalCodAmount",
    count(distinct case
        when ((t.tour_type = 'FORWARD' and t2.is_drop_task) 
            or (t.tour_type = 'REVERSE' and t2.is_drop_task is false)) 
        then t2.trip_id
    end) as "totalShipments",
    count(case 
        when t2.is_escalated is true 
        then 1 
    end) as "totalEscalations",
    count(case 
        when t.tour_type = 'FORWARD' 
            and t2.is_drop_task 
            and t2.payment_type = 'COD' 
        then 1 
    end) as "totalCodOrders",
    count(case
        when t2.status = 'ACCEPTED' 
            and ((t.tour_type = 'FORWARD' and t2.is_drop_task) 
                or (t.tour_type = 'REVERSE' and t2.is_drop_task is false)) 
        then 1
    end) as "totalTripsAccepted",
    count(case 
        when t2.is_fake_attempt is true 
            and t2.status in ('STARTED','ONGOING','ONHOLD','CANCELLED') 
        then 1 
    end) as "totalFakeRemarks",
    count(case
        when t2.status in ('STARTED', 'ONGOING','ONHOLD', 'ACCEPTED') 
            and ((t.tour_type = 'FORWARD' and t2.is_drop_task) 
                OR (t.tour_type = 'REVERSE' and t2.is_drop_task is false)) 
        then 1
    end) as "totalOngoing",
    count(case
        when ((t.tour_type = 'FORWARD' and t2.is_drop_task) 
                or (t.tour_type = 'REVERSE' and t2.is_drop_task is false)) 
            and t2.status in ('CANCELLED', 'LOST') 
        then 1
    end) as "totalFailedDelivered",
    count(case
        when t2.status = 'COMPLETED' 
            and ((t.tour_type = 'FORWARD' and t2.is_drop_task) 
                or (t.tour_type = 'REVERSE' and t2.is_drop_task is false)) 
        then 1
    end) as "totalDelivered",
    count(case 
        when t.tour_type = 'FORWARD' 
            and t2.is_drop_task 
            and t2.payment_type = 'PREPAID' 
            and t2.status = 'COMPLETED' 
        then 1 
    end) as "totalPrepaidDelivered",
    count(case 
        when t.tour_type = 'FORWARD' 
            and t2.is_drop_task 
            and t2.payment_type = 'PREPAID' 
            and t2.status = 'CANCELLED' 
        then 1 
    end) as "totalPrepaidFailedDelivered",
    count(case
        when t.tour_type = 'FORWARD' 
            and t2.is_drop_task 
            and t2.payment_type = 'COD' 
            and t2.status = 'COMPLETED' 
        then 1 
    end) as "totalCodDelivered",
    count(case 
        when t.tour_type = 'FORWARD' 
            and t2.is_drop_task 
            and t2.payment_type = 'COD' 
            and t2.status = 'CANCELLED' 
        then 1 
    end) as "totalCodFailedDelivered",
    max(t.last_activity_time) as "lastActivityTime"
from
    rider r
join 
    tour t on t.rider_id = r.rider_id and t.node_id = :nodeId
join 
    trip t2 on t2.tour_id = t.tour_id
where
    (:status is null or t.status in :status)
    and t.created_at::date = current_date
    and t2.status <> 'CLOSED'
group by 1,2,3,4