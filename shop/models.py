from decimal import Decimal
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Category(models.Model):
    name = models.CharField('Название', max_length=150)
    slug = models.SlugField('URL-слаг', max_length=160, unique=True)
    description = models.TextField('Описание', blank=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shop:product_list_by_category', args=[self.slug])


class Product(models.Model):
    class Material(models.TextChoices):
        STEEL = 'steel', 'Сталь'
        STAINLESS = 'stainless', 'Нержавеющая сталь'
        BRASS = 'brass', 'Латунь'

    class Coating(models.TextChoices):
        ZINC = 'zinc', 'Цинк'
        YELLOW_ZINC = 'yellow_zinc', 'Жёлтый цинк'
        OXIDE = 'oxide', 'Оксид'
        NONE = 'none', 'Без покрытия'

    class HeadType(models.TextChoices):
        COUNTERSUNK = 'countersunk', 'Потайная'
        PAN = 'pan', 'Полукруглая'
        HEX = 'hex', 'Шестигранная'
        WASHER = 'washer', 'Прессшайба'

    class Packaging(models.TextChoices):
        PCS = 'pcs', 'шт.'
        KG = 'kg', 'кг'
        BOX = 'box', 'коробка'

    category = models.ForeignKey(
        Category,
        related_name='products',
        on_delete=models.CASCADE,
        verbose_name='Категория',
    )
    name = models.CharField('Название', max_length=200)
    slug = models.SlugField('URL-слаг', max_length=220, unique=True)
    sku = models.CharField('Артикул', max_length=50, unique=True)
    size = models.CharField('Размер (диаметр × длина)', max_length=50)
    diameter = models.DecimalField('Диаметр (мм)', max_digits=5, decimal_places=2)
    length = models.PositiveIntegerField('Длина (мм)')
    material = models.CharField(
        'Материал',
        max_length=20,
        choices=Material.choices,
        default=Material.STEEL,
    )
    coating = models.CharField(
        'Покрытие',
        max_length=20,
        choices=Coating.choices,
        default=Coating.ZINC,
    )
    head_type = models.CharField(
        'Тип головки',
        max_length=20,
        choices=HeadType.choices,
        default=HeadType.COUNTERSUNK,
    )
    packaging = models.CharField(
        'Упаковка',
        max_length=20,
        choices=Packaging.choices,
        default=Packaging.BOX,
    )
    pack_note = models.CharField('Фасовка (примечание)', max_length=60, blank=True)
    price = models.DecimalField('Цена (₽)', max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField('Остаток на складе', default=0)
    available = models.BooleanField('В наличии', default=True)
    description = models.TextField('Описание', blank=True)
    image = models.ImageField('Изображение', upload_to='products/', blank=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['category', 'available']),
            models.Index(fields=['price']),
        ]
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    def __str__(self):
        return f'{self.name} ({self.size})'

    def get_absolute_url(self):
        return reverse('shop:product_detail', args=[self.slug])

    @property
    def is_in_stock(self):
        return self.available and self.stock > 0


class PromoCode(models.Model):
    code = models.CharField('Промокод', max_length=32, unique=True)
    discount_percent = models.PositiveSmallIntegerField(
        'Скидка (%)',
        validators=[MinValueValidator(1), MaxValueValidator(90)],
    )
    active = models.BooleanField('Активен', default=True)
    valid_from = models.DateTimeField('Действует с', default=timezone.now)
    valid_to = models.DateTimeField('Действует до', null=True, blank=True)

    class Meta:
        ordering = ['-active', 'code']
        verbose_name = 'Промокод'
        verbose_name_plural = 'Промокоды'

    def __str__(self):
        return f'{self.code} (-{self.discount_percent}%)'

    def is_valid_now(self):
        now = timezone.now()
        if not self.active:
            return False
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_to and now > self.valid_to:
            return False
        return True


class Order(models.Model):
    class Status(models.TextChoices):
        NEW = 'new', 'Новый'
        PROCESSING = 'processing', 'В обработке'
        SHIPPED = 'shipped', 'Отправлен'
        COMPLETED = 'completed', 'Выполнен'
        CANCELLED = 'cancelled', 'Отменён'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='orders',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Пользователь',
    )
    full_name = models.CharField('ФИО получателя', max_length=150)
    email = models.EmailField('Email')
    phone = models.CharField('Телефон', max_length=30)
    city = models.CharField('Город', max_length=100)
    address = models.TextField('Адрес доставки')
    comment = models.TextField('Комментарий к заказу', blank=True)
    status = models.CharField(
        'Статус',
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
    )
    promo_code = models.ForeignKey(
        PromoCode,
        related_name='orders',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Промокод',
    )
    discount_percent = models.PositiveSmallIntegerField('Скидка (%)', default=0)
    paid = models.BooleanField('Оплачен', default=False)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return f'Заказ №{self.id} — {self.full_name}'

    def get_subtotal(self):
        return sum((item.get_cost() for item in self.items.all()), Decimal('0.00'))

    def get_discount_amount(self):
        subtotal = self.get_subtotal()
        if self.discount_percent:
            return (subtotal * Decimal(self.discount_percent) / Decimal('100')).quantize(Decimal('0.01'))
        return Decimal('0.00')

    def get_total_cost(self):
        return self.get_subtotal() - self.get_discount_amount()


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name='items',
        on_delete=models.CASCADE,
        verbose_name='Заказ',
    )
    product = models.ForeignKey(
        Product,
        related_name='order_items',
        on_delete=models.PROTECT,
        verbose_name='Товар',
    )
    price = models.DecimalField('Цена на момент заказа (₽)', max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField('Количество', default=1)

    class Meta:
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Позиции заказа'

    def __str__(self):
        return f'{self.product.name} × {self.quantity}'

    def get_cost(self):
        return self.price * self.quantity
