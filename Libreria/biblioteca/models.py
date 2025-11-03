from django.db import models
from django.contrib.auth.models import User

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre

class Autor(models.Model):
    nombre = models.CharField(max_length=120)
    email = models.EmailField(unique=True, blank=True, null=True)
    pais = models.CharField(max_length=80, blank=True)

    def __str__(self):
        return self.nombre

class Editorial(models.Model):
    nombre = models.CharField(max_length=120, unique=True)
    sitio_web = models.URLField(blank=True)

    def __str__(self):
        return self.nombre

class Libro(models.Model):
    titulo = models.CharField(max_length=200)
    autor = models.ForeignKey(Autor, on_delete=models.PROTECT, related_name="libros")  # 1–N
    editorial = models.ForeignKey(Editorial, on_delete=models.SET_NULL, null=True, blank=True)
    categorias = models.ManyToManyField(Categoria, blank=True)  # N–N
    isbn = models.CharField(max_length=20, unique=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    publicado = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.titulo} — {self.autor}"

class Cliente(models.Model):
    nombre = models.CharField(max_length=120)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.nombre

class Pedido(models.Model):  # 1–N: un cliente puede tener muchos pedidos
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="pedidos")
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, default="pendiente")  # pendiente/pagado/enviado/cancelado

    def __str__(self):
        return f"Pedido #{self.id} de {self.cliente}"

    @property
    def total(self):
        from django.db.models import Sum, F
        agg = self.detalles.aggregate(monto=Sum(F('cantidad') * F('precio_unitario')))
        return agg['monto'] or 0

class DetallePedido(models.Model):  # N–N: Pedido  Libro
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="detalles")
    libro = models.ForeignKey(Libro, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        if not self.precio_unitario:
            self.precio_unitario = self.libro.precio
        super().save(*args, **kwargs)

class PerfilUsuario(models.Model):  # 1–1 con User
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil")
    rut = models.CharField(max_length=12, blank=True)
    telefono = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"Perfil de {self.user.username}"