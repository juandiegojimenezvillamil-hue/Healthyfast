document.addEventListener("DOMContentLoaded", function () {
    const modalProducto = document.getElementById('modalProducto');
    let currentModalProduct = null;

    if (modalProducto) {
        modalProducto.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            if (!button) return;

            const id = button.getAttribute('data-id');
            const nombre = button.getAttribute('data-nombre') || 'Producto';
            const desc = button.getAttribute('data-desc') || 'Sin descripción disponible.';
            const precio = Number(button.getAttribute('data-precio') || 0);
            const stock = button.getAttribute('data-stock') || 0;
            const imagenUrl = button.getAttribute('data-imagen') || '';
            const categoria = button.getAttribute('data-categoria') || '';

            currentModalProduct = { id, nombre, precio, stock };

            document.getElementById('modalProductoTitulo').textContent = nombre;
            document.getElementById('modalProductoDesc').textContent = desc;
            document.getElementById('modalProductoPrecio').textContent = '$' + precio.toLocaleString('es-CO') + ' COP';
            document.getElementById('modalProductoStock').textContent = 'Stock: ' + stock + ' uds';
            
            const catEl = document.getElementById('modalProductoCategoria');
            if (catEl) catEl.textContent = categoria;

            const imagen = document.getElementById('modalProductoImagen');
            if (imagen) {
                imagen.src = imagenUrl;
                imagen.alt = nombre;
            }
        });

        const btnModalAgregar = document.getElementById('btnModalAgregarCarrito');
        if (btnModalAgregar) {
            btnModalAgregar.addEventListener('click', function () {
                if (currentModalProduct && currentModalProduct.id) {
                    agregarAlCarrito(currentModalProduct.id, currentModalProduct.nombre, currentModalProduct.precio);
                    const bsModal = bootstrap.Modal.getInstance(modalProducto);
                    if (bsModal) bsModal.hide();
                }
            });
        }
    }

    // 1. Quitar Loader animado al cargar la página
    const loader = document.getElementById("pantalla-loader");
    if (loader) {
        setTimeout(() => {
            loader.style.opacity = "0";
            loader.style.visibility = "hidden";
        }, 600);
    }

    // 2. Lógica nativa de alternancia de Modo Oscuro con persistencia
    const botonDark = document.getElementById("toggle-darkmode");
    const menuToggle = document.querySelector('.navbar-toggler');
    const menuNav = document.getElementById('navMenu');
    const TEMA_KEY = 'themeHealthyFast';

    function setMenuMovil(open) {
        if (!menuNav) return;
        menuNav.classList.toggle('show', open);
        menuNav.setAttribute('aria-expanded', String(open));
        if (menuToggle) menuToggle.setAttribute('aria-expanded', String(open));
    }

    if (menuToggle && menuNav) {
        menuToggle.addEventListener('click', function (event) {
            event.preventDefault();
            const estaAbierto = menuNav.classList.contains('show');
            setMenuMovil(!estaAbierto);
        });
    }

    document.addEventListener('click', function (event) {
        if (!menuNav || !menuToggle) return;

        const clicDentroMenu = menuNav.contains(event.target);
        const clicEnToggle = menuToggle.contains(event.target);

        if (menuNav.classList.contains('show') && !clicDentroMenu && !clicEnToggle) {
            setMenuMovil(false);
        }
    });

    function aplicarTema(tema) {
        if (tema === 'dark') {
            document.documentElement.setAttribute('data-theme', 'dark');
            if (botonDark) botonDark.innerHTML = '<i class="fa-solid fa-sun"></i>';
        } else {
            document.documentElement.removeAttribute('data-theme');
            if (botonDark) botonDark.innerHTML = '<i class="fa-solid fa-moon"></i>';
        }
    }

    function cargarTemaPreferido() {
        const temaGuardado = localStorage.getItem(TEMA_KEY);
        if (temaGuardado === 'dark') {
            aplicarTema('dark');
        } else {
            aplicarTema('light');
        }
    }

    if (botonDark) {
        cargarTemaPreferido();
        botonDark.addEventListener("click", () => {
            const temaActual = document.documentElement.getAttribute("data-theme");
            if (temaActual === "dark") {
                aplicarTema('light');
                localStorage.setItem(TEMA_KEY, 'light');
            } else {
                aplicarTema('dark');
                localStorage.setItem(TEMA_KEY, 'dark');
            }
        });
    }

    // 3. Sistema Scroll Reveal usando el API nativo de Navegadores
    const elementosReveal = document.querySelectorAll(".scroll-reveal");
    const observador = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = "1";
                entry.target.style.transform = "translateY(0)";
            }
        });
    }, { threshold: 0.1 });

    elementosReveal.forEach(el => {
        el.style.opacity = "0";
        el.style.transform = "translateY(30px)";
        el.style.transition = "all 0.6s ease-out";
        observador.observe(el);
    });

    cargarCarritoLocal();
    renderizarCarrito();

    const btnProcessOrder = document.getElementById('btn-process-order');
    if (btnProcessOrder) {
        btnProcessOrder.addEventListener('click', function () {
            if (carrito.length === 0) {
                showToast('El carrito está vacío. Agrega productos antes de pagar.', 'danger');
                return;
            }
            window.location.href = '/envio';
        });
    }
});

