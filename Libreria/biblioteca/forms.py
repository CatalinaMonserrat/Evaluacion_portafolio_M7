from django import forms
from .models import Libro

class LibroForm(forms.ModelForm):
    class Meta:
        model = Libro
        fields = ["titulo", "autor", "editorial", "categorias", "isbn", "precio", "stock", "publicado", "activo"]
        widgets = {
            "publicado": forms.DateInput(attrs={"type": "date"}),
        }