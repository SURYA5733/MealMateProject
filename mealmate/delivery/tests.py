from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from .models import Customer, Restaurant, Item, Cart, CartItem


class ModelTests(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(
            username="testuser",
            password="password123",
            email="test@example.com",
            mobile="9876543210",
            address="123 Test Street, Test City",
        )
        self.restaurant = Restaurant.objects.create(
            name="Pizza Palace",
            cuisine="Italian",
            rating=4.5,
        )
        self.item = Item.objects.create(
            restaurant=self.restaurant,
            name="Margherita Pizza",
            description="Classic cheese and tomato pizza",
            price=250.0,
            vegeterian=True,
        )

    def test_customer_creation_and_str(self):
        self.assertEqual(str(self.customer), "testuser")
        self.assertEqual(self.customer.email, "test@example.com")

    def test_restaurant_creation_and_str(self):
        self.assertEqual(str(self.restaurant), "Pizza Palace")
        self.assertEqual(self.restaurant.rating, 4.5)

    def test_item_creation_and_str(self):
        self.assertEqual(str(self.item), "Margherita Pizza (Pizza Palace)")
        self.assertEqual(self.item.price, 250.0)

    def test_cart_quantity_and_total_price(self):
        cart = Cart.objects.create(customer=self.customer)
        self.assertEqual(cart.total_price(), 0)
        self.assertEqual(cart.total_items(), 0)

        # Add 2 pizzas
        ci1 = CartItem.objects.create(cart=cart, item=self.item, quantity=2)
        self.assertEqual(ci1.subtotal(), 500.0)
        self.assertEqual(str(ci1), "2x Margherita Pizza")

        # Add 1 garlic bread
        item2 = Item.objects.create(
            restaurant=self.restaurant,
            name="Garlic Bread",
            description="Warm toasted garlic bread",
            price=120.0,
            vegeterian=True,
        )
        CartItem.objects.create(cart=cart, item=item2, quantity=1)

        self.assertEqual(cart.total_items(), 3)
        self.assertEqual(cart.total_price(), 620.0)
        self.assertEqual(str(cart), "Cart of testuser")


class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.customer = Customer.objects.create(
            username="testcustomer",
            password="testpassword",
            email="customer@example.com",
            mobile="9876543210",
            address="456 Market Road",
        )
        self.admin_user = Customer.objects.create(
            username="admin",
            password="adminpassword",
            email="admin@example.com",
            mobile="9000000000",
            address="Admin Office HQ",
        )
        self.restaurant = Restaurant.objects.create(
            name="Burger Hub",
            cuisine="American",
            rating=4.2,
        )
        self.item = Item.objects.create(
            restaurant=self.restaurant,
            name="Veggie Burger",
            description="Crispy patty with fresh lettuce and sauce",
            price=150.0,
            vegeterian=True,
        )

    def test_index_view(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'delivery/index.html')

    def test_signup_success(self):
        response = self.client.post(
            reverse('signup'),
            {
                'username': 'newuser',
                'password': 'secretpassword',
                'email': 'newuser@example.com',
                'mobile': '9123456780',
                'address': '789 Grand Avenue',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'delivery/signin.html')
        self.assertTrue(Customer.objects.filter(username='newuser').exists())

    def test_signup_duplicate_username(self):
        response = self.client.post(
            reverse('signup'),
            {
                'username': 'testcustomer',
                'password': 'differentpassword',
                'email': 'diff@example.com',
                'mobile': '9123456789',
                'address': 'Some Address',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'delivery/signup.html')
        self.assertContains(response, "Username already exists")

    def test_signin_customer_success(self):
        response = self.client.post(
            reverse('signin'),
            {'username': 'testcustomer', 'password': 'testpassword'},
        )
        self.assertRedirects(
            response, reverse('customer_home', kwargs={'username': 'testcustomer'})
        )

    def test_signin_admin_success(self):
        response = self.client.post(
            reverse('signin'),
            {'username': 'admin', 'password': 'adminpassword'},
        )
        self.assertRedirects(response, reverse('admin_home'))

    def test_signin_invalid_credentials(self):
        response = self.client.post(
            reverse('signin'),
            {'username': 'testcustomer', 'password': 'wrongpassword'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'delivery/signin.html')
        self.assertContains(response, "Invalid username or password")

    def test_admin_home_view(self):
        response = self.client.get(reverse('admin_home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'delivery/admin_home.html')

    def test_customer_home_view(self):
        response = self.client.get(
            reverse('customer_home', kwargs={'username': 'testcustomer'})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'delivery/customer_home.html')
        self.assertContains(response, 'Burger Hub')

    def test_view_menu_displays_quantity(self):
        cart, _ = Cart.objects.get_or_create(customer=self.customer)
        CartItem.objects.create(cart=cart, item=self.item, quantity=4)

        response = self.client.get(
            reverse(
                'view_menu',
                kwargs={'restaurant_id': self.restaurant.id, 'username': 'testcustomer'},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '4')

    def test_restaurant_crud(self):
        # Add restaurant
        add_response = self.client.post(
            reverse('add_restaurant'),
            {
                'name': 'Taco Fiesta',
                'cuisine': 'Mexican',
                'rating': '4.8',
                'picture': '',
            },
        )
        self.assertRedirects(add_response, reverse('open_show_restaurant'))
        new_restaurant = Restaurant.objects.get(name='Taco Fiesta')
        self.assertEqual(new_restaurant.rating, 4.8)

        # Update restaurant
        update_response = self.client.post(
            reverse('update_restaurant', kwargs={'restaurant_id': new_restaurant.id}),
            {
                'name': 'Taco Fiesta Cantina',
                'cuisine': 'Mexican-Fusion',
                'rating': '4.9',
                'picture': '',
            },
        )
        self.assertRedirects(update_response, reverse('open_show_restaurant'))
        new_restaurant.refresh_from_db()
        self.assertEqual(new_restaurant.name, 'Taco Fiesta Cantina')
        self.assertEqual(new_restaurant.cuisine, 'Mexican-Fusion')

        # Delete restaurant
        delete_response = self.client.get(
            reverse('delete_restaurant', kwargs={'restaurant_id': new_restaurant.id})
        )
        self.assertRedirects(delete_response, reverse('open_show_restaurant'))
        self.assertFalse(Restaurant.objects.filter(id=new_restaurant.id).exists())

    def test_menu_crud(self):
        # Add item
        add_response = self.client.post(
            reverse('update_menu', kwargs={'restaurant_id': self.restaurant.id}),
            {
                'name': 'Cheese Fries',
                'description': 'Crispy fries with warm cheddar',
                'price': '99.00',
                'vegeterian': 'on',
                'picture': '',
            },
        )
        self.assertRedirects(
            add_response,
            reverse('open_update_menu', kwargs={'restaurant_id': self.restaurant.id}),
        )
        new_item = Item.objects.get(name='Cheese Fries', restaurant=self.restaurant)
        self.assertEqual(new_item.price, 99.0)

        # Delete item
        delete_response = self.client.get(
            reverse('delete_item', kwargs={'item_id': new_item.id})
        )
        self.assertRedirects(
            delete_response,
            reverse('open_update_menu', kwargs={'restaurant_id': self.restaurant.id}),
        )
        self.assertFalse(Item.objects.filter(id=new_item.id).exists())

    def test_cart_operations_multiple_quantity(self):
        # Add to cart first time (quantity = 1)
        self.client.get(
            reverse(
                'add_to_cart',
                kwargs={'item_id': self.item.id, 'username': 'testcustomer'},
            )
        )
        cart = Cart.objects.get(customer=self.customer)
        cart_item = CartItem.objects.get(cart=cart, item=self.item)
        self.assertEqual(cart_item.quantity, 1)

        # Add to cart second time (quantity should become 2)
        self.client.get(
            reverse(
                'add_to_cart',
                kwargs={'item_id': self.item.id, 'username': 'testcustomer'},
            )
        )
        cart_item.refresh_from_db()
        self.assertEqual(cart_item.quantity, 2)
        self.assertEqual(cart.total_price(), 300.0)

        # Show cart page
        cart_page = self.client.get(
            reverse('show_cart', kwargs={'username': 'testcustomer'})
        )
        self.assertEqual(cart_page.status_code, 200)
        self.assertContains(cart_page, 'Veggie Burger')
        self.assertContains(cart_page, '300.0')

        # Decrease quantity (2 -> 1)
        self.client.get(
            reverse(
                'decrease_cart_item',
                kwargs={'item_id': self.item.id, 'username': 'testcustomer'},
            )
        )
        cart_item.refresh_from_db()
        self.assertEqual(cart_item.quantity, 1)
        self.assertEqual(cart.total_price(), 150.0)

        # Remove from cart
        remove_response = self.client.get(
            reverse(
                'remove_from_cart',
                kwargs={'item_id': self.item.id, 'username': 'testcustomer'},
            )
        )
        self.assertRedirects(
            remove_response,
            reverse('show_cart', kwargs={'username': 'testcustomer'}),
        )
        self.assertEqual(cart.cart_items.count(), 0)

    def test_checkout_empty_cart(self):
        response = self.client.get(
            reverse('checkout', kwargs={'username': 'testcustomer'})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Your cart is empty')

    @patch('razorpay.Client')
    def test_checkout_with_items_and_orders(self, mock_razorpay):
        mock_client = mock_razorpay.return_value
        mock_client.order.create.return_value = {'id': 'order_test_123456'}
        mock_client.utility.verify_payment_signature.return_value = True

        # Add 3 items to cart
        cart, _ = Cart.objects.get_or_create(customer=self.customer)
        CartItem.objects.create(cart=cart, item=self.item, quantity=3)

        response = self.client.get(
            reverse('checkout', kwargs={'username': 'testcustomer'})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'order_test_123456')
        self.assertContains(response, 'Veggie Burger')
        self.assertContains(response, '450.0')

        # Verify and place order
        verify_response = self.client.post(
            reverse('verify_and_place_order', kwargs={'username': 'testcustomer'}),
            {
                'razorpay_order_id': 'order_test_123456',
                'razorpay_payment_id': 'pay_test_999',
                'razorpay_signature': 'valid_sig',
            },
        )
        self.assertRedirects(
            verify_response, reverse('orders', kwargs={'username': 'testcustomer'})
        )

        # Check Order was persisted in database
        self.assertEqual(self.customer.orders.count(), 1)
        placed_order = self.customer.orders.first()
        self.assertEqual(placed_order.total_amount, 450.0)
        self.assertEqual(placed_order.order_items.count(), 1)
        self.assertEqual(placed_order.order_items.first().quantity, 3)

        # Test orders confirmation and history view
        orders_response = self.client.get(
            reverse('orders', kwargs={'username': 'testcustomer'})
        )
        self.assertEqual(orders_response.status_code, 200)
        self.assertContains(orders_response, 'Order #')
        self.assertContains(orders_response, 'Veggie Burger')
        self.assertContains(orders_response, '450.0')
        self.assertEqual(cart.cart_items.count(), 0)
