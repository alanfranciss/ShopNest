from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Product

def index(request):
    products = Product.objects.all().order_by('-created_at')[:8]
    return render(request, 'index.html', {'products': products})

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # We are using email as the username
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            
            from .models import UserProfile
            profile, _ = UserProfile.objects.get_or_create(user=user)
            if profile.cart_data:
                request.session['cart'] = profile.cart_data
            if profile.wishlist_data:
                request.session['wishlist'] = profile.wishlist_data
                
            if user.is_superuser:
                return redirect('admin_dash')
            else:
                return redirect('index')
        else:
            messages.error(request, 'Invalid email or password.')

    return render(request, 'login.html')

def logout_view(request):
    if request.user.is_authenticated:
        from .models import UserProfile
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        
        cart_data = request.session.get('cart')
        wishlist_data = request.session.get('wishlist')
        
        if cart_data is not None:
            profile.cart_data = cart_data
        if wishlist_data is not None:
            profile.wishlist_data = wishlist_data
            
        profile.save()

    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('index')

def signup_view(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('signup')

        if User.objects.filter(username=email).exists():
            messages.error(request, 'Email is already registered.')
            return redirect('signup')
        
        user = User.objects.create_user(
            username=email, 
            email=email, 
            password=password, 
            first_name=first_name, 
            last_name=last_name
        )
        user.save()
        messages.success(request, 'Account created successfully! Please login.')
        return redirect('login')

    return render(request, 'signup.html')

@login_required(login_url='login')
def admin_dash_view(request):
    if not request.user.is_superuser:
        return redirect('index')
    from .models import UserProfile
    pending_sellers = UserProfile.objects.filter(is_seller_pending=True).select_related('user')
    return render(request, 'admindash.html', {'pending_sellers': pending_sellers})

@login_required(login_url='login')
def approve_seller(request, user_id):
    if not request.user.is_superuser:
        return redirect('index')
    from .models import UserProfile
    profile = get_object_or_404(UserProfile, user__id=user_id)
    profile.is_seller = True
    profile.is_seller_pending = False
    profile.save()
    messages.success(request, f'Approved seller application for {profile.user.email}')
    return redirect('admin_dash')

@login_required(login_url='login')
def reject_seller(request, user_id):
    if not request.user.is_superuser:
        return redirect('index')
    from .models import UserProfile
    profile = get_object_or_404(UserProfile, user__id=user_id)
    profile.is_seller_pending = False
    profile.save()
    messages.success(request, f'Rejected seller application for {profile.user.email}')
    return redirect('admin_dash')

from .models import UserProfile, Order

@login_required(login_url='login')
def user_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.save()
        
        profile.phone = request.POST.get('phone', '')
        profile.address = request.POST.get('address', '')
        profile.city = request.POST.get('city', '')
        profile.zip_code = request.POST.get('zip_code', '')
        profile.save()
        
        messages.success(request, 'Your profile has been updated.')
        return redirect('user')
        
    return render(request, 'user.html', {'profile': profile, 'orders': orders})

from django.shortcuts import render, redirect, get_object_or_404
from .models import Category

def categories_view(request):
    categories = Category.objects.all()
    return render(request, 'categories.html', {'categories': categories})

from django.db.models import Q

def products_view(request):
    category_id = request.GET.get('category')
    search_query = request.GET.get('q')
    
    if category_id:
        category = get_object_or_404(Category, id=category_id)
        products = Product.objects.filter(category=category)
    else:
        category = None
        products = Product.objects.all()
        
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
        
    products = products.order_by('-created_at')
        
    return render(request, 'products.html', {'products': products, 'current_category': category, 'search_query': search_query})

def product_detail_view(request, id):
    product = get_object_or_404(Product, id=id)
    similar_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    return render(request, 'product_detail.html', {'product': product, 'similar_products': similar_products})

def about_view(request):
    return render(request, 'about.html')

from .cart import Cart
from django.views.decorators.http import require_POST

@require_POST
def cart_add(request, id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=id)
    quantity = int(request.POST.get('quantity', 1))
    update_quantity = request.POST.get('update_quantity', 'False') == 'True'
    
    if update_quantity and quantity <= 0:
        cart.remove(product)
        messages.warning(request, f'Removed {product.name} from your cart.')
    else:
        current_in_cart = cart.cart.get(str(product.id), {}).get('quantity', 0)
        target_quantity = quantity if update_quantity else current_in_cart + quantity
        
        if target_quantity > product.quantity:
            messages.error(request, f'Sorry, only {product.quantity} units of {product.name} are available in stock.')
            quantity = product.quantity if update_quantity else (product.quantity - current_in_cart)
            
            if not update_quantity and quantity <= 0:
                return redirect('cart_detail')

        if quantity > 0 or update_quantity:      
            cart.add(product=product, quantity=quantity, update_quantity=update_quantity)
            if update_quantity:
                messages.success(request, f'Updated quantity for {product.name}.')
            else:
                messages.success(request, f'Added {product.name} to your cart.')
            
    return redirect('cart_detail')

def cart_remove(request, id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=id)
    cart.remove(product)
    messages.warning(request, f'Removed {product.name} from your cart.')
    return redirect('cart_detail')

def cart_detail(request):
    cart = Cart(request)
    return render(request, 'cart.html', {'cart': cart})

from .wishlist import Wishlist

@require_POST
def wishlist_add(request, id):
    wishlist = Wishlist(request)
    product = get_object_or_404(Product, id=id)
    wishlist.add(product=product)
    messages.success(request, f'Added {product.name} to your wishlist.')
    return redirect(request.META.get('HTTP_REFERER', 'products'))

def wishlist_remove(request, id):
    wishlist = Wishlist(request)
    product = get_object_or_404(Product, id=id)
    wishlist.remove(product)
    messages.warning(request, f'Removed {product.name} from your wishlist.')
    return redirect(request.META.get('HTTP_REFERER', 'wishlist_detail'))

def wishlist_detail(request):
    wishlist = Wishlist(request)
    return render(request, 'wishlist.html', {'wishlist': wishlist})

from .models import Order, OrderItem

def checkout_view(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.warning(request, "Your cart is empty.")
        return redirect('products')
        
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        address = request.POST.get('address')
        city = request.POST.get('city')
        zip_code = request.POST.get('zip_code')
        payment_method = request.POST.get('payment_method', 'Credit Card')
        
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            first_name=first_name,
            last_name=last_name,
            email=email,
            address=address,
            city=city,
            zip_code=zip_code,
            payment_method=payment_method,
            total_amount=sum(item['price'] * item['quantity'] for item in cart)
        )
        
        for item in cart:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                price=item['price'],
                quantity=item['quantity']
            )
            
        cart.clear()
        request.session['order_id'] = order.id
        return redirect('order_success')
        
    return render(request, 'checkout.html', {'cart': cart})

