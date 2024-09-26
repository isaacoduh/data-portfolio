INSERT INTO university (country, name, founded, type, enrollment, link)
VALUES (%s, %s, %s, %s, %s, %s)
ON CONFLICT (country, name) DO UPDATE
SET
    founded=EXCLUDED.founded,
    type = EXCLUDED.type,
    enrollment = EXCLUDED.enrollment,
    link = EXCLUDED.link;