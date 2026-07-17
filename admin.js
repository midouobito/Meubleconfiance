// admin.js
let currentUser = null;

// DOM Elements
const loginScreen = document.getElementById('loginScreen');
const dashboardScreen = document.getElementById('dashboardScreen');
const loginForm = document.getElementById('loginForm');
const loginError = document.getElementById('loginError');
const logoutBtn = document.getElementById('logoutBtn');

const navBtns = document.querySelectorAll('.nav-btn');
const tabContents = document.querySelectorAll('.tab-content');

const productsTableBody = document.getElementById('productsTableBody');
const ordersTableBody = document.getElementById('ordersTableBody');

const productModal = document.getElementById('productModal');
const productForm = document.getElementById('productForm');
const btnNewProduct = document.getElementById('btnNewProduct');

// Initialize
async function checkAuth() {
  const { data: { session } } = await supabaseClient.auth.getSession();
  if (session) {
    currentUser = session.user;
    showDashboard();
  } else {
    showLogin();
  }
}

// Authentication
loginForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const email = document.getElementById('loginEmail').value;
  const password = document.getElementById('loginPassword').value;
  
  loginForm.querySelector('button').disabled = true;
  loginError.style.display = 'none';

  const { data, error } = await supabaseClient.auth.signInWithPassword({
    email: email,
    password: password,
  });

  if (error) {
    loginError.textContent = "خطأ في تسجيل الدخول: " + error.message;
    loginError.style.display = 'block';
    loginForm.querySelector('button').disabled = false;
  } else {
    currentUser = data.user;
    showDashboard();
  }
});

logoutBtn.addEventListener('click', async () => {
  await supabaseClient.auth.signOut();
  currentUser = null;
  showLogin();
});

function showLogin() {
  loginScreen.style.display = 'flex';
  dashboardScreen.style.display = 'none';
}

function showDashboard() {
  loginScreen.style.display = 'none';
  dashboardScreen.style.display = 'flex';
  loadProducts();
  loadOrders();
}

// Tabs Logic
navBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    navBtns.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const target = btn.getAttribute('data-target');
    tabContents.forEach(tc => {
      tc.style.display = tc.id === target ? 'block' : 'none';
    });
  });
});

// Load Products
async function loadProducts() {
  const { data: products, error } = await supabaseClient
    .from('products')
    .select('*')
    .order('created_at', { ascending: false });

  if (error) {
    console.error("Error loading products:", error);
    return;
  }

  productsTableBody.innerHTML = products.map(p => `
    <tr>
      <td class="thumb-td"><img src="${p.images && p.images.length > 0 ? p.images[0] : 'https://picsum.photos/50'}" alt=""></td>
      <td>${p.name}</td>
      <td>${p.category || '-'}</td>
      <td>${p.price}</td>
      <td><span class="status-badge ${p.is_active ? 'status-active' : 'status-inactive'}">${p.is_active ? 'مرئي' : 'مخفي'}</span></td>
      <td>
        <button class="action-btn" onclick="editProduct('${p.id}')">تعديل</button>
        <button class="action-btn action-delete" onclick="deleteProduct('${p.id}')">حذف</button>
      </td>
    </tr>
  `).join('');
}

// Load Orders
async function loadOrders() {
  const { data: orders, error } = await supabaseClient
    .from('orders')
    .select('*')
    .order('created_at', { ascending: false });

  if (error) {
    console.error("Error loading orders:", error);
    return;
  }

  const statusMap = {
    'pending': 'في الانتظار',
    'confirmed': 'مؤكدة',
    'shipped': 'قيد التوصيل',
    'delivered': 'تم التسليم',
    'cancelled': 'ملغاة'
  };

  ordersTableBody.innerHTML = orders.map(o => `
    <tr>
      <td dir="ltr" style="text-align:right;">${new Date(o.created_at).toLocaleString('en-GB')}</td>
      <td>${o.customer_name}</td>
      <td dir="ltr" style="text-align:right;">${o.customer_phone}</td>
      <td>${o.customer_wilaya}<br><small style="color:#666;">${o.customer_address || ''}</small></td>
      <td>${o.product_name}<br><small style="color:#666; font-weight:bold;">${o.price} دج</small></td>
      <td>
        <select onchange="updateOrderStatus('${o.id}', this.value)" style="padding:5px; border-radius:4px;" class="status-badge status-${o.status}">
          <option value="pending" ${o.status === 'pending' ? 'selected' : ''}>في الانتظار</option>
          <option value="confirmed" ${o.status === 'confirmed' ? 'selected' : ''}>مؤكدة</option>
          <option value="shipped" ${o.status === 'shipped' ? 'selected' : ''}>قيد التوصيل</option>
          <option value="delivered" ${o.status === 'delivered' ? 'selected' : ''}>تم التسليم</option>
          <option value="cancelled" ${o.status === 'cancelled' ? 'selected' : ''}>ملغاة</option>
        </select>
      </td>
      <td>
        <button class="action-btn action-delete" onclick="deleteOrder('${o.id}')">حذف</button>
      </td>
    </tr>
  `).join('');
}

