from .cart import Cart
from .wishlist import Wishlist

def cart(request):
    return {'cart': Cart(request)}

def wishlist(request):
    wishlist_obj = Wishlist(request)
    wishlist_product_ids = [int(pid) for pid in wishlist_obj.wishlist.keys()]
    return {
        'wishlist': wishlist_obj, 
        'wishlist_product_ids': wishlist_product_ids
    }
