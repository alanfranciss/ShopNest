from django.conf import settings
from .models import Product

class Wishlist:
    def __init__(self, request):
        self.session = request.session
        wishlist = self.session.get('wishlist')
        if not wishlist:
            wishlist = self.session['wishlist'] = {}
        self.wishlist = wishlist

    def add(self, product):
        product_id = str(product.id)
        if product_id not in self.wishlist:
            self.wishlist[product_id] = {'price': str(product.price)}
            self.save()

    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.wishlist:
            del self.wishlist[product_id]
            self.save()

    def __iter__(self):
        from copy import deepcopy
        product_ids = self.wishlist.keys()
        products = Product.objects.filter(id__in=product_ids)
        wishlist = deepcopy(self.wishlist)
        for product in products:
            wishlist[str(product.id)]['product'] = product
        for item in wishlist.values():
            yield item

    def __len__(self):
        return len(self.wishlist.keys())

    def clear(self):
        if 'wishlist' in self.session:
            del self.session['wishlist']
            self.save()

    def save(self):
        self.session.modified = True
