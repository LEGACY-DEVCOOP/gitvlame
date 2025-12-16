-- Enable UUID extension (if using Postgres < 13 or need uuid_generate_v4)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. User Table
CREATE TABLE "User" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "github_id" TEXT NOT NULL,
    "username" TEXT NOT NULL,
    "avatar_url" TEXT,
    "access_token" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "User_pkey" PRIMARY KEY ("id")
);

-- Unique Index for GitHub ID
CREATE UNIQUE INDEX "User_github_id_key" ON "User"("github_id");

-- 2. Judgment Table
CREATE TABLE "Judgment" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "user_id" UUID NOT NULL,
    "repo_owner" TEXT NOT NULL,
    "repo_name" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "description" TEXT,
    "file_path" TEXT,
    "period_days" INTEGER NOT NULL DEFAULT 7,
    "status" TEXT NOT NULL,
    "case_number" TEXT NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Judgment_pkey" PRIMARY KEY ("id")
);

-- Unique Index for Case Number
CREATE UNIQUE INDEX "Judgment_case_number_key" ON "Judgment"("case_number");

-- 3. Suspect Table
CREATE TABLE "Suspect" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "judgment_id" UUID NOT NULL,
    "username" TEXT NOT NULL,
    "avatar_url" TEXT,
    "responsibility" INTEGER NOT NULL,
    "reason" TEXT,
    "commit_count" INTEGER,
    "last_commit_msg" TEXT,
    "last_commit_date" TIMESTAMP(3),

    CONSTRAINT "Suspect_pkey" PRIMARY KEY ("id")
);

-- 4. Blame Table
CREATE TABLE "Blame" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "judgment_id" UUID NOT NULL,
    "target_username" TEXT NOT NULL,
    "target_avatar" TEXT,
    "responsibility" INTEGER NOT NULL,
    "reason" TEXT,
    "message" TEXT,
    "intensity" TEXT NOT NULL DEFAULT 'medium',
    "image_url" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Blame_pkey" PRIMARY KEY ("id")
);

-- Unique Index for Blame (One-to-One with Judgment)
CREATE UNIQUE INDEX "Blame_judgment_id_key" ON "Blame"("judgment_id");

-- Add Relationships (Foreign Keys)
ALTER TABLE "Judgment" ADD CONSTRAINT "Judgment_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE "Suspect" ADD CONSTRAINT "Suspect_judgment_id_fkey" FOREIGN KEY ("judgment_id") REFERENCES "Judgment"("id") ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE "Blame" ADD CONSTRAINT "Blame_judgment_id_fkey" FOREIGN KEY ("judgment_id") REFERENCES "Judgment"("id") ON DELETE CASCADE ON UPDATE CASCADE;
