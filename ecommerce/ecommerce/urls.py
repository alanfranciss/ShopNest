"""
URL configuration for ecommerce project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup_view, name='signup'),
    path('admin_dash/', views.admin_dash_view, name='admin_dash'),
    path('user/', views.user_view, name='user'),
    path('categories/', views.categories_view, name='categories'),
    path('products/', views.products_view, name='products'),
    path('product/<int:id>/', views.product_detail_view, name='product_detail'),
    path('about/', views.about_view, name='about'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:id>/', views.cart_remove, name='cart_remove'),
    path('wishlist/', views.wishlist_detail, name='wishlist_detail'),
    path('wishlist/add/<int:id>/', views.wishlist_add, name='wishlist_add'),
    path('wishlist/remove/<int:id>/', views.wishlist_remove, name='wishlist_remove'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('order-success/', views.order_success_view, name='order_success'),
    path('order/<int:id>/', views.order_detail_view, name='order_detail'),
    path('order/cancel/<int:item_id>/', views.cancel_order_item, name='cancel_order_item'),
    path('order/cancel-all/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('seller-dashboard/', views.seller_dashboard_view, name='seller_dashboard'),
    path('seller/add-product/', views.seller_add_product, name='seller_add_product'),
    path('seller/update-status/<int:item_id>/', views.update_item_status, name='update_item_status'),
    path('seller-registration/', views.seller_registration_view, name='seller_registration'),
    path('admin/approve-seller/<int:user_id>/', views.approve_seller, name='approve_seller'),
    path('admin/reject-seller/<int:user_id>/', views.reject_seller, name='reject_seller'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
