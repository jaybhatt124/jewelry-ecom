import random
import string
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings as django_settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from django.http import HttpResponse
from django.db.models import Sum
from .models import Product, Category, Cart, Order, OrderItem, Review, UserProfile, ContactMessage, PasswordResetOTP
from .forms import RegistrationForm, LoginForm, CheckoutForm, ReviewForm, UserForm, UserProfileForm, ContactForm, ProductForm


def home(request):
    if not request.user.is_authenticated:
        return redirect('login')
    featured_products = Product.objects.all().order_by('-created_at')[:4]
    categories = Category.objects.all()
    return render(request, 'home.html', {'featured_products': featured_products, 'categories': categories})


def shop(request):
    products = Product.objects.all()
    categories = Category.objects.all()
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)
    for_whom = request.GET.get('for_whom')
    if for_whom:
        products = products.filter(for_whom=for_whom)
    sort = request.GET.get('sort')
    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    context = {
        'products': products, 'categories': categories,
        'selected_category': int(category_id) if category_id else None, 'selected_sort': sort
    }
    return render(request, 'shop.html', context)


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    reviews = product.reviews.all().order_by('-created_at')
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    user_has_reviewed = False
    if request.user.is_authenticated:
        user_has_reviewed = Review.objects.filter(user=request.user, product=product).exists()
    if request.method == 'POST' and request.user.is_authenticated:
        if user_has_reviewed:
            messages.error(request, 'You have already reviewed this product.')
        else:
            review_form = ReviewForm(request.POST)
            if review_form.is_valid():
                review = review_form.save(commit=False)
                review.product = product
                review.user = request.user
                review.save()
                messages.success(request, 'Your review has been submitted!')
                return redirect('product_detail', product_id=product.id)
    else:
        review_form = ReviewForm()
    context = {'product': product, 'reviews': reviews, 'related_products': related_products,
               'review_form': review_form, 'user_has_reviewed': user_has_reviewed}
    return render(request, 'product_detail.html', context)


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            UserProfile.objects.create(user=user)
            messages.success(request, 'Registration successful! Please login.')
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        return redirect('home')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                if user.is_staff:
                    return redirect('admin_dashboard')
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('home')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('home')


@login_required
def cart_view(request):
    cart_items = Cart.objects.filter(user=request.user)
    subtotal = sum(item.subtotal() for item in cart_items)
    return render(request, 'cart.html', {'cart_items': cart_items, 'subtotal': subtotal})


def add_to_cart(request, product_id):
    if not request.user.is_authenticated:
        messages.error(request, 'Please login to add items to your cart.')
        return redirect('login')
    product = get_object_or_404(Product, id=product_id)
    if product.stock <= 0:
        messages.error(request, 'Sorry, this item is out of stock.')
        return redirect('product_detail', product_id=product.id)
    cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)
    if not created:
        if cart_item.quantity < product.stock:
            cart_item.quantity += 1
            cart_item.save()
            messages.success(request, 'Quantity updated in your cart.')
        else:
            messages.error(request, 'Cannot add more. Stock limit reached.')
    else:
        messages.success(request, 'Added to your cart.')
    return redirect('cart')


