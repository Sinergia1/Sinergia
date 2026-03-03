// scripts.js - Funcionalidad completa para LocalMarket

// ===== CONFIGURACIÓN GLOBAL =====
const CONFIG = {
    WHATSAPP_NUMBER: '521234567890',
    STORAGE_KEYS: {
        CART: 'localmarket_cart',
        USER: 'localmarket_user',
        THEME: 'localmarket_theme',
        PRODUCTS: 'localmarket_products',
        ORDERS: 'localmarket_orders',
        ADDRESSES: 'localmarket_addresses'
    }
};

// ===== UTILIDADES =====
const Utils = {
    formatPrice(price, currency = 'Q') {
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
    }
};

// ===== MANEJO DEL CARRITO =====
const CartManager = {
    getCart() {
        const defaultCart = { items: [], total: 0, subtotal: 0, shipping: 35 };
        return Utils.getStorage(CONFIG.STORAGE_KEYS.CART) || defaultCart;
    },

    addItem(product) {
        const cart = this.getCart();
        const productWithId = {
            ...product,
            id: product.id || Utils.generateId()
        };
        
        const existingItem = cart.items.find(item => item.id === productWithId.id);
        
        if (existingItem) {
            existingItem.quantity += product.quantity || 1;
        } else {
            cart.items.push({
                ...productWithId,
                quantity: product.quantity || 1
            });
        }
        
        this.updateCartTotals(cart);
        Utils.setStorage(CONFIG.STORAGE_KEYS.CART, cart);
        this.updateCartBadge();
        Utils.showToast('✅ Producto agregado al carrito');
        
        // Disparar evento para actualizar otras páginas
        window.dispatchEvent(new Event('cartUpdated'));
        return cart;
    },

    updateQuantity(productId, change) {
        const cart = this.getCart();
        const item = cart.items.find(i => i.id === productId);
        
        if (item) {
            item.quantity = Math.max(1, (item.quantity || 1) + change);
        }
        
        this.updateCartTotals(cart);
        Utils.setStorage(CONFIG.STORAGE_KEYS.CART, cart);
        this.updateCartBadge();
        this.renderCartPage();
        Utils.showToast('🔄 Cantidad actualizada');
        
        window.dispatchEvent(new Event('cartUpdated'));
        return cart;
    },

    removeItem(productId) {
        const cart = this.getCart();
        cart.items = cart.items.filter(i => i.id !== productId);
        this.updateCartTotals(cart);
        Utils.setStorage(CONFIG.STORAGE_KEYS.CART, cart);
        this.updateCartBadge();
        this.renderCartPage();
        Utils.showToast('🗑️ Producto eliminado');
        
        window.dispatchEvent(new Event('cartUpdated'));
    },

    clearCart() {
        Utils.setStorage(CONFIG.STORAGE_KEYS.CART, { items: [], total: 0, subtotal: 0, shipping: 35 });
        this.updateCartBadge();
        this.renderCartPage();
        Utils.showToast('🧹 Carrito vaciado');
        
        window.dispatchEvent(new Event('cartUpdated'));
    },

    updateCartTotals(cart) {
        cart.subtotal = cart.items.reduce((sum, item) => sum + (item.price * item.quantity), 0);
        cart.shipping = cart.subtotal > 0 ? 35 : 0;
        cart.total = cart.subtotal + cart.shipping;
        return cart;
    },

    updateCartBadge() {
        const cart = this.getCart();
        const cartButtons = document.querySelectorAll('[data-cart-badge]');
        const totalItems = cart.items.reduce((sum, item) => sum + item.quantity, 0);
        
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

    renderCartPage() {
        const tableBody = document.querySelector('[data-cart-table-body]');
        const cartContainer = document.querySelector('[data-cart-container]');
        const cartCount = document.querySelector('[data-cart-count]');
        
        if (!tableBody && !cartContainer) return;

        const cart = this.getCart();
        
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
                                <img class="h-full w-full object-cover" src="${item.image || 'https://via.placeholder.com/100'}" alt="${item.name}">
                            </div>
                            <div>
                                <p class="font-bold text-dark-green text-lg">${item.name}</p>
                                <p class="text-sm text-slate-500">Marca: ${item.brand || 'LocalMarket'}</p>
                                <p class="text-primary font-semibold mt-1">${Utils.formatPrice(item.price)}</p>
                            </div>
                        </div>
                    </td>
                    <td class="px-6 py-6">
                        <div class="flex items-center justify-center">
                            <div class="flex items-center border border-slate-200 dark:border-slate-600 rounded-lg overflow-hidden">
                                <button class="px-3 py-1 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors" onclick="CartManager.updateQuantity('${item.id}', -1)">
                                    <span class="material-symbols-outlined text-sm">remove</span>
                                </button>
                                <span class="px-4 py-1 text-sm font-bold min-w-[40px] text-center">${item.quantity}</span>
                                <button class="px-3 py-1 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors" onclick="CartManager.updateQuantity('${item.id}', 1)">
                                    <span class="material-symbols-outlined text-sm">add</span>
                                </button>
                            </div>
                        </div>
                    </td>
                    <td class="px-6 py-6 text-right">
                        <span class="font-bold text-dark-green">${Utils.formatPrice(item.price * item.quantity)}</span>
                    </td>
                    <td class="px-6 py-6 text-right">
                        <button class="text-slate-400 hover:text-red-500 transition-colors p-2" onclick="CartManager.removeItem('${item.id}')">
                            <span class="material-symbols-outlined">delete</span>
                        </button>
                    </td>
                </tr>
            `).join('');
        }

        this.updateCartSummary();
    },

    updateCartSummary() {
        const subtotalEl = document.querySelector('[data-cart-subtotal]');
        const shippingEl = document.querySelector('[data-cart-shipping]');
        const totalEl = document.querySelector('[data-cart-total]');
        
        if (!subtotalEl) return;

        const cart = this.getCart();
        subtotalEl.textContent = Utils.formatPrice(cart.subtotal || 0);
        if (shippingEl) shippingEl.textContent = Utils.formatPrice(cart.shipping || 0);
        if (totalEl) totalEl.textContent = Utils.formatPrice(cart.total || 0);
    }
};

// ===== AUTENTICACIÓN =====
const AuthManager = {
    getCurrentUser() {
        return Utils.getStorage(CONFIG.STORAGE_KEYS.USER);
    },

    isLoggedIn() {
        return !!this.getCurrentUser();
    },

    login(email, password) {
        try {
            const mockUser = {
                id: Utils.generateId(),
                name: 'Carlos Rodríguez',
                email: email,
                memberSince: 'Enero 2024',
                phone: '+34 600 000 000',
                avatar: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBdgxuOYEXDKx-zu_UatR-_EC6kmQZpsszFdVsVsptxJeiUEOGKE-5RMXZRQmUVpOMnJ3JMmw3T1-w46MUkvnki1UiN9qmZ5gkaEV3gf09gpXbgQcAt1x-yE5HyzaYYN6l7yTix2KLg_IRJzRkkw-yaga-fbEDEEP772VfD2rMAvrGQl1Z4Nxk3Gd8UIL0i7xwWJ4ODnlVWQAy0bix8j4uppG5vBUBzuh9V-TPa5Fj6KfcGPSGtu6t_gjl2XT08I0QRneLFrdURi60H'
            };
            
            Utils.setStorage(CONFIG.STORAGE_KEYS.USER, mockUser);
            Utils.showToast('👋 ¡Bienvenido de vuelta!');
            
            setTimeout(() => {
                Utils.navigateTo('inicio.html');
            }, 1000);
            
            return mockUser;
        } catch (error) {
            Utils.showToast('❌ Error al iniciar sesión', 'error');
            throw error;
        }
    },

    register(userData) {
        try {
            Utils.showToast('✅ Registro exitoso. Por favor inicia sesión.');
            setTimeout(() => {
                Utils.navigateTo('inicio_secion.html');
            }, 1500);
            return true;
        } catch (error) {
            Utils.showToast('❌ Error al registrar', 'error');
            throw error;
        }
    },

    logout() {
        localStorage.removeItem(CONFIG.STORAGE_KEYS.USER);
        Utils.showToast('👋 Sesión cerrada');
        setTimeout(() => {
            Utils.navigateTo('inicio.html');
        }, 1000);
    },

    updateProfile(profileData) {
        const currentUser = this.getCurrentUser();
        if (currentUser) {
            const updatedUser = { ...currentUser, ...profileData };
            Utils.setStorage(CONFIG.STORAGE_KEYS.USER, updatedUser);
            Utils.showToast('✅ Perfil actualizado');
            return updatedUser;
        }
    },

    loadProfileData() {
        const user = this.getCurrentUser();
        if (!user) return;

        const nameInput = document.getElementById('profile-name');
        const emailInput = document.getElementById('profile-email');
        const phoneInput = document.getElementById('profile-phone');

        if (nameInput) nameInput.value = user.name || '';
        if (emailInput) emailInput.value = user.email || '';
        if (phoneInput) phoneInput.value = user.phone || '';
    }
};

// ===== MANEJO DE DIRECCIONES =====
const AddressManager = {
    getAddresses() {
        return Utils.getStorage(CONFIG.STORAGE_KEYS.ADDRESSES) || [
            {
                id: '1',
                type: 'Casa',
                address: 'Calle Mayor 123, 4ºB',
                city: '28001 Madrid, España',
                isDefault: true
            },
            {
                id: '2',
                type: 'Oficina',
                address: 'Av. de la Castellana 50',
                city: '28046 Madrid, España',
                isDefault: false
            }
        ];
    },

    renderAddresses() {
        const container = document.querySelector('.grid.grid-cols-1.md\\:grid-cols-2.gap-4');
        if (!container) return;

        const addresses = this.getAddresses();
        
        container.innerHTML = addresses.map(addr => `
            <div class="${addr.isDefault ? 'border-2 border-primary/20 bg-primary/5' : 'border border-slate-200'} p-5 rounded-xl flex flex-col gap-2 relative">
                ${addr.isDefault ? '<span class="absolute top-4 right-4 bg-primary text-white text-[10px] px-2 py-0.5 rounded-full font-bold">PREDETERMINADA</span>' : ''}
                <h4 class="font-bold text-slate-900 flex items-center gap-2">
                    <span class="material-symbols-outlined text-lg">${addr.type === 'Casa' ? 'home' : 'work'}</span>
                    ${addr.type}
                </h4>
                <p class="text-sm text-slate-600">${addr.address}<br/>${addr.city}</p>
                <div class="flex gap-4 mt-4 text-xs font-bold uppercase tracking-tight">
                    <button class="text-verde-profundo hover:underline" onclick="AddressManager.editAddress('${addr.id}')">Editar</button>
                    <button class="text-slate-400 hover:text-red-500" onclick="AddressManager.deleteAddress('${addr.id}')">Eliminar</button>
                    ${!addr.isDefault ? '<button class="text-primary hover:underline" onclick="AddressManager.setDefault(\'' + addr.id + '\')">Predeterminar</button>' : ''}
                </div>
            </div>
        `).join('');
    },

    addAddress(address) {
        const addresses = this.getAddresses();
        const newAddress = {
            ...address,
            id: Utils.generateId(),
            isDefault: addresses.length === 0
        };
        addresses.push(newAddress);
        Utils.setStorage(CONFIG.STORAGE_KEYS.ADDRESSES, addresses);
        this.renderAddresses();
        Utils.showToast('✅ Dirección agregada');
    },

    deleteAddress(id) {
        let addresses = this.getAddresses();
        addresses = addresses.filter(a => a.id !== id);
        if (addresses.length > 0 && !addresses.some(a => a.isDefault)) {
            addresses[0].isDefault = true;
        }
        Utils.setStorage(CONFIG.STORAGE_KEYS.ADDRESSES, addresses);
        this.renderAddresses();
        Utils.showToast('🗑️ Dirección eliminada');
    },

    setDefault(id) {
        const addresses = this.getAddresses();
        addresses.forEach(a => a.isDefault = (a.id === id));
        Utils.setStorage(CONFIG.STORAGE_KEYS.ADDRESSES, addresses);
        this.renderAddresses();
        Utils.showToast('⭐ Dirección predeterminada actualizada');
    },

    editAddress(id) {
        const address = this.getAddresses().find(a => a.id === id);
        if (address) {
            // Aquí iría un modal de edición
            Utils.showToast('Función de edición próximamente', 'info');
        }
    }
};

// ===== MANEJO DE PEDIDOS =====
const OrderManager = {
    getOrders() {
        return Utils.getStorage(CONFIG.STORAGE_KEYS.ORDERS) || [
            { id: '#ART-8942', date: '12 Feb, 2024', total: 45.50, status: 'Entregado' },
            { id: '#ART-8821', date: '05 Feb, 2024', total: 120.00, status: 'En camino' }
        ];
    },

    renderOrders() {
        const tbody = document.querySelector('tbody');
        if (!tbody) return;

        const orders = this.getOrders();
        
        tbody.innerHTML = orders.map(order => `
            <tr class="border-b border-slate-50">
                <td class="py-4 font-medium text-slate-900">${order.id}</td>
                <td class="py-4 text-slate-600">${order.date}</td>
                <td class="py-4 text-slate-900 font-semibold">${Utils.formatPrice(order.total)}</td>
                <td class="py-4">
                    <span class="px-3 py-1 ${order.status === 'Entregado' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'} rounded-full text-xs font-bold">${order.status}</span>
                </td>
            </tr>
        `).join('');
    },

    createOrder(cart) {
        const order = {
            id: `#ART-${Math.floor(Math.random() * 10000)}`,
            date: new Date().toLocaleDateString('es-ES', { day: '2-digit', month: 'short', year: 'numeric' }),
            total: cart.total,
            status: 'Pendiente',
            items: cart.items
        };

        const orders = this.getOrders();
        orders.unshift(order);
        Utils.setStorage(CONFIG.STORAGE_KEYS.ORDERS, orders);
        return order;
    }
};

