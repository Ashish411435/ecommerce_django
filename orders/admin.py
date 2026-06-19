from django.contrib import admin
from .models import Payment, Order, OrderProduct

# Register your models here.


class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    extra = 0
    readonly_fields = [
        "payment",
        "user",
        "product",
        "quantity",
        "product_price",
        "ordered",
        "variations",
    ]


class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "order_number",
        "full_name",
        "phone_number",
        "email",
        "tax",
        "order_total",
        "status",
        "is_ordered",
        "payment_status",
        "payment_method",
        "order_note",
        "created_at",
    ]

    list_filter = ["status", "is_ordered"]
    search_fields = ["first_name", "last_name", "email", "phone_number", "order_number"]
    list_per_page = 20
    inlines = [OrderProductInline]

    def payment_method(self, obj):
        return obj.payment.payment_method if obj.payment else "-"

    def payment_status(self, obj):
        return obj.payment.status if obj.payment else "-"


admin.site.register(Order, OrderAdmin)
admin.site.register(OrderProduct)
admin.site.register(Payment)
