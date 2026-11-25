from django.urls import path
from . import api_views

urlpatterns = [
    path('categories/', api_views.CategoryListAPIView.as_view(), name='api_category_list'),
    path('products/', api_views.ProductListAPIView.as_view(), name='api_product_list'),
    path('products/<slug:slug>/', api_views.ProductDetailAPIView.as_view(), name='api_product_detail'),
    path('orders/', api_views.UserOrderListAPIView.as_view(), name='api_order_list'),
]
