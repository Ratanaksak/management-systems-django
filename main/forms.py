# forms.py
from django import forms
from .models import Person

class PersonForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = ['name', 'address', 'price_usd', 'price_khr', 'gender', 'relationship', 'province', 'district', 'commune', 'village']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter full name'}),
            'price_usd': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter price in USD'}),
            'price_khr': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter price in KHR'}),
            'gender': forms.RadioSelect(choices=[('Male', 'Male'), ('Female', 'Female')]),
            'relationship': forms.RadioSelect(choices=[('Wife', 'Wife'), ('Husband', 'Husband')]),
            'province': forms.Select(attrs={'class': 'form-control'}),
            'district': forms.Select(attrs={'class': 'form-control'}),
            'commune': forms.Select(attrs={'class': 'form-control'}),
            'village': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': 'Full Name',
            'address': 'Address',
            'price_usd': 'Price (USD)',
            'price_khr': 'Price (KHR)',
            'gender': 'Gender',
            'relationship': 'Relationship',
            'province': 'Province',
            'district': 'District',
            'commune': 'Commune',
            'village': 'Village',
        }