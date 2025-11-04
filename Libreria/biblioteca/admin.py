from django.contrib import admin
from .models import Categoria, Autor, Editorial, Libro, Cliente, Pedido, DetallePedido, PerfilUsuario, Boletin

@admin.register(Libro)
class LibroAdmin(admin.ModelAdmin):
    list_display = ("id", "titulo", "autor", "precio", "stock", "activo")
    list_filter = ("activo", "autor", "categorias")
    search_fields = ("titulo", "autor__nombre", "isbn")
    filter_horizontal = ("categorias",)

admin.site.register([Categoria, Autor, Editorial, Cliente, Pedido, DetallePedido, PerfilUsuario, Boletin])