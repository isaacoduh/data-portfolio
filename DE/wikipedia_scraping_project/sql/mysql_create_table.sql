CREATE TABLE university (
    id BIGINT AUTO_INCREMENT NOT NULL,
    country VARCHAR(255) NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    founded INT NOT NULL,
    `type` VARCHAR(255) NOT NULL,
    enrollment BIGINT NOT NULL,
    link VARCHAR(255) NOT NULL,

    UNIQUE KEY unique_combination (`country`, `name`),
    PRIMARY KEY (id)
)