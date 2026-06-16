from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

from .models import Cart, CartItem
from store.models import Product
from store.models import Variation as VariationModel


# Create your views here.
def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart


def add_cart(request, product_id):
    current_user = request.user
    product = Product.objects.get(id=product_id)
    product_variation = []
    if current_user.is_authenticated:
        if request.method == "POST":
            for item in request.POST:
                if item == "csrfmiddlewaretoken":
                    continue
                key = item
                value = request.POST[key]
                try:
                    variation = VariationModel.objects.get(
                        product=product,
                        variation_category__iexact=key,
                        variation_value__iexact=value,
                    )
                    product_variation.append(variation)
                except Exception as e:
                    print("ERROR:", e)

        cart_item_exists = CartItem.objects.filter(
            product=product, user=current_user
        ).exists()
        if cart_item_exists:
            cart_item = CartItem.objects.filter(product=product, user=current_user)
            print("Cart Item: ", cart_item)
            existing_var_list = []
            cart_item_ids = []
            for item in cart_item:
                existing_variation = item.variations.all()
                existing_var_list.append(list(existing_variation))
                cart_item_ids.append(item.id)

            if product_variation in existing_var_list:
                print("hello 1 :-----------------")
                # Increase the cart quantity
                index = existing_var_list.index(product_variation)
                print("Index: === ", index)
                index_id = cart_item_ids[index]
                print("Index Id: === ", index_id)
                existing_cart_item = CartItem.objects.get(product=product, id=index_id)
                print(
                    "Existing Cart Item: === ",
                    existing_cart_item.product,
                    existing_cart_item.variations,
                    existing_cart_item.quantity,
                )
                existing_cart_item.quantity += 1
                existing_cart_item.save()
                print("Quantity Increased: === ", existing_cart_item.quantity)
                print("hello saved :-----------------")
            else:
                create_cart_item(request, product, current_user, product_variation)
        else:
            create_cart_item(request, product, current_user, product_variation)
    else:
        if request.method == "POST":
            for item in request.POST:
                if item == "csrfmiddlewaretoken":
                    continue
                key = item
                value = request.POST[key]
                try:
                    variation = VariationModel.objects.get(
                        product=product,
                        variation_category__iexact=key,
                        variation_value__iexact=value,
                    )
                    product_variation.append(variation)
                except Exception as e:
                    print("ERROR:", e)

        try:
            cart = Cart.objects.get(
                cart_id=_cart_id(request)
            )  # get the cart using the cart_id id present in the session
        except Cart.DoesNotExist:
            cart = Cart.objects.create(cart_id=_cart_id(request))
        cart.save()

        cart_item_exists = CartItem.objects.filter(product=product, cart=cart).exists()
        if cart_item_exists:
            cart_item = CartItem.objects.filter(product=product, cart=cart)
            print("Else Cart Item: ", cart_item)
            # existing_variations -> databse
            # current variations -> product_variation
            # item_id -> database
            existing_var_list = []
            cart_item_ids = []
            for item in cart_item:
                existing_variation = item.variations.all()
                existing_var_list.append(list(existing_variation))
                cart_item_ids.append(item.id)

            if product_variation in existing_var_list:
                print("Else hello 1 :-----------------")
                # Increase the cart quantity
                index = existing_var_list.index(product_variation)
                index_id = cart_item_ids[index]
                existing_cart_item = CartItem.objects.get(product=product, id=index_id)
                existing_cart_item.quantity += 1
                existing_cart_item.save()
                print("Else hello saved :-----------------")
            else:
                create_cart_item(request, product, cart, product_variation)
        else:
            create_cart_item(request, product, cart, product_variation)
    return redirect("cart")


def create_cart_item(request, product, cart, product_variation):
    if request.user.is_authenticated:
        cart_item = CartItem.objects.create(
            product=product,
            quantity=1,
            user=cart,
        )
    else:
        cart_item = CartItem.objects.create(
            product=product,
            quantity=1,
            cart=cart,
        )
    if product_variation:
        cart_item.variations.set(product_variation)
    cart_item.save()


def remove_cart(request, product_id, cart_item_id):
    try:
        product = get_object_or_404(Product, id=product_id)
        current_user = request.user
        if current_user.is_authenticated:
            cart_item = CartItem.objects.get(
                product=product, user=current_user, id=cart_item_id
            )
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(
                product=product, cart=cart, id=cart_item_id
            )
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass
    return redirect("cart")


def remove_cart_item(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    current_user = request.user
    if current_user.is_authenticated:
        cart_item = CartItem.objects.get(
            product=product, user=current_user, id=cart_item_id
        )
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
    cart_item.delete()
    return redirect("cart")


def cart(request, total=0, quantity=0, cart_items=None):
    tax = 0
    grand_total = 0
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += cart_item.product.price * cart_item.quantity
            quantity += cart_item.quantity
        tax = (2 * total) / 100
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass

    context = {
        "total": total,
        "quantity": quantity,
        "cart_items": cart_items,
        "tax": tax,
        "grand_total": grand_total,
    }
    return render(request, "store/cart.html", context)


@login_required(login_url="login")
def checkout(request, total=0, quantity=0, cart_items=None):
    tax = 0
    grand_total = 0
    try:
        cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        if cart_items.exists():
            for cart_item in cart_items:
                total += cart_item.product.price * cart_item.quantity
                quantity += cart_item.quantity
            tax = (2 * total) / 100
            grand_total = total + tax
        else:
            return redirect("dashboard")
    except ObjectDoesNotExist:
        pass

    context = {
        "total": total,
        "quantity": quantity,
        "cart_items": cart_items,
        "tax": tax,
        "grand_total": grand_total,
    }
    return render(request, "store/checkout.html", context)
