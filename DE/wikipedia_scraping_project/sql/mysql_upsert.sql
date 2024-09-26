INSERT INTO university (country, `name`, founded, `type`, enrollment, link)
VALUES (%s, %s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE
    founded=VALUES(founded),
    type = VALUES(`type`),
    enrollment = VALUES(enrollment),
    link = VALUES(link)