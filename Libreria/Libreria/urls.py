from django.contrib import admin
from django.urls import path, include
from biblioteca import views as bib_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("cuentas/", include("django.contrib.auth.urls")),  # login/logout
    path("", include("biblioteca.urls")),                   # home y rutas de la app
]

# Manejo de errores (usa templates/403.html y 404.html)
handler403 = bib_views.error_403
handler404 = bib_views.error_404