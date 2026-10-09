from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import razorpay  # type: ignore[import-not-found]

from .models import Customer, Restaurant, Item, Cart

# Create your views here.
def index(request):
    return render(request, 'delivery/index.html')

def open_signup(request):
    return render(request, 'delivery/signup.html')

def open_signin(request):
    return render(request, 'delivery/signin.html')

def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        mobile = request.POST.get('mobile')
        address = request.POST.get('address')

        try:
            Customer.objects.get(username=username)
            return HttpResponse("Duplicate username!")
        except Customer.DoesNotExist:
            Customer.objects.create(
                username=username,
                password=password,
                email=email,
                mobile=mobile,
                address=address,
            )
    return render(request, 'delivery/signin.html')

def signin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            Customer.objects.get(username=username, password=password)
            if username == 'admin':
                return render(request, 'delivery/admin_home.html')
            else:
                restaurantList = Restaurant.objects.all()
                return render(
                    request,
                    'delivery/customer_home.html',
                    {'restaurantList': restaurantList, 'username': username},
                )
        except Customer.DoesNotExist:
            return HttpResponse("Registration failed")

def open_add_restaurant(request):
    return render(request, 'delivery/add_restaurant.html')

def add_restaurant(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        picture = request.POST.get('picture')
        cuisine = request.POST.get('cuisine')
        rating = request.POST.get('rating')

        try:
            Restaurant.objects.get(name=name)
            return HttpResponse("Duplicate restaurant!")
        except Restaurant.DoesNotExist:
            Restaurant.objects.create(
                name=name,
                picture=picture,
                cuisine=cuisine,
                rating=rating,
            )
    return render(request, 'delivery/admin_home.html')

def open_show_restaurant(request):
    restaurantList = Restaurant.objects.all()
    return render(
        request, 'delivery/show_restaurants.html', {"restaurantList": restaurantList}
    )

def open_update_restaurant(request, restaurant_id):
    restaurant = Restaurant.objects.get(id=restaurant_id)
    return render(
        request, 'delivery/update_restaurant.html', {"restaurant": restaurant}
    )

def update_restaurant(request, restaurant_id):
    restaurant = Restaurant.objects.get(id=restaurant_id)
    if request.method == 'POST':
        name = request.POST.get('name')
        picture = request.POST.get('picture')
        cuisine = request.POST.get('cuisine')
        rating = request.POST.get('rating')

        restaurant.name = name
        restaurant.picture = picture
        restaurant.cuisine = cuisine
        restaurant.rating = rating
        restaurant.save()

    restaurantList = Restaurant.objects.all()
    return render(
        request, 'delivery/show_restaurants.html', {"restaurantList": restaurantList}
    )

def delete_restaurant(request, restaurant_id):
    restaurant = Restaurant.objects.get(id=restaurant_id)
    restaurant.delete()

    restaurantList = Restaurant.objects.all()
    return render(
        request, 'delivery/show_restaurants.html', {"restaurantList": restaurantList}
    )

def open_update_menu(request, restaurant_id):
    restaurant = Restaurant.objects.get(id=restaurant_id)
    itemList = restaurant.items.all()
    return render(
        request,
        'delivery/update_menu.html',
        {"itemList": itemList, "restaurant": restaurant},
    )

def update_menu(request, restaurant_id):
    restaurant = Restaurant.objects.get(id=restaurant_id)

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        vegeterian = request.POST.get('vegeterian') == 'on'
        picture = request.POST.get('picture')

        try:
            Item.objects.get(name=name)
            return HttpResponse("Duplicate item!")
        except Item.DoesNotExist:
            Item.objects.create(
                restaurant=restaurant,
                name=name,
                description=description,
                price=price,
                vegeterian=vegeterian,
                picture=picture,
            )
    return render(request, 'delivery/admin_home.html')

def view_menu(request, restaurant_id, username):
    restaurant = Restaurant.objects.get(id=restaurant_id)
    itemList = restaurant.items.all()
    return render(
        request,
        'delivery/customer_menu.html',
        {"itemList": itemList, "restaurant": restaurant, "username": username},
    )

def add_to_cart(request, item_id, username):
    item = Item.objects.get(id=item_id)
    customer = Customer.objects.get(username=username)

    cart, created = Cart.objects.get_or_create(customer=customer)
    cart.items.add(item)

    return HttpResponse('added to cart')

def show_cart(request, username):
    customer = Customer.objects.get(username=username)
    cart = Cart.objects.filter(customer=customer).first()
    items = cart.items.all() if cart else []
    total_price = cart.total_price() if cart else 0

    return render(
        request,
        'delivery/cart.html',
        {"itemList": items, "total_price": total_price, "username": username},
    )

def checkout(request, username):
    customer = get_object_or_404(Customer, username=username)
    cart = Cart.objects.filter(customer=customer).first()
    cart_items = cart.items.all() if cart else []
    total_price = cart.total_price() if cart else 0

    if total_price == 0:
        return render(
            request,
            'delivery/checkout.html',
            {
                'error': 'Your cart is empty!',
            },
        )

    # Convert total price to paise safely
    amount_in_paise = int(float(total_price) * 100)

    # Initialize Razorpay client
    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    # Create Razorpay order
    order_data = {
        'amount': amount_in_paise,
        'currency': 'INR',
        'payment_capture': '1',
    }
    order = client.order.create(data=order_data)

    return render(
        request,
        'delivery/checkout.html',
        {
            'username': username,
            'customer': customer,
            'cart_items': cart_items,
            'total_price': total_price,
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            'order_id': order['id'],
            'amount_in_paise': amount_in_paise,
        },
    )

@csrf_exempt
def verify_and_place_order(request, username):
    """Verifies Razorpay payment signature and redirects to order confirmation."""
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
            # Verify cryptographic signature from Razorpay
            client.utility.verify_payment_signature(params_dict)

            # Route to orders page to display confirmation and clear cart
            return redirect('orders', username=username)

        except razorpay.errors.SignatureVerificationError:
            return HttpResponseBadRequest("Payment verification failed!")

    return HttpResponseBadRequest("Invalid request method.")

def orders(request, username):
    customer = get_object_or_404(Customer, username=username)
    cart = Cart.objects.filter(customer=customer).first()

    cart_items = list(cart.items.all()) if cart else []
    total_price = cart.total_price() if cart else 0

    # Clear the cart after order placement
    if cart:
        cart.items.clear()

    return render(
        request,
        'delivery/orders.html',
        {
            'username': username,
            'customer': customer,
            'cart_items': cart_items,
            'total_price': total_price,
        },
    )