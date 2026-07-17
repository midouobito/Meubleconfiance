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
 * Maps a facebook_posts table row into a structured product object 
 * that fits your existing HTML templates perfectly.
 */
function mapPostToProduct(post) {
  // Use permanently archived media URLs if available, otherwise original URLs
  let images = [];
  if (post.stored_media && post.stored_media.length > 0) {
    images = post.stored_media.filter(img => img && img.trim() !== "");
  }

  if (images.length === 0 && post.media_urls && post.media_urls.length > 0) {
    images = post.media_urls.filter(img => img && img.trim() !== "");
  }

  // Fallback image if no media found
  if (images.length === 0) {
    images.push("https://picsum.photos/seed/fb-placeholder/900/700");
  }

  // 1. Try to extract price from post text (e.g. 185,000 دج or 185 000 DA)
  let price = 0;
  const priceRegex = /(\d+[\d\s,]*000)\s*(دج|DA)/i;
  const match = post.post_text ? post.post_text.match(priceRegex) : null;
  if (match) {
    price = parseInt(match[1].replace(/\s|,/g, ""));
  }

  // 2. Generate a name from the first line of the post text
  let name = "منتج مميز";
  if (post.post_text) {
    const lines = post.post_text.split('\n').map(l => l.trim()).filter(l => l.length > 0);
    if (lines.length > 0) {
      name = lines[0].substring(0, 45);
      if (lines[0].length > 45) name += "...";
    }
  }

  // 3. Match categories based on keyword presence
  let category = "ديكور وإكسسوارات";
  const textLower = (post.post_text || "").toLowerCase();
  if (textLower.includes("صالون") || textLower.includes("salon")) {
    category = "صالونات";
  } else if (textLower.includes("غرفة نوم") || textLower.includes("chambre")) {
    category = "غرف نوم";
  } else if (textLower.includes("طاولة") || textLower.includes("table")) {
    category = "طاولات وكراسي";
  } else if (textLower.includes("مطبخ") || textLower.includes("cuisine")) {
    category = "مطابخ";
  } else if (textLower.includes("مكتب") || textLower.includes("bureau")) {
    category = "مكاتب";
  }

  return {
    id: post.id, // UUID primary key
    name: name,
    category: category,
    price: price,
    oldPrice: null,
    material: "خشب صلب عالي الجودة", // Default placeholder
    dimensions: "حسب الطلب",
    colors: ["#5C4A3A", "#EDE7DA"],
    images: images,
    badge: post.likes_count > 0 ? `${post.likes_count} 👍` : null,
    description: post.post_text || "لا يوجد وصف لهذا المنشور.",
    originalUrl: post.post_url,
    publishedAt: post.published_at
  };
}
