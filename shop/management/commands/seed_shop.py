from decimal import Decimal
from io import BytesIO
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from PIL import Image, ImageDraw, ImageFont
from shop.models import Category, Product, PromoCode


COATING_COLORS = {
    'zinc': ((190, 198, 208), (130, 140, 152)),
    'yellow_zinc': ((226, 186, 72), (174, 134, 34)),
    'oxide': ((56, 62, 72), (30, 34, 42)),
    'none': ((175, 148, 86), (125, 102, 52)),
}

CATEGORY_ACCENTS = {
    'wood-screws': (180, 95, 36),
    'metal-screws': (45, 95, 155),
    'furniture-screws': (120, 82, 56),
    'roofing-screws': (156, 46, 54),
    'washer-head-screws': (46, 125, 112),
    'dowel-nails': (98, 74, 146),
}


def render_fastener_image(product_data, cat_slug):
    img = Image.new('RGB', (640, 480), (245, 247, 250))
    draw = ImageDraw.Draw(img)

    accent = CATEGORY_ACCENTS.get(cat_slug, (45, 65, 95))
    body_main, body_dark = COATING_COLORS.get(
        product_data['coating'], ((180, 188, 198), (120, 128, 138))
    )

    # Subtle blueprint grid background
    for x in range(0, 640, 32):
        draw.line([(x, 0), (x, 480)], fill=(232, 237, 244), width=1)
    for y in range(0, 480, 32):
        draw.line([(0, y), (640, y)], fill=(232, 237, 244), width=1)

    # Top accent bar
    draw.rectangle([(0, 0), (640, 14)], fill=accent)

    # Draw stylized screw / dowel horizontally in center
    cy = 235
    head_type = product_data['head_type']
    is_dowel = cat_slug == 'dowel-nails'

    if is_dowel:
        # Plastic dowel sleeve + metal nail
        draw.rounded_rectangle([(130, cy - 26), (440, cy + 26)], radius=10, fill=(215, 110, 45), outline=(140, 65, 22), width=3)
        draw.rectangle([(108, cy - 38), (138, cy + 38)], fill=(215, 110, 45), outline=(140, 65, 22), width=3)
        for tx in range(180, 415, 24):
            draw.line([(tx, cy - 24), (tx - 10, cy - 34)], fill=(140, 65, 22), width=4)
            draw.line([(tx, cy + 24), (tx - 10, cy + 34)], fill=(140, 65, 22), width=4)
        # Nail shaft
        draw.rectangle([(135, cy - 10), (505, cy + 10)], fill=body_main, outline=body_dark, width=2)
        draw.polygon([(505, cy - 10), (545, cy), (505, cy + 10)], fill=body_dark)
    else:
        # Shaft
        draw.rectangle([(165, cy - 16), (485, cy + 16)], fill=body_main, outline=body_dark, width=3)
        # Tip
        draw.polygon([(485, cy - 16), (542, cy), (485, cy + 16)], fill=body_main, outline=body_dark)
        # Threads
        for tx in range(215, 485, 18):
            draw.line([(tx, cy - 23), (tx + 10, cy + 23)], fill=body_dark, width=4)

        # Head by type
        if head_type == 'countersunk':
            draw.polygon([(115, cy - 48), (170, cy - 16), (170, cy + 16), (115, cy + 48)], fill=body_main, outline=body_dark)
            draw.rectangle([(105, cy - 48), (118, cy + 48)], fill=body_dark)
        elif head_type == 'hex':
            draw.rectangle([(105, cy - 40), (160, cy + 40)], fill=body_main, outline=body_dark, width=3)
            draw.line([(105, cy - 14), (160, cy - 14)], fill=body_dark, width=2)
            draw.line([(105, cy + 14), (160, cy + 14)], fill=body_dark, width=2)
            # EPDM washer for roofing
            if cat_slug == 'roofing-screws':
                draw.rectangle([(160, cy - 46), (174, cy + 46)], fill=(40, 44, 52))
        elif head_type == 'washer':
            draw.ellipse([(102, cy - 34), (168, cy + 34)], fill=body_main, outline=body_dark, width=3)
            draw.rectangle([(148, cy - 46), (166, cy + 46)], fill=body_dark)
        else:  # pan
            draw.pieslice([(108, cy - 38), (222, cy + 38)], start=90, end=270, fill=body_main, outline=body_dark, width=3)
            draw.line([(165, cy - 38), (165, cy + 38)], fill=body_dark, width=3)

    # Dimension callout line
    draw.line([(110, 345), (540, 345)], fill=accent, width=2)
    draw.line([(110, 336), (110, 354)], fill=accent, width=2)
    draw.line([(540, 336), (540, 354)], fill=accent, width=2)

    try:
        font_lg = ImageFont.truetype('arial.ttf', 24)
        font_sm = ImageFont.truetype('arial.ttf', 16)
    except OSError:
        font_lg = ImageFont.load_default()
        font_sm = ImageFont.load_default()

    # Badges
    draw.rounded_rectangle([(24, 34), (210, 74)], radius=8, fill=accent)
    draw.text((38, 44), product_data['sku'], fill=(255, 255, 255), font=font_sm)

    size_text = product_data['size']
    draw.rounded_rectangle([(245, 362), (405, 404)], radius=8, fill=(255, 255, 255), outline=accent, width=2)
    draw.text((264, 370), size_text, fill=(30, 38, 52), font=font_lg)

    draw.text((24, 434), 'KREPMASTER TECHNICAL SPEC', fill=(110, 122, 138), font=font_sm)

    buf = BytesIO()
    img.save(buf, format='PNG')
    return ContentFile(buf.getvalue(), name=f"{product_data['slug']}.png")


