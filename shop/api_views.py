from django.db.models import Q
from rest_framework import generics, permissions
from .models import Category, Order, Product
from .serializers import CategorySerializer, OrderSerializer, ProductSerializer


class CategoryListAPIView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ProductListAPIView(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        qs = Product.objects.filter(available=True).select_related('category')
        params = self.request.query_params
        q = params.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(name__icontains=q)
                | Q(sku__icontains=q)
                | Q(size__icontains=q)
                | Q(description__icontains=q)
            )
        if category := params.get('category'):
            qs = qs.filter(category__slug=category)
        if material := params.get('material'):
            qs = qs.filter(material=material)
        if coating := params.get('coating'):
            qs = qs.filter(coating=coating)
        if min_price := params.get('min_price'):
            qs = qs.filter(price__gte=min_price)
        if max_price := params.get('max_price'):
            qs = qs.filter(price__lte=max_price)
        return qs


class ProductDetailAPIView(generics.RetrieveAPIView):
    queryset = Product.objects.filter(available=True).select_related('category')
    serializer_class = ProductSerializer
    lookup_field = 'slug'


class UserOrderListAPIView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items__product')
