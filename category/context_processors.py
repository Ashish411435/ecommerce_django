from .models import Category

def category_links(request):
    cat_links = Category.objects.all()
    return dict(categories=cat_links)