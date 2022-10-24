from rest_framework import permissions
from accounts.models import Account

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of object to edit it
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.added_by == request.user

    def has_permission(self, request, view):
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        try:
            user = Account.objects.get(email=request.user.email)
            group = user.group
            if group.name == 'Seller':
                return True
        except Exception:
            print('You are not logged in.')
