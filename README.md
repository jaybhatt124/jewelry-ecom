# LuxeAura Jewels - E-Commerce Website

LuxeAura Jewels is a clean, simple, and fully functional luxury e-commerce website built entirely with the Django framework. This project serves as a comprehensive college project meant to demonstrate core capabilities of web development, database handling, authentication, and templating aesthetics using a vanilla tech stack, prioritizing high-quality design without the bulk of overly complex third-party API gateways.

## 🚀 Features

- **Authentication System:** Full login, logout, and registration flows with dynamic password visibility toggles and active session management.
- **Product Catalog:** Featured products, responsive grid layouts, and active product category filtering and sorting.
- **Dynamic Shopping Cart:** Add to cart logic, quantity adjustment, automated stock limitations, subtotal calculations, and item removal.
- **Product Details & Reviews:** Immersive detail pages equipped with live Star Rating displays, related products, and the ability for verified users to submit reviews.
- **Checkout Processing:** Straightforward Cash on Delivery (COD) processing with dynamic stock reductions and robust order bindings.
- **User Dashboard:** Dedicated user profiles capable of storing addresses, phone numbers, avatars, processing password changes, and displaying past order histories.
- **Admin Management:** fully integrated Django Administration panel to manage Orders, Users, Categories, Settings, and Products.

---

## 💻 Tech Stack Used

- **Backend Framework:** Django 5.2 (Latest Stable)
- **Programming Language:** Python 3.11+
- **Database Architecture:** SQLite (Standard Django Configuration)
- **Frontend UI / Templating:** HTML5, CSS3, JavaScript (Vanilla), Django Template Engine
- **Styling Libraries:** Bootstrap 5 (Responsive Layouts), FontAwesome (Icons), Google Fonts (Playfair Display / Lato)
- **Environment Management:** Python `venv`

---

## ⚙️ Installation & Setup Guide

Follow these steps to launch the LuxeAura development server on your machine natively.

### 1. Requirements
Ensure you have Python installed globally on your machine (Preferably Python 3.10 or higher).

### 2. Activate the Virtual Environment
Navigate to the project directory containing your `manage.py` file and activate the environment.
```bash
# On Windows PowerShell
.\venv\Scripts\Activate.ps1

# On Mac/Linux
source venv/bin/activate
```

### 3. Install Dependencies
*(Note: If the `venv` already has Django installed, you may skip this step)*
If installing on a fresh clone, run:
```bash
pip install django pillow
```

### 4. Apply Database Migrations
Ensure the SQLite database schema is built and updated.
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create an Administrator Account
You will need a Superuser account to bypass standard user permissions and add Products or Categories from the backend dashboard:
```bash
python manage.py createsuperuser
```
*(Follow the prompt to set your admin username, email, and password)*

### 6. Run the Development Server
```bash
python manage.py runserver
```

### 7. Access the Application
- **Main Website:** Go to `http://127.0.0.1:8000/` in your browser.
- **Admin Dashboard:** Go to `http://127.0.0.1:8000/admin/` and log in with your superuser credentials to manage the store.

---

## 🎨 Theme Notes for Developers
LuxeAura uses a custom minimal beige and gold luxury theme embedded globally through `style.css` and Bootstrap integration.
- Primary Gold Accent: `#cfa052`
- Primary Typography: `Playfair Display` (Serif style for Headings)

This project does not implement real Payment Gateways (Stripe/PayPal) and instead strictly relies on form-driven Cash on Delivery processing suitable for academic and local demonstrations.
