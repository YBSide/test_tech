-- Прежде всего хочется уточнить, что задания по SQL были выполнены, используя синтаксис MS SQL,
-- так как по синтаксису создания таблицы в условии подходил именно данный способ.
-- Задания тестировались на сайте https://sqliteonline.com/, так как он позволяет выбрать синтаксис для нескольких БД (в том числе и для MS SQL)
-- Также я, если требуется, использую сортировку по началу сессии, а не по id сессии, потому что данных, которые используются в условии,
-- есть случай, когда для одного и того же игрока, есть сессия с id большим, чем id другой сессии, но при этом эта сессия по времени начинается раньше
-- (пример такой сессии из условия, где session_id = 13 для player_id = 1)

-- Задание 1

-- Так как в рамках данного задания нужно получить три набора данных, но конкретные выходные поля в условии указаны только
-- для третьего набора, поэтому для первых двух наборов я привожу описания выходных полей

-- 1) - Продолжительность всех сессий для игрока в рамках дня в минутах.

-- Для данного запроса выходные поля следующие:
--     player_id - id игрока, согласно изначальной таблице
--     day - день (дата), так как по условию задания нужно получить продолжительность сессий игрока в рамках дня
--     session_duration - продолжительность всех сессий в минутах для игрока в рамках дня (поле day)

-- Решение

-- В CTE table_with_surrounding_time добавляю поля: prev_end_time, next_start_time, чтобы получать время окончания прошлой и время начала следующей сессий
WITH table_with_surrounding_time AS (
  SELECT 
    player_id,
    country,
    start_time,
    end_time,
    LAG(end_time) OVER (PARTITION BY player_id ORDER BY start_time) AS prev_end_time,
    LEAD(start_time) OVER (PARTITION BY player_id ORDER BY start_time) AS next_start_time
  FROM game_sessions
),

-- В CTE table_with_merged_time поле merged_interval_start_time заполняется, если оно является началом сессии, 
-- которую уже нельзя объединить с другой сессией из-за разницы >= 5 минут.
-- Аналогичным образом заполняется поле merged_interval_end_time, если оно является окончанием сессии, которую тоже нельзя объеденить с другой
table_with_merged_time as (
  SELECT
    player_id,
    country,
    start_time,
    end_time,
    prev_end_time,
    next_start_time,
    CASE 
      WHEN ABS(DATEDIFF(minute, start_time, prev_end_time)) < 5 THEN NULL
      ELSE start_time
    END AS merged_interval_start_time,
    CASE 
      WHEN ABS(DATEDIFF(minute, end_time, next_start_time)) < 5 THEN NULL
      ELSE end_time
    END AS merged_interval_end_time
  FROM table_with_surrounding_time),
  
-- Две последующие CTE: table_with_nulls, table_without_nulls нужны, чтобы получить уже список сессий для игроков с учетом объединенных сессий, между которыми разница меньше 5 минут
table_with_nulls as (
  SELECT 
    player_id, 
    merged_interval_start_time,
    country,
    CASE 
      WHEN merged_interval_end_time IS NULL 
        THEN LEAD(merged_interval_end_time) OVER (PARTITION BY player_id ORDER BY start_time)
      ELSE  merged_interval_end_time
    END AS merged_interval_end_time_final
  from table_with_merged_time
  where (merged_interval_start_time IS NOT NULL) or (merged_interval_end_time IS NOT NULL)),
  
table_without_nulls as (
  select 
    player_id, 
    country,
    merged_interval_start_time, 
    merged_interval_end_time_final as merged_interval_end_time
  FROM table_with_nulls
  where (merged_interval_start_time IS NOT NULL) and (merged_interval_end_time_final IS NOT NULL)
)
  

-- Получаем продолжительность всех сессий для игрока в рамках дня в минутах
select 
  player_id, 
  CONVERT(date, merged_interval_start_time) as day, 
  SUM(ABS(DATEDIFF(minute, merged_interval_end_time, merged_interval_start_time))) as session_duration
FROM table_without_nulls
GROUP BY player_id, CONVERT(date, merged_interval_start_time);


-- 2) Продолжительность самой короткой и длинной сессии для игрока в рамках дня в минутах. 

-- Решение

-- Для выполнения этого задания используются прошлые CTE
-- Поля: 
--     player_id - id игрока, согласно изначальной таблице
--     day - день (дата), так как по условию задания нужно получить продолжительность сессий игрока в рамках дня
--     shortest_session - продолжительность самой короткой сессии для игрока в рамках дня
--     longest_session - продолжительность самой длинной сессии для игрока в рамках дня
SELECT player_id, day, MIN(num_of_minutes) as shortest_session, MAX(num_of_minutes) as longest_session
FROM
(SELECT
  player_id, 
  CONVERT(date, merged_interval_start_time) as day, 
  merged_interval_start_time as interval_start_time,
  merged_interval_end_time as interval_end_time,
  SUM(ABS(DATEDIFF(minute, merged_interval_end_time, merged_interval_start_time))) as num_of_minutes
FROM table_without_nulls
GROUP BY player_id, CONVERT(date, merged_interval_start_time), merged_interval_start_time, merged_interval_end_time) t
GROUP by player_id, day;


-- 3) - Также необходимо вывести ранг игрока в рамках страны. Игроки с самой большой продолжительностью всех сессий будут иметь наивысший ранг.
-- Здесь пример выходных данных был дан в условии, поэтому вывожу именно те же поля. Здесь также были использованы прошлые CTE

-- Решение

SELECT
  player_id, 
  country, 
  SUM(num_of_minutes) as duration_of_all_sessions,
  MIN(num_of_minutes) as shortest_session,
  MAX(num_of_minutes) as longest_session,
  ROW_NUMBER() OVER (PARTITION BY country ORDER BY SUM(num_of_minutes) desc) as rank_of_the_user
FROM
(SELECT
  player_id, 
  country,
  CONVERT(date, merged_interval_start_time) as day, 
  merged_interval_start_time as interval_start_time,
  merged_interval_end_time as interval_end_time,
  SUM(ABS(DATEDIFF(minute, merged_interval_end_time, merged_interval_start_time))) as num_of_minutes
FROM table_without_nulls
GROUP BY player_id, country, CONVERT(date, merged_interval_start_time), merged_interval_start_time, merged_interval_end_time) t
GROUP by player_id, country;