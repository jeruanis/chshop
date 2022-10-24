from django import template
from django.template.defaultfilters import stringfilter
import random

register = template.Library()

@register.filter
@stringfilter #this will make the output string
def slashq(value):
    return value.replace("'" ,"\'")

@register.filter()
def int(value):
    return int(value)

@register.filter()
def rand_num(value):
    return random.randint(0,100)

@register.filter()
def rand_let(value):
    return random.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXWZ')

@register.filter
def items(value):
    """
    Simple filter to return the items of the dict. Useful when the dict may
    have a key 'items' which is resolved first in Django template dot-notation
    lookup.  See issue #4931
    Also see: https://stackoverflow.com/questions/15416662/django-template-loop-over-dictionary-items-with-items-as-key
    """
    if value is None:
        # `{% for k, v in value.items %}` doesn't raise when value is None or
        # not in the context, so neither should `{% for k, v in value|items %}`
        return []
    return value.items()