// ===== WHATSAPP INTEGRATION =====
const WhatsAppManager = {
    sendOrder(cart) {
        if (!cart || cart.items.length === 0) {
            Utils.showToast('❌ El carrito está vacío', 'error');
            return;
        }

        const itemsList = cart.items.map(item => 
            `• ${item.name} x${item.quantity} - ${Utils.formatPrice(item.price * item.quantity)}`
        ).join('\n');

        const message = encodeURIComponent(
            `🛍️ *Nuevo pedido LocalMarket*\n\n` +
            `*Productos:*\n${itemsList}\n\n` +
            `*Subtotal:* ${Utils.formatPrice(cart.subtotal)}\n` +
            `*Envío:* ${Utils.formatPrice(cart.shipping)}\n` +
            `*Total:* ${Utils.formatPrice(cart.total)}\n\n` +
            `Por favor, confirma disponibilidad y método de pago.`
        );

        window.open(`https://wa.me/${CONFIG.WHATSAPP_NUMBER}?text=${message}`, '_blank');
        
        // Crear orden después de enviar por WhatsApp
        const order = OrderManager.createOrder(cart);
        Utils.showToast('✅ Pedido enviado por WhatsApp');
        
        // Limpiar carrito después de enviar el pedido
        setTimeout(() => {
            CartManager.clearCart();
        }, 1000);
    },

    contactStore(storeName) {
        const message = encodeURIComponent(
            `Hola, me interesan los productos de ${storeName}. ¿Podrías darme más información?`
        );
        window.open(`https://wa.me/${CONFIG.WHATSAPP_NUMBER}?text=${message}`, '_blank');
    }
};

