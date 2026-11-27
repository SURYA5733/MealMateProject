from django.db import models


class Customer(models.Model):
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=50)
    email = models.CharField(max_length=100)
    mobile = models.CharField(max_length=15)
    address = models.CharField(max_length=255)

    def __str__(self):
        return self.username


class Restaurant(models.Model):
    name = models.CharField(max_length=100, unique=True)
    picture = models.URLField(
        max_length=500,
        default='https://cdn-icons-png.flaticon.com/256/6643/6643359.png',
    )
    cuisine = models.CharField(max_length=200)
    rating = models.FloatField()

    def __str__(self):
        return self.name


class Item(models.Model):
    restaurant = models.ForeignKey(
        Restaurant, on_delete=models.CASCADE, related_name="items"
    )
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255)
    price = models.FloatField()
    vegeterian = models.BooleanField(default=False)
    picture = models.URLField(
        max_length=500,
        default='https://www.indiafilings.com/learn/wp-content/uploads/2024/08/How-to-Start-Food-Business.jpg',
    )

    def __str__(self):
        return f"{self.name} ({self.restaurant.name})"


class Cart(models.Model):
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="cart"
    )

    def total_price(self):
        return round(sum(ci.subtotal() for ci in self.cart_items.all()), 2)

    def total_items(self):
        return sum(ci.quantity for ci in self.cart_items.all())

    def __str__(self):
        return f"Cart of {self.customer.username}"


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart, on_delete=models.CASCADE, related_name="cart_items"
    )
    item = models.ForeignKey(
        Item, on_delete=models.CASCADE, related_name="cart_items"
    )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('cart', 'item')

    def subtotal(self):
        return round(self.item.price * self.quantity, 2)

    def __str__(self):
        return f"{self.quantity}x {self.item.name}"


class Order(models.Model):
    STATUS_CHOICES = (
        ('Placed', 'Order Placed'),
        ('Preparing', 'Preparing Food'),
        ('Out for Delivery', 'Out for Delivery'),
        ('Delivered', 'Delivered'),
    )
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="orders"
    )
    order_id = models.CharField(max_length=100, blank=True)
    payment_id = models.CharField(max_length=100, blank=True)
    total_amount = models.FloatField()
    delivery_address = models.CharField(max_length=255)
    status = models.CharField(
        max_length=30, choices=STATUS_CHOICES, default='Placed'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} - {self.customer.username} (₹{self.total_amount})"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="order_items"
    )
    item_name = models.CharField(max_length=100)
    price = models.FloatField()
    quantity = models.PositiveIntegerField(default=1)

    def subtotal(self):
        return round(self.price * self.quantity, 2)

    def __str__(self):
        return f"{self.quantity}x {self.item_name}"
