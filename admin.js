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

window.editProduct = function(id) {
  window.location.href = 'admin-product.html?id=' + id;
}

window.deleteProduct = async function(id) {
  if (confirm("هل أنت متأكد من حذف هذا المنتج؟")) {
    await supabaseClient.from('products').delete().eq('id', id);
    loadProducts();
  }
}

// Start
checkAuth();
