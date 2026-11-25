from rest_framework import serializers
from .models import Category, Order, OrderItem, Product, PromoCode


class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(source='products.count', read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'product_count']


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_slug = serializers.CharField(source='category.slug', read_only=True)
    material_display = serializers.CharField(source='get_material_display', read_only=True)
    coating_display = serializers.CharField(source='get_coating_display', read_only=True)
    head_type_display = serializers.CharField(source='get_head_type_display', read_only=True)
    packaging_display = serializers.CharField(source='get_packaging_display', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'sku',
            'name',
            'slug',
            'category',
            'category_name',
            'category_slug',
            'size',
            'diameter',
            'length',
            'material',
            'material_display',
            'coating',
            'coating_display',
            'head_type',
            'head_type_display',
            'packaging',
            'packaging_display',
            'pack_note',
            'price',
            'stock',
            'available',
            'description',
            'image',
        ]


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    cost = serializers.DecimalField(source='get_cost', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'price', 'quantity', 'cost']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    total_cost = serializers.DecimalField(
        source='get_total_cost',
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = Order
        fields = [
            'id',
            'full_name',
            'email',
            'phone',
            'city',
            'address',
            'status',
            'status_display',
            'discount_percent',
            'paid',
            'total_cost',
            'created_at',
            'items',
        ]


class PromoCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromoCode
        fields = ['code', 'discount_percent', 'active', 'valid_from', 'valid_to']
