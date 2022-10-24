from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Account
from django.utils.html import format_html

class AccountAdmin(UserAdmin):
    list_display = ('thumbnail', 'email', 'username', 'first_name', 'last_name', 'last_login', 'date_joined', 'is_active')
    list_display_links = ('email', 'first_name', 'last_name')
    readonly_fields = ('last_login', 'date_joined')
    ordering = ('-date_joined',)

    filter_horizontal =()
    list_filter = ()
    fieldsets = ()

    def thumbnail(self, object):
        return format_html('<img src="{}" style="border-radius:50%" width="30">'.format(object.profile_pic.url))
    thumbnail.short_description = 'Profile Picture'

admin.site.register(Account, AccountAdmin)
