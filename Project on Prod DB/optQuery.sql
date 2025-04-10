WITH filtered_tours AS (
    SELECT 
        t.rider_id,
        t.tour_id,
        t.tour_type,
        t.start_time,
        t.end_time,
        t.last_activity_time
    FROM 
        tour t
    WHERE 
        t.created_at::date = current_date
        AND t.node_id = :nodeId
        AND (:status IS NULL OR t.status IN :status)
),
trip_data AS (
    SELECT 
        t2.tour_id,
        t2.trip_id,
        t2.is_drop_task,
        t2.trip_rating,
        t2.cod_amount,
        t2.is_escalated,
        t2.payment_type,
        t2.status,
        t2.is_fake_attempt
    FROM 
        trip t2
    WHERE 
        t2.status <> 'CLOSED'
)
SELECT
    ft.rider_id AS "riderId",
    r.rider_name AS "riderName",
    r.rider_profile_url AS "riderProfileUrl",
    r.phone AS "riderPhoneNumber",
    string_agg(DISTINCT ft.tour_type, ',') AS "tourTypes",
    MAX(ft.start_time) AS "timestamp",
    MAX(ft.end_time) AS "endTime",
    COUNT(DISTINCT 
        CASE
            WHEN ((ft.tour_type = 'FORWARD' AND td.is_drop_task) 
                OR (ft.tour_type = 'REVERSE' AND td.is_drop_task IS FALSE)) 
            THEN ft.tour_id
        END) AS "countOfTours",
    CAST(
        ROUND(AVG(
            CASE 
            WHEN td.trip_rating IS NULL 
            THEN 0 ELSE td.trip_rating 
            END)::numeric, 2) 
        AS double precision
    ) AS "rating",
    SUM(td.cod_amount) AS "totalCodAmount",
    COUNT(DISTINCT 
        CASE
            WHEN ((ft.tour_type = 'FORWARD' AND td.is_drop_task) 
                OR (ft.tour_type = 'REVERSE' AND td.is_drop_task IS FALSE)) 
            THEN td.trip_id
        END) AS "totalShipments",
    COUNT(CASE 
        WHEN td.is_escalated IS TRUE 
        THEN 1 
    END) AS "totalEscalations",
    COUNT(CASE 
        WHEN td.payment_type = 'COD'
            AND ft.tour_type = 'FORWARD' 
            AND td.is_drop_task
        THEN 1 
    END) AS "totalCodOrders",
    COUNT(CASE
        WHEN td.status = 'ACCEPTED' 
            AND ((ft.tour_type = 'FORWARD' AND td.is_drop_task) 
                OR (ft.tour_type = 'REVERSE' AND td.is_drop_task IS FALSE)) 
        THEN 1
    END) AS "totalTripsAccepted",
    COUNT(CASE 
        WHEN td.is_fake_attempt IS TRUE 
            AND td.status IN ('STARTED','ONGOING','ONHOLD','CANCELLED') 
        THEN 1 
    END) AS "totalFakeRemarks",
    COUNT(CASE
        WHEN td.status IN ('STARTED', 'ONGOING','ONHOLD', 'ACCEPTED') 
            AND ((ft.tour_type = 'FORWARD' AND td.is_drop_task) 
                OR (ft.tour_type = 'REVERSE' AND td.is_drop_task IS FALSE)) 
        THEN 1
    END) AS "totalOngoing",
    COUNT(CASE
        WHEN td.status IN ('CANCELLED', 'LOST') 
            AND ((ft.tour_type = 'FORWARD' AND td.is_drop_task) 
                OR (ft.tour_type = 'REVERSE' AND td.is_drop_task IS FALSE)) 
        THEN 1
    END) AS "totalFailedDelivered",
    COUNT(CASE
        WHEN td.status = 'COMPLETED' 
            AND ((ft.tour_type = 'FORWARD' AND td.is_drop_task) 
                OR (ft.tour_type = 'REVERSE' AND td.is_drop_task IS FALSE)) 
        THEN 1
    END) AS "totalDelivered",
    COUNT(CASE 
        WHEN td.payment_type = 'PREPAID' 
            AND td.status = 'COMPLETED' 
            AND ft.tour_type = 'FORWARD' 
            AND td.is_drop_task 
        THEN 1 
    END) AS "totalPrepaidDelivered",
    COUNT(CASE 
        WHEN td.status = 'CANCELLED'
            AND td.payment_type = 'PREPAID' 
            AND ft.tour_type = 'FORWARD' 
            AND td.is_drop_task  
        THEN 1 
    END) AS "totalPrepaidFailedDelivered",
    COUNT(CASE 
        WHEN td.payment_type = 'COD' 
            AND td.status = 'COMPLETED' 
            AND ft.tour_type = 'FORWARD' 
            AND td.is_drop_task 
        THEN 1 
    END) AS "totalCodDelivered",
    COUNT(CASE 
        WHEN td.status = 'CANCELLED'
            AND td.payment_type = 'COD'  
            AND ft.tour_type = 'FORWARD' 
            AND td.is_drop_task 
        THEN 1 
    END) AS "totalCodFailedDelivered",
    MAX(ft.last_activity_time) AS "lastActivityTime"
FROM
    filtered_tours ft
JOIN 
    rider r ON ft.rider_id = r.rider_id
JOIN 
    trip_data td ON td.tour_id = ft.tour_id
GROUP BY 
    ft.rider_id, r.rider_name, r.rider_profile_url, r.phone;