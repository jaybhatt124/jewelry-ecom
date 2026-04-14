"""
LuxeAura Database Viewer
========================
Run this script to browse your database tables in the terminal.

Usage:
    python db_viewer.py
    python db_viewer.py users
    python db_viewer.py orders
    python db_viewer.py products
    python db_viewer.py categories
    python db_viewer.py cart
    python db_viewer.py orderitems
    python db_viewer.py reviews
    python db_viewer.py otp
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'luxeaura.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth.models import User
from store.models import (
    Category, Product, Cart, Order, OrderItem,
    Review, UserProfile, ContactMessage, PasswordResetOTP
)

SEP  = '-' * 80
DSEP = '=' * 80

def header(title):
    print(f'\n{DSEP}')
    print(f'  {title}')
    print(DSEP)

def row(*cols, widths):
    line = ''
    for val, w in zip(cols, widths):
        s = str(val)[:w-2]
        line += s.ljust(w)
    print(line)

def show_users():
    header('TABLE: Users (auth_user)')
    users = User.objects.all().order_by('id')
    print(f'Total records: {users.count()}\n')
    widths = [5, 20, 30, 10, 10]
    row('ID', 'Username', 'Email', 'Staff', 'Active', widths=widths)
    print(SEP)
    for u in users:
        row(u.id, u.username, u.email or '—', u.is_staff, u.is_active, widths=widths)

def show_products():
    header('TABLE: Products (store_product)')
    items = Product.objects.select_related('category').order_by('id')
    print(f'Total records: {items.count()}\n')
    widths = [5, 25, 15, 10, 8, 10]
    row('ID', 'Name', 'Category', 'Price', 'Stock', 'For Whom', widths=widths)
    print(SEP)
    for p in items:
        row(p.id, p.name, p.category.name, f'Rs.{p.price}', p.stock, p.for_whom, widths=widths)

def show_categories():
    header('TABLE: Categories (store_category)')
    cats = Category.objects.all().order_by('id')
    print(f'Total records: {cats.count()}\n')
    widths = [5, 40]
    row('ID', 'Name', widths=widths)
    print(SEP)
    for c in cats:
        row(c.id, c.name, widths=widths)

def show_orders():
    header('TABLE: Orders (store_order)')
    orders = Order.objects.select_related('user').order_by('-id')
    print(f'Total records: {orders.count()}\n')
    widths = [5, 20, 15, 12, 30]
    row('ID', 'Customer', 'Total', 'Status', 'Date', widths=widths)
    print(SEP)
    for o in orders:
        row(o.id, o.user.username, f'Rs.{o.total_price}', o.status,
            o.created_at.strftime('%Y-%m-%d %H:%M'), widths=widths)
        # show items under each order
        for item in o.items.all():
            print(f'     └─ {item.product.name} x{item.quantity}  Rs.{item.price}')

def show_orderitems():
    header('TABLE: Order Items (store_orderitem)')
    items = OrderItem.objects.select_related('order','product').order_by('-id')
    print(f'Total records: {items.count()}\n')
    widths = [5, 8, 25, 8, 10]
    row('ID', 'OrderID', 'Product', 'Qty', 'Price', widths=widths)
    print(SEP)
    for i in items:
        row(i.id, i.order.id, i.product.name, i.quantity, f'Rs.{i.price}', widths=widths)

def show_cart():
    header('TABLE: Cart Items (store_cart)')
    cart = Cart.objects.select_related('user','product').order_by('user')
    print(f'Total records: {cart.count()}\n')
    widths = [5, 20, 30, 8]
    row('ID', 'User', 'Product', 'Qty', widths=widths)
    print(SEP)
    for c in cart:
        row(c.id, c.user.username, c.product.name, c.quantity, widths=widths)

def show_reviews():
    header('TABLE: Reviews (store_review)')
    reviews = Review.objects.select_related('user','product').order_by('-id')
    print(f'Total records: {reviews.count()}\n')
    widths = [5, 20, 25, 8, 30]
    row('ID', 'User', 'Product', 'Rating', 'Comment', widths=widths)
    print(SEP)
    for r in reviews:
        row(r.id, r.user.username, r.product.name, f'{r.rating}/5', r.comment[:28], widths=widths)

def show_otp():
    header('TABLE: Password Reset OTPs (store_passwordresetotp)')
    otps = PasswordResetOTP.objects.order_by('-id')
    print(f'Total records: {otps.count()}\n')
    widths = [5, 30, 8, 8, 22]
    row('ID', 'Email', 'OTP', 'Used', 'Created At', widths=widths)
    print(SEP)
    for o in otps:
        row(o.id, o.email, o.otp, o.is_used,
            o.created_at.strftime('%Y-%m-%d %H:%M:%S'), widths=widths)

def show_all():
    show_users()
    show_categories()
    show_products()
    show_orders()
    show_cart()
    show_reviews()
    show_otp()

TABLE_MAP = {
    'users':      show_users,
    'products':   show_products,
    'categories': show_categories,
    'orders':     show_orders,
    'orderitems': show_orderitems,
    'cart':       show_cart,
    'reviews':    show_reviews,
    'otp':        show_otp,
    'all':        show_all,
}

if __name__ == '__main__':
    arg = sys.argv[1].lower() if len(sys.argv) > 1 else 'all'
    fn  = TABLE_MAP.get(arg)
    if fn:
        fn()
    else:
        print(f'\nUnknown table "{arg}". Available options:')
        for k in TABLE_MAP:
            print(f'  python db_viewer.py {k}')
    print()