def order_success_view(request):
    order_id = request.session.get('order_id')
    if not order_id:
        return redirect('index')
    
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'order_success.html', {'order': order})

@login_required(login_url='login')
def order_detail_view(request, id):
    order = get_object_or_404(Order, id=id)
    
    # Security check: ensure order belongs to the logged in user or is an admin
    if order.user != request.user and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to view this order.')
        return redirect('user')
        
    return render(request, 'order_detail.html', {'order': order})

@login_required(login_url='login')
@require_POST
def cancel_order_item(request, item_id):
    item = get_object_or_404(OrderItem, id=item_id)
    
    # Check if the user is the buyer or the seller
    is_buyer = item.order.user == request.user
    is_seller = item.product.seller == request.user
    
    if not (is_buyer or is_seller or request.user.is_superuser):
        messages.error(request, 'You do not have permission to cancel this item.')
        return redirect(request.META.get('HTTP_REFERER', 'index'))
        
    if item.status in ['Shipped', 'Delivered']:
        messages.error(request, 'Cannot cancel an item that has already been shipped or delivered.')
        return redirect(request.META.get('HTTP_REFERER', 'index'))
        
    item.status = 'Cancelled'
    item.save()
    item.order.status = 'Cancelled'
    item.order.save()
    
    messages.success(request, f'Item "{item.product.name}" has been cancelled.')
    return redirect(request.META.get('HTTP_REFERER', 'index'))

@login_required(login_url='login')
@require_POST
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if order.status in ['Shipped', 'Delivered']:
        messages.error(request, 'Cannot cancel an order that has already been shipped or delivered.')
        return redirect(request.META.get('HTTP_REFERER', 'index'))
        
    order.status = 'Cancelled'
    order.save()
    
    for item in order.items.all():
        if item.status not in ['Shipped', 'Delivered']:
            item.status = 'Cancelled'
            item.save()
            
    messages.success(request, f'Order #ORD-{order.id}9928 has been cancelled.')
    return redirect(request.META.get('HTTP_REFERER', 'index'))

