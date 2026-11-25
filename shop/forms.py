from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Order


class CartAddProductForm(forms.Form):
    quantity = forms.IntegerField(
        label='Количество',
        min_value=1,
        max_value=999,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 1,
            'max': 999,
            'inputmode': 'numeric',
        }),
    )
    override = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.HiddenInput,
    )


class PromoCodeApplyForm(forms.Form):
    code = forms.CharField(
        label='Промокод',
        max_length=32,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Например: MASTER10',
            'autocomplete': 'off',
            'autocorrect': 'off',
            'autocapitalize': 'characters',
            'spellcheck': 'false',
        }),
    )


class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['full_name', 'email', 'phone', 'city', 'address', 'comment']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'autocomplete': 'name',
                'enterkeyhint': 'next',
                'placeholder': 'Иванов Иван Иванович',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'autocomplete': 'email',
                'autocorrect': 'off',
                'autocapitalize': 'none',
                'spellcheck': 'false',
                'enterkeyhint': 'next',
                'placeholder': 'ivan@example.com',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'tel',
                'autocomplete': 'tel',
                'inputmode': 'tel',
                'enterkeyhint': 'next',
                'placeholder': '+7 (999) 123-45-67',
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'autocomplete': 'address-level2',
                'enterkeyhint': 'next',
                'placeholder': 'Москва',
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'autocomplete': 'street-address',
                'placeholder': 'Улица, дом, корпус, квартира или пункт выдачи',
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Удобное время доставки, код домофона (необязательно)',
            }),
        }


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(
        label='Email',
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'autocomplete': 'email',
            'autocorrect': 'off',
            'autocapitalize': 'none',
            'spellcheck': 'false',
        }),
    )
    first_name = forms.CharField(
        label='Имя',
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autocomplete': 'given-name',
        }),
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'autocomplete': 'username',
            'autocorrect': 'off',
            'autocapitalize': 'none',
            'spellcheck': 'false',
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'autocomplete': 'new-password',
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'autocomplete': 'new-password',
        })