// ===== FILTROS Y BÚSQUEDA =====
const FilterManager = {
    filterProducts(category) {
        const products = document.querySelectorAll('[data-product]');
        const categoryButtons = document.querySelectorAll('[data-filter]');
        
        categoryButtons.forEach(btn => {
            if (btn.getAttribute('data-filter') === category) {
                btn.classList.add('bg-mint-green', 'text-dark-green', 'font-bold');
                btn.classList.remove('hover:bg-slate-100', 'text-slate-600', 'font-medium');
            } else {
                btn.classList.remove('bg-mint-green', 'text-dark-green', 'font-bold');
                btn.classList.add('hover:bg-slate-100', 'text-slate-600', 'font-medium');
            }
        });

        products.forEach(product => {
            if (category === 'todos') {
                product.style.display = 'block';
            } else {
                const productCategory = product.getAttribute('data-category');
                product.style.display = productCategory === category ? 'block' : 'none';
            }
        });
    },

    searchProducts(query) {
        const products = document.querySelectorAll('[data-product]');
        const searchTerm = query.toLowerCase().trim();

        products.forEach(product => {
            const title = product.querySelector('[data-product-title], h4, h5')?.textContent.toLowerCase() || '';
            const brand = product.querySelector('[data-product-brand], .text-primary')?.textContent.toLowerCase() || '';
            
            if (title.includes(searchTerm) || brand.includes(searchTerm)) {
                product.style.display = 'block';
            } else {
                product.style.display = 'none';
            }
        });
    },

    sortProducts(sortBy) {
        const grid = document.getElementById('products-grid');
        if (!grid) return;

        const products = Array.from(grid.children);
        
        products.sort((a, b) => {
            const priceA = parseFloat(a.querySelector('[data-product-price]')?.textContent || '0');
            const priceB = parseFloat(b.querySelector('[data-product-price]')?.textContent || '0');
            
            if (sortBy === 'Precio: Menor a Mayor') {
                return priceA - priceB;
            } else if (sortBy === 'Precio: Mayor a Menor') {
                return priceB - priceA;
            }
            return 0;
        });

        grid.innerHTML = '';
        products.forEach(product => grid.appendChild(product));
    }
};

