from django import template

register = template.Library()

@register.filter
def has_approved_seller_profile(user):
    return hasattr(user, 'seller_profile') and user.seller_profile.is_approved