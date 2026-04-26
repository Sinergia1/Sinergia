// scripts.js - Funcionalidad completa para LocalMarket CON CONEXIÓN A BASE DE DATOS
// Versión con requerimiento de cuenta y datos completos

// ===== CONFIGURACIÓN GLOBAL =====
const CONFIG = {
    WHATSAPP_NUMBER: '521234567890',
    API_BASE: '',
    STORAGE_KEYS: {
        CART: 'localmarket_cart',
        USER: 'localmarket_user',
        THEME: 'localmarket_theme',
        SESSION: 'localmarket_session'
    }
};

// ===== UTILIDADES =====
const Utils = {
    formatPrice(price, currency = '$') {
        return `${currency} ${parseFloat(price).toFixed(2)}`;
    },

    setStorage(key, data) {
        localStorage.setItem(key, JSON.stringify(data));
    },

    getStorage(key) {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : null;
    },

    showToast(message, type = 'success', duration = 3000) {
        const existingToast = document.querySelector('.toast');
        if (existingToast) existingToast.remove();

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'slideIn 0.3s reverse';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    },

    generateId() {
        return Date.now() + Math.random().toString(36).substr(2, 9);
    },

    getCurrentPage() {
        return window.location.pathname.split('/').pop() || 'inicio.html';
    },

    navigateTo(page) {
        window.location.href = page;
    },

    getSessionId() {
        let sessionId = localStorage.getItem(CONFIG.STORAGE_KEYS.SESSION);
        if (!sessionId) {
            sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem(CONFIG.STORAGE_KEYS.SESSION, sessionId);
        }
        return sessionId;
    },

    async fetchAPI(endpoint, options = {}) {
        const url = CONFIG.API_BASE + endpoint;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };
        
        try {
            const response = await fetch(url, { ...defaultOptions, ...options });
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            console.log(`API Response from ${endpoint}:`, data);
            return data;
        } catch (error) {
            console.error('API Error:', error);
            this.showToast(error.message || 'Error de conexión', 'error');
            throw error;
        }
    },

    async uploadUserPhoto(usuarioId, file) {
        const formData = new FormData();
        formData.append('foto', file);
        formData.append('usuario_id', usuarioId);
        
        try {
            const response = await fetch('/api/upload/perfil', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Error al subir foto');
            }
            
            return data;
        } catch (error) {
            console.error('Error uploading photo:', error);
            this.showToast('Error al subir la foto', 'error');
            throw error;
        }
    },

    checkAuth(redirectTo = 'inicio_secion.html') {
        const user = this.getStorage(CONFIG.STORAGE_KEYS.USER);
        if (!user) {
            this.showToast('⚠️ Debes iniciar sesión para comprar', 'info');
            setTimeout(() => this.navigateTo(redirectTo), 1500);
            return false;
        }
        return user;
    },

    validateUserHasAddress() {
        const user = this.getStorage(CONFIG.STORAGE_KEYS.USER);
        if (!user) return false;
        
        let direcciones = user.direcciones;
        if (typeof direcciones === 'string') {
            try {
                direcciones = JSON.parse(direcciones);
            } catch {
                direcciones = [];
            }
        }
        
        if (!direcciones || direcciones.length === 0) {
            this.showToast('⚠️ Debes agregar una dirección antes de comprar', 'error');
            setTimeout(() => this.navigateTo('mi_perfil.html'), 2000);
            return false;
        }
        
        return true;
    },

    validateUserHasPhone() {
        const user = this.getStorage(CONFIG.STORAGE_KEYS.USER);
        if (!user) return false;
        
        if (!user.telefono || user.telefono.trim() === '') {
            this.showToast('⚠️ Debes agregar un número de teléfono en tu perfil', 'error');
            setTimeout(() => this.navigateTo('mi_perfil.html'), 2000);
            return false;
        }
        
        return true;
    },

    validateUserProfileComplete() {
        const user = this.getStorage(CONFIG.STORAGE_KEYS.USER);
        if (!user) return false;
        
        const missingFields = [];
        
        if (!user.nombre || user.nombre.trim() === '') missingFields.push('nombre');
        if (!user.correo || user.correo.trim() === '') missingFields.push('correo');
        if (!user.telefono || user.telefono.trim() === '') missingFields.push('teléfono');
        
        let direcciones = user.direcciones;
        if (typeof direcciones === 'string') {
            try {
                direcciones = JSON.parse(direcciones);
            } catch {
                direcciones = [];
            }
        }
        
        if (!direcciones || direcciones.length === 0) missingFields.push('dirección');
        
        if (missingFields.length > 0) {
            this.showToast(`⚠️ Completa tu perfil: ${missingFields.join(', ')}`, 'error');
            setTimeout(() => this.navigateTo('mi_perfil.html'), 2000);
            return false;
        }
        
        return true;
    },

    getDefaultAddress() {
        const user = this.getStorage(CONFIG.STORAGE_KEYS.USER);
        if (!user) return null;
        
        let direcciones = user.direcciones;
        if (typeof direcciones === 'string') {
            try {
                direcciones = JSON.parse(direcciones);
            } catch {
                direcciones = [];
            }
        }
        
        if (!direcciones || direcciones.length === 0) return null;
        
        const defaultAddr = direcciones.find(addr => addr.predeterminada === true) || direcciones[0];
        return defaultAddr;
    },

    async loadUserData() {
        const user = this.getStorage(CONFIG.STORAGE_KEYS.USER);
        if (!user) return null;
        
        const sidebarName = document.getElementById('sidebar-user-name');
        const sidebarEmail = document.getElementById('sidebar-user-email');
        const profileName = document.getElementById('profile-name');
        const profileEmail = document.getElementById('profile-email');
        const profilePhone = document.getElementById('profile-phone');
        
        if (sidebarName) sidebarName.textContent = user.nombre || 'Usuario';
        if (sidebarEmail) sidebarEmail.textContent = user.correo || '';
        if (profileName) profileName.value = user.nombre || '';
        if (profileEmail) profileEmail.value = user.correo || '';
        if (profilePhone) profilePhone.value = user.telefono || '';
        
        this.updateAvatar();
        
        return user;
    },

    updateAvatar() {
        const container = document.getElementById('avatar-container');
        if (!container) return;
        
        const user = this.getStorage(CONFIG.STORAGE_KEYS.USER);
        
        if (user && user.foto_url) {
            container.innerHTML = `<img class="w-full h-full object-cover rounded-full" src="${user.foto_url}" alt="Avatar"/>`;
        } else {
            const inicial = user && user.nombre ? user.nombre.charAt(0).toUpperCase() : '?';
            container.innerHTML = `<div class="avatar-placeholder">${inicial}</div>`;
        }
    },

    setupPasswordToggles() {
        document.querySelectorAll('[data-toggle-password]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const targetId = btn.getAttribute('data-toggle-password');
                const input = document.getElementById(targetId);
                const icon = btn.querySelector('span');
                
                if (input && icon) {
                    if (input.type === 'password') {
                        input.type = 'text';
                        icon.textContent = 'visibility_off';
                    } else {
                        input.type = 'password';
                        icon.textContent = 'visibility';
                    }
                }
            });
        });
        
        const toggleBtn = document.getElementById('togglePassword');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => {
                const input = document.getElementById('password');
                const icon = toggleBtn.querySelector('span');
                if (input && icon) {
                    if (input.type === 'password') {
                        input.type = 'text';
                        icon.textContent = 'visibility_off';
                    } else {
                        input.type = 'password';
                        icon.textContent = 'visibility';
                    }
                }
            });
        }

        window.togglePassword = function(fieldId) {
            const field = document.getElementById(fieldId);
            const button = field.nextElementSibling;
            const icon = button.querySelector('span');
            
            if (field.type === 'password') {
                field.type = 'text';
                icon.textContent = 'visibility_off';
            } else {
                field.type = 'password';
                icon.textContent = 'visibility';
            }
        };
    }
};

