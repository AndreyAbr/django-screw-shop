# КрепМастер — Интернет-магазин шурупов и метизов на Django

Полнофункциональный интернет-магазин по продаже крепёжных изделий (шурупов, саморезов, конфирматов, кровельных шурупов, шурупов с прессшайбой и дюбель-гвоздей), разработанный на Django.

## Функциональность

### Обязательный минимум
- **Модели БД (`shop/models.py`)**: `Category`, `Product`, `Order`, `OrderItem` (а также `PromoCode`) со связями `ForeignKey`.
- **Характеристики товаров**: название, артикул, размер (`диаметр × длина`), материал (сталь, нержавейка, латунь), покрытие (цинк, жёлтый цинк, оксид, без покрытия), тип головки (потайная, полукруглая, шестигранная, прессшайба), упаковка (шт., кг, коробка), цена и остаток на складе.
- **Страницы сайта**: каталог (`/`), категория (`/category/<slug>/`), карточка товара (`/product/<slug>/`), корзина (`/cart/`), оформление заказа (`/checkout/`), подтверждение заказа (`/order/success/<id>/`), авторизация (`/accounts/login/`, `/accounts/register/`) и история заказов (`/accounts/orders/`).
- **Наследование шаблонов**: единый базовый шаблон `shop/templates/shop/base.html` (`{% extends %}`).
- **Корзина на сессиях (`shop/cart.py`)**: добавление, изменение количества, удаление товаров, автоматический учёт остатков.
- **Оформление заказа (`shop/forms.py`)**: форма с CSRF-защитой, POST-обработкой, атомарным списанием остатков со склада.
- **Административная панель (`shop/admin.py`)**: настроены `list_display`, `list_filter`, `search_fields`, `list_editable`, `prepopulated_fields` и `OrderItemInline`.
- **Статика и медиа**: собственные стили `shop/static/shop/css/style.css` + Bootstrap 5 и изображения товаров в `media/products/`.

### Дополнительные возможности
- **Поиск по каталогу** на `Q`-объектах (название, артикул, размер, описание, категория).
- **Фильтрация** по категории, цене (от/до), размеру, материалу, покрытию, типу головки, наличию и сортировке.
- **Пагинация каталога** с сохранением параметров фильтрации.
- **Авторизация и история заказов** пользователя.
- **Слаги в URL** категорий и товаров.
- **Статусы заказов**: новый, в обработке, отправлен, выполнен, отменён.
- **Промокоды и скидки**: `MASTER10` (-10%), `OPT15` (-15%), `WELCOME5` (-5%).
- **Адаптивная вёрстка** на Bootstrap 5.
- **REST API** на Django REST Framework:
  - `GET /api/categories/` — список категорий
  - `GET /api/products/` — каталог товаров (поддерживает фильтры `?q=`, `?category=`, `?material=`, `?coating=`, `?min_price=`, `?max_price=`)
  - `GET /api/products/<slug>/` — детальная информация о товаре
  - `GET /api/orders/` — история заказов авторизованного пользователя

## Структура проекта

```text
myshop/
├── manage.py
├── myshop/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── shop/
│   ├── management/commands/seed_shop.py
│   ├── migrations/
│   ├── templates/shop/
│   │   ├── base.html
│   │   ├── product_list.html
│   │   ├── product_detail.html
│   │   ├── cart.html
│   │   ├── checkout.html
│   │   ├── order_success.html
│   │   ├── login.html
│   │   ├── register.html
│   │   └── order_history.html
│   ├── static/shop/css/style.css
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   ├── cart.py
│   ├── context_processors.py
│   ├── admin.py
│   ├── serializers.py
│   ├── api_views.py
│   ├── api_urls.py
│   └── tests.py
├── media/
├── requirements.txt
└── README.md
```

## Инструкция по запуску

1. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
2. Примените миграции:
   ```bash
   python manage.py migrate
   ```
3. Заполните базу тестовым каталогом (6 категорий, 18 товаров с изображениями, промокоды и суперпользователь):
   ```bash
   python manage.py seed_shop
   ```
4. Запустите сервер разработки:
   ```bash
   python manage.py runserver
   ```
5. Откройте в браузере:
   - Магазин: http://127.0.0.1:8000/
   - Админ-панель: http://127.0.0.1:8000/admin/ (логин `admin`, пароль `admin123`)
   - REST API: http://127.0.0.1:8000/api/products/

## Запуск тестов

```bash
python manage.py test
```
