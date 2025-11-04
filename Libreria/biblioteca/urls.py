from django.urls import path
from . import views

app_name = "biblioteca"

urlpatterns = [
    # Home
    path("", views.home, name="home"),

    # Libros (CRUD)
    path("libros/", views.lista_libros, name="libro_lista"),
    path("libros/nuevo/", views.crear_libro, name="libro_crear"),
    path("libros/<int:pk>/", views.detalle_libro, name="libro_detalle"),
    path("libros/<int:pk>/editar/", views.editar_libro, name="libro_editar"),
    path("libros/<int:pk>/eliminar/", views.eliminar_libro, name="libro_eliminar"),

    # Carrito y checkout
    path("carrito/", views.carrito, name="carrito"),
    path("carrito/agregar/<int:pk>/", views.agregar_al_carrito, name="agregar_al_carrito"),
    path("checkout/", views.checkout, name="checkout"),

    # Panel de ventas
    path("panel-ventas/", views.panel_ventas, name="panel_ventas"),
]