// ===== MANEJO DEL CARRITO =====
const CartManager = {
    async getCart() {
        const sessionId = Utils.getSessionId();
        try {
            const items = await Utils.fetchAPI(`/api/carrito/${sessionId}`);
            return this.calculateCartTotals(items);
        } catch (error) {
            console.error('Error getting cart:', error);
            return { items: [], subtotal: 0, shipping: 35, total: 0 };
        }
    },

    calculateCartTotals(items) {
        const subtotal = items.reduce((sum, item) => sum + (parseFloat(item.precio) * item.cantidad), 0);
        return {
            items: items,
            subtotal: subtotal,
            shipping: subtotal > 0 ? 35 : 0,
            total: subtotal + (subtotal > 0 ? 35 : 0)
        };
    },

    async addItem(product) {
        const user = Utils.checkAuth();
        if (!user) return false;
        
        if (!Utils.validateUserHasPhone()) return false;
        if (!Utils.validateUserHasAddress()) return false;
        
        const sessionId = Utils.getSessionId();
        
        try {
            await Utils.fetchAPI('/api/carrito/agregar', {
                method: 'POST',
                body: JSON.stringify({
                    session_id: sessionId,
                    producto_id: product.id,
                    cantidad: product.quantity || 1
                })
            });
            
            await this.updateCartBadge();
            Utils.showToast('✅ Producto agregado al carrito');
            window.dispatchEvent(new Event('cartUpdated'));
            return true;
        } catch (error) {
            console.error('Error adding to cart:', error);
            Utils.showToast('Error al agregar al carrito', 'error');
            return false;
        }
    },

    async updateQuantity(itemId, change) {
        try {
            const cart = await this.getCart();
            const item = cart.items.find(i => i.id === itemId);
            
            if (item) {
                const newQuantity = Math.max(1, item.cantidad + change);
                await Utils.fetchAPI('/api/carrito/actualizar', {
                    method: 'PUT',
                    body: JSON.stringify({
                        item_id: itemId,
                        cantidad: newQuantity
                    })
                });
            }
            
            await this.renderCartPage();
            await this.updateCartBadge();
            Utils.showToast('🔄 Cantidad actualizada');
            window.dispatchEvent(new Event('cartUpdated'));
        } catch (error) {
            console.error('Error updating quantity:', error);
            Utils.showToast('Error al actualizar', 'error');
        }
    },

    async removeItem(itemId) {
        try {
            await Utils.fetchAPI(`/api/carrito/eliminar/${itemId}`, {
                method: 'DELETE'
            });
            
            await this.renderCartPage();
            await this.updateCartBadge();
            Utils.showToast('🗑️ Producto eliminado');
            window.dispatchEvent(new Event('cartUpdated'));
        } catch (error) {
            console.error('Error removing item:', error);
            Utils.showToast('Error al eliminar', 'error');
        }
    },

    async clearCart() {
        const sessionId = Utils.getSessionId();
        
        if (confirm('¿Estás seguro de vaciar el carrito?')) {
            try {
                await Utils.fetchAPI(`/api/carrito/limpiar/${sessionId}`, {
                    method: 'DELETE'
                });
                
                await this.renderCartPage();
                await this.updateCartBadge();
                Utils.showToast('🧹 Carrito vaciado');
                window.dispatchEvent(new Event('cartUpdated'));
            } catch (error) {
                console.error('Error clearing cart:', error);
                Utils.showToast('Error al vaciar carrito', 'error');
            }
        }
    },

    async updateCartBadge() {
        const cart = await this.getCart();
        const cartButtons = document.querySelectorAll('[data-cart-badge]');
        const totalItems = cart.items.reduce((sum, item) => sum + item.cantidad, 0);
        
        cartButtons.forEach(btn => {
            let badge = btn.querySelector('.cart-badge');
            if (totalItems > 0) {
                if (!badge) {
                    badge = document.createElement('span');
                    badge.className = 'cart-badge';
                    btn.style.position = 'relative';
                    btn.appendChild(badge);
                }
                badge.textContent = totalItems > 9 ? '9+' : totalItems;
            } else if (badge) {
                badge.remove();
            }
        });
    },

    async renderCartPage() {
        const tableBody = document.querySelector('[data-cart-table-body]');
        const cartContainer = document.querySelector('[data-cart-container]');
        const cartCount = document.querySelector('[data-cart-count]');
        
        if (!tableBody && !cartContainer) return;

        const cart = await this.getCart();
        
        if (cartCount) {
            cartCount.textContent = cart.items.length;
        }
        
        if (cart.items.length === 0) {
            if (cartContainer) {
                cartContainer.innerHTML = `
                    <div class="text-center py-12">
                        <span class="material-symbols-outlined text-6xl text-slate-300 mb-4">shopping_cart</span>
                        <h3 class="text-xl font-bold text-slate-600 mb-2">Tu carrito está vacío</h3>
                        <p class="text-slate-400 mb-6">¡Explora nuestros productos y encuentra algo especial!</p>
                        <button onclick="Utils.navigateTo('inicio.html')" class="inline-block bg-primary text-dark-green px-6 py-3 rounded-lg font-bold hover:bg-primary/90 transition-all">
                            Ver productos
                        </button>
                    </div>
                `;
            }
            return;
        }

        if (tableBody) {
            tableBody.innerHTML = cart.items.map(item => `
                <tr class="group hover:bg-slate-50/50 dark:hover:bg-slate-800/50 transition-colors" data-product-id="${item.id}">
                    <td class="px-6 py-6">
                        <div class="flex items-center gap-4">
                            <div class="h-20 w-20 rounded-lg overflow-hidden bg-slate-100 flex-shrink-0">
                                <img class="h-full w-full object-cover" src="${item.imagen_url || 'https://via.placeholder.com/100'}" alt="${item.nombre}">
                            </div>
                            <div>
                                <p class="font-bold text-dark-green text-lg">${item.nombre}</p>
                                <p class="text-sm text-slate-500">${item.empresa_nombre || 'LocalMarket'}</p>
                                <p class="text-primary font-semibold mt-1">${Utils.formatPrice(item.precio)}</p>
                            </div>
                        </div>
                    </td>
                    <td class="px-6 py-6">
                        <div class="flex items-center justify-center">
                            <div class="flex items-center border border-slate-200 dark:border-slate-600 rounded-lg overflow-hidden">
                                <button class="px-3 py-1 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors" onclick="CartManager.updateQuantity(${item.id}, -1)">
                                    <span class="material-symbols-outlined text-sm">remove</span>
                                </button>
                                <span class="px-4 py-1 text-sm font-bold min-w-[40px] text-center">${item.cantidad}</span>
                                <button class="px-3 py-1 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors" onclick="CartManager.updateQuantity(${item.id}, 1)">
                                    <span class="material-symbols-outlined text-sm">add</span>
                                </button>
                            </div>
                        </div>
                    </td>
                    <td class="px-6 py-6 text-right">
                        <span class="font-bold text-dark-green">${Utils.formatPrice(item.precio * item.cantidad)}</span>
                    </td>
                    <td class="px-6 py-6 text-right">
                        <button class="text-slate-400 hover:text-red-500 transition-colors p-2" onclick="CartManager.removeItem(${item.id})">
                            <span class="material-symbols-outlined">delete</span>
                        </button>
                    </td>
                </tr>
            `).join('');
        }

        this.updateCartSummary(cart);
    },

    updateCartSummary(cart) {
        const subtotalEl = document.querySelector('[data-cart-subtotal]');
        const shippingEl = document.querySelector('[data-cart-shipping]');
        const totalEl = document.querySelector('[data-cart-total]');
        
        if (subtotalEl) subtotalEl.textContent = Utils.formatPrice(cart.subtotal || 0);
        if (shippingEl) shippingEl.textContent = Utils.formatPrice(cart.shipping || 0);
        if (totalEl) totalEl.textContent = Utils.formatPrice(cart.total || 0);
    },

    groupItemsByCompany(items) {
        const grouped = {};
        
        items.forEach(item => {
            const companyName = item.empresa_nombre || 'LocalMarket';
            const companyPhone = item.empresa_telefono || CONFIG.WHATSAPP_NUMBER;
            
            if (!grouped[companyName]) {
                grouped[companyName] = {
                    phone: companyPhone,
                    items: [],
                    subtotal: 0
                };
            }
            
            grouped[companyName].items.push(item);
            grouped[companyName].subtotal += item.precio * item.cantidad;
        });
        
        return grouped;
    }
};