@login_required
def update_cart(request, cart_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(Cart, id=cart_id, user=request.user)
        action = request.POST.get('action')
        if action == 'increase':
            if cart_item.quantity < cart_item.product.stock:
                cart_item.quantity += 1
                cart_item.save()
            else:
                messages.error(request, 'Cannot exceed available stock.')
        elif action == 'decrease':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart_item.delete()
                messages.success(request, 'Item removed from cart.')
    return redirect('cart')


@login_required
def remove_from_cart(request, cart_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(Cart, id=cart_id, user=request.user)
        cart_item.delete()
        messages.success(request, 'Item removed from your cart.')
    return redirect('cart')


@login_required
def checkout(request):
    cart_items = Cart.objects.filter(user=request.user)
    if not cart_items.exists():
        messages.error(request, 'Your cart is empty.')
        return redirect('shop')
    subtotal = sum(item.subtotal() for item in cart_items)
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            address = form.cleaned_data['address']
            for item in cart_items:
                if item.quantity > item.product.stock:
                    messages.error(request, f'Not enough stock for {item.product.name}.')
                    return redirect('cart')
            request.session['checkout_address'] = address
            return redirect('payment')
    else:
        initial_data = {}
        try:
            if request.user.profile.address:
                initial_data['address'] = request.user.profile.address
        except UserProfile.DoesNotExist:
            pass
        form = CheckoutForm(initial=initial_data)
    return render(request, 'checkout.html', {'cart_items': cart_items, 'subtotal': subtotal, 'form': form})


@login_required
def order_confirm(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'order_confirm.html', {'order': order})


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'order_history.html', {'orders': orders})


@login_required
def profile_view(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    total_orders = Order.objects.filter(user=request.user).count()
    if request.method == 'POST':
        if 'update_profile' in request.POST:
            user_form = UserForm(request.POST, instance=request.user)
            profile_form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('profile')
        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            user_form = UserForm(instance=request.user)
            profile_form = UserProfileForm(instance=user_profile)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password updated!')
                return redirect('profile')
            else:
                messages.error(request, 'Please correct the error below.')
                return render(request, 'profile.html', {
                    'user_form': user_form, 'profile_form': profile_form,
                    'password_form': password_form, 'total_orders': total_orders
                })
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=user_profile)
        password_form = PasswordChangeForm(request.user)
    context = {'user_form': user_form, 'profile_form': profile_form,
               'password_form': password_form, 'total_orders': total_orders}
    return render(request, 'profile.html', context)


def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Thank you! Your message has been sent.')
            return redirect('contact')
    else:
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {'name': request.user.username, 'email': request.user.email}
        form = ContactForm(initial=initial_data)
    return render(request, 'contact.html', {'form': form})


def about_view(request):
    return render(request, 'about.html')


# ─────────────────────────────────────────────
# ADMIN VIEWS
# ─────────────────────────────────────────────

def staff_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_staff:
            messages.error(request, 'Access denied. Admin only.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


@staff_required
def admin_dashboard(request):
    total_orders = Order.objects.count()
    total_products = Product.objects.count()
    total_users = User.objects.filter(is_staff=False).count()
    total_revenue = Order.objects.aggregate(Sum('total_price'))['total_price__sum'] or 0
    recent_orders = Order.objects.order_by('-created_at')[:8]
    recent_products = Product.objects.order_by('-created_at')[:5]
    context = {
        'total_orders': total_orders, 'total_products': total_products,
        'total_users': total_users, 'total_revenue': total_revenue,
        'recent_orders': recent_orders, 'recent_products': recent_products,
    }
    return render(request, 'admin_dashboard.html', context)


@staff_required
def admin_products(request):
    products = Product.objects.all().order_by('-created_at')
    return render(request, 'admin_products.html', {'products': products})


@staff_required
def admin_add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product added successfully! Now visible to customers.')
            return redirect('admin_products')
    else:
        form = ProductForm()
    return render(request, 'admin_product_form.html', {'form': form, 'product': None})


@staff_required
def admin_edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('admin_products')
    else:
        form = ProductForm(instance=product)
    return render(request, 'admin_product_form.html', {'form': form, 'product': product})


@staff_required
def admin_delete_product(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        product.delete()
        messages.success(request, 'Product deleted.')
    return redirect('admin_products')


@staff_required
def admin_orders(request):
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'admin_orders.html', {'orders': orders})


@staff_required
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'admin_order_detail.html', {'order': order})


@staff_required
def admin_update_order_status(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')
        if new_status in ['Pending', 'Shipped', 'Delivered']:
            order.status = new_status
            order.save()
            messages.success(request, f'Order #{order.id} updated to {new_status}.')
    return redirect(request.META.get('HTTP_REFERER', 'admin_orders'))


@staff_required
def admin_download_bill(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    items = order.items.all()

    rows = ""
    for i, item in enumerate(items, 1):
        subtotal = item.quantity * item.price
        rows += f"""
      <tr>
        <td>{i}</td>
        <td><strong>{item.product.name}</strong><br><span style="font-size:0.8rem;color:#6B5E52">{item.product.category.name} · For {item.product.for_whom}</span></td>
        <td style="text-align:center">{item.quantity}</td>
        <td style="text-align:right">&#8377;{item.price}</td>
        <td style="text-align:right"><strong>&#8377;{subtotal}</strong></td>
      </tr>"""

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Invoice LXA-{order.id:05d}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,400&family=Jost:wght@300;400;500&display=swap');
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{font-family:'Jost',sans-serif;background:#fff;color:#1A1614;padding:50px;max-width:800px;margin:0 auto;font-size:14px}}
  .no-print{{background:#1A1614;color:#C9A84C;padding:14px 20px;margin:-50px -50px 40px;display:flex;justify-content:space-between;align-items:center}}
  .no-print span{{font-family:'Cormorant Garamond',serif;font-size:1.1rem;letter-spacing:2px}}
  .print-btn{{background:#C9A84C;color:#1A1614;border:none;padding:9px 22px;cursor:pointer;font-family:'Jost',sans-serif;font-weight:500;font-size:0.85rem;letter-spacing:1px;border-radius:2px;margin-left:8px}}
  .close-btn{{background:transparent;color:#888;border:1px solid #444;padding:9px 18px;cursor:pointer;font-family:'Jost',sans-serif;font-size:0.8rem;border-radius:2px}}
  .header{{display:flex;justify-content:space-between;align-items:flex-start;padding-bottom:25px;margin-bottom:30px;border-bottom:3px solid #C9A84C}}
  .logo{{font-family:'Cormorant Garamond',serif;font-size:3rem;font-weight:300;color:#C9A84C;letter-spacing:5px;line-height:1}}
  .logo em{{color:#1A1614;font-style:italic}}
  .logo-sub{{font-size:0.75rem;letter-spacing:4px;text-transform:uppercase;color:#6B5E52;margin-top:5px}}
  .inv-meta{{text-align:right}}
  .inv-meta h2{{font-family:'Cormorant Garamond',serif;font-size:2rem;font-weight:300;letter-spacing:3px;margin-bottom:8px}}
  .inv-meta p{{font-size:0.85rem;color:#6B5E52;line-height:1.8}}
  .inv-meta strong{{color:#1A1614}}
  .badge{{display:inline-block;padding:3px 12px;border-radius:20px;font-size:0.75rem;font-weight:500}}
  .badge-pending{{background:#fff3cd;color:#856404}}
  .badge-shipped{{background:#cce5ff;color:#004085}}
  .badge-delivered{{background:#d4edda;color:#155724}}
  .two-col{{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:30px}}
  .info-box{{background:#FAF7F2;border:1px solid #E8DDD0;border-radius:4px;padding:18px}}
  .info-box h3{{font-size:0.65rem;letter-spacing:3px;text-transform:uppercase;color:#6B5E52;margin-bottom:10px;border-bottom:1px solid #E8DDD0;padding-bottom:6px}}
  .info-box p{{line-height:1.8;font-size:0.9rem}}
  table{{width:100%;border-collapse:collapse;margin-bottom:0}}
  thead tr{{background:#1A1614}}
  th{{color:#C9A84C;padding:12px 15px;text-align:left;font-size:0.7rem;letter-spacing:2px;text-transform:uppercase;font-weight:400}}
  td{{padding:12px 15px;border-bottom:1px solid #E8DDD0;vertical-align:top}}
  tbody tr:last-child td{{border-bottom:none}}
  tbody tr:nth-child(even){{background:#FDFAF6}}
  .totals{{border-top:2px solid #C9A84C;padding:15px 15px 0}}
  .t-row{{display:flex;justify-content:space-between;padding:6px 0;font-size:0.9rem}}
  .t-row.grand{{font-size:1.2rem;font-weight:600;color:#8B6914;border-top:1px dashed #C9A84C;margin-top:6px;padding-top:10px}}
  .footer{{text-align:center;margin-top:40px;padding:20px;border-top:1px solid #E8DDD0;font-style:italic;color:#6B5E52;font-size:0.85rem;line-height:1.8}}
  @media print{{.no-print{{display:none!important}}body{{padding:20px}}}}
</style>
</head>
<body>

<div class="no-print">
  <span>LuxeAura · Invoice Preview</span>
  <div>
    <button class="print-btn" onclick="window.print()">🖨 Print / Save PDF</button>
    <button class="close-btn" onclick="window.close()">✕ Close</button>
  </div>
</div>

<div class="header">
  <div>
    <div class="logo">Luxe<em>Aura</em></div>
    <div class="logo-sub">Fine Jewellery Since 1987</div>
  </div>
  <div class="inv-meta">
    <h2>INVOICE</h2>
    <p>Invoice No: <strong>LXA-{order.id:05d}</strong></p>
    <p>Date: <strong>{order.created_at.strftime('%B %d, %Y')}</strong></p>
    <p>Status: <span class="badge badge-{order.status.lower()}">{order.status}</span></p>
  </div>
</div>

<div class="two-col">
  <div class="info-box">
    <h3>Bill To</h3>
    <p><strong>{order.user.username}</strong><br>
    {order.user.email or 'No email on file'}<br>
    <span style="color:#6B5E52">&#128205; {order.address}</span></p>
  </div>
  <div class="info-box">
    <h3>Payment Details</h3>
    <p>Method: <strong>Cash on Delivery</strong><br>
    Order ID: <strong>#{order.id}</strong><br>
    Items: <strong>{items.count()} item(s)</strong></p>
  </div>
</div>

<table>
  <thead>
    <tr>
      <th style="width:40px">#</th>
      <th>Item Description</th>
      <th style="text-align:center;width:60px">Qty</th>
      <th style="text-align:right;width:100px">Unit Price</th>
      <th style="text-align:right;width:110px">Amount</th>
    </tr>
  </thead>
  <tbody>
    {rows}
  </tbody>
</table>

<div class="totals">
  <div class="t-row"><span>Subtotal</span><span>&#8377;{order.total_price}</span></div>
  <div class="t-row"><span>Shipping</span><span style="color:#2e7d32">FREE</span></div>
  <div class="t-row"><span>GST / Tax</span><span>Included</span></div>
  <div class="t-row grand"><span>Grand Total</span><span>&#8377;{order.total_price}</span></div>
</div>

<div class="footer">
  Thank you for shopping with LuxeAura — where beauty meets craft.<br>
  For queries: support@luxeaura.com &nbsp;|&nbsp; +91 98765 43210<br>
  <span style="font-size:0.75rem;color:#aaa">This is a computer-generated invoice and does not require a signature.</span>
</div>

</body>
</html>"""

    response = HttpResponse(html, content_type='text/html; charset=utf-8')
    response['Content-Disposition'] = f'inline; filename="LuxeAura_Invoice_{order.id}.html"'
    return response


# ─────────────────────────────────────────────
# OTP-BASED FORGOT PASSWORD VIEWS
# ─────────────────────────────────────────────

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))


def forgot_password_email(request):
    """Step 1 - User enters email, 6-digit OTP sent via SMTP"""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        if not email:
            return render(request, 'forgot_password.html', {'error': 'Please enter your email address.'})

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return render(request, 'forgot_password.html', {
                'error': 'No account found with this email address.'
            })

        # Delete old OTPs for this email
        PasswordResetOTP.objects.filter(email=email).delete()

        # Create new OTP
        otp_code = generate_otp()
        PasswordResetOTP.objects.create(email=email, otp=otp_code)

        # Send via SMTP
        try:
            send_mail(
                subject='Your LuxeAura Password Reset OTP',
                message=(
                    f'Hello {user.username},\n\n'
                    f'Your OTP for password reset is:\n\n'
                    f'        {otp_code}\n\n'
                    f'This OTP is valid for {getattr(django_settings, "OTP_EXPIRE_MINUTES", 10)} minutes.\n'
                    f'Do not share it with anyone.\n\n'
                    f'If you did not request this, please ignore this email.\n\n'
                    f'— LuxeAura Team'
                ),
                from_email=django_settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as e:
            return render(request, 'forgot_password.html', {
                'error': f'Could not send email. Please check SMTP settings in settings.py. ({str(e)})'
            })

        request.session['otp_email'] = email
        return redirect('forgot_password_verify')

    return render(request, 'forgot_password.html')


def forgot_password_verify(request):
    """Step 2 - Single page: OTP box + new password + confirm + login link"""
    if request.user.is_authenticated:
        return redirect('home')

    email = request.session.get('otp_email')
    if not email:
        return redirect('forgot_password')

    if request.method == 'POST':
        otp_entered      = request.POST.get('otp', '').strip()
        new_password     = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        if not otp_entered or not new_password or not confirm_password:
            return render(request, 'forgot_password_verify.html', {
                'email': email, 'error': 'All fields are required.'
            })

        if new_password != confirm_password:
            return render(request, 'forgot_password_verify.html', {
                'email': email, 'error': 'Passwords do not match.'
            })

        if len(new_password) < 6:
            return render(request, 'forgot_password_verify.html', {
                'email': email, 'error': 'Password must be at least 6 characters long.'
            })

        # Verify OTP within expiry window
        expire_minutes = getattr(django_settings, 'OTP_EXPIRE_MINUTES', 10)
        cutoff = timezone.now() - timezone.timedelta(minutes=expire_minutes)

        otp_record = PasswordResetOTP.objects.filter(
            email=email,
            otp=otp_entered,
            is_used=False,
            created_at__gte=cutoff
        ).last()

        if not otp_record:
            return render(request, 'forgot_password_verify.html', {
                'email': email,
                'error': 'OTP is invalid or has expired. Please request a new one.'
            })

        # Valid — update password
        try:
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            otp_record.is_used = True
            otp_record.save()
            if 'otp_email' in request.session:
                del request.session['otp_email']
            return render(request, 'forgot_password_verify.html', {'success': True})
        except User.DoesNotExist:
            return redirect('forgot_password')

    return render(request, 'forgot_password_verify.html', {'email': email})


import random
import string
from django.core.mail import EmailMultiAlternatives

def send_order_receipt(order):
    user  = order.user
    items = order.items.all()
    rows = ""
    for item in items:
        rows += f"<tr><td style='padding:8px 12px;border-bottom:1px solid #f0e8dc'>{item.product.name}</td><td style='padding:8px 12px;border-bottom:1px solid #f0e8dc;text-align:center'>{item.quantity}</td><td style='padding:8px 12px;border-bottom:1px solid #f0e8dc;text-align:right'>Rs.{item.subtotal()}</td></tr>"
    html_body = f"""
    <div style='max-width:600px;margin:0 auto;font-family:Calibri,sans-serif'>
      <div style='background:#1A1614;padding:24px;text-align:center'>
        <h1 style='color:#C9A84C;font-family:Georgia,serif;font-weight:300;letter-spacing:6px;margin:0'>LuxeAura</h1>
      </div>
      <div style='background:#27ae60;padding:12px;text-align:center'>
        <p style='color:#fff;margin:0;font-weight:600'>Payment Successful — Order Confirmed</p>
      </div>
      <div style='padding:24px;background:#fff'>
        <p>Hello <strong>{user.username}</strong>,</p>
        <p style='color:#6B5E52'>Your payment was successful. Here is your receipt.</p>
        <table style='width:100%;border-collapse:collapse;margin:16px 0;font-size:0.9rem'>
          <tr><td style='color:#888;padding:4px 0'>Order Number</td><td style='text-align:right;font-weight:700'>#{order.id:05d}</td></tr>
          <tr><td style='color:#888;padding:4px 0'>Payment Method</td><td style='text-align:right;color:#C9A84C;font-weight:600'>{order.payment_method}</td></tr>
          <tr><td style='color:#888;padding:4px 0'>Transaction ID</td><td style='text-align:right;font-family:monospace'>{order.payment_id}</td></tr>
          <tr><td style='color:#888;padding:4px 0'>Delivery Address</td><td style='text-align:right'>{order.address}</td></tr>
        </table>
        <table style='width:100%;border-collapse:collapse'>
          <thead><tr style='background:#1A1614'><th style='padding:8px 12px;color:#C9A84C;text-align:left;font-weight:400'>Item</th><th style='padding:8px 12px;color:#C9A84C;text-align:center;font-weight:400'>Qty</th><th style='padding:8px 12px;color:#C9A84C;text-align:right;font-weight:400'>Total</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>
        <div style='border-top:2px solid #C9A84C;padding:12px 0;display:flex;justify-content:space-between;font-size:1.1rem;font-weight:700'>
          <span>Grand Total</span><span style='color:#8B6914'>Rs.{order.total_price}</span>
        </div>
      </div>
      <div style='background:#1A1614;padding:12px;text-align:center'>
        <span style='color:#C9A84C;letter-spacing:4px;font-family:Georgia,serif'>LUXEAURA</span>
      </div>
    </div>"""
    try:
        msg = EmailMultiAlternatives(
            subject=f"LuxeAura — Order #{order.id:05d} Confirmed",
            body=f"Hello {user.username}, your order #{order.id} is confirmed. Total: Rs.{order.total_price}",
            from_email=django_settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send()
    except Exception as e:
        print(f"Receipt email error: {e}")


@login_required
def payment(request):
    address = request.session.get('checkout_address')
    if not address:
        return redirect('checkout')
    cart_items = Cart.objects.filter(user=request.user)
    if not cart_items.exists():
        return redirect('shop')
    subtotal = sum(item.subtotal() for item in cart_items)
    return render(request, 'payment.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'address': address,
    })


@login_required
def process_payment(request):
    if request.method != 'POST':
        return redirect('payment')
    address = request.session.get('checkout_address')
    if not address:
        return redirect('checkout')
    cart_items = Cart.objects.filter(user=request.user)
    if not cart_items.exists():
        return redirect('shop')
    for item in cart_items:
        if item.quantity > item.product.stock:
            messages.error(request, f'Sorry, {item.product.name} is out of stock.')
            return redirect('cart')
    subtotal   = sum(item.subtotal() for item in cart_items)
    pay_method = request.POST.get('pay_method', 'Demo Card')
    pay_id     = 'LXA' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    order = Order.objects.create(
        user=request.user,
        total_price=subtotal,
        address=address,
        status='Pending',
        payment_method=pay_method,
        payment_id=pay_id,
    )
    for item in cart_items:
        OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity, price=item.product.price)
        item.product.stock -= item.quantity
        item.product.save()
    cart_items.delete()
    if 'checkout_address' in request.session:
        del request.session['checkout_address']
    if request.user.email:
        send_order_receipt(order)
    return redirect('order_confirm', order_id=order.id)
