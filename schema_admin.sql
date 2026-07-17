-- ============================================================
-- schema_admin.sql
-- Exécutez ce script dans l'éditeur SQL de Supabase
-- (Database > SQL Editor > New Query)
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- -------------------------------------------------------
-- Table des Produits
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    fb_post_id TEXT UNIQUE, -- Pour éviter les doublons depuis le scraper
    name TEXT NOT NULL,
    description TEXT,
    price NUMERIC DEFAULT 0,
    old_price NUMERIC,
    category TEXT DEFAULT 'Autre',
    material TEXT,
    dimensions TEXT,
    colors TEXT[],
    images TEXT[] DEFAULT '{}',
    badge TEXT,
    original_url TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- -------------------------------------------------------
-- Table des Commandes (COD)
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID REFERENCES public.products(id) ON DELETE SET NULL,
    product_name TEXT,
    price NUMERIC,
    customer_name TEXT NOT NULL,
    customer_phone TEXT NOT NULL,
    customer_wilaya TEXT NOT NULL,
    customer_address TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'shipped', 'delivered', 'cancelled')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- -------------------------------------------------------
-- Triggers pour updated_at
-- -------------------------------------------------------
CREATE OR REPLACE FUNCTION public.update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_timestamp_products ON public.products;
CREATE TRIGGER set_timestamp_products
BEFORE UPDATE ON public.products
FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();

DROP TRIGGER IF EXISTS set_timestamp_orders ON public.orders;
CREATE TRIGGER set_timestamp_orders
BEFORE UPDATE ON public.orders
FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();

-- -------------------------------------------------------
-- Migration des données existantes (de facebook_posts vers products)
-- -------------------------------------------------------
INSERT INTO public.products (fb_post_id, name, description, price, category, images, created_at, original_url, badge)
SELECT 
    post_id, 
    -- Nom basé sur la première ligne
    COALESCE(NULLIF(TRIM(split_part(post_text, E'\n', 1)), ''), 'Produit Facebook'), 
    post_text,
    -- Tentative d'extraction de prix
    COALESCE((SUBSTRING(REPLACE(post_text, ' ', ''), '([0-9]+)000(?:دج|DA|da)'))::numeric * 1000, 0),
    -- Catégorie basique
    CASE 
        WHEN post_text ILIKE '%صالون%' OR post_text ILIKE '%salon%' THEN 'صالونات'
        WHEN post_text ILIKE '%غرفة نوم%' OR post_text ILIKE '%chambre%' THEN 'غرف نوم'
        WHEN post_text ILIKE '%طاولة%' OR post_text ILIKE '%table%' THEN 'طاولات وكراسي'
        WHEN post_text ILIKE '%مطبخ%' OR post_text ILIKE '%cuisine%' THEN 'مطابخ'
        WHEN post_text ILIKE '%مكتب%' OR post_text ILIKE '%bureau%' THEN 'مكاتب'
        ELSE 'ديكور وإكسسوارات'
    END,
    COALESCE(NULLIF(stored_media, '{}'), media_urls, '{}'),
    published_at,
    post_url,
    CASE WHEN likes_count > 0 THEN likes_count || ' 👍' ELSE NULL END
FROM public.facebook_posts
ON CONFLICT (fb_post_id) DO NOTHING;

-- -------------------------------------------------------
-- Sécurité (Row Level Security - RLS)
-- -------------------------------------------------------
ALTER TABLE public.products ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.orders ENABLE ROW LEVEL SECURITY;

-- Produits : Lecture publique, écriture réservée aux utilisateurs connectés (admin)
CREATE POLICY "Lecture publique des produits" ON public.products
    FOR SELECT TO anon, authenticated USING (is_active = true);

CREATE POLICY "Gestion admin des produits" ON public.products
    FOR ALL TO authenticated USING (true) WITH CHECK (true);

-- Commandes : Insertion publique, lecture/gestion réservée aux admins
CREATE POLICY "Insertion publique des commandes" ON public.orders
    FOR INSERT TO anon, authenticated WITH CHECK (true);

CREATE POLICY "Gestion admin des commandes" ON public.orders
    FOR ALL TO authenticated USING (true) WITH CHECK (true);