class Command(BaseCommand):
    help = 'Заполняет базу данных тестовыми категориями, товарами, промокодами и суперпользователем.'

    def handle(self, *args, **options):
        categories_data = [
            ('Шурупы по дереву', 'wood-screws', 'Крупный шаг резьбы для надёжной фиксации в массиве древесины, фанере и ДСП.'),
            ('Шурупы по металлу (саморезы)', 'metal-screws', 'Частая резьба и острый либо сверловой наконечник для листового металла и профилей.'),
            ('Шурупы мебельные (конфирматы)', 'furniture-screws', 'Евровинты и стяжки для корпусной мебели из ЛДСП и МДФ.'),
            ('Шурупы кровельные', 'roofing-screws', 'Шестигранная головка, сверло и уплотнительная EPDM-шайба для профнастила и металлочерепицы.'),
            ('Шурупы с прессшайбой', 'washer-head-screws', 'Увеличенная прижимная шляпка для тонколистового металла, пластика и обшивки.'),
            ('Дюбель-гвозди', 'dowel-nails', 'Комплекты для быстрого ударного монтажа в бетон, полнотелый кирпич и камень.'),
        ]

        categories = {}
        for name, slug, desc in categories_data:
            cat, _ = Category.objects.update_or_create(
                slug=slug,
                defaults={'name': name, 'description': desc},
            )
            categories[slug] = cat

        products_data = [
            # Шурупы по дереву
            {
                'category': 'wood-screws', 'sku': 'KM-WD-3535', 'slug': 'shurup-po-derevu-35x35-oksid',
                'name': 'Шуруп по дереву фосфатированный', 'size': '3.5×35 мм',
                'diameter': Decimal('3.50'), 'length': 35, 'material': 'steel',
                'coating': 'oxide', 'head_type': 'countersunk', 'packaging': 'box',
                'pack_note': '500 шт.', 'price': Decimal('390.00'), 'stock': 45,
                'description': 'Универсальный чёрный шуруп по дереву с редким шагом резьбы и потайной головкой PH2.',
            },
            {
                'category': 'wood-screws', 'sku': 'KM-WD-4550', 'slug': 'shurup-po-derevu-45x50-yellow',
                'name': 'Шуруп по дереву жёлтый цинк', 'size': '4.5×50 мм',
                'diameter': Decimal('4.50'), 'length': 50, 'material': 'steel',
                'coating': 'yellow_zinc', 'head_type': 'countersunk', 'packaging': 'box',
                'pack_note': '250 шт.', 'price': Decimal('520.00'), 'stock': 60,
                'description': 'Антикоррозийное покрытие жёлтый цинк для внутренних и уличных столярных работ.',
            },
            {
                'category': 'wood-screws', 'sku': 'KM-WD-5080', 'slug': 'shurup-konstrukcionnyj-50x80-nerzh',
                'name': 'Шуруп конструкционный по дереву A2', 'size': '5.0×80 мм',
                'diameter': Decimal('5.00'), 'length': 80, 'material': 'stainless',
                'coating': 'none', 'head_type': 'countersunk', 'packaging': 'box',
                'pack_note': '100 шт.', 'price': Decimal('890.00'), 'stock': 28,
                'description': 'Нержавеющая сталь A2 для террасной доски, фасадов и влажных помещений.',
            },
            # Шурупы по металлу (саморезы)
            {
                'category': 'metal-screws', 'sku': 'KM-MT-3525', 'slug': 'samorez-po-metallu-35x25-oksid',
                'name': 'Саморез по металлу частая резьба', 'size': '3.5×25 мм',
                'diameter': Decimal('3.50'), 'length': 25, 'material': 'steel',
                'coating': 'oxide', 'head_type': 'countersunk', 'packaging': 'kg',
                'pack_note': '~820 шт.', 'price': Decimal('460.00'), 'stock': 52,
                'description': 'Для крепления гипсокартона к металлическому профилю толщиной до 0.9 мм.',
            },
            {
                'category': 'metal-screws', 'sku': 'KM-MT-4219', 'slug': 'samorez-po-metallu-sverlo-42x19',
                'name': 'Саморез по металлу со сверлом DIN 7504', 'size': '4.2×19 мм',
                'diameter': Decimal('4.20'), 'length': 19, 'material': 'steel',
                'coating': 'zinc', 'head_type': 'pan', 'packaging': 'box',
                'pack_note': '500 шт.', 'price': Decimal('640.00'), 'stock': 34,
                'description': 'Сверловой наконечник позволяет крепить листы стали до 2 мм без предварительного сверления.',
            },
            {
                'category': 'metal-screws', 'sku': 'KM-MT-4832', 'slug': 'samorez-po-metallu-48x32-nerzh',
                'name': 'Саморез по металлу нержавеющий DIN 7981', 'size': '4.8×32 мм',
                'diameter': Decimal('4.80'), 'length': 32, 'material': 'stainless',
                'coating': 'none', 'head_type': 'pan', 'packaging': 'box',
                'pack_note': '200 шт.', 'price': Decimal('980.00'), 'stock': 19,
                'description': 'Полукруглая головка и коррозионностойкая сталь A2 для наружных металлоконструкций.',
            },
            # Шурупы мебельные (конфирматы)
            {
                'category': 'furniture-screws', 'sku': 'KM-FN-6450', 'slug': 'konfirmat-mebelnyj-64x50-cink',
                'name': 'Конфирмат мебельный (евровинт)', 'size': '6.4×50 мм',
                'diameter': Decimal('6.40'), 'length': 50, 'material': 'steel',
                'coating': 'zinc', 'head_type': 'countersunk', 'packaging': 'box',
                'pack_note': '200 шт.', 'price': Decimal('420.00'), 'stock': 75,
                'description': 'Классический мебельный конфирмат под шестигранник HEX 4 для стяжки плит ЛДСП 16–18 мм.',
            },
            {
                'category': 'furniture-screws', 'sku': 'KM-FN-7050', 'slug': 'konfirmat-usilennyj-70x50-cink',
                'name': 'Конфирмат усиленный 7×50', 'size': '7.0×50 мм',
                'diameter': Decimal('7.00'), 'length': 50, 'material': 'steel',
                'coating': 'zinc', 'head_type': 'countersunk', 'packaging': 'box',
                'pack_note': '200 шт.', 'price': Decimal('490.00'), 'stock': 40,
                'description': 'Увеличенный диаметр резьбы обеспечивает высокую прочность соединений корпусной мебели.',
            },
            {
                'category': 'furniture-screws', 'sku': 'KM-FN-4016', 'slug': 'shurup-mebelnyj-latun-40x16',
                'name': 'Шуруп мебельный декоративный латунный', 'size': '4.0×16 мм',
                'diameter': Decimal('4.00'), 'length': 16, 'material': 'brass',
                'coating': 'none', 'head_type': 'pan', 'packaging': 'pcs',
                'pack_note': 'поштучно', 'price': Decimal('12.50'), 'stock': 500,
                'description': 'Латунный шуруп для крепления декоративных петель, ручек и фурнитуры.',
            },
            # Шурупы кровельные
            {
                'category': 'roofing-screws', 'sku': 'KM-RF-4829', 'slug': 'samorez-krovelnyj-48x29-cink',
                'name': 'Шуруп кровельный с EPDM-шайбой', 'size': '4.8×29 мм',
                'diameter': Decimal('4.80'), 'length': 29, 'material': 'steel',
                'coating': 'zinc', 'head_type': 'hex', 'packaging': 'box',
                'pack_note': '250 шт.', 'price': Decimal('780.00'), 'stock': 55,
                'description': 'Кровельный саморез для крепления профнастила к деревянной обрешётке, герметичная шайба EPDM.',
            },
            {
                'category': 'roofing-screws', 'sku': 'KM-RF-4835', 'slug': 'samorez-krovelnyj-48x35-cink',
                'name': 'Шуруп кровельный по дереву 4.8×35', 'size': '4.8×35 мм',
                'diameter': Decimal('4.80'), 'length': 35, 'material': 'steel',
                'coating': 'zinc', 'head_type': 'hex', 'packaging': 'box',
                'pack_note': '250 шт.', 'price': Decimal('840.00'), 'stock': 38,
                'description': 'Шестигранная головка 8 мм, усиленное цинковое покрытие и атмосферостойкая прокладка.',
            },
            {
                'category': 'roofing-screws', 'sku': 'KM-RF-5550', 'slug': 'samorez-krovelnyj-po-metallu-55x50',
                'name': 'Шуруп кровельный по металлу с буром', 'size': '5.5×50 мм',
                'diameter': Decimal('5.50'), 'length': 50, 'material': 'steel',
                'coating': 'zinc', 'head_type': 'hex', 'packaging': 'box',
                'pack_note': '100 шт.', 'price': Decimal('690.00'), 'stock': 24,
                'description': 'Мощный сверловой наконечник для крепления кровельных панелей к металлическим прогонам до 5 мм.',
            },
            # Шурупы с прессшайбой
            {
                'category': 'washer-head-screws', 'sku': 'KM-WH-4216', 'slug': 'samorez-pressshajba-ostryj-42x16',
                'name': 'Шуруп с прессшайбой острый', 'size': '4.2×16 мм',
                'diameter': Decimal('4.20'), 'length': 16, 'material': 'steel',
                'coating': 'zinc', 'head_type': 'washer', 'packaging': 'box',
                'pack_note': '500 шт.', 'price': Decimal('510.00'), 'stock': 80,
                'description': 'Широкая прижимная головка надёжно фиксирует тонколистовые материалы и сайдинг без продавливания.',
            },
            {
                'category': 'washer-head-screws', 'sku': 'KM-WH-4225', 'slug': 'samorez-pressshajba-sverlo-42x25',
                'name': 'Шуруп с прессшайбой со сверлом', 'size': '4.2×25 мм',
                'diameter': Decimal('4.20'), 'length': 25, 'material': 'steel',
                'coating': 'zinc', 'head_type': 'washer', 'packaging': 'box',
                'pack_note': '500 шт.', 'price': Decimal('620.00'), 'stock': 64,
                'description': 'Для крепления металлических профилей, коробов и облицовочных панелей до 2 мм.',
            },
            {
                'category': 'washer-head-screws', 'sku': 'KM-WH-4232', 'slug': 'samorez-pressshajba-42x32-kg',
                'name': 'Шуруп с прессшайбой весовой', 'size': '4.2×32 мм',
                'diameter': Decimal('4.20'), 'length': 32, 'material': 'steel',
                'coating': 'zinc', 'head_type': 'washer', 'packaging': 'kg',
                'pack_note': '~410 шт.', 'price': Decimal('590.00'), 'stock': 30,
                'description': 'Выгодная весовая фасовка 1 кг для монтажных бригад и строительных объектов.',
            },
            # Дюбель-гвозди
            {
                'category': 'dowel-nails', 'sku': 'KM-DN-0640', 'slug': 'dyubel-gvozd-6x40-potaj',
                'name': 'Дюбель-гвоздь с потайным бортиком', 'size': '6.0×40 мм',
                'diameter': Decimal('6.00'), 'length': 40, 'material': 'steel',
                'coating': 'zinc', 'head_type': 'countersunk', 'packaging': 'box',
                'pack_note': '200 шт.', 'price': Decimal('340.00'), 'stock': 90,
                'description': 'Быстрый ударный монтаж плинтусов, направляющих профилей и кабель-каналов в бетон и кирпич.',
            },
            {
                'category': 'dowel-nails', 'sku': 'KM-DN-0660', 'slug': 'dyubel-gvozd-6x60-grib',
                'name': 'Дюбель-гвоздь грибовидная манжета', 'size': '6.0×60 мм',
                'diameter': Decimal('6.00'), 'length': 60, 'material': 'steel',
                'coating': 'yellow_zinc', 'head_type': 'pan', 'packaging': 'box',
                'pack_note': '100 шт.', 'price': Decimal('310.00'), 'stock': 70,
                'description': 'Грибовидный бортик увеличивает площадь прижима при креплении деревянных реек и обрешётки.',
            },
            {
                'category': 'dowel-nails', 'sku': 'KM-DN-0880', 'slug': 'dyubel-gvozd-8x80-usilennyj',
                'name': 'Дюбель-гвоздь усиленный 8×80', 'size': '8.0×80 мм',
                'diameter': Decimal('8.00'), 'length': 80, 'material': 'steel',
                'coating': 'zinc', 'head_type': 'countersunk', 'packaging': 'box',
                'pack_note': '100 шт.', 'price': Decimal('560.00'), 'stock': 42,
                'description': 'Для ответственного сквозного монтажа тяжёлых конструкций и металлических кронштейнов.',
            },
        ]

        created_count = 0
        for pdata in products_data:
            cat_slug = pdata['category']
            defaults = {k: v for k, v in pdata.items() if k not in ('category', 'slug')}
            defaults['category'] = categories[cat_slug]
            defaults['available'] = True
            product, created = Product.objects.update_or_create(
                slug=pdata['slug'],
                defaults=defaults,
            )
            if not product.image:
                img_file = render_fastener_image(pdata, cat_slug)
                product.image.save(img_file.name, img_file, save=True)
            if created:
                created_count += 1

        for code, discount in [('MASTER10', 10), ('OPT15', 15), ('WELCOME5', 5)]:
            PromoCode.objects.update_or_create(
                code=code,
                defaults={'discount_percent': discount, 'active': True},
            )

        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@krepmaster.local', 'admin123')
            self.stdout.write(self.style.SUCCESS('Создан суперпользователь: admin / admin123'))

        self.stdout.write(
            self.style.SUCCESS(
                f'Готово! Категорий: {Category.objects.count()}, товаров: {Product.objects.count()} (новых: {created_count}), промокодов: {PromoCode.objects.count()}.'
            )
        )
