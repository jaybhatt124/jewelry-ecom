from django.urls import path
from . import views

urlpatterns = [
    # ── AUTH ──────────────────────────────────────────────────
    path('login/',    views.login_view,   name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/',   views.logout_view,  name='logout'),

    # ── OTP FORGOT PASSWORD ───────────────────────────────────
    path('forgot-password/',        views.forgot_password_email,  name='forgot_password'),
    path('forgot-password/verify/', views.forgot_password_verify, name='forgot_password_verify'),

    # ── STORE ─────────────────────────────────────────────────
    path('',                          views.home,           name='home'),
    path('shop/',                     views.shop,           name='shop'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('contact/',                  views.contact_view,   name='contact'),
    path('about/',                    views.about_view,     name='about'),

    # ── CART ──────────────────────────────────────────────────
    path('cart/',                              views.cart_view,        name='cart'),
    path('add-to-cart/<int:product_id>/',      views.add_to_cart,      name='add_to_cart'),
    path('update-cart/<int:cart_id>/',         views.update_cart,      name='update_cart'),
    path('remove-from-cart/<int:cart_id>/',    views.remove_from_cart, name='remove_from_cart'),

    # ── ORDERS ────────────────────────────────────────────────
    path('checkout/',                     views.checkout,       name='checkout'),
    path('payment/',                      views.payment,        name='payment'),
    path('payment/process/',              views.process_payment, name='process_payment'),
    path('order-confirm/<int:order_id>/', views.order_confirm,  name='order_confirm'),
    path('orders/',                       views.order_history,  name='order_history'),

    # ── PROFILE ───────────────────────────────────────────────
    path('profile/', views.profile_view, name='profile'),

    # ── ADMIN PANEL ───────────────────────────────────────────
    path('admin-panel/',                                      views.admin_dashboard,           name='admin_dashboard'),
    path('admin-panel/products/',                             views.admin_products,            name='admin_products'),
    path('admin-panel/products/add/',                         views.admin_add_product,         name='admin_add_product'),
    path('admin-panel/products/edit/<int:product_id>/',       views.admin_edit_product,        name='admin_edit_product'),
    path('admin-panel/products/delete/<int:product_id>/',     views.admin_delete_product,      name='admin_delete_product'),
    path('admin-panel/orders/',                               views.admin_orders,              name='admin_orders'),
    path('admin-panel/orders/<int:order_id>/',                views.admin_order_detail,        name='admin_order_detail'),
    path('admin-panel/orders/<int:order_id>/status/',         views.admin_update_order_status, name='admin_update_order_status'),
    path('admin-panel/orders/<int:order_id>/bill/',           views.admin_download_bill,       name='admin_download_bill'),
]