// ===== INICIALIZACIÓN =====
document.addEventListener('DOMContentLoaded', () => {
    const currentPage = Utils.getCurrentPage();

    // Inicializar badge del carrito
    CartManager.updateCartBadge();

    // Configurar navegación de enlaces
    document.querySelectorAll('a[href]').forEach(link => {
        link.addEventListener('click', (e) => {
            const href = link.getAttribute('href');
            if (href && !href.startsWith('http') && !href.startsWith('#')) {
                e.preventDefault();
                Utils.navigateTo(href);
            }
        });
    });

    // ===== PÁGINA: inicio.html =====
    if (currentPage === 'inicio.html') {
        // Filtros de categoría
        document.querySelectorAll('[data-filter]').forEach(btn => {
            btn.addEventListener('click', () => {
                const category = btn.getAttribute('data-filter');
                FilterManager.filterProducts(category);
            });
        });

        // Búsqueda
        const searchInput = document.querySelector('[data-search-input]');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                FilterManager.searchProducts(e.target.value);
            });
        }
    }

    // ===== PÁGINA: carrito.html =====
    if (currentPage === 'carrito.html') {
        CartManager.renderCartPage();
        
        // Botón limpiar carrito
        document.querySelector('[data-clear-cart]')?.addEventListener('click', () => {
            if (confirm('¿Estás seguro de vaciar el carrito?')) {
                CartManager.clearCart();
            }
        });

        // Botón WhatsApp
        document.querySelector('[data-whatsapp-order]')?.addEventListener('click', () => {
            WhatsAppManager.sendOrder(CartManager.getCart());
        });

        // Métodos de pago
        document.querySelectorAll('input[name="payment"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                Utils.showToast(`Método de pago seleccionado: ${e.target.closest('label').querySelector('.text-xs').textContent}`, 'info');
            });
        });
    }

    // ===== PÁGINA: mi perfil.html =====
    if (currentPage === 'mi perfil.html') {
        const user = AuthManager.getCurrentUser();
        
        if (!user) {
            Utils.showToast('Por favor inicia sesión primero', 'info');
            setTimeout(() => {
                Utils.navigateTo('inicio_secion.html');
            }, 1500);
            return;
        }

        // Cargar datos del perfil
        AuthManager.loadProfileData();

        // Cargar direcciones
        AddressManager.renderAddresses();

        // Cargar pedidos
        OrderManager.renderOrders();

        // Formulario de perfil
        const profileForm = document.querySelector('[data-profile-form]');
        if (profileForm) {
            profileForm.addEventListener('submit', (e) => {
                e.preventDefault();
                
                const profileData = {
                    name: document.getElementById('profile-name').value,
                    email: document.getElementById('profile-email').value,
                    phone: document.getElementById('profile-phone').value
                };
                
                AuthManager.updateProfile(profileData);
            });
        }

        // Cerrar sesión
        document.querySelector('[data-logout]')?.addEventListener('click', (e) => {
            e.preventDefault();
            if (confirm('¿Estás seguro de cerrar sesión?')) {
                AuthManager.logout();
            }
        });

        // Agregar dirección
        document.getElementById('add-address')?.addEventListener('click', () => {
            const type = prompt('Tipo de dirección (Casa/Oficina/Otro):', 'Casa');
            if (!type) return;
            
            const address = prompt('Dirección:', '');
            if (!address) return;
            
            const city = prompt('Ciudad:', '');
            if (!city) return;
            
            AddressManager.addAddress({
                type: type,
                address: address,
                city: city
            });
        });
    }

    // ===== PÁGINA: inicio de secion.html =====
    if (currentPage === 'inicio_secion.html') {
        const loginForm = document.querySelector('form');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => {
                e.preventDefault();
                const email = document.getElementById('email').value;
                const password = document.getElementById('password').value;
                
                if (!email || !password) {
                    Utils.showToast('Por favor completa todos los campos', 'error');
                    return;
                }
                
                AuthManager.login(email, password);
            });
        }

        // Toggle contraseña
        document.querySelector('[data-toggle-password]')?.addEventListener('click', () => {
            const input = document.getElementById('password');
            const icon = document.querySelector('[data-toggle-password] span');
            if (input.type === 'password') {
                input.type = 'text';
                icon.textContent = 'visibility_off';
            } else {
                input.type = 'password';
                icon.textContent = 'visibility';
            }
        });
    }

    // ===== PÁGINA: registro de usuario.html =====
    if (currentPage === 'registro de usuario.html') {
        const registerForm = document.querySelector('form');
        if (registerForm) {
            registerForm.addEventListener('submit', (e) => {
                e.preventDefault();
                
                const nombre = document.getElementById('nombre')?.value;
                const email = document.getElementById('email')?.value;
                const password = document.getElementById('password')?.value;
                const confirmPassword = document.getElementById('confirm_password')?.value;
                
                if (!nombre || !email || !password || !confirmPassword) {
                    Utils.showToast('Por favor completa todos los campos', 'error');
                    return;
                }
                
                if (password !== confirmPassword) {
                    Utils.showToast('Las contraseñas no coinciden', 'error');
                    return;
                }

                if (password.length < 6) {
                    Utils.showToast('La contraseña debe tener al menos 6 caracteres', 'error');
                    return;
                }

                const userData = {
                    name: nombre,
                    email: email,
                    password: password
                };

                AuthManager.register(userData);
            });
        }

        // Toggle contraseñas
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
    }

    // ===== PÁGINA: tiendas.html =====
    if (currentPage === 'tiendas.html') {
        // Contactar por WhatsApp
        document.querySelectorAll('[data-whatsapp-contact]').forEach(btn => {
            btn.addEventListener('click', () => {
                const storeName = document.querySelector('h2')?.textContent || 'Artesanías del Valle';
                WhatsAppManager.contactStore(storeName);
            });
        });

        // Ordenar productos
        const sortSelect = document.getElementById('sort-products');
        if (sortSelect) {
            sortSelect.addEventListener('change', (e) => {
                FilterManager.sortProducts(e.target.value);
            });
        }

        // Botón cargar más
        document.getElementById('load-more')?.addEventListener('click', () => {
            Utils.showToast('Función próximamente', 'info');
        });

        // Botón filtrar
        document.getElementById('filter-btn')?.addEventListener('click', () => {
            Utils.showToast('Filtros próximamente', 'info');
        });
    }

    // ===== CONFIGURACIÓN GLOBAL DE BOTONES AGREGAR AL CARRITO =====
    document.querySelectorAll('[data-add-to-cart]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const productCard = e.target.closest('[data-product]');
            
            if (productCard) {
                const titleEl = productCard.querySelector('[data-product-title], h4, h5');
                const priceEl = productCard.querySelector('[data-product-price]');
                const brandEl = productCard.querySelector('[data-product-brand], .text-primary');
                const imgEl = productCard.querySelector('img');
                
                const product = {
                    id: Utils.generateId(),
                    name: titleEl?.textContent?.trim() || 'Producto',
                    price: parseFloat(priceEl?.textContent?.replace(/[^0-9.]/g, '') || '0'),
                    image: imgEl?.src || '',
                    brand: brandEl?.textContent?.trim() || 'LocalMarket'
                };
                
                if (product.price > 0) {
                    CartManager.addItem(product);
                    
                    // Animación del botón
                    btn.innerHTML = '<span class="material-symbols-outlined text-[18px]">check</span> Agregado';
                    btn.style.backgroundColor = '#10b981';
                    setTimeout(() => {
                        btn.innerHTML = '<span class="material-symbols-outlined text-[18px]">add_shopping_cart</span> Agregar al carrito';
                        btn.style.backgroundColor = '';
                    }, 2000);
                } else {
                    Utils.showToast('Error: Precio no válido', 'error');
                }
            }
        });
    });

    // Escuchar eventos de actualización del carrito
    window.addEventListener('cartUpdated', () => {
        CartManager.updateCartBadge();
    });
});

// Hacer managers globales
window.CartManager = CartManager;
window.AuthManager = AuthManager;
window.Utils = Utils;
window.WhatsAppManager = WhatsAppManager;
window.AddressManager = AddressManager;
window.OrderManager = OrderManager;
window.FilterManager = FilterManager;