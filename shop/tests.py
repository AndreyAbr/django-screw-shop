from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from .models import Category, Order, OrderItem, Product, PromoCode


class ShopTests(TestCase):
    def setUp(self):
        self.cat_wood = Category.objects.create(
            name='Шурупы по дереву',
            slug='wood-screws',
        )
        self.cat_metal = Category.objects.create(
            name='Шурупы по металлу',
            slug='metal-screws',
        )
        self.p1 = Product.objects.create(
            category=self.cat_wood,
            name='Шуруп по дереву оцинкованный',
            slug='wood-45x50',
            sku='TEST-001',
            size='4.5×50 мм',
            diameter=Decimal('4.50'),
            length=50,
            material='steel',
            coating='zinc',
            head_type='countersunk',
            packaging='box',
            price=Decimal('500.00'),
            stock=10,
            available=True,
        )
        self.p2 = Product.objects.create(
            category=self.cat_metal,
            name='Саморез по металлу со сверлом',
            slug='metal-42x19',
            sku='TEST-002',
            size='4.2×19 мм',
            diameter=Decimal('4.20'),
            length=19,
            material='stainless',
            coating='none',
            head_type='pan',
            packaging='box',
            price=Decimal('900.00'),
            stock=5,
            available=True,
        )
        self.promo = PromoCode.objects.create(
            code='MASTER10',
            discount_percent=10,
            active=True,
        )

    def test_catalog_search_and_filters(self):
        resp = self.client.get(reverse('shop:product_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.p1.name)
        self.assertContains(resp, self.p2.name)

        resp_q = self.client.get(reverse('shop:product_list'), {'q': 'сверлом'})
        self.assertContains(resp_q, self.p2.name)
        self.assertNotContains(resp_q, self.p1.name)

        resp_cat = self.client.get(reverse('shop:product_list_by_category', args=[self.cat_wood.slug]))
        self.assertContains(resp_cat, self.p1.name)
        self.assertNotContains(resp_cat, self.p2.name)

        resp_price = self.client.get(reverse('shop:product_list'), {'price_min': '700'})
        self.assertContains(resp_price, self.p2.name)
        self.assertNotContains(resp_price, self.p1.name)

    def test_product_detail_by_slug(self):
        resp = self.client.get(self.p1.get_absolute_url())
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, '4.5×50 мм')

    def test_session_cart_promo_and_checkout(self):
        # Add to cart
        resp = self.client.post(
            reverse('shop:cart_add', args=[self.p1.id]),
            {'quantity': 2, 'override': False},
        )
        self.assertRedirects(resp, reverse('shop:cart_detail'))

        # Apply promo code
        self.client.post(reverse('shop:promo_apply'), {'code': 'MASTER10'})
        cart_resp = self.client.get(reverse('shop:cart_detail'))
        self.assertContains(cart_resp, 'MASTER10')
        self.assertContains(cart_resp, '900,00')

        # Checkout
        checkout_resp = self.client.post(
            reverse('shop:checkout'),
            {
                'full_name': 'Иванов Иван',
                'email': 'ivan@example.com',
                'phone': '+79991234567',
                'city': 'Москва',
                'address': 'ул. Строителей, д. 10',
                'comment': 'Позвонить заранее',
            },
        )
        order = Order.objects.first()
        self.assertIsNotNone(order)
        self.assertRedirects(checkout_resp, reverse('shop:order_success', args=[order.id]))
        self.assertEqual(order.discount_percent, 10)
        self.assertEqual(order.get_total_cost(), Decimal('900.00'))
        self.assertEqual(OrderItem.objects.filter(order=order).count(), 1)

        # Stock decremented
        self.p1.refresh_from_db()
        self.assertEqual(self.p1.stock, 8)

    def test_auth_and_order_history(self):
        user = User.objects.create_user(username='buyer', password='strongpassword123', email='b@example.com')
        Order.objects.create(
            user=user,
            full_name='Покупатель',
            email='b@example.com',
            phone='+79990000000',
            city='Казань',
            address='ул. Мира, 1',
        )
        self.client.login(username='buyer', password='strongpassword123')
        resp = self.client.get(reverse('shop:order_history'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Казань')

    def test_rest_api_endpoints(self):
        resp_cats = self.client.get('/api/categories/')
        self.assertEqual(resp_cats.status_code, 200)
        resp_prods = self.client.get('/api/products/')
        self.assertEqual(resp_prods.status_code, 200)
        self.assertEqual(resp_prods.json()['count'], 2)
        resp_detail = self.client.get(f'/api/products/{self.p1.slug}/')
        self.assertEqual(resp_detail.status_code, 200)
        self.assertEqual(resp_detail.json()['sku'], 'TEST-001')
