MERGE INTO university target
USING #staging source
ON (source.university = target.name AND source.Country = target.country)
WHEN MATCHED THEN UPDATE
SET
    target.founded = source.Founded,
    target.type = source.Type,
    target.enrollment = source.Enrollment,
    target.link = source.Link
WHEN NOT MATCHED THEN
INSERT (country, name, founded, type, enrollment, link)
VALUES (source.Country, source.University, source.Founded, source.Type, source.Enrollment, source.Link);