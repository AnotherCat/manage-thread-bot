-- upgrade --
CREATE TABLE IF NOT EXISTS "guilds" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY
);
CREATE TABLE IF NOT EXISTS "threads" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "keep_alive" BOOL NOT NULL  DEFAULT False,
    "waiting_on_poll" BOOL NOT NULL  DEFAULT False,
    "guild_id" BIGINT NOT NULL REFERENCES "guilds" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(20) NOT NULL,
    "content" JSONB NOT NULL
);
