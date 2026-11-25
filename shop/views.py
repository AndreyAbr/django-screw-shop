from decimal import Decimal, InvalidOperation
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .cart import Cart
from .forms import (
    CartAddProductForm,
    OrderCreateForm,
    PromoCodeApplyForm,
    UserRegisterForm,
)
from .models import Category, Order, OrderItem, Product, PromoCode


def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True).select_related('category')

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    query = request.GET.get('q', '').strip()
    if query:
        products = products.filter(
            Q(name__icontains=query)
            | Q(sku__icontains=query)
            | Q(size__icontains=query)
            | Q(description__icontains=query)
            | Q(category__name__icontains=query)
        )

    size_filter = request.GET.get('size', '').strip()
    if size_filter:
        products = products.filter(size__icontains=size_filter)

    material_filter = request.GET.get('material', '').strip()
    if material_filter:
        products = products.filter(material=material_filter)

    coating_filter = request.GET.get('coating', '').strip()
    if coating_filter:
        products = products.filter(coating=coating_filter)

    head_type_filter = request.GET.get('head_type', '').strip()
    if head_type_filter:
        products = products.filter(head_type=head_type_filter)

    price_min = request.GET.get('price_min', '').strip()
    price_max = request.GET.get('price_max', '').strip()
    if price_min:
        try:
            products = products.filter(price__gte=Decimal(price_min))
        except InvalidOperation:
            pass
    if price_max:
        try:
            products = products.filter(price__lte=Decimal(price_max))
        except InvalidOperation:
            pass

    if request.GET.get('in_stock') == '1':
        products = products.filter(stock__gt=0)

    sort = request.GET.get('sort', 'name')
    sort_map = {
        'name': 'name',
        'price_asc': 'price',
        'price_desc': '-price',
        'newest': '-created_at',
    }
    products = products.order_by(sort_map.get(sort, 'name'))

    paginator = Paginator(products, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    query_params = request.GET.copy()
    query_params.pop('page', None)
    query_string = query_params.urlencode()

    sizes = (
        Product.objects.filter(available=True)
        .values_list('size', flat=True)
        .distinct()
        .order_by('diameter', 'length')
    )

    context = {
        'category': category,
        'categories': categories,
        'page_obj': page_obj,
        'products': page_obj.object_list,
        'total_count': paginator.count,
        'query': query,
        'size_filter': size_filter,
        'material_filter': material_filter,
        'coating_filter': coating_filter,
        'head_type_filter': head_type_filter,
        'price_min': price_min,
        'price_max': price_max,
        'in_stock': request.GET.get('in_stock') == '1',
        'sort': sort,
        'query_string': query_string,
        'sizes': sizes,
        'materials': Product.Material.choices,
        'coatings': Product.Coating.choices,
        'head_types': Product.HeadType.choices,
    }
    return render(request, 'shop/product_list.html', context)


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related('category'),
        slug=slug,
        available=True,
    )
    cart_form = CartAddProductForm()
    related_products = (
        Product.objects.filter(category=product.category, available=True)
        .exclude(id=product.id)
        .select_related('category')[:4]
    )
    return render(
        request,
        'shop/product_detail.html',
        {
            'product': product,
            'cart_form': cart_form,
            'related_products': related_products,
        },
    )


@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id, available=True)
    if product.stock <= 0:
        messages.warning(request, f'Товар «{product.name}» временно отсутствует на складе.')
        return redirect(request.META.get('HTTP_REFERER') or product.get_absolute_url())

    form = CartAddProductForm(request.POST)
    if form.is_valid():
        cd = form.cleaned_data
        cart.add(
            product=product,
            quantity=cd['quantity'],
            override_quantity=cd['override'],
        )
        if cd['override']:
            messages.success(request, f'Количество «{product.name}» обновлено.')
        else:
            messages.success(request, f'«{product.name}» добавлен в корзину.')
    else:
        messages.error(request, 'Укажите корректное количество товара.')
    return redirect(request.POST.get('next') or 'shop:cart_detail')


@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    messages.info(request, f'«{product.name}» удалён из корзины.')
    return redirect('shop:cart_detail')