@login_required(login_url='login')
def seller_dashboard_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    
    # Redirect non-sellers to registration
    if not profile.is_seller:
        return redirect('seller_registration')

    products = Product.objects.filter(seller=request.user).select_related('category').order_by('-created_at')
    
    products_by_category = {}
    for product in products:
        category_name = product.category.name if hasattr(product, 'category') and product.category else 'Uncategorized'
        if category_name not in products_by_category:
            products_by_category[category_name] = []
        products_by_category[category_name].append(product)
    
    # Fetch OrderItems instead of Orders
    seller_items = OrderItem.objects.filter(product__seller=request.user).select_related('order', 'product').order_by('-order__created_at')

    total_products = products.count()
    # Total unique orders
    total_orders = Order.objects.filter(items__product__seller=request.user).distinct().count()
    
    total_revenue = sum(
        item.price * item.quantity 
        for item in seller_items
    )

    context = {
        'products': products,
        'products_by_category': products_by_category,
        'seller_items': seller_items,
        'total_products': total_products,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'status_choices': OrderItem.STATUS_CHOICES,
    }
    return render(request, 'seller_dashboard.html', context)

from django.views.decorators.http import require_POST

@login_required(login_url='login')
@require_POST
def update_item_status(request, item_id):
    # Verify the item belongs to the seller
    item = get_object_or_404(OrderItem, id=item_id, product__seller=request.user)
    new_status = request.POST.get('status')
    tracking_number = request.POST.get('tracking_number')
    tracking_status = request.POST.get('tracking_status')
    
    valid_statuses = [choice[0] for choice in OrderItem.STATUS_CHOICES]
    if new_status in valid_statuses:
        item.status = new_status
        if tracking_number is not None:
            item.tracking_number = tracking_number
        if tracking_status is not None:
            item.tracking_status = tracking_status
        item.save()
        
        # Sync the parent order status
        item.order.status = new_status
        item.order.save()
        
        messages.success(request, f'Status for "{item.product.name}" updated to {new_status}.')
    else:
        messages.error(request, 'Invalid status update.')
        
    return redirect('seller_dashboard')


def seller_registration_view(request):
    if request.method == 'POST':
        # If user is already authenticated, request upgrade
        if request.user.is_authenticated:
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            if not profile.is_seller and not profile.is_seller_pending:
                profile.is_seller_pending = True
                profile.save()
                messages.success(request, 'Your request to become a seller has been submitted and is pending admin approval.')
            return redirect('seller_registration')
        
        # If user is new, register them and set as pending
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('seller_registration')

        if User.objects.filter(username=email).exists():
            messages.error(request, 'Email is already registered.')
            return redirect('seller_registration')
        
        user = User.objects.create_user(
            username=email, 
            email=email, 
            password=password, 
            first_name=first_name, 
            last_name=last_name
        )
        user.save()
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.is_seller_pending = True
        profile.save()
        
        # Log them in right away
        authenticated_user = authenticate(request, username=email, password=password)
        if authenticated_user:
            login(request, authenticated_user)
            messages.success(request, 'Account created! Your seller application is pending admin approval.')
            return redirect('seller_registration')
        else:
            messages.success(request, 'Seller account created and pending approval! Please login.')
            return redirect('login')

    return render(request, 'seller_registration.html')

@login_required(login_url='login')
def seller_add_product(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if not profile.is_seller:
        return redirect('seller_registration')

    if request.method == 'POST':
        category_id = request.POST.get('category')
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        quantity = request.POST.get('quantity')
        image = request.FILES.get('image')

        if category_id and name and price and quantity:
            category = get_object_or_404(Category, id=category_id)
            Product.objects.create(
                seller=request.user,
                category=category,
                name=name,
                description=description,
                price=price,
                quantity=quantity,
                image=image
            )
            messages.success(request, 'Product added successfully.')
            return redirect('seller_dashboard')
        else:
            messages.error(request, 'Please fill all required fields.')

    categories = Category.objects.all()
    return render(request, 'seller_add_product.html', {'categories': categories})