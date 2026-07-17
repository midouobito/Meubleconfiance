-- ============================================================
--  Facebook Posts Table – Run this once in your Supabase SQL
--  editor (Database > SQL Editor > New Query)
-- ============================================================

-- Enable UUID extension (already enabled on Supabase by default)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- -------------------------------------------------------
-- Main table
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.facebook_posts (
    id              UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    post_id         TEXT            NOT NULL,          -- Facebook's own post identifier
    page_name       TEXT            NOT NULL,          -- e.g. "CocaColaMorocco"
    post_text       TEXT,                              -- Full visible text of the post
    post_url        TEXT,                              -- Canonical link to the post
    published_at    TIMESTAMPTZ,                       -- When the post was published
    media_type      TEXT            CHECK (
                        media_type IN ('text', 'image', 'video', 'reel', 'link', 'unknown')
                    ),
    media_urls      TEXT[]          DEFAULT '{}',      -- Original FB media URLs (expire!)
    stored_media    TEXT[]          DEFAULT '{}',      -- Permanent URLs after upload to Supabase Storage
    likes_count     INTEGER         DEFAULT 0,
    shares_count    INTEGER         DEFAULT 0,
    comments_count  INTEGER         DEFAULT 0,
    scraped_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT facebook_posts_post_id_key UNIQUE (post_id)
);

-- -------------------------------------------------------
-- Indexes for common query patterns
-- -------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_fb_posts_page_name    ON public.facebook_posts (page_name);
CREATE INDEX IF NOT EXISTS idx_fb_posts_published_at ON public.facebook_posts (published_at DESC);
CREATE INDEX IF NOT EXISTS idx_fb_posts_scraped_at   ON public.facebook_posts (scraped_at DESC);
CREATE INDEX IF NOT EXISTS idx_fb_posts_media_type   ON public.facebook_posts (media_type);

-- -------------------------------------------------------
-- Auto-update `updated_at` trigger
-- -------------------------------------------------------
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_fb_posts_updated_at ON public.facebook_posts;
CREATE TRIGGER trg_fb_posts_updated_at
    BEFORE UPDATE ON public.facebook_posts
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- -------------------------------------------------------
-- Row Level Security (RLS) – service-role key bypasses this
-- -------------------------------------------------------
ALTER TABLE public.facebook_posts ENABLE ROW LEVEL SECURITY;

-- Allow the anon/authenticated roles to SELECT only
CREATE POLICY "Public read access" ON public.facebook_posts
    FOR SELECT TO anon, authenticated USING (true);

-- Only service_role (your backend) can INSERT / UPDATE / DELETE
CREATE POLICY "Service role full access" ON public.facebook_posts
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- -------------------------------------------------------
-- Supabase Storage bucket for permanent media archival
-- Run in a separate query after creating the table:
-- -------------------------------------------------------
-- INSERT INTO storage.buckets (id, name, public)
-- VALUES ('facebook-media', 'facebook-media', true)
-- ON CONFLICT (id) DO NOTHING;
