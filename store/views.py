from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import HttpResponse
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# Models
from store.models import Product, ProductGallery, ReviewRating
from category.models import Category
from cart.models import CartItem
from orders.models import OrderProduct

from cart.views import _cart_id
from store.forms import ReviewForm


# Create your views here.
def store(request, category_slug=None):
    if category_slug != None:
        filter_categories = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(
            category=filter_categories, is_available=True
        ).order_by("product_name")
        products_count = products.count()
        paginator = Paginator(products, 6)
        page = request.GET.get("page")
        paged_products = paginator.get_page(page)
    else:
        products = (
            Product.objects.all().filter(is_available=True).order_by("product_name")
        )
        products_count = products.count()
        paginator = Paginator(products, 6)
        page = request.GET.get("page")
        paged_products = paginator.get_page(page)

    context = {
        "products": paged_products,
        "products_count": products_count,
    }

    return render(request, "store/store.html", context)


def product_detail(request, category_slug, product_slug):

    single_product = get_object_or_404(
        Product.objects.select_related("category"),
        category__slug=category_slug,
        slug=product_slug,
    )

    in_cart = CartItem.objects.filter(
        cart__cart_id=_cart_id(request), product=single_product
    ).exists()

    order_product = False

    if request.user.is_authenticated:
        order_product = OrderProduct.objects.filter(
            user=request.user,
            product=single_product,
        ).exists()

    reviews = ReviewRating.objects.filter(product=single_product, status=True)

    product_gallery = ProductGallery.objects.filter(product=single_product)

    context = {
        "single_product": single_product,
        "in_cart": in_cart,
        "order_product": order_product,
        "reviews": reviews,
        "product_gallery": product_gallery,
    }

    return render(
        request,
        "store/product_detail.html",
        context,
    )


# Search Functionality
def search(request):
    if "keyword" in request.GET:
        keyword = request.GET["keyword"]
        if keyword:
            search_query = Q(product_name__icontains=keyword) | Q(
                description__icontains=keyword
            )
            products = Product.objects.filter(search_query).order_by("modified_date")
            products_count = products.count()
    context = {
        "products": products,
        "products_count": products_count,
    }
    return render(request, "store/store.html", context)


@login_required(login_url="store")
def submit_review(request, product_id):
    if request.method != "POST":
        return redirect("store")

    redirect_url = request.META.get("HTTP_REFERER", "/")

    review = ReviewRating.objects.filter(
        user=request.user,
        product_id=product_id,
    ).first()

    form = ReviewForm(
        request.POST,
        instance=review,
    )

    if form.is_valid():
        review = form.save(commit=False)

        review.product_id = product_id
        review.user = request.user
        review.ip = request.META.get("REMOTE_ADDR")

        review.save()

        messages.success(
            request,
            "Thank you! Your review has been saved.",
        )

    return redirect(redirect_url)
