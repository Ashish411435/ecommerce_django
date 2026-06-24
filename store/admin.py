from django.contrib import admin
from .models import Product, Variation, ReviewRating

# Register your models here.


class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "product_name",
        "category",
        "price",
        "image",
        "stock",
        "is_available",
        "modified_date",
    )
    prepopulated_fields = {"slug": ("product_name",)}


class VariationAdmin(admin.ModelAdmin):
    list_display = ("product", "variation_category", "variation_value", "is_active")
    list_editable = ("is_active",)
    list_filter = ("product", "variation_category", "variation_value", "is_active")


class ReviewRatingAdmin(admin.ModelAdmin):
    list_display = [
        "user_email",
        "subject",
        "review",
        "rating",
        "ip",
        "status",
        "created_at",
        "updated_at",
    ]

    def user_email(self, obj):
        return obj.user.email if obj.user else "-"


admin.site.register(Product, ProductAdmin)
admin.site.register(Variation, VariationAdmin)
admin.site.register(ReviewRating, ReviewRatingAdmin)
