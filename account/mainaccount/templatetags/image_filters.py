from django import template

register = template.Library()

@register.filter
def get_main_image(images):
    return images.filter(is_main=True).first()

@register.filter
def get_hover_image(images):
    return images.filter(is_main=False).first()