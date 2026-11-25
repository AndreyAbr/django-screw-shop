from django.contrib import admin
from .models import Category, Order, OrderItem, Product, PromoCode


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'product_count']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

    @admin.display(description='Товаров')
    def product_count(self, obj):
        return obj.products.count()


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'sku',
        'name',
        'category',
        'size',
        'material',
        'coating',
        'head_type',
        'packaging',
        'price',
        'stock',
        'available',
    ]
    list_filter = ['category', 'available', 'material', 'coating', 'head_type', 'packaging']
    list_editable = ['price', 'stock', 'available']
    search_fields = ['name', 'sku', 'size', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['category', 'name']


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_percent', 'active', 'valid_from', 'valid_to']
    list_filter = ['active', 'valid_from', 'valid_to']
    search_fields = ['code']
    list_editable = ['active', 'discount_percent']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    extra = 0
    readonly_fields = ['get_cost_display']

    @admin.display(description='Сумма')
    def get_cost_display(self, obj):
        if obj.id:
            return f'{obj.get_cost()} ₽'
        return '—'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'full_name',
        'phone',
        'city',
        'status',
        'paid',
        'discount_percent',
        'total_cost_display',
        'created_at',
    ]
    list_filter = ['status', 'paid', 'created_at', 'city']
    list_editable = ['status', 'paid']
    search_fields = ['id', 'full_name', 'email', 'phone', 'city', 'address']
    inlines = [OrderItemInline]
    readonly_fields = ['created_at', 'updated_at', 'total_cost_display']

    @admin.display(description='Итого')
    def total_cost_display(self, obj):
        return f'{obj.get_total_cost()} ₽'


admin.site.site_header = 'КрепМастер — Панель управления'
admin.site.site_title = 'КрепМастер Админ'
admin.site.index_title = 'Управление интернет-магазином метизов'
