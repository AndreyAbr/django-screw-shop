from decimal import Decimal
from django.conf import settings
from .models import Product, PromoCode


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart
        self.promo_code_id = self.session.get(settings.PROMO_SESSION_ID)

    def add(self, product, quantity=1, override_quantity=False):
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0,
                'price': str(product.price),
            }
        if override_quantity:
            new_qty = quantity
        else:
            new_qty = self.cart[product_id]['quantity'] + quantity

        if product.stock > 0:
            new_qty = min(new_qty, product.stock)
        if new_qty <= 0:
            self.remove(product)
            return
        self.cart[product_id]['quantity'] = new_qty
        self.cart[product_id]['price'] = str(product.price)
        self.save()

    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def save(self):
        self.session.modified = True

    def __iter__(self):
        product_ids = list(self.cart.keys())
        products = Product.objects.filter(id__in=product_ids).select_related('category')
        products_map = {str(p.id): p for p in products}
        for product_id, item_data in list(self.cart.items()):
            product = products_map.get(product_id)
            if product is None:
                continue
            price = Decimal(item_data['price'])
            quantity = int(item_data['quantity'])
            yield {
                'product': product,
                'price': price,
                'quantity': quantity,
                'total_price': price * quantity,
            }

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_subtotal(self):
        return sum(
            (Decimal(item['price']) * item['quantity'] for item in self.cart.values()),
            Decimal('0.00'),
        )

    @property
    def promo_code(self):
        if self.promo_code_id:
            try:
                promo = PromoCode.objects.get(id=self.promo_code_id)
                if promo.is_valid_now():
                    return promo
            except PromoCode.DoesNotExist:
                pass
        return None

    def set_promo_code(self, promo):
        self.session[settings.PROMO_SESSION_ID] = promo.id if promo else None
        self.promo_code_id = promo.id if promo else None
        self.save()

    def get_discount(self):
        promo = self.promo_code
        if promo:
            return (
                self.get_subtotal() * Decimal(promo.discount_percent) / Decimal('100')
            ).quantize(Decimal('0.01'))
        return Decimal('0.00')

    def get_total_price(self):
        return self.get_subtotal() - self.get_discount()

    def clear(self):
        self.session.pop(settings.CART_SESSION_ID, None)
        self.session.pop(settings.PROMO_SESSION_ID, None)
        self.cart = {}
        self.promo_code_id = None
        self.save()
