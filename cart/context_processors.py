from django.db.models import Sum

from .models import Cart, CartItem
from .views import _cart_id


def cart_counter(request):
    cart_count = 0
    if "admin" in request.path:
        return {}
    else:
        if request.user.is_authenticated:
            cart_count = (
                CartItem.objects.filter(user=request.user)
                .aggregate(total=Sum("quantity"))
                .get("total")
                or 0
            )
        else:
            cart_exists = Cart.objects.filter(cart_id=_cart_id(request)).exists()
            if cart_exists:
                cart = Cart.objects.filter(cart_id=_cart_id(request)).first()
                cart_count = (
                    CartItem.objects.filter(cart=cart)
                    .aggregate(total=Sum("quantity"))
                    .get("total")
                    or 0
                )
    return dict(cart_count=cart_count)
