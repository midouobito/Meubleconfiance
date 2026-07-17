// admin-product.js

// Check Auth
async function checkAuth() {
  const { data: { session } } = await supabaseClient.auth.getSession();
  if (!session) {
    window.location.href = 'admin.html';
  } else {
    initPage();
  }
}

const urlParams = new URLSearchParams(window.location.search);
const productId = urlParams.get('id');

const pageTitle = document.getElementById('pageTitle');
const productForm = document.getElementById('productForm');

const prodId = document.getElementById('prodId');
const prodName = document.getElementById('prodName');
const prodDesc = document.getElementById('prodDesc');
const prodPrice = document.getElementById('prodPrice');
const prodOldPrice = document.getElementById('prodOldPrice');
const prodCategory = document.getElementById('prodCategory');
const prodMaterial = document.getElementById('prodMaterial');
const prodDimensions = document.getElementById('prodDimensions');
const prodActive = document.getElementById('prodActive');
const prodImageUrls = document.getElementById('prodImageUrls');
const prodImageFile = document.getElementById('prodImageFile');
const imagePreviewGrid = document.getElementById('imagePreviewGrid');
const uploadHint = document.getElementById('uploadHint');

const btnSaveTop = document.getElementById('btnSaveProductTop');
const btnSaveBottom = document.getElementById('btnSaveProductBottom');

async function initPage() {
  if (productId) {
    pageTitle.textContent = 'تعديل المنتج';
    await loadProductData(productId);
  } else {
    pageTitle.textContent = 'إضافة منتج جديد';
  }
}

async function loadProductData(id) {
  const { data: product, error } = await supabaseClient
    .from('products')
    .select('*')
    .eq('id', id)
    .single();

  if (error) {
    alert("خطأ في جلب البيانات: " + error.message);
    window.location.href = 'admin.html';
    return;
  }

  prodId.value = product.id;
  prodName.value = product.name || '';
  prodDesc.value = product.description || '';
  prodPrice.value = product.price || '';
  prodOldPrice.value = product.old_price || '';
  prodCategory.value = product.category || 'Autre';
  prodMaterial.value = product.material || '';
  prodDimensions.value = product.dimensions || '';
  prodActive.value = product.is_active ? 'true' : 'false';
  
  if (product.images && product.images.length > 0) {
    prodImageUrls.value = product.images.join(', ');
    renderImagePreviews(product.images);
  }
}

let selectedFiles = [];

// Media Uploader Preview
prodImageFile.addEventListener('change', (e) => {
  const files = Array.from(e.target.files);
  if (files.length > 0) {
    selectedFiles = selectedFiles.concat(files);
    updatePreviewGrid();
  }
});

prodImageUrls.addEventListener('input', () => {
  updatePreviewGrid();
});

function updatePreviewGrid() {
  const urlsText = prodImageUrls.value;
  let urls = urlsText.split(',').map(s => s.trim()).filter(s => s);
  
  // Create object URLs for local files
  const fileUrls = selectedFiles.map(file => URL.createObjectURL(file));
  
  const allImages = [...urls, ...fileUrls];
  renderImagePreviews(allImages);
}

function renderImagePreviews(images) {
  if (images.length > 0) {
    uploadHint.style.display = 'none';
    imagePreviewGrid.innerHTML = images.map(src => `<img src="${src}" class="preview-item">`).join('');
  } else {
    uploadHint.style.display = 'block';
    imagePreviewGrid.innerHTML = '';
  }
}

// Save Logic
productForm.addEventListener('submit', handleSave);
btnSaveTop.addEventListener('click', (e) => {
  e.preventDefault();
  productForm.dispatchEvent(new Event('submit'));
});

async function handleSave(e) {
  e.preventDefault();
  
  btnSaveTop.disabled = true;
  btnSaveBottom.disabled = true;
  btnSaveBottom.textContent = "جاري الحفظ...";

  let uploadedUrls = [];
  
  // Upload all selected files
  if (selectedFiles.length > 0) {
    for (const file of selectedFiles) {
      const fileExt = file.name.split('.').pop();
      const fileName = `admin_uploads/${Date.now()}_${Math.random().toString(36).substring(7)}.${fileExt}`;
      const { data, error: uploadError } = await supabaseClient.storage
        .from('facebook-media')
        .upload(fileName, file);
      
      if (uploadError) {
        alert("خطأ في رفع الصورة: " + uploadError.message);
        resetButtons();
        return;
      }
      const { data: publicUrlData } = supabaseClient.storage.from('facebook-media').getPublicUrl(fileName);
      uploadedUrls.push(publicUrlData.publicUrl);
    }
  }

  // Gather URLs from textarea
  const textUrls = prodImageUrls.value.split(',').map(s => s.trim()).filter(s => s);
  
  const finalImages = [...textUrls, ...uploadedUrls];

  const productData = {
    name: prodName.value,
    description: prodDesc.value,
    price: prodPrice.value ? parseInt(prodPrice.value) : 0,
    old_price: prodOldPrice.value ? parseInt(prodOldPrice.value) : null,
    category: prodCategory.value,
    material: prodMaterial.value,
    dimensions: prodDimensions.value,
    is_active: prodActive.value === 'true',
    images: finalImages
  };

  if (productId) {
    // Update
    const { error } = await supabaseClient.from('products').update(productData).eq('id', productId);
    if (error) {
      alert("خطأ في التعديل: " + error.message);
      resetButtons();
      return;
    }
  } else {
    // Insert
    const { error } = await supabaseClient.from('products').insert([productData]);
    if (error) {
      alert("خطأ في الإضافة: " + error.message);
      resetButtons();
      return;
    }
  }

  // Redirect back to dashboard
  window.location.href = 'admin.html';
}

function resetButtons() {
  btnSaveTop.disabled = false;
  btnSaveBottom.disabled = false;
  btnSaveBottom.textContent = "حفظ المنتج";
}

checkAuth();
