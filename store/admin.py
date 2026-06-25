from django.contrib import admin
from .models import Product, ProductGallery, Variation, ReviewRating
import admin_thumbnails

# Register your models here.


@admin_thumbnails.thumbnail("image")
class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1


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

    inlines = [ProductGalleryInline]


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
admin.site.register(ProductGallery)
