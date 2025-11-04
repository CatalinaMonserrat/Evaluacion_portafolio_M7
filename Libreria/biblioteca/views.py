from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, F
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Libro, Cliente, Pedido, DetallePedido
from .forms import LibroForm


# --------- Helpers (carrito en sesión) ---------
def _get_cart(request):
    """
    Estructura en sesión:
    request.session["cart"] = {
        str(libro_id): cantidad, ...
    }
    """
    cart = request.session.get("cart", {})
    return cart

def _save_cart(request, cart):
    request.session["cart"] = cart
    request.session.modified = True

def _cart_items_and_total(cart):
    """
    Devuelve (items, total) donde items es lista de diccionarios:
    {libro, cantidad, precio, subtotal}
    """
    items = []
    total = 0
    if not cart:
        return items, total
    libro_ids = [int(k) for k in cart.keys()]
    libros = {l.id: l for l in Libro.objects.filter(id__in=libro_ids)}
    for k, qty in cart.items():
        lid = int(k)
        libro = libros.get(lid)
        if not libro:
            continue
        precio = libro.precio
        subtotal = precio * qty
        items.append({"libro": libro, "cantidad": qty, "precio": precio, "subtotal": subtotal})
        total += subtotal
    return items, total


# --------- Páginas básicas ---------
def home(request):
    return render(request, "biblioteca/home.html")


def error_403(request, exception=None):
    return render(request, "403.html", status=403)

def error_404(request, exception=None):
    return render(request, "404.html", status=404)


# --------- Libros (CRUD) ---------
def lista_libros(request):
    q = request.GET.get("q", "").strip()
    qs = Libro.objects.all().order_by("-id")
    if q:
        qs = qs.filter(Q(titulo__icontains=q) | Q(isbn__icontains=q) | Q(autor__nombre__icontains=q))

    paginator = Paginator(qs, 12)  # 12 tarjetas por página
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "biblioteca/libro_list.html", {
        "libros": page_obj.object_list,
        "q": q,
        "page_obj": page_obj,
    })

def detalle_libro(request, pk):
    libro = get_object_or_404(Libro, pk=pk)
    return render(request, "biblioteca/libro_detail.html", {"libro": libro})

@login_required(login_url="/cuentas/login/")
def crear_libro(request):
    form = LibroForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Libro agregado correctamente.")
        return redirect("biblioteca:libro_lista")
    return render(request, "biblioteca/libro_form.html", {"form": form, "titulo": "Nuevo Libro"})

@login_required(login_url="/cuentas/login/")
def editar_libro(request, pk):
    libro = get_object_or_404(Libro, pk=pk)
    form = LibroForm(request.POST or None, instance=libro)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Libro actualizado correctamente.")
        return redirect("biblioteca:libro_lista")
    return render(request, "biblioteca/libro_form.html", {"form": form, "titulo": "Editar Libro"})

@login_required(login_url="/cuentas/login/")
def eliminar_libro(request, pk):
    libro = get_object_or_404(Libro, pk=pk)
    if request.method == "POST":
        libro.delete()
        messages.success(request, "Libro eliminado.")
        return redirect("biblioteca:libro_lista")
    return render(request, "biblioteca/libro_confirm_delete.html", {"obj": libro})


# --------- Carrito & Checkout ---------
def agregar_al_carrito(request, pk):
    """Agrega 1 unidad del libro al carrito y redirige al listado."""
    libro = get_object_or_404(Libro, pk=pk, activo=True)
    cart = _get_cart(request)
    cart[str(libro.id)] = cart.get(str(libro.id), 0) + 1
    _save_cart(request, cart)
    messages.success(request, f"Se agregó '{libro.titulo}' al carrito.")
    return redirect("biblioteca:libro_lista")

def carrito(request):
    cart = _get_cart(request)
    items, total = _cart_items_and_total(cart)
    ctx = {"items": items, "total": total}
    return render(request, "biblioteca/carrito.html", ctx)

def checkout(request):
    cart = _get_cart(request)
    items, total = _cart_items_and_total(cart)

    if request.method == "POST":
        nombre = request.POST.get("nombre")
        email = request.POST.get("email")

        if not items:
            messages.warning(request, "Tu carrito está vacío.")
            return redirect("biblioteca:carrito")

        # Cliente (simple: crea o usa el existente por email)
        cliente, _ = Cliente.objects.get_or_create(email=email, defaults={"nombre": nombre})

        # Pedido
        pedido = Pedido.objects.create(cliente=cliente, estado="pagado")

        # Detalles
        for it in items:
            DetallePedido.objects.create(
                pedido=pedido,
                libro=it["libro"],
                cantidad=it["cantidad"],
                precio_unitario=it["precio"],
            )
            # disminuye stock (opcional)
            it["libro"].stock = max(0, it["libro"].stock - it["cantidad"])
            it["libro"].save(update_fields=["stock"])

        # limpia carrito
        _save_cart(request, {})
        messages.success(request, f"Pedido #{pedido.id} registrado. ¡Gracias por tu compra!")
        return redirect("biblioteca:panel_ventas")

    ctx = {"items": items, "total": total}
    return render(request, "biblioteca/checkout.html", ctx)


# --------- Panel de ventas (resumen) ---------
@login_required(login_url="/cuentas/login/")
def panel_ventas(request):
    hoy = timezone.now().date()
    # ventas del día (suma de subtotales)
    ventas_hoy = (DetallePedido.objects
                  .filter(pedido__fecha__date=hoy)
                  .aggregate(m=Sum(F("cantidad") * F("precio_unitario")))["m"]) or 0

    unidades = (DetallePedido.objects
                .filter(pedido__fecha__date=hoy)
                .aggregate(u=Sum("cantidad"))["u"]) or 0

    # pedidos del mes
    primer_dia_mes = hoy.replace(day=1)
    pedidos_mes = Pedido.objects.filter(fecha__date__gte=primer_dia_mes).count()

    ctx = {"resumen": {
        "ventas_hoy": ventas_hoy,
        "unidades": unidades,
        "pedidos_mes": pedidos_mes,
    }}
    return render(request, "biblioteca/panel_ventas.html", ctx)