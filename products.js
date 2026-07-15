// بيانات المنتجات — بيانات تجريبية، استبدلها بمنتجاتك الحقيقية وصورك الخاصة
const PRODUCTS = [
  {
    id: 1,
    name: "طقم صالون رويال ٧ مقاعد",
    category: "صالونات",
    price: 185000,
    oldPrice: 210000,
    material: "خشب زان + قماش مخملي",
    dimensions: "٣٢٠ × ٩٠ × ٨٥ سم",
    colors: ["#5C4A3A", "#8C6C2C", "#2E2A24"],
    images: [
      "https://picsum.photos/seed/salon-royal-1/900/700",
      "https://picsum.photos/seed/salon-royal-2/900/700",
      "https://picsum.photos/seed/salon-royal-3/900/700"
    ],
    badge: "الأكثر مبيعاً",
    description: "طقم صالون فخم بتصميم كلاسيكي معاصر، هيكل من خشب الزان الصلب وحشوة إسفنجية عالية الكثافة تضمن راحة تدوم طويلاً. تنجيد مخملي متين سهل التنظيف، مناسب للصالونات الواسعة والمتوسطة."
  },
  {
    id: 2,
    name: "طقم غرفة نوم كلاسيك بريستيج",
    category: "غرف نوم",
    price: 240000,
    material: "خشب زان + MDF مطلي",
    dimensions: "سرير ١٦٠×٢٠٠ + دولاب ٦ أبواب + تسريحة",
    colors: ["#EDE7DA", "#8C6C2C", "#2E2A24"],
    images: [
      "https://picsum.photos/seed/chambre-prestige-1/900/700",
      "https://picsum.photos/seed/chambre-prestige-2/900/700",
      "https://picsum.photos/seed/chambre-prestige-3/900/700"
    ],
    badge: "جديد",
    description: "طقم غرفة نوم كامل يجمع بين الفخامة والعملية: سرير بظهرية منحوتة، دولاب واسع بستة أبواب مع مرايا، وتسريحة أنيقة بمقعد مبطن. تشطيب لامع يقاوم الخدوش."
  },
  {
    id: 3,
    name: "طاولة سفرة بيضاوية ٨ كراسي",
    category: "طاولات وكراسي",
    price: 98000,
    material: "خشب طبيعي + قشرة جوز",
    dimensions: "٢٢٠ × ١٠٠ × ٧٥ سم",
    colors: ["#5C4A3A", "#2E2A24"],
    images: [
      "https://picsum.photos/seed/table-salle-1/900/700",
      "https://picsum.photos/seed/table-salle-2/900/700",
      "https://picsum.photos/seed/table-salle-3/900/700"
    ],
    badge: null,
    description: "طاولة سفرة بيضاوية بقشرة خشب الجوز الطبيعي، تتسع لثمانية أشخاص براحة. تأتي مع ثمانية كراسي مبطنة بأرجل خشبية متينة، مثالية للعائلات الكبيرة والمناسبات."
  },
  {
    id: 4,
    name: "مطبخ عصري لاكيه رمادي",
    category: "مطابخ",
    price: 320000,
    material: "MDF لاكيه + كوريان",
    dimensions: "حسب المقاس (٤ أمتار قياسي)",
    colors: ["#454F3E", "#EDE7DA", "#2E2A24"],
    images: [
      "https://picsum.photos/seed/cuisine-moderne-1/900/700",
      "https://picsum.photos/seed/cuisine-moderne-2/900/700",
      "https://picsum.photos/seed/cuisine-moderne-3/900/700"
    ],
    badge: "الأكثر طلباً",
    description: "مطبخ بتصميم عصري بخطوط نظيفة وطلاء لاكيه مطفي مقاوم للبصمات. رخام كوريان مقاوم للحرارة والخدش، مع نظام تخزين ذكي يستغل كل زاوية."
  },
  {
    id: 5,
    name: "مكتب عمل تنفيذي",
    category: "مكاتب",
    price: 75000,
    material: "خشب MDF + معدن",
    dimensions: "١٤٠ × ٧٠ × ٧٥ سم",
    colors: ["#2E2A24", "#8C6C2C"],
    images: [
      "https://picsum.photos/seed/bureau-exec-1/900/700",
      "https://picsum.photos/seed/bureau-exec-2/900/700",
      "https://picsum.photos/seed/bureau-exec-3/900/700"
    ],
    badge: null,
    description: "مكتب تنفيذي بتصميم أنيق يضم أدراج جانبية بأقفال، سطح مقاوم للخدش، وقاعدة معدنية متينة. مناسب لمكاتب المنزل والشركات الصغيرة."
  },
  {
    id: 6,
    name: "طقم صالون مودرن L",
    category: "صالونات",
    price: 165000,
    oldPrice: 180000,
    material: "خشب صنوبر + قماش مقاوم",
    dimensions: "٢٩٠ × ١٨٠ × ٨٠ سم",
    colors: ["#454F3E", "#2E2A24", "#EDE7DA"],
    images: [
      "https://picsum.photos/seed/salon-l-1/900/700",
      "https://picsum.photos/seed/salon-l-2/900/700",
      "https://picsum.photos/seed/salon-l-3/900/700"
    ],
    badge: "عرض خاص",
    description: "كنبة زاوية بتصميم مودرن مريح، مثالية للصالونات العصرية. قماش مقاوم للبقع وسهل التنظيف، مع وسائد إضافية مرفقة مجاناً."
  },
  {
    id: 7,
    name: "غرفة نوم أطفال مزدوجة",
    category: "غرف نوم",
    price: 155000,
    material: "خشب MDF لاكيه",
    dimensions: "سريرين ٩٠×١٩٠ + خزانة + مكتب",
    colors: ["#EDE7DA", "#454F3E"],
    images: [
      "https://picsum.photos/seed/chambre-enfant-1/900/700",
      "https://picsum.photos/seed/chambre-enfant-2/900/700",
      "https://picsum.photos/seed/chambre-enfant-3/900/700"
    ],
    badge: "جديد",
    description: "طقم غرفة نوم للأطفال يضم سريرين، خزانة ملابس، ومكتب دراسة. ألوان زاهية وآمنة، حواف مدورة لسلامة الأطفال، ومساحة تخزين وفيرة."
  },
  {
    id: 8,
    name: "طاولة قهوة رخامية",
    category: "ديكور وإكسسوارات",
    price: 32000,
    material: "رخام صناعي + معدن ذهبي",
    dimensions: "١١٠ × ٦٠ × ٤٥ سم",
    colors: ["#EDE7DA", "#B08D3F"],
    images: [
      "https://picsum.photos/seed/table-basse-1/900/700",
      "https://picsum.photos/seed/table-basse-2/900/700",
      "https://picsum.photos/seed/table-basse-3/900/700"
    ],
    badge: null,
    description: "طاولة قهوة بسطح رخامي أنيق وقاعدة معدنية بلون ذهبي، تضيف لمسة فخامة لأي صالون. تصميم خفيف يناسب المساحات الصغيرة والكبيرة."
  },
  {
    id: 9,
    name: "طقم صالون تركي كلاسيك",
    category: "صالونات",
    price: 205000,
    material: "خشب زان + قماش شينيل",
    dimensions: "٣٤٠ × ٩٥ × ٩٠ سم",
    colors: ["#5C4A3A", "#8C6C2C"],
    images: [
      "https://picsum.photos/seed/salon-turc-1/900/700",
      "https://picsum.photos/seed/salon-turc-2/900/700",
      "https://picsum.photos/seed/salon-turc-3/900/700"
    ],
    badge: "الأكثر مبيعاً",
    description: "طقم صالون بطراز تركي فاخر، نقوش خشبية يدوية وتنجيد شينيل ناعم الملمس. راحة استثنائية بفضل الإسفنج الطبي عالي الكثافة."
  },
  {
    id: 10,
    name: "خزانة مطبخ إضافية أدراج",
    category: "مطابخ",
    price: 48000,
    material: "MDF لاكيه",
    dimensions: "١٢٠ × ٤٥ × ٩٠ سم",
    colors: ["#454F3E", "#EDE7DA"],
    images: [
      "https://picsum.photos/seed/buffet-cuisine-1/900/700",
      "https://picsum.photos/seed/buffet-cuisine-2/900/700",
      "https://picsum.photos/seed/buffet-cuisine-3/900/700"
    ],
    badge: null,
    description: "خزانة تخزين إضافية للمطبخ بأدراج واسعة وأبواب ناعمة الإغلاق، تساعد على تنظيم الأواني والمستلزمات بمساحة أنيقة."
  },
  {
    id: 11,
    name: "مرآة ديكور دائرية إطار ذهبي",
    category: "ديكور وإكسسوارات",
    price: 14500,
    material: "زجاج + إطار معدني",
    dimensions: "قطر ٨٠ سم",
    colors: ["#B08D3F"],
    images: [
      "https://picsum.photos/seed/miroir-deco-1/900/700",
      "https://picsum.photos/seed/miroir-deco-2/900/700",
      "https://picsum.photos/seed/miroir-deco-3/900/700"
    ],
    badge: "جديد",
    description: "مرآة ديكورية دائرية بإطار معدني ذهبي رفيع، تضيف لمسة عصرية لأي جدار في الصالون أو المدخل أو غرفة النوم."
  },
  {
    id: 12,
    name: "كرسي مكتب دوار مريح",
    category: "مكاتب",
    price: 22000,
    material: "جلد صناعي + معدن",
    dimensions: "٦٠ × ٦٠ × ١١٠-١٢٠ سم",
    colors: ["#2E2A24", "#5C4A3A"],
    images: [
      "https://picsum.photos/seed/chaise-bureau-1/900/700",
      "https://picsum.photos/seed/chaise-bureau-2/900/700",
      "https://picsum.photos/seed/chaise-bureau-3/900/700"
    ],
    badge: null,
    description: "كرسي مكتب دوار قابل لتعديل الارتفاع، دعم قطني مريح، وعجلات ناعمة تحمي الأرضية. مثالي لساعات العمل الطويلة."
  },
  {
    id: 13,
    name: "طقم صالون صغير شقق",
    category: "صالونات",
    price: 92000,
    oldPrice: 105000,
    material: "خشب صنوبر + قماش",
    dimensions: "٢١٠ × ١٥٠ × ٧٥ سم",
    colors: ["#8C6C2C", "#EDE7DA"],
    images: [
      "https://picsum.photos/seed/salon-appart-1/900/700",
      "https://picsum.photos/seed/salon-appart-2/900/700",
      "https://picsum.photos/seed/salon-appart-3/900/700"
    ],
    badge: "عرض خاص",
    description: "طقم صالون مضغوط مصمم خصيصاً للشقق والمساحات الصغيرة، دون التنازل عن الراحة أو الأناقة. سهل التركيب والنقل."
  },
  {
    id: 14,
    name: "طاولة طعام مستطيلة ٦ كراسي",
    category: "طاولات وكراسي",
    price: 68000,
    material: "خشب زان مصمت",
    dimensions: "١٨٠ × ٩٠ × ٧٥ سم",
    colors: ["#5C4A3A", "#2E2A24"],
    images: [
      "https://picsum.photos/seed/table-6-1/900/700",
      "https://picsum.photos/seed/table-6-2/900/700",
      "https://picsum.photos/seed/table-6-3/900/700"
    ],
    badge: null,
    description: "طاولة طعام مستطيلة من خشب الزان المصمت، تصميم يجمع المتانة والبساطة، مع ستة كراسي منسقة بتنجيد مريح."
  }
];

const CATEGORIES = [
  "الكل",
  "صالونات",
  "غرف نوم",
  "طاولات وكراسي",
  "مطابخ",
  "مكاتب",
  "ديكور وإكسسوارات"
];

function formatPrice(n) {
  return n.toLocaleString("en-US") + " دج";
}
