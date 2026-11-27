from django.http import HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import razorpay  # type: ignore[import-not-found]

from .models import Customer, Restaurant, Item, Cart, CartItem, Order, OrderItem


def index(request):
    return render(request, 'delivery/index.html')


def open_signup(request):
    return render(request, 'delivery/signup.html')


def open_signin(request):
    return render(request, 'delivery/signin.html')


def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        email = request.POST.get('email', '').strip()
        mobile = request.POST.get('mobile', '').strip()
        address = request.POST.get('address', '').strip()

        if not username or not password:
            return render(
                request,
                'delivery/signup.html',
                {'error': 'Username and password are required.'},
            )

        if Customer.objects.filter(username=username).exists():
            return render(
                request,
                'delivery/signup.html',
                {'error': 'Username already exists! Please choose another.'},
            )

        Customer.objects.create(
            username=username,
            password=password,
            email=email,
            mobile=mobile,
            address=address,
        )
        return render(
            request,
            'delivery/signin.html',
            {'success': 'Account created successfully! Please sign in.'},
        )
    return redirect('open_signup')


def signin(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        try:
            customer = Customer.objects.get(username=username, password=password)
            if username == 'admin':
                return redirect('admin_home')
            else:
                return redirect('customer_home', username=customer.username)
        except Customer.DoesNotExist:
            return render(
                request,
                'delivery/signin.html',
                {'error': 'Invalid username or password!'},
            )
    return redirect('open_signin')


def admin_home(request):
    restaurant_count = Restaurant.objects.count()
    item_count = Item.objects.count()
    customer_count = Customer.objects.count()
    order_count = Order.objects.count()
    recent_orders = Order.objects.select_related('customer').prefetch_related('order_items')[:10]
    return render(
        request,
        'delivery/admin_home.html',
        {
            'restaurant_count': restaurant_count,
            'item_count': item_count,
            'customer_count': customer_count,
            'order_count': order_count,
            'recent_orders': recent_orders,
        },
    )


def customer_home(request, username):
    customer = get_object_or_404(Customer, username=username)
    restaurantList = Restaurant.objects.all()
    cart = Cart.objects.filter(customer=customer).first()
    cart_count = cart.total_items() if cart else 0
    order_count = customer.orders.count()
    return render(
        request,
        'delivery/customer_home.html',
        {
            'restaurantList': restaurantList,
            'customer': customer,
            'username': username,
            'cart_count': cart_count,
            'order_count': order_count,
        },
    )


def open_add_restaurant(request):
    return render(request, 'delivery/add_restaurant.html')


def add_restaurant(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        picture = request.POST.get('picture', '').strip()
        cuisine = request.POST.get('cuisine', '').strip()
        rating = request.POST.get('rating', '0').strip()

        if not name:
            return render(
                request,
                'delivery/add_restaurant.html',
                {'error': 'Restaurant name is required.'},
            )

        if Restaurant.objects.filter(name=name).exists():
            return render(
                request,
                'delivery/add_restaurant.html',
                {'error': f"A restaurant named '{name}' already exists!"},
            )

        if not picture:
            picture = 'https://cdn-icons-png.flaticon.com/256/6643/6643359.png'

        try:
            rating_val = float(rating)
        except ValueError:
            rating_val = 0.0

        Restaurant.objects.create(
            name=name,
            picture=picture,
            cuisine=cuisine,
            rating=rating_val,
        )
        return redirect('open_show_restaurant')

    return redirect('open_add_restaurant')


def open_show_restaurant(request):
    restaurantList = Restaurant.objects.all()
    return render(
        request,
        'delivery/show_restaurants.html',
        {'restaurantList': restaurantList},
    )


def open_update_restaurant(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    return render(
        request,
        'delivery/update_restaurant.html',
        {'restaurant': restaurant},
    )


def update_restaurant(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        picture = request.POST.get('picture', '').strip()
        cuisine = request.POST.get('cuisine', '').strip()
        rating = request.POST.get('rating', '').strip()

        if name:
            restaurant.name = name
        if picture:
            restaurant.picture = picture
        if cuisine:
            restaurant.cuisine = cuisine
        if rating:
            try:
                restaurant.rating = float(rating)
            except ValueError:
                pass
        restaurant.save()

    return redirect('open_show_restaurant')


def delete_restaurant(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    restaurant.delete()
    return redirect('open_show_restaurant')


def open_update_menu(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    itemList = restaurant.items.all()
    return render(
        request,
        'delivery/update_menu.html',
        {'itemList': itemList, 'restaurant': restaurant},
    )


def update_menu(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        price = request.POST.get('price', '0').strip()
        vegeterian = request.POST.get('vegeterian') == 'on'
        picture = request.POST.get('picture', '').strip()

        if not name:
            return render(
                request,
                'delivery/update_menu.html',
                {
                    'itemList': restaurant.items.all(),
                    'restaurant': restaurant,
                    'error': 'Item name is required.',
                },
            )

        if Item.objects.filter(restaurant=restaurant, name=name).exists():
            return render(
                request,
                'delivery/update_menu.html',
                {
                    'itemList': restaurant.items.all(),
                    'restaurant': restaurant,
                    'error': f"Item '{name}' already exists in this restaurant's menu!",
                },
            )

        if not picture:
            picture = 'https://www.indiafilings.com/learn/wp-content/uploads/2024/08/How-to-Start-Food-Business.jpg'

        try:
            price_val = float(price)
        except ValueError:
            price_val = 0.0

        Item.objects.create(
            restaurant=restaurant,
            name=name,
            description=description,
            price=price_val,
            vegeterian=vegeterian,
            picture=picture,
        )
        return redirect('open_update_menu', restaurant_id=restaurant.id)

    return redirect('open_update_menu', restaurant_id=restaurant.id)


def delete_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    restaurant_id = item.restaurant.id
    item.delete()
    return redirect('open_update_menu', restaurant_id=restaurant_id)


def view_menu(request, restaurant_id, username):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    itemList = list(restaurant.items.all())
    customer = get_object_or_404(Customer, username=username)
    cart = Cart.objects.filter(customer=customer).first()
    cart_count = cart.total_items() if cart else 0

    cart_quantities = {}
    if cart:
        for ci in cart.cart_items.all():
            cart_quantities[ci.item_id] = ci.quantity

    for item in itemList:
        item.cart_quantity = cart_quantities.get(item.id, 0)

    return render(
        request,
        'delivery/customer_menu.html',
        {
            'itemList': itemList,
            'restaurant': restaurant,
            'customer': customer,
            'username': username,
            'cart_count': cart_count,
        },
    )


def add_to_cart(request, item_id, username):
    item = get_object_or_404(Item, id=item_id)
    customer = get_object_or_404(Customer, username=username)

    cart, _ = Cart.objects.get_or_create(customer=customer)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, item=item)
    if not created:
        cart_item.quantity += 1
        cart_item.save()

    referer = request.META.get('HTTP_REFERER', '')
    if 'show_cart' in referer:
        return redirect('show_cart', username=username)

    return redirect('view_menu', restaurant_id=item.restaurant.id, username=username)


def decrease_cart_item(request, item_id, username):
    customer = get_object_or_404(Customer, username=username)
    cart = Cart.objects.filter(customer=customer).first()
    if cart:
        cart_item = CartItem.objects.filter(cart=cart, item_id=item_id).first()
        if cart_item:
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart_item.delete()

    referer = request.META.get('HTTP_REFERER', '')
    if 'view_menu' in referer:
        item = get_object_or_404(Item, id=item_id)
        return redirect('view_menu', restaurant_id=item.restaurant.id, username=username)

    return redirect('show_cart', username=username)


def remove_from_cart(request, item_id, username):
    customer = get_object_or_404(Customer, username=username)
    cart = Cart.objects.filter(customer=customer).first()
    if cart:
        CartItem.objects.filter(cart=cart, item_id=item_id).delete()

    return redirect('show_cart', username=username)


def show_cart(request, username):
    customer = get_object_or_404(Customer, username=username)
    cart = Cart.objects.filter(customer=customer).first()
    cart_items = cart.cart_items.select_related('item').all() if cart else []
    total_price = cart.total_price() if cart else 0
    total_items = cart.total_items() if cart else 0

    return render(
        request,
        'delivery/cart.html',
        {
            'cart_items': cart_items,
            'customer': customer,
            'total_price': total_price,
            'total_items': total_items,
            'username': username,
        },
    )


def checkout(request, username):
    customer = get_object_or_404(Customer, username=username)
    cart = Cart.objects.filter(customer=customer).first()
    cart_items = cart.cart_items.select_related('item').all() if cart else []
    total_price = cart.total_price() if cart else 0

    if total_price == 0 or not cart_items:
        return render(
            request,
            'delivery/checkout.html',
            {
                'username': username,
                'customer': customer,
                'cart_items': [],
                'total_price': 0,
                'error': 'Your cart is empty! Please add items before checking out.',
            },
        )

    amount_in_paise = int(float(total_price) * 100)

    try:
        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
        order_data = {
            'amount': amount_in_paise,
            'currency': 'INR',
            'payment_capture': '1',
        }
        order = client.order.create(data=order_data)
        order_id = order['id']
    except Exception as e:
        return render(
            request,
            'delivery/checkout.html',
            {
                'username': username,
                'customer': customer,
                'cart_items': cart_items,
                'total_price': total_price,
                'error': f'Unable to initiate Razorpay payment: {e}. Please ensure network connectivity and valid gateway credentials.',
            },
        )

    return render(
        request,
        'delivery/checkout.html',
        {
            'username': username,
            'customer': customer,
            'cart_items': cart_items,
            'total_price': total_price,
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            'order_id': order_id,
            'amount_in_paise': amount_in_paise,
        },
    )


@csrf_exempt
def verify_and_place_order(request, username):
    """Verifies Razorpay payment signature, creates Order & OrderItems, and redirects to orders."""
    if request.method == "POST":
        payment_id = request.POST.get('razorpay_payment_id', '')
        order_id = request.POST.get('razorpay_order_id', '')
        signature = request.POST.get('razorpay_signature', '')

        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        params_dict = {
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature,
        }

        try:
            client.utility.verify_payment_signature(params_dict)

            customer = get_object_or_404(Customer, username=username)
            cart = Cart.objects.filter(customer=customer).first()
            if cart and cart.cart_items.exists():
                order = Order.objects.create(
                    customer=customer,
                    order_id=order_id,
                    payment_id=payment_id,
                    total_amount=cart.total_price(),
                    delivery_address=customer.address or 'Standard Delivery Address',
                    status='Placed',
                )
                for ci in cart.cart_items.select_related('item').all():
                    OrderItem.objects.create(
                        order=order,
                        item_name=ci.item.name,
                        price=ci.item.price,
                        quantity=ci.quantity,
                    )
                cart.cart_items.all().delete()

            return redirect('orders', username=username)
        except razorpay.errors.SignatureVerificationError:
            return HttpResponseBadRequest("Payment verification failed!")
        except Exception as e:
            return HttpResponseBadRequest(f"Verification error: {e}")

    return HttpResponseBadRequest("Invalid request method.")


def orders(request, username):
    customer = get_object_or_404(Customer, username=username)
    user_orders = customer.orders.prefetch_related('order_items').all()
    cart = Cart.objects.filter(customer=customer).first()
    cart_count = cart.total_items() if cart else 0

    return render(
        request,
        'delivery/orders.html',
        {
            'username': username,
            'customer': customer,
            'orders': user_orders,
            'cart_count': cart_count,
        },
    )