async function updateOrderStatus(id, newStatus) {
  const { error } = await supabaseClient
    .from('orders')
    .update({ status: newStatus })
    .eq('id', id);
  if (error) alert("خطأ في تحديث الحالة");
  loadOrders();
}

async function deleteOrder(id) {
  if (confirm("هل أنت متأكد من حذف هذه الطلبية؟")) {
    await supabaseClient.from('orders').delete().eq('id', id);
    loadOrders();
  }
}

// Product Management
btnNewProduct.addEventListener('click', () => {
  productForm.reset();
  document.getElementById('prodId').value = '';
  document.getElementById('productModalTitle').textContent = 'إضافة منتج جديد';
  document.getElementById('prodImagePreview').style.display = 'none';
  productModal.style.display = 'block';
});

document.querySelector('.close-modal').addEventListener('click', () => {
  productModal.style.display = 'none';
});

window.addEventListener('click', (e) => {
  if (e.target === productModal) productModal.style.display = 'none';
});

productForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const btn = document.getElementById('btnSaveProduct');
  btn.disabled = true;
  btn.textContent = "جاري الحفظ...";

  const id = document.getElementById('prodId').value;
  const name = document.getElementById('prodName').value;
  const desc = document.getElementById('prodDesc').value;
  const price = document.getElementById('prodPrice').value;
  const oldPrice = document.getElementById('prodOldPrice').value;
  const cat = document.getElementById('prodCategory').value;
  const material = document.getElementById('prodMaterial').value;
  const dimensions = document.getElementById('prodDimensions').value;
  const isActive = document.getElementById('prodActive').checked;
  
  let imageUrl = document.getElementById('prodImageUrl').value;
  const imageFile = document.getElementById('prodImageFile').files[0];

  // If a file is selected, upload it
  if (imageFile) {
    const fileExt = imageFile.name.split('.').pop();
    const fileName = `admin_uploads/${Date.now()}.${fileExt}`;
    const { data, error } = await supabaseClient.storage
      .from('facebook-media')
      .upload(fileName, imageFile);
    
    if (error) {
      alert("خطأ في رفع الصورة: " + error.message);
      btn.disabled = false;
      btn.textContent = "حفظ المنتج";
      return;
    }
    const { data: publicUrlData } = supabaseClient.storage.from('facebook-media').getPublicUrl(fileName);
    imageUrl = publicUrlData.publicUrl;
  }

  const productData = {
    name: name,
    description: desc,
    price: price ? parseInt(price) : 0,
    old_price: oldPrice ? parseInt(oldPrice) : null,
    category: cat,
    material: material,
    dimensions: dimensions,
    is_active: isActive,
  };

  if (imageUrl) {
    productData.images = [imageUrl];
  }

  if (id) {
    // Update
    await supabaseClient.from('products').update(productData).eq('id', id);
  } else {
    // Insert
    // Prevent overriding fb_post_id manually to keep it null
    await supabaseClient.from('products').insert([productData]);
  }

  productModal.style.display = 'none';
  btn.disabled = false;
  btn.textContent = "حفظ المنتج";
  loadProducts();
});

window.editProduct = async function(id) {
  const { data: product, error } = await supabaseClient.from('products').select('*').eq('id', id).single();
  if (product) {
    document.getElementById('prodId').value = product.id;
    document.getElementById('prodName').value = product.name;
    document.getElementById('prodDesc').value = product.description;
    document.getElementById('prodPrice').value = product.price;
    document.getElementById('prodOldPrice').value = product.old_price || '';
    document.getElementById('prodCategory').value = product.category;
    document.getElementById('prodMaterial').value = product.material || '';
    document.getElementById('prodDimensions').value = product.dimensions || '';
    document.getElementById('prodActive').checked = product.is_active;
    document.getElementById('prodImageUrl').value = product.images && product.images.length > 0 ? product.images[0] : '';
    
    if (product.images && product.images.length > 0) {
      document.getElementById('prodImagePreview').src = product.images[0];
      document.getElementById('prodImagePreview').style.display = 'block';
    } else {
      document.getElementById('prodImagePreview').style.display = 'none';
    }

    document.getElementById('productModalTitle').textContent = 'تعديل المنتج';
    productModal.style.display = 'block';
  }
}

window.deleteProduct = async function(id) {
  if (confirm("هل أنت متأكد من حذف هذا المنتج؟")) {
    await supabaseClient.from('products').delete().eq('id', id);
    loadProducts();
  }
}

// Start
checkAuth();