// ===== PRODUCTOS =====
const ProductManager = {
    async loadProducts(category = 'todos') {
        try {
            let url = '/api/productos';
            if (category !== 'todos') {
                url += `?categoria=${category}`;
            }
            
            console.log('Cargando productos de:', url);
            const productos = await Utils.fetchAPI(url);
            console.log('Productos recibidos:', productos);
            
            this.renderProducts(productos);
        } catch (error) {
            console.error('Error loading products:', error);
        }
    },

    renderProducts(productos) {
        const container = document.getElementById('productos-container');
        if (!container) return;

        if (productos.length === 0) {
            container.innerHTML = `
                <div class="col-span-full text-center py-12">
                    <span class="material-symbols-outlined text-6xl text-gray-300 mb-4">inventory</span>
                    <p class="text-gray-500">No hay productos disponibles</p>
                </div>
            `;
            return;
        }

        container.innerHTML = productos.map(p => {
            const productJson = JSON.stringify({
                id: p.id,
                name: p.nombre,
                price: p.precio
            }).replace(/'/g, "\\'");
            
            const imageUrl = p.imagen_url || 'https://images.unsplash.com/photo-1600857544200-b2f666a9a2ec?w=400&h=400&fit=crop';
            
            return `
                <div class="bg-white rounded-xl overflow-hidden shadow-sm border border-slate-100 hover:shadow-md transition-shadow group" data-product data-category="${p.categoria}">
                    <div class="w-full aspect-square bg-slate-100 bg-cover bg-center" 
                         style="background-image: url('${imageUrl}');"></div>
                    <div class="p-4 space-y-2">
                        <span class="text-[10px] font-bold uppercase tracking-wider text-primary" data-product-brand>
                            ${p.empresa_nombre || 'LocalMarket'}
                        </span>
                        <h5 class="text-dark-green font-bold text-sm" data-product-title>${p.nombre}</h5>
                        <p class="text-dark-green font-black text-lg" data-product-price>${Utils.formatPrice(p.precio)}</p>
                        <button class="w-full mt-2 bg-dark-green text-white py-2 rounded-lg text-sm font-bold hover:bg-opacity-90 transition-all flex items-center justify-center gap-2" 
                                onclick='CartManager.addItem(${productJson})'>
                            <span class="material-symbols-outlined text-[18px]">add_shopping_cart</span>
                            Agregar al carrito
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    },

    async searchProducts(query) {
        try {
            const productos = await Utils.fetchAPI('/api/productos');
            const searchTerm = query.toLowerCase().trim();
            
            const filtered = productos.filter(p => 
                p.nombre.toLowerCase().includes(searchTerm) || 
                (p.empresa_nombre && p.empresa_nombre.toLowerCase().includes(searchTerm))
            );
            
            this.renderProducts(filtered);
        } catch (error) {
            console.error('Error searching products:', error);
        }
    },

    async filterByCategory(category) {
        await this.loadProducts(category);
        
        document.querySelectorAll('[data-filter]').forEach(btn => {
            if (btn.getAttribute('data-filter') === category) {
                btn.classList.add('bg-mint-green', 'text-dark-green', 'font-bold');
                btn.classList.remove('hover:bg-slate-100', 'text-slate-600', 'font-medium');
            } else {
                btn.classList.remove('bg-mint-green', 'text-dark-green', 'font-bold');
                btn.classList.add('hover:bg-slate-100', 'text-slate-600', 'font-medium');
            }
        });
    }
};

// ===== EMPRESAS =====
const EmpresaManager = {
    async loadEmpresas() {
        try {
            const empresas = await Utils.fetchAPI('/api/empresas');
            this.renderEmpresas(empresas);
        } catch (error) {
            console.error('Error loading empresas:', error);
        }
    },

    renderEmpresas(empresas) {
        const container = document.getElementById('empresas-container');
        if (!container) return;

        if (empresas.length === 0) {
            container.innerHTML = '<p class="text-center w-full">No hay empresas disponibles</p>';
            return;
        }

        container.innerHTML = empresas.map(empresa => `
            <a href="tiendas.html?store=${encodeURIComponent(empresa.nombre)}" class="flex flex-col items-center gap-2 min-w-[100px]">
                <div class="w-20 h-20 rounded-full border-2 border-primary/20 p-1">
                    <div class="w-full h-full rounded-full bg-cover bg-center" style="background-image: url('${empresa.logo_url || 'https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=200&h=200&fit=crop'}');"></div>
                </div>
                <span class="text-sm font-medium">${empresa.nombre}</span>
            </a>
        `).join('');
    },

    async getEmpresaById(empresaId) {
        try {
            return await Utils.fetchAPI(`/api/empresas/${empresaId}`);
        } catch (error) {
            console.error('Error getting empresa:', error);
            return null;
        }
    }
};

// ===== TIENDAS =====
const StoreManager = {
    async loadStoreData(storeName) {
        try {
            console.log('Buscando tienda:', storeName);
            
            const response = await fetch(`/api/empresas/buscar?nombre=${encodeURIComponent(storeName)}`);
            
            if (!response.ok) {
                throw new Error('Tienda no encontrada');
            }
            
            const empresa = await response.json();
            console.log('Empresa encontrada:', empresa);

            const nameDisplay = document.getElementById('store-name-display');
            const nameEl = document.getElementById('store-name');
            const logoImg = document.getElementById('store-logo');
            const descEl = document.getElementById('store-description');
            const locationEl = document.getElementById('store-location');
            const paymentEl = document.getElementById('payment-methods');
            const phoneEl = document.getElementById('store-phone');

            if (nameDisplay) nameDisplay.textContent = empresa.nombre;
            if (nameEl) nameEl.textContent = empresa.nombre;
            if (logoImg) {
                logoImg.src = empresa.logo_url || 'https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=200&h=200&fit=crop';
            }
            
            if (descEl) {
                descEl.textContent = empresa.descripcion || 'Productos locales de calidad';
            }
            
            if (locationEl) {
                locationEl.textContent = empresa.ubicacion || empresa.direccion || 'México';
            }
            
            if (paymentEl) {
                paymentEl.textContent = empresa.metodo_pago || 'Efectivo, Transferencia';
            }
            
            if (phoneEl) {
                phoneEl.textContent = empresa.telefono || 'No disponible';
            }
            
            if (weekdaysEl) weekdaysEl.textContent = '9:00 - 18:00';
            if (saturdayEl) saturdayEl.textContent = '9:00 - 14:00';
            if (sundayEl) sundayEl.textContent = 'Cerrado';

            await this.loadStoreProducts(empresa.id);
            
        } catch (error) {
            console.error('Error loading store:', error);
            Utils.showToast('Error al cargar la tienda', 'error');
            
            const nameDisplay = document.getElementById('store-name-display');
            if (nameDisplay) nameDisplay.textContent = 'Tienda no encontrada';
        }
    },

    async loadStoreProducts(empresaId) {
        try {
            console.log('Cargando productos para empresa ID:', empresaId);
            const response = await fetch(`/api/empresas/${empresaId}/productos`);
            const productos = await response.json();
            console.log('Productos encontrados:', productos);
            
            const grid = document.getElementById('products-grid');
            if (!grid) return;
    
            if (productos.length === 0) {
                grid.innerHTML = `
                    <div class="col-span-full text-center py-8 sm:py-12">
                        <span class="material-symbols-outlined text-4xl sm:text-6xl text-gray-300 mb-4">inventory</span>
                        <p class="text-gray-500 text-sm sm:text-base">No hay productos disponibles en esta tienda</p>
                    </div>
                `;
                return;
            }
    
            grid.innerHTML = productos.map(p => {
                const productJson = JSON.stringify({
                    id: p.id,
                    name: p.nombre,
                    price: p.precio
                }).replace(/'/g, "\\'");
                
                const imageUrl = p.imagen_url || 'https://images.unsplash.com/photo-1600857544200-b2f666a9a2ec?w=400&h=400&fit=crop';
                
                return `
                    <div class="product-card-fixed">
                        <div class="product-image-fixed" style="background-image: url('${imageUrl}');"></div>
                        <div class="product-content-fixed">
                            <span class="product-brand-fixed">${this.escapeHtml(p.categoria || 'General')}</span>
                            <h4 class="product-title-full">${this.escapeHtml(p.nombre)}</h4>
                            <div class="product-price-fixed">${Utils.formatPrice(p.precio)}</div>
                            <button class="product-button-fixed" onclick='CartManager.addItem(${productJson})'>
                                <span class="material-symbols-outlined text-sm sm:text-[18px]">add_shopping_cart</span>
                                Agregar
                            </button>
                        </div>
                    </div>
                `;
            }).join('');
            
        } catch (error) {
            console.error('Error loading store products:', error);
        }
    },
    
    escapeHtml(str) {
        if (!str) return '';
        return str.replace(/[&<>]/g, function(m) {
            if (m === '&') return '&amp;';
            if (m === '<') return '&lt;';
            if (m === '>') return '&gt;';
            return m;
        });
    }
};

// ===== AUTENTICACIÓN =====
const AuthManager = {
    async getCurrentUser() {
        const user = Utils.getStorage(CONFIG.STORAGE_KEYS.USER);
        if (!user) return null;
        return user;
    },

    async login(email, password) {
        try {
            const user = await Utils.fetchAPI('/api/login', {
                method: 'POST',
                body: JSON.stringify({ email, password })
            });
            
            Utils.setStorage(CONFIG.STORAGE_KEYS.USER, user);
            Utils.showToast('👋 ¡Bienvenido de vuelta!');
            
            setTimeout(() => {
                if (user.rol === 'administrador') {
                    Utils.navigateTo('panel_admin.html');
                } else if (user.rol === 'socio') {
                    Utils.navigateTo('panel_empresa.html');
                } else {
                    Utils.navigateTo('mi_perfil.html');
                }
            }, 1000);
            
            return user;
        } catch (error) {
            console.error('Login error:', error);
            throw error;
        }
    },

    logout() {
        if (confirm('¿Estás seguro de cerrar sesión?')) {
            localStorage.removeItem(CONFIG.STORAGE_KEYS.USER);
            Utils.showToast('👋 Sesión cerrada');
            setTimeout(() => Utils.navigateTo('inicio.html'), 1000);
        }
    },

    checkExistingSession() {
        const user = Utils.getStorage(CONFIG.STORAGE_KEYS.USER);
        return !!(user && user.id);
    },

    redirectIfLoggedIn() {
        if (this.checkExistingSession()) {
            Utils.navigateTo('mi_perfil.html');
            return true;
        }
        return false;
    },

    async loadProfileData() {
        const user = await this.getCurrentUser();
        if (!user) return;

        const nameInput = document.getElementById('profile-name');
        const emailInput = document.getElementById('profile-email');
        const phoneInput = document.getElementById('profile-phone');

        if (nameInput) nameInput.value = user.nombre || '';
        if (emailInput) emailInput.value = user.correo || '';
        if (phoneInput) phoneInput.value = user.telefono || '';
        
        const sidebarName = document.getElementById('sidebar-user-name');
        if (sidebarName) sidebarName.textContent = user.nombre || 'Usuario';
        
        const sidebarEmail = document.getElementById('sidebar-user-email');
        if (sidebarEmail) sidebarEmail.textContent = user.correo || '';
    }
};

// ===== PEDIDOS =====
const OrderManager = {
    async createOrder(cart, direccion, notas = '') {
        const user = await AuthManager.getCurrentUser();
        if (!user) {
            Utils.showToast('Debes iniciar sesión', 'error');
            setTimeout(() => Utils.navigateTo('inicio_secion.html'), 1500);
            return;
        }

        try {
            const result = await Utils.fetchAPI('/api/pedidos', {
                method: 'POST',
                body: JSON.stringify({
                    usuario_id: user.id,
                    session_id: Utils.getSessionId(),
                    items: cart.items.map(item => ({
                        producto_id: item.producto_id || item.id,
                        cantidad: item.cantidad,
                        precio: item.precio
                    })),
                    total: cart.total,
                    direccion: direccion,
                    notas: notas
                })
            });
            
            Utils.showToast('✅ Pedido creado exitosamente');
            return result;
        } catch (error) {
            console.error('Error creating order:', error);
            Utils.showToast('Error al crear pedido', 'error');
            throw error;
        }
    },

    async loadUserOrders() {
        const user = await AuthManager.getCurrentUser();
        if (!user) return;

        try {
            const pedidos = await Utils.fetchAPI(`/api/usuarios/${user.id}/pedidos`);
            this.renderOrders(pedidos);
        } catch (error) {
            console.error('Error loading orders:', error);
        }
    },

    renderOrders(pedidos) {
        const tbody = document.getElementById('orders-table-body');
        if (!tbody) return;

        if (pedidos.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="4" class="py-8 text-center text-slate-500">
                        No tienes pedidos aún
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = pedidos.map(p => `
            <tr class="border-b border-slate-50">
                <td class="py-4 font-medium text-slate-900">#ART-${p.id}</td>
                <td class="py-4 text-slate-600">${new Date(p.fecha).toLocaleDateString('es-ES', { day: '2-digit', month: 'short', year: 'numeric' })}</td>
                <td class="py-4 text-slate-900 font-semibold">${Utils.formatPrice(p.total)}</td>
                <td class="py-4">
                    <span class="px-3 py-1 ${p.estado === 'entregado' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'} rounded-full text-xs font-bold">
                        ${p.estado.charAt(0).toUpperCase() + p.estado.slice(1).replace('_', ' ')}
                    </span>
                </td>
            </tr>
        `).join('');
    }
};

// ===== WHATSAPP - ENVÍO MÚLTIPLE =====
const WhatsAppManager = {
    async sendOrder() {
        const cart = await CartManager.getCart();
        if (!cart || cart.items.length === 0) {
            Utils.showToast('❌ El carrito está vacío', 'error');
            return;
        }

        const user = await AuthManager.getCurrentUser();
        if (!user) {
            Utils.showToast('Debes iniciar sesión', 'error');
            setTimeout(() => Utils.navigateTo('inicio_secion.html'), 1500);
            return;
        }
        
        if (!Utils.validateUserHasPhone()) return;
        if (!Utils.validateUserHasAddress()) return;
        
        const address = Utils.getDefaultAddress();
        if (!address) {
            Utils.showToast('No tienes una dirección registrada', 'error');
            return;
        }
        
        const direccionCompleta = `${address.direccion}, ${address.ciudad || ''}`;
        const groupedItems = CartManager.groupItemsByCompany(cart.items);
        const companyNames = Object.keys(groupedItems);
        
        if (companyNames.length === 0) return;
        
        Utils.showToast(`📤 Enviando pedido a ${companyNames.length} empresa(s)...`, 'info', 2000);
        
        let mensajesEnviados = 0;
        
        for (const companyName of companyNames) {
            const companyData = groupedItems[companyName];
            const itemsList = companyData.items.map(item => 
                `• ${item.nombre} x${item.cantidad} - ${Utils.formatPrice(item.precio * item.cantidad)}`
            ).join('\n');
            
            const message = encodeURIComponent(
                `🛍️ *NUEVO PEDIDO - LocalMarket*\n\n` +
                `*Tienda:* ${companyName}\n` +
                `*Cliente:* ${user.nombre}\n` +
                `*Teléfono:* ${user.telefono}\n` +
                `*Dirección:* ${direccionCompleta}\n\n` +
                `*Productos solicitados:*\n${itemsList}\n\n` +
                `*Subtotal tienda:* ${Utils.formatPrice(companyData.subtotal)}\n` +
                `*Envío:* ${Utils.formatPrice(companyData.subtotal > 0 ? 35 : 0)}\n\n` +
                `*METODO DE PAGO:* Efectivo / Transferencia\n` +
                `*ENTREGA:* Confirmar disponibilidad\n\n` +
                `📌 *Por favor confirma disponibilidad y total a pagar.*`
            );
            
            let phoneNumber = companyData.phone || CONFIG.WHATSAPP_NUMBER;
            let cleanPhone = phoneNumber.replace(/\D/g, '');
            if (!cleanPhone.startsWith('52') && cleanPhone.length === 10) {
                cleanPhone = '52' + cleanPhone;
            }
            
            window.open(`https://wa.me/${cleanPhone}?text=${message}`, '_blank');
            mensajesEnviados++;
            
            await new Promise(resolve => setTimeout(resolve, 500));
        }
        
        setTimeout(async () => {
            const sessionId = Utils.getSessionId();
            await Utils.fetchAPI(`/api/carrito/limpiar/${sessionId}`, { method: 'DELETE' });
            await CartManager.updateCartBadge();
            Utils.showToast(`✅ Pedido enviado a ${mensajesEnviados} empresa(s). Revisa WhatsApp para confirmar.`, 'success', 5000);
            
            setTimeout(() => {
                Utils.navigateTo('inicio.html');
            }, 3000);
        }, 1000);
    },

    contactStore(storeName, storePhone) {
        const user = Utils.getStorage(CONFIG.STORAGE_KEYS.USER);
        
        let phoneNumber = storePhone || CONFIG.WHATSAPP_NUMBER;
        let cleanPhone = phoneNumber.replace(/\D/g, '');
        if (!cleanPhone.startsWith('52') && cleanPhone.length === 10) {
            cleanPhone = '52' + cleanPhone;
        }
        
        let message;
        if (user && user.nombre) {
            message = encodeURIComponent(
                `Hola, soy ${user.nombre}. Me interesan los productos de ${storeName}. ¿Podrías darme más información?`
            );
        } else {
            message = encodeURIComponent(
                `Hola, me interesan los productos de ${storeName}. ¿Podrías darme más información?`
            );
        }
        
        window.open(`https://wa.me/${cleanPhone}?text=${message}`, '_blank');
    }
};

// ===== SOLICITUDES DE VENDEDORES =====
const SolicitudManager = {
    async enviarSolicitud(data) {
        try {
            console.log('Enviando solicitud:', data);
            
            const response = await fetch('/api/solicitudes', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (response.ok) {
                Utils.showToast('✅ Solicitud enviada correctamente. Pronto recibirás una respuesta.', 'success');
                setTimeout(() => Utils.navigateTo('inicio.html'), 2000);
                return result;
            } else {
                Utils.showToast(result.error || 'Error al enviar solicitud', 'error');
                return null;
            }
        } catch (error) {
            console.error('Error enviando solicitud:', error);
            Utils.showToast('Error de conexión con el servidor', 'error');
        }
    },

    async cargarSolicitudes() {
        try {
            const response = await fetch('/api/solicitudes');
            const solicitudes = await response.json();
            
            console.log('Solicitudes cargadas:', solicitudes);
            this.renderSolicitudes(solicitudes);
            return solicitudes;
        } catch (error) {
            console.error('Error cargando solicitudes:', error);
            const tbody = document.getElementById('solicitudes-table-body');
            if (tbody) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="5" class="px-6 py-8 text-center text-red-500">
                            Error al cargar solicitudes. Verifica la conexión.
                        </td>
                    </tr>
                `;
            }
        }
    },

    renderSolicitudes(solicitudes) {
        const tbody = document.getElementById('solicitudes-table-body');
        if (!tbody) return;

        if (!solicitudes || solicitudes.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="px-6 py-8 text-center text-gray-500">
                        No hay solicitudes pendientes
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = solicitudes.map(s => `
            <tr class="hover:bg-gray-50 transition-colors ${s.estado === 'pendiente' ? 'bg-yellow-50' : ''}">
                <td class="px-6 py-4">
                    <div class="flex items-center gap-3">
                        <div class="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center text-[#f4a4b4]">
                            <span class="material-symbols-outlined">store</span>
                        </div>
                        <div>
                            <div class="font-medium text-gray-900">${s.nombre_negocio}</div>
                            <div class="text-xs text-gray-500">${s.propietario}</div>
                        </div>
                    </div>
                </td>
                <td class="px-6 py-4">
                    <div class="text-sm">
                        <div>${s.email}</div>
                        <div class="text-xs text-gray-500">${s.telefono}</div>
                    </div>
                </td>
                <td class="px-6 py-4">
                    <div class="text-sm">
                        <div>${s.ciudad}</div>
                        <div class="text-xs text-gray-500">${s.direccion ? s.direccion.substring(0, 30) + '...' : ''}</div>
                    </div>
                </td>
                <td class="px-6 py-4">
                    <span class="px-3 py-1 ${s.estado === 'pendiente' ? 'bg-yellow-100 text-yellow-700' : 
                                             s.estado === 'aprobada' ? 'bg-green-100 text-green-700' : 
                                             'bg-red-100 text-red-700'} rounded-full text-xs font-bold">
                        ${s.estado.charAt(0).toUpperCase() + s.estado.slice(1)}
                    </span>
                </td>
                <td class="px-6 py-4">
                    ${s.estado === 'pendiente' ? `
                        <div class="flex gap-2">
                            <button class="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-bold transition-all" onclick="SolicitudManager.aprobarSolicitud(${s.id})">
                                Aprobar
                            </button>
                            <button class="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg text-sm font-bold transition-all" onclick="SolicitudManager.rechazarSolicitud(${s.id})">
                                Rechazar
                            </button>
                        </div>
                    ` : `
                        <span class="text-sm text-gray-400">${s.estado === 'aprobada' ? '✅ Aprobada' : '❌ Rechazada'}</span>
                    `}
                </td>
            </tr>
        `).join('');
    },

    async aprobarSolicitud(id) {
        if (!confirm('¿Estás seguro de aprobar esta solicitud? Se creará una empresa y se asignará rol de socio.')) return;
        
        try {
            const response = await fetch(`/api/solicitudes/${id}/aprobar`, {
                method: 'PUT'
            });
            
            if (response.ok) {
                Utils.showToast('✅ Solicitud aprobada. Empresa creada.', 'success');
                this.cargarSolicitudes();
            } else {
                const error = await response.json();
                Utils.showToast(error.error || 'Error al aprobar solicitud', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            Utils.showToast('Error de conexión', 'error');
        }
    },

    async rechazarSolicitud(id) {
        if (!confirm('¿Estás seguro de rechazar esta solicitud?')) return;
        
        try {
            const response = await fetch(`/api/solicitudes/${id}/rechazar`, {
                method: 'PUT'
            });
            
            if (response.ok) {
                Utils.showToast('Solicitud rechazada', 'info');
                this.cargarSolicitudes();
            } else {
                Utils.showToast('Error al rechazar solicitud', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            Utils.showToast('Error de conexión', 'error');
        }
    }
};

// ===== FUNCIÓN PARA GUARDAR PERFIL =====
async function saveProfile(event) {
    event.preventDefault();
    
    const currentUser = await AuthManager.getCurrentUser();
    if (!currentUser) {
        Utils.showToast('Debes iniciar sesión', 'error');
        return;
    }
    
    const updatedUser = {
        nombre: document.getElementById('profile-name').value,
        correo: document.getElementById('profile-email').value,
        telefono: document.getElementById('profile-phone').value
    };
    
    try {
        const response = await fetch(`/api/usuarios/${currentUser.id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(updatedUser)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            const newUserData = { ...currentUser, ...updatedUser };
            localStorage.setItem('localmarket_user', JSON.stringify(newUserData));
            
            document.getElementById('sidebar-user-name').textContent = newUserData.nombre;
            document.getElementById('sidebar-user-email').textContent = newUserData.correo;
            
            Utils.showToast('✅ Perfil actualizado correctamente', 'success');
        } else {
            Utils.showToast(data.error || 'Error al actualizar perfil', 'error');
        }
    } catch (error) {
        console.error('Error updating profile:', error);
        Utils.showToast('Error al actualizar perfil', 'error');
    }
}

// ===== FUNCIÓN PARA SUBIR FOTO =====
async function uploadPhoto(input) {
    if (!input.files || !input.files[0]) return;
    
    const currentUser = await AuthManager.getCurrentUser();
    if (!currentUser) return;
    
    const formData = new FormData();
    formData.append('foto', input.files[0]);
    formData.append('usuario_id', currentUser.id);
    
    try {
        Utils.showToast('Subiendo foto...', 'info');
        
        const response = await fetch('/api/upload/perfil', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentUser.foto_url = data.foto_url;
            localStorage.setItem('localmarket_user', JSON.stringify(currentUser));
            Utils.updateAvatar();
            Utils.showToast('✅ Foto actualizada correctamente');
        } else {
            Utils.showToast(data.error || 'Error al subir foto', 'error');
        }
    } catch (error) {
        console.error('Error uploading photo:', error);
        Utils.showToast('Error de conexión', 'error');
    }
}

// ===== FUNCIÓN PARA MANEJAR REGISTRO =====
async function handleRegister(event) {
    event.preventDefault();
    
    const btn = document.getElementById('registerBtn');
    const originalText = btn ? btn.innerHTML : '';
    
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="material-symbols-outlined animate-spin">refresh</span> Registrando...';
    }
    
    const nombre = document.getElementById('nombre')?.value;
    const email = document.getElementById('email')?.value;
    const telefono = document.getElementById('telefono')?.value;
    const password = document.getElementById('password')?.value;
    const confirmPassword = document.getElementById('confirm_password')?.value;
    
    if (!nombre || !email || !telefono || !password || !confirmPassword) {
        Utils.showToast('Por favor completa todos los campos', 'error');
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
        return;
    }
    
    if (password !== confirmPassword) {
        Utils.showToast('Las contraseñas no coinciden', 'error');
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
        return;
    }
    
    if (password.length < 6) {
        Utils.showToast('La contraseña debe tener al menos 6 caracteres', 'error');
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
        return;
    }
    
    try {
        const response = await fetch('/api/registro', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ nombre, email, telefono, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            localStorage.setItem('localmarket_user', JSON.stringify(data));
            Utils.showToast('✅ ¡Registro exitoso!', 'success');
            
            setTimeout(() => {
                window.location.href = 'mi_perfil.html';
            }, 1500);
        } else {
            Utils.showToast(data.error || 'Error al registrar', 'error');
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = originalText;
            }
        }
        
    } catch (error) {
        console.error('❌ Error en registro:', error);
        Utils.showToast('Error de conexión con el servidor', 'error');
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    }
}

// ===== FUNCIÓN PARA MANEJAR LOGIN =====
async function handleLogin(event) {
    event.preventDefault();
    
    const btn = document.getElementById('loginBtn');
    const originalText = btn ? btn.innerHTML : '';
    
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="material-symbols-outlined animate-spin">refresh</span> Iniciando...';
    }
    
    const email = document.getElementById('email')?.value;
    const password = document.getElementById('password')?.value;
    
    if (!email || !password) {
        Utils.showToast('Por favor completa todos los campos', 'error');
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
        return;
    }
    
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            localStorage.setItem('localmarket_user', JSON.stringify(data));
            Utils.showToast('👋 ¡Bienvenido de vuelta!', 'success');
            
            setTimeout(() => {
                if (data.rol === 'administrador') {
                    window.location.href = 'panel_admin.html';
                } else if (data.rol === 'socio') {
                    window.location.href = 'panel_empresa.html';
                } else {
                    window.location.href = 'mi_perfil.html';
                }
            }, 1000);
        } else {
            Utils.showToast(data.error || 'Credenciales inválidas', 'error');
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = originalText;
            }
        }
        
    } catch (error) {
        console.error('❌ Error en login:', error);
        Utils.showToast('Error de conexión con el servidor', 'error');
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    }
}