def cart_detail(request):
    cart = Cart(request)
    items = list(cart)
    for item in items:
        item['update_quantity_form'] = CartAddProductForm(
            initial={'quantity': item['quantity'], 'override': True}
        )
    promo_form = PromoCodeApplyForm()
    return render(
        request,
        'shop/cart.html',
        {
            'cart': cart,
            'items': items,
            'promo_form': promo_form,
        },
    )


@require_POST
def promo_apply(request):
    cart = Cart(request)
    form = PromoCodeApplyForm(request.POST)
    if form.is_valid():
        code = form.cleaned_data['code'].strip().upper()
        try:
            promo = PromoCode.objects.get(code__iexact=code)
            if promo.is_valid_now():
                cart.set_promo_code(promo)
                messages.success(
                    request,
                    f'Промокод {promo.code} применён! Скидка {promo.discount_percent}%.',
                )
            else:
                messages.warning(request, 'Срок действия промокода истёк или он неактивен.')
        except PromoCode.DoesNotExist:
            messages.error(request, 'Промокод не найден.')
    return redirect('shop:cart_detail')


@require_POST
def promo_remove(request):
    cart = Cart(request)
    cart.set_promo_code(None)
    messages.info(request, 'Промокод отменён.')
    return redirect('shop:cart_detail')


def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.warning(request, 'Корзина пуста. Добавьте товары перед оформлением заказа.')
        return redirect('shop:product_list')

    initial = {}
    if request.user.is_authenticated:
        full_name = request.user.get_full_name() or request.user.username
        initial = {
            'full_name': full_name,
            'email': request.user.email,
        }

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                order = form.save(commit=False)
                if request.user.is_authenticated:
                    order.user = request.user
                promo = cart.promo_code
                if promo:
                    order.promo_code = promo
                    order.discount_percent = promo.discount_percent
                order.save()

                for item in cart:
                    product = item['product']
                    qty = item['quantity']
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        price=item['price'],
                        quantity=qty,
                    )
                    Product.objects.filter(id=product.id, stock__gte=qty).update(
                        stock=F('stock') - qty
                    )

            cart.clear()
            request.session['last_order_id'] = order.id
            messages.success(request, f'Заказ №{order.id} успешно оформлен!')
            return redirect('shop:order_success', order_id=order.id)
    else:
        form = OrderCreateForm(initial=initial)

    return render(
        request,
        'shop/checkout.html',
        {
            'cart': cart,
            'form': form,
        },
    )


def order_success(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related('items__product'),
        id=order_id,
    )
    allowed = (
        request.session.get('last_order_id') == order.id
        or (request.user.is_authenticated and (order.user_id == request.user.id or request.user.is_staff))
    )
    if not allowed:
        messages.error(request, 'Нет доступа к просмотру этого заказа.')
        return redirect('shop:product_list')
    return render(request, 'shop/order_success.html', {'order': order})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('shop:product_list')
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}! Аккаунт создан.')
            return redirect('shop:product_list')
    else:
        form = UserRegisterForm()
    return render(request, 'shop/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('shop:product_list')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Вы вошли как {user.username}.')
            next_url = request.POST.get('next') or request.GET.get('next')
            return redirect(next_url or 'shop:product_list')
    else:
        form = AuthenticationForm(request)

    form.fields['username'].widget.attrs.update({
        'class': 'form-control',
        'autocomplete': 'username',
        'autocorrect': 'off',
        'autocapitalize': 'none',
        'spellcheck': 'false',
    })
    form.fields['password'].widget.attrs.update({
        'class': 'form-control',
        'autocomplete': 'current-password',
    })
    return render(request, 'shop/login.html', {'form': form, 'next': request.GET.get('next', '')})


@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, 'Вы вышли из аккаунта.')
    return redirect('shop:product_list')


@login_required
def order_history(request):
    orders = (
        Order.objects.filter(user=request.user)
        .prefetch_related('items__product')
        .select_related('promo_code')
    )
    return render(request, 'shop/order_history.html', {'orders': orders})