// 4. Lógica de Negocio del Carrito Reactivo Lateral
let carrito = [];
const STORAGE_KEY = 'carritoHealthyFast';

function cargarCarritoLocal() {
    const guardado = localStorage.getItem(STORAGE_KEY);
    if (guardado) {
        try {
            carrito = JSON.parse(guardado);
        } catch (error) {
            carrito = [];
        }
    }
}

function guardarCarritoLocal() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(carrito));
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast-notification');
    if (!toast) return;
    toast.textContent = message;
    toast.className = `toast-notification toast-${type} toast-show`;
    clearTimeout(window.toastTimeout);
    window.toastTimeout = setTimeout(() => {
        toast.classList.remove('toast-show');
    }, 3200);
}

function agregarAlCarrito(id, nombre, precio) {
    let existente = carrito.find(p => p.id === id);
    if (existente) {
        existente.cantidad++;
        showToast(`${nombre} agregado al carrito (${existente.cantidad} unidades).`, 'success');
    } else {
        carrito.push({ id: id, nombre: nombre, precio: precio, cantidad: 1 });
        showToast(`${nombre} agregado al carrito.`, 'success');
    }
    guardarCarritoLocal();
    renderizarCarrito();
}

function eliminarDelCarrito(id) {
    const indice = carrito.findIndex(item => String(item.id) === String(id));
    if (indice === -1) return;

    const productoEliminado = carrito.splice(indice, 1)[0];
    guardarCarritoLocal();
    renderizarCarrito();
    showToast(`${productoEliminado.nombre} eliminado del carrito.`, 'warning');
}

function renderizarCarrito() {
    const cuerpo = document.getElementById("items-carrito-render");
    const contador = document.getElementById("badge-contador");
    const totalText = document.getElementById("total-precio-render");

    if (!cuerpo || !contador || !totalText) return;
    
    if (carrito.length === 0) {
        cuerpo.innerHTML = '<p class="text-muted text-center py-4">Bolsa vacía.</p>';
        contador.innerText = "0";
        totalText.innerText = "$0 COP";
        return;
    }
    
    let html = "";
    let total = 0;
    let unidades = 0;
    
    carrito.forEach(item => {
        total += item.precio * item.cantidad;
        unidades += item.cantidad;
        html += `
            <div class="d-flex justify-content-between align-items-start mb-2 p-2 bg-light rounded text-dark">
                <div class="me-2">
                    <h6 class="m-0 small fw-bold">${item.nombre}</h6>
                    <small>${item.cantidad}x - $${item.precio.toLocaleString()} COP</small>
                </div>
                <div class="d-flex align-items-center gap-2">
                    <span class="badge bg-danger rounded-pill">$${(item.precio * item.cantidad).toLocaleString()}</span>
                    <button
                        type="button"
                        class="btn btn-sm btn-outline-danger btn-eliminar-item"
                        data-id="${item.id}"
                        aria-label="Eliminar ${item.nombre}"
                    >
                        <i class="fa-solid fa-trash"></i>
                    </button>
                </div>
            </div>`;
    });
    
    cuerpo.innerHTML = html;
    contador.innerText = unidades;
    totalText.innerText = `$${total.toLocaleString()} COP`;

    cuerpo.querySelectorAll('.btn-eliminar-item').forEach(boton => {
        boton.addEventListener('click', function () {
            eliminarDelCarrito(this.dataset.id);
        });
    });

    const totalPago = document.getElementById('total-pago-render');
    if (totalPago) {
        totalPago.innerText = `$${total.toLocaleString()} COP`;
    }
}

