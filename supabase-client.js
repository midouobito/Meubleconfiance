/**
 * supabase-client.js – Supabase client initialization & data mapping
 * 
 * Loaded in frontend pages to fetch Facebook posts dynamically.
 * Make sure to load this script AFTER loading the Supabase CDN script:
 * <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
 */

// ── Supabase Credentials ─────────────────────────────────────────────────────
// Replace with your rotated public anon key. NEVER use your service_role key here.
const SUPABASE_URL = "https://oaqiawqxxxaqzcalmxsh.supabase.co";
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9hcWlhd3F4eHhhcXpjYWxteHNoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQyODQ2MzEsImV4cCI6MjA5OTg2MDYzMX0.SwCu3-7ITl3b1qHPCvE1DMk6NkY3B4vMSSGa4fGug1U";

const supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

/**
 * Maps a products table row into a structured product object 
 * that fits your existing HTML templates perfectly.
 */
function mapRowToProduct(row) {
  let images = row.images && row.images.length > 0 ? row.images : ["https://picsum.photos/seed/fb-placeholder/900/700"];
  
  return {
    id: row.id, // UUID primary key
    name: row.name || "Produit sans nom",
    category: row.category || "Autre",
    price: row.price || 0,
    oldPrice: row.old_price || null,
    material: row.material || "خشب صلب عالي الجودة", // Default placeholder
    dimensions: row.dimensions || "حسب الطلب",
    colors: row.colors || ["#5C4A3A", "#EDE7DA"],
    images: images,
    badge: row.badge,
    description: row.description || "لا يوجد وصف.",
    originalUrl: row.original_url,
    publishedAt: row.created_at
  };
}
