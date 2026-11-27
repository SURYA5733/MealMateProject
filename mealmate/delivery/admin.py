from django.contrib import admin
from .models import Customer, Restaurant, Item, Cart, CartItem, Order, OrderItem


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'mobile', 'address')
    search_fields = ('username', 'email', 'mobile')


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'cuisine', 'rating')
    search_fields = ('name', 'cuisine')


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'restaurant', 'price', 'vegeterian')
    list_filter = ('vegeterian', 'restaurant')
    search_fields = ('name', 'restaurant__name')


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'total_price', 'total_items')
    search_fields = ('customer__username',)
    inlines = [CartItemInline]


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart', 'item', 'quantity', 'subtotal')
    list_filter = ('cart', 'item')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'total_amount', 'status', 'order_id', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('customer__username', 'order_id', 'payment_id')
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'item_name', 'price', 'quantity', 'subtotal')