// ===== FUNCIÓN PARA VERIFICAR ACCESO =====
function checkAccess(requiredRole = null) {
    const user = Utils.getStorage(CONFIG.STORAGE_KEYS.USER);
    
    if (!user) {
        Utils.showToast('Por favor inicia sesión primero', 'info');
        setTimeout(() => Utils.navigateTo('inicio_secion.html'), 1500);
        return false;
    }
    
    if (requiredRole && user.rol !== requiredRole) {
        Utils.showToast('No tienes permisos para acceder a esta página', 'error');
        setTimeout(() => {
            if (user.rol === 'administrador') {
                Utils.navigateTo('panel_admin.html');
            } else if (user.rol === 'socio') {
                Utils.navigateTo('panel_empresa.html');
            } else {
                Utils.navigateTo('inicio.html');
            }
        }, 1500);
        return false;
    }
    
    return true;
}

// ===== FUNCIONES PARA GESTIÓN DE DIRECCIONES =====
function loadAddresses(direcciones) {
    const container = document.getElementById('addresses-container');
    if (!container) return;
    
    try {
        const addresses = typeof direcciones === 'string' ? JSON.parse(direcciones) : direcciones;
        
        if (!addresses || addresses.length === 0) {
            container.innerHTML = '<div class="col-span-full text-center text-slate-500 py-8">No tienes direcciones guardadas</div>';
            return;
        }
        
        container.innerHTML = addresses.map((addr, index) => `
            <div class="border border-slate-200 dark:border-slate-600 p-5 rounded-xl flex flex-col gap-2 relative dark:bg-slate-700/30">
                ${addr.predeterminada ? '<span class="absolute top-4 right-4 bg-primary text-dark-green text-[10px] px-2 py-0.5 rounded-full font-bold">PREDETERMINADA</span>' : ''}
                <h4 class="font-bold text-slate-900 dark:text-white flex items-center gap-2">
                    <span class="material-symbols-outlined text-lg">${addr.tipo === 'Casa' ? 'home' : addr.tipo === 'Oficina' ? 'work' : 'location_on'}</span>
                    ${addr.tipo || 'Dirección'}
                </h4>
                <p class="text-sm text-slate-600 dark:text-slate-400">${addr.direccion}<br/>${addr.ciudad || ''}</p>
                <div class="flex gap-4 mt-4 text-xs font-bold uppercase tracking-tight">
                    ${!addr.predeterminada ? `<button class="text-verde-profundo dark:text-primary hover:underline" onclick="setDefaultAddress(${index})">Establecer como predeterminada</button>` : ''}
                    <button class="text-verde-profundo dark:text-primary hover:underline" onclick="editAddress(${index})">Editar</button>
                    <button class="text-slate-400 hover:text-red-500" onclick="deleteAddress(${index})">Eliminar</button>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error loading addresses:', error);
    }
}

function setDefaultAddress(index) {
    const currentUser = Utils.getStorage(CONFIG.STORAGE_KEYS.USER);
    if (!currentUser) return;
    
    let addresses = currentUser.direcciones;
    if (typeof addresses === 'string') {
        try {
            addresses = JSON.parse(addresses);
        } catch {
            addresses = [];
        }
    }
    
    addresses.forEach(addr => {
        addr.predeterminada = false;
    });
    
    if (addresses[index]) {
        addresses[index].predeterminada = true;
    }
    
    currentUser.direcciones = addresses;
    localStorage.setItem(CONFIG.STORAGE_KEYS.USER, JSON.stringify(currentUser));
    
    loadAddresses(addresses);
    Utils.showToast('📍 Dirección predeterminada actualizada', 'success');
}

function addNewAddress() {
    const currentUser = Utils.getStorage(CONFIG.STORAGE_KEYS.USER);
    if (!currentUser) return;
    
    const tipo = prompt('Tipo de dirección (Casa/Oficina/Otro):', 'Casa');
    if (!tipo) return;
    
    const direccion = prompt('Dirección:', '');
    if (!direccion) return;
    
    const ciudad = prompt('Ciudad:', '');
    if (!ciudad) return;
    
    let addresses = currentUser.direcciones || [];
    if (typeof addresses === 'string') {
        try {
            addresses = JSON.parse(addresses);
        } catch {
            addresses = [];
        }
    }
    
    addresses.push({ tipo, direccion, ciudad, predeterminada: addresses.length === 0 });
    currentUser.direcciones = addresses;
    
    localStorage.setItem(CONFIG.STORAGE_KEYS.USER, JSON.stringify(currentUser));
    loadAddresses(addresses);
    Utils.showToast('✅ Dirección agregada correctamente', 'success');
}

function editAddress(index) {
    const currentUser = Utils.getStorage(CONFIG.STORAGE_KEYS.USER);
    if (!currentUser) return;
    
    let addresses = currentUser.direcciones || [];
    if (typeof addresses === 'string') {
        try {
            addresses = JSON.parse(addresses);
        } catch {
            addresses = [];
        }
    }
    
    const addr = addresses[index];
    
    if (!addr) return;
    
    const nuevaDireccion = prompt('Editar dirección:', addr.direccion);
    if (nuevaDireccion) {
        addr.direccion = nuevaDireccion;
        currentUser.direcciones = addresses;
        localStorage.setItem(CONFIG.STORAGE_KEYS.USER, JSON.stringify(currentUser));
        loadAddresses(addresses);
        Utils.showToast('✅ Dirección actualizada', 'success');
    }
}

function deleteAddress(index) {
    if (!confirm('¿Estás seguro de eliminar esta dirección?')) return;
    
    const currentUser = Utils.getStorage(CONFIG.STORAGE_KEYS.USER);
    if (!currentUser) return;
    
    let addresses = currentUser.direcciones || [];
    if (typeof addresses === 'string') {
        try {
            addresses = JSON.parse(addresses);
        } catch {
            addresses = [];
        }
    }
    
    const wasDefault = addresses[index]?.predeterminada;
    addresses.splice(index, 1);
    
    if (wasDefault && addresses.length > 0) {
        addresses[0].predeterminada = true;
    }
    
    currentUser.direcciones = addresses;
    
    localStorage.setItem(CONFIG.STORAGE_KEYS.USER, JSON.stringify(currentUser));
    loadAddresses(addresses);
    Utils.showToast('✅ Dirección eliminada', 'success');
}

// ===== FUNCIÓN PARA SWITCH DE TABS =====
function switchTab(tabName) {
    document.querySelectorAll('.menu-btn').forEach(btn => {
        btn.classList.remove('active-menu');
        btn.classList.add('text-slate-300');
    });
    
    const activeBtn = document.querySelector(`[data-menu="${tabName}"]`);
    if (activeBtn) {
        activeBtn.classList.add('active-menu');
        activeBtn.classList.remove('text-slate-300');
    }
    
    document.querySelectorAll('.section-content').forEach(section => {
        section.classList.remove('active');
    });
    
    const activeSection = document.getElementById(`section-${tabName}`);
    if (activeSection) {
        activeSection.classList.add('active');
    }
}

// ===== INICIALIZACIÓN =====
document.addEventListener('DOMContentLoaded', async () => {
    const currentPage = Utils.getCurrentPage();
    console.log('Página actual:', currentPage);

    Utils.setupPasswordToggles();

    if (!currentPage.includes('panel_')) {
        await CartManager.updateCartBadge();
    }

    if (currentPage === 'inicio.html') {
        await ProductManager.loadProducts();
        await EmpresaManager.loadEmpresas();
        
        document.querySelectorAll('[data-filter]').forEach(btn => {
            btn.addEventListener('click', () => {
                const category = btn.getAttribute('data-filter');
                ProductManager.filterByCategory(category);
            });
        });

        const searchInput = document.querySelector('[data-search-input]');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                ProductManager.searchProducts(e.target.value);
            });
        }
    }

    if (currentPage === 'carrito.html') {
        const user = Utils.getStorage(CONFIG.STORAGE_KEYS.USER);
        
        if (!user) {
            Utils.showToast('⚠️ Debes iniciar sesión para ver tu carrito', 'info');
            setTimeout(() => Utils.navigateTo('inicio_secion.html'), 1500);
            return;
        }
        
        if (!Utils.validateUserHasAddress()) {
            const container = document.querySelector('[data-cart-container]');
            if (container) {
                container.innerHTML = `
                    <div class="text-center py-12">
                        <span class="material-symbols-outlined text-6xl text-slate-300 mb-4">location_off</span>
                        <h3 class="text-xl font-bold text-slate-600 mb-2">¡Falta tu dirección!</h3>
                        <p class="text-slate-400 mb-6">Para realizar un pedido necesitas tener una dirección registrada.</p>
                        <button onclick="Utils.navigateTo('mi_perfil.html')" class="inline-block bg-primary text-dark-green px-6 py-3 rounded-lg font-bold hover:bg-primary/90 transition-all">
                            Agregar dirección
                        </button>
                    </div>
                `;
                return;
            }
        }
        
        await CartManager.renderCartPage();
        
        document.querySelector('[data-clear-cart]')?.addEventListener('click', () => {
            CartManager.clearCart();
        });

        document.querySelector('[data-whatsapp-order]')?.addEventListener('click', () => {
            WhatsAppManager.sendOrder();
        });
    }

    if (currentPage === 'tiendas.html') {
        const urlParams = new URLSearchParams(window.location.search);
        const storeName = urlParams.get('store');
        
        if (storeName) {
            await StoreManager.loadStoreData(storeName);
        }

        document.querySelector('[data-whatsapp-contact]')?.addEventListener('click', () => {
            const storeName = document.getElementById('store-name')?.textContent || 'Tienda Local';
            const storePhone = document.getElementById('store-phone')?.textContent;
            WhatsAppManager.contactStore(storeName, storePhone);
        });
    }

    if (currentPage === 'mi_perfil.html') {
        const user = Utils.getStorage(CONFIG.STORAGE_KEYS.USER);
        
        if (!user) {
            Utils.showToast('Por favor inicia sesión primero', 'info');
            setTimeout(() => Utils.navigateTo('inicio_secion.html'), 1500);
            return;
        }
        
        if (user.rol === 'administrador') {
            window.location.href = 'panel_admin.html';
            return;
        }
        
        if (user.rol === 'socio') {
            window.location.href = 'panel_empresa.html';
            return;
        }
        
        await Utils.loadUserData();
        await OrderManager.loadUserOrders();
        
        if (user.direcciones) {
            loadAddresses(user.direcciones);
        }

        document.getElementById('photoInput')?.addEventListener('change', function() {
            uploadPhoto(this);
        });

        const profileForm = document.getElementById('profile-form');
        if (profileForm) {
            profileForm.removeEventListener('submit', saveProfile);
            profileForm.addEventListener('submit', saveProfile);
        }

        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.removeEventListener('click', AuthManager.logout);
            logoutBtn.addEventListener('click', AuthManager.logout);
        }
    }

    if (currentPage === 'inicio_secion.html') {
        const user = Utils.getStorage(CONFIG.STORAGE_KEYS.USER);
        if (user && user.id) {
            if (user.rol === 'administrador') {
                window.location.href = 'panel_admin.html';
            } else if (user.rol === 'socio') {
                window.location.href = 'panel_empresa.html';
            } else {
                window.location.href = 'mi_perfil.html';
            }
            return;
        }

        const loginForm = document.querySelector('form');
        if (loginForm) {
            loginForm.removeEventListener('submit', handleLogin);
            loginForm.addEventListener('submit', handleLogin);
        }
    }

    if (currentPage === 'registro_usuario.html') {
        const user = Utils.getStorage(CONFIG.STORAGE_KEYS.USER);
        if (user && user.id) {
            window.location.href = 'mi_perfil.html';
            return;
        }

        const registerForm = document.getElementById('registerForm');
        if (registerForm) {
            registerForm.removeEventListener('submit', handleRegister);
            registerForm.addEventListener('submit', handleRegister);
        }
    }

    if (currentPage === 'formulario_solicitud.html') {
        const form = document.getElementById('seller-request-form');
        if (form) {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const formData = {
                    nombre_negocio: document.getElementById('business-name').value,
                    propietario: document.getElementById('owner-name').value,
                    email: document.getElementById('email').value,
                    telefono: document.getElementById('phone').value,
                    ciudad: document.getElementById('city').value,
                    direccion: document.getElementById('direccion')?.value || '',
                    descripcion: document.getElementById('description').value
                };

                await SolicitudManager.enviarSolicitud(formData);
            });
        }
    }

    if (currentPage === 'panel_admin.html') {
        if (!checkAccess('administrador')) return;
        const response = await fetch('/api/solicitudes');
        const solicitudes = await response.json();
        SolicitudManager.renderSolicitudes(solicitudes);
    }

    if (currentPage === 'panel_empresa.html' || currentPage === 'panel_empresas.html') {
        if (!checkAccess('socio')) return;
        
        const user = await AuthManager.getCurrentUser();
        if (user && user.empresa_id) {
            const response = await fetch(`/api/empresas/${user.empresa_id}/stats`);
            const stats = await response.json();
            
            document.getElementById('stats-productos').textContent = stats.productos || 0;
            document.getElementById('stats-categorias').textContent = stats.categorias || 0;
            document.getElementById('stats-ventas').textContent = stats.ventas || 0;
        }
    }

    if (!currentPage.includes('panel_')) {
        window.addEventListener('cartUpdated', async () => {
            await CartManager.updateCartBadge();
        });
    }
});

// Función global de escape HTML
if (typeof window.escapeHtml !== 'function') {
    window.escapeHtml = function(str) {
        if (!str) return '';
        return str.replace(/[&<>]/g, function(m) {
            if (m === '&') return '&amp;';
            if (m === '<') return '&lt;';
            if (m === '>') return '&gt;';
            return m;
        });
    };
}

// Hacer funciones globales
window.CartManager = CartManager;
window.AuthManager = AuthManager;
window.Utils = Utils;
window.WhatsAppManager = WhatsAppManager;
window.ProductManager = ProductManager;
window.StoreManager = StoreManager;
window.OrderManager = OrderManager;
window.EmpresaManager = EmpresaManager;
window.SolicitudManager = SolicitudManager;
window.saveProfile = saveProfile;
window.uploadPhoto = uploadPhoto;
window.handleRegister = handleRegister;
window.handleLogin = handleLogin;
window.switchTab = switchTab;
window.addNewAddress = addNewAddress;
window.editAddress = editAddress;
window.deleteAddress = deleteAddress;
window.setDefaultAddress = setDefaultAddress;
window.loadAddresses = loadAddresses;
window.checkAccess = checkAccess;