// 5. Rellenar modal único de edición antes de mostrar
document.addEventListener('DOMContentLoaded', function() {
    const formAgregar = document.getElementById('formAgregarProducto');
    const selectorImagen = document.getElementById('selectImagenProducto');
    const inputNombre = document.getElementById('inputNombreProducto');
    const selectCategoria = document.getElementById('selectCategoriaProducto');
    const selectSubcategoria = document.getElementById('selectSubcategoriaProducto');
    const inputPrecio = document.getElementById('inputPrecioProducto');
    const inputStock = document.getElementById('inputStockProducto');
    const textareaDescripcion = document.getElementById('textareaDescripcionProducto');

    if (formAgregar && selectorImagen) {
        const completarFormulario = (producto) => {
            if (!producto) return;
            if (inputNombre) inputNombre.value = producto.nombre || '';
            if (selectCategoria) selectCategoria.value = producto.categoria || 'body';
            if (selectSubcategoria) selectSubcategoria.value = producto.subcategoria || '';
            if (inputPrecio) inputPrecio.value = producto.precio || '';
            if (inputStock) inputStock.value = producto.stock || '';
            if (textareaDescripcion) textareaDescripcion.value = producto.desc || '';
        };

        selectorImagen.addEventListener('change', function () {
            const imagen = this.value;
            if (!imagen) {
                if (inputNombre) inputNombre.value = '';
                if (selectCategoria) selectCategoria.value = 'body';
                if (selectSubcategoria) selectSubcategoria.value = '';
                if (inputPrecio) inputPrecio.value = '';
                if (inputStock) inputStock.value = '';
                if (textareaDescripcion) textareaDescripcion.value = '';
                return;
            }

            fetch(`/admin/producto/auto?imagen=${encodeURI(imagen)}`)
                .then(response => response.json())
                .then(data => {
                    const producto = data && data.datos ? data.datos : null;
                    completarFormulario(producto);
                })
                .catch(() => {});
        });
    }

    var editarModal = document.getElementById('modalEditar');
    if (!editarModal) return;

    // Limpiar backdrops residuales
    function cleanupBackdrops() {
        document.querySelectorAll('.modal-backdrop').forEach(function(el){ el.remove(); });
        document.body.classList.remove('modal-open');
    }

    cleanupBackdrops();

    editarModal.addEventListener('show.bs.modal', function (event) {
        var button = event.relatedTarget; // Button that triggered the modal
        if (!button) return;

        var id = button.getAttribute('data-id');
        var nombre = button.getAttribute('data-nombre') || '';
        var categoria = button.getAttribute('data-categoria') || '';
        var precio = button.getAttribute('data-precio') || '';
        var stock = button.getAttribute('data-stock') || '';
        var desc = button.getAttribute('data-desc') || '';
        var imagen = button.getAttribute('data-imagen') || '';
        var subcategoria = button.getAttribute('data-subcategoria') || '';

        // Rellenar inputs
        document.getElementById('editNombre').value = nombre;
        document.getElementById('editCategoria').value = categoria;
        document.getElementById('editPrecio').value = precio;
        document.getElementById('editStock').value = stock;
        document.getElementById('editDesc').value = desc;
        document.getElementById('editImagen').value = imagen;
        document.getElementById('editSubcategoria').value = subcategoria;

        // Actualizar action del formulario
        var form = document.getElementById('formEditar');
        form.action = '/admin/producto/editar/' + id;
    });

    // Limpiar backdrops cuando el modal se oculta
    editarModal.addEventListener('hidden.bs.modal', function() {
        cleanupBackdrops();
    });

    // Asegurar que los botones de editar limpien backdrops antes de intentar abrir modal
    document.querySelectorAll('.edit-btn').forEach(function(btn){
        btn.addEventListener('click', function(){ cleanupBackdrops(); });
    });
});
