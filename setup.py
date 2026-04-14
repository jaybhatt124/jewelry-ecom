#!/usr/bin/env python3
"""
LuxeAura Setup Script
Run this once to initialize the database and create the admin user.
"""
import os
import sys
import django

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'luxeaura.settings')
django.setup()

from django.contrib.auth.models import User
from store.models import Category, Product

print("=== LuxeAura Setup ===\n")

# Create admin user
print("Creating admin user...")
try:
    admin = User.objects.get(username='admin')
    admin.email = 'admin@gmail.com'
    admin.is_staff = True
    admin.is_superuser = True
    admin.set_password('admin@123')
    admin.save()
    print("  ✓ Admin user updated")
except User.DoesNotExist:
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@gmail.com',
        password='admin@123'
    )
    print("  ✓ Admin user created")

print(f"\n  Admin Login: admin@gmail.com / admin@123")
print(f"  Username: admin\n")

# Create sample categories
print("Creating sample categories...")
cats = ['Rings', 'Necklaces', 'Earrings', 'Bracelets', 'Bangles', 'Pendants']
for cat_name in cats:
    cat, created = Category.objects.get_or_create(name=cat_name)
    if created:
        print(f"  ✓ Category: {cat_name}")

# Create sample products
print("\nCreating sample products...")
samples = [
    {
        'name': 'Diamond Solitaire Ring',
        'category': 'Rings',
        'description': 'A timeless 18k gold ring featuring a brilliant 0.5ct diamond solitaire. Perfect for engagements and special occasions.',
        'price': 45000,
        'stock': 10,
        'for_whom': 'Women',
    },
    {
        'name': 'Gold Chain Necklace',
        'category': 'Necklaces',
        'description': 'Elegant 22k gold chain necklace, 18 inches long. A versatile piece that pairs beautifully with any outfit.',
        'price': 28500,
        'stock': 15,
        'for_whom': 'Both',
    },
    {
        'name': 'Pearl Drop Earrings',
        'category': 'Earrings',
        'description': 'Freshwater pearl drop earrings set in sterling silver. Classic and sophisticated for every occasion.',
        'price': 8500,
        'stock': 20,
        'for_whom': 'Women',
    },
    {
        'name': "Men's Silver Bracelet",
        'category': 'Bracelets',
        'description': 'Heavy gauge sterling silver bracelet with a brushed finish. Bold and masculine styling.',
        'price': 12000,
        'stock': 8,
        'for_whom': 'Men',
    },
    {
        'name': 'Gold Kada Bangle',
        'category': 'Bangles',
        'description': 'Traditional 22k gold kada bangle with intricate engravings. Available in sizes S, M, L.',
        'price': 35000,
        'stock': 12,
        'for_whom': 'Women',
    },
    {
        'name': 'Ruby Heart Pendant',
        'category': 'Pendants',
        'description': 'Heart-shaped ruby pendant set in 18k rose gold. A romantic and unique gift for someone special.',
        'price': 18500,
        'stock': 7,
        'for_whom': 'Women',
    },
]

for item in samples:
    if not Product.objects.filter(name=item['name']).exists():
        cat = Category.objects.get(name=item['category'])
        Product.objects.create(
            name=item['name'],
            category=cat,
            description=item['description'],
            price=item['price'],
            stock=item['stock'],
            for_whom=item['for_whom'],
        )
        print(f"  ✓ Product: {item['name']}")

print("\n=== Setup Complete! ===")
print("\nRun the server with:")
print("  python manage.py runserver")
print("\nVisit:")
print("  Store:  http://localhost:8000/")
print("  Admin:  http://localhost:8000/admin-panel/")
print("  Login:  admin / admin@123")
