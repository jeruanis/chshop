from django import forms
from .models import Account
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _
from django.core.validators import RegexValidator
import re
from django.shortcuts import render

class RegistrationForm(forms.ModelForm):
    alphabet_fname  = RegexValidator(r'^[a-zA-Z]*$', 'Only letters are allowed in first name.')
    alphabet_lname  = RegexValidator(r'^[a-zA-Z]*$', 'Only letters are allowed in last name.')
    first_name      =forms.CharField(min_length=1, max_length=50, help_text='Required', validators=[alphabet_fname])
    last_name       =forms.CharField(min_length=1, max_length=50, help_text='Required', validators=[alphabet_lname])
    email           =forms.EmailField(max_length=100, help_text='Required')
    phone           =forms.CharField(max_length=50)
    password        = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Enter Password'}))
    confirm_password= forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Confirm Password'}))

    class Meta:
        model = Account
        fields = ['first_name', 'last_name', 'phone', 'email', 'password', 'confirm_password', 'country']

    def clean_confirm_password(self):
        cd=super(RegistrationForm, self).clean()
        if cd['password'] != cd['confirm_password']:
            raise ValidationError(
                _('Password do not match.'),
                code='password_no_matched1',
            )
        if len(cd['password']) < 6:
            raise ValidationError(
                _('Password must be at least 6 characters.'),
                code='password_too_short1',
            )
        if not re.findall('[A-Z]', cd['password']):
            raise ValidationError(
                _("The password must contain uppercase letters"),
                code='password_no_upper1',
            )
        if not re.findall('[a-z]', cd['password']):
            raise ValidationError(
                _("The password must contain lowercase letters"),
                code='password_no_lower1',
            )
        if not re.findall('\d', cd['password']):
            raise ValidationError(
                _("The password must contain at least 1 digit, 0-9."),
                code='password_no_number1',
            )
        if not re.findall('[()[\]{}|\\`~!@#$%^&*_\-+=;:\'",<>./?]', cd['password']):
            raise ValidationError(
                _("The password must contain at least 1 symbol: " +
                  "()[]{}|\`~!@#$%^&*_-+=;:'\",<>./?"),
                code='password_no_symbol1',
            )
        return cd['confirm_password']


    def __init__(self, *args, **kwargs): 
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs['placeholder'] = 'Enter First Name'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Enter Last Name'
        self.fields['phone'].widget.attrs['placeholder'] = 'Enter Phone Number'
        self.fields['email'].widget.attrs['placeholder'] = 'Enter Email'
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'
            self.fields[field].widget.attrs['style'] = 'height:42px;box-shadow: none !important;border-radius: 3px;height: 41px;outline: none !important;border-color: #a79b9b;'


class LoginForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Enter Password'}))
    class Meta:
        model = Account
        fields = ['email', 'password']

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.fields['email'].widget.attrs['placeholder'] = 'Enter Email'

        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'
            self.fields[field].widget.attrs['autocomplete'] = 'off'
            self.fields[field].widget.attrs['style'] = 'height:42px;box-shadow: none !important;border-radius: 3px;height: 41px;outline: none !important;border-color: #a79b9b;'


class EditProfileForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['first_name', 'last_name', 'email', 'phone', 'profession', 'address_line_1', 'address_line_2', 'country', 'state', 'city', 'zip']

    def __init__(self, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'


class CheckoutForm(forms.ModelForm):

    class Meta:
        model = Account
        fields = ['first_name', 'last_name', 'email', 'phone', 'address_line_1', 'address_line_2', 'country', 'state', 'city', 'zip']

    def __init__(self, *args, **kwargs):
        super(CheckoutForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

        self.fields['city'].required =True
        self.fields['state'].required =True
        self.fields['country'].required =True

class UserProfilePicForm(forms.ModelForm):
    profile_pic = forms.ImageField(required=False, error_messages = {'invalid':("Image files only")}, widget=forms.FileInput)

    class Meta:
        model = Account
        fields = ['profile_pic']

    def __init__(self, *args, **kwargs):
        super(UserProfilePicForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control d-none'
            self.fields[field].widget.attrs['onchange'] = 'readURL(this)'
            self.fields[field].widget.attrs['name'] = 'profile_pic'
            self.fields[field].widget.attrs['id'] = 'id_profile_image'

class PwdChangeForm(forms.ModelForm): #we need to put validation because the default is lacking
    old_password=forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Enter Old Password'}))
    new_password1=forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Enter New Password'}))
    new_password2=forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Confirm New Password'}))

    class Meta:
        model=Account
        fields=['old_password', 'new_password1', 'new_password2']

    def __init__(self, *args, **kwargs):
        super(PwdChangeForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

    def clean_new_password2(self):
        cd=self.cleaned_data
        if cd['new_password1'] != cd['new_password2']:
            raise ValidationError(
                _('Password do not match.'),
                code='password_no_matched1',
            )
        if len(cd['new_password1']) < 6:
            raise ValidationError(
                _('Password must be at least 6 characters.'),
                code='password_too_short1',
            )
        if not re.findall('[A-Z]', cd['new_password1']):
            raise ValidationError(
                _("The password must contain uppercase letters"),
                code='password_no_upper1',
            )
        if not re.findall('[a-z]', cd['new_password1']):
            raise ValidationError(
                _("The password must contain lowercase letters"),
                code='password_no_lower1',
            )
        if not re.findall('\d', cd['new_password1']):
            raise ValidationError(
                _("The password must contain at least 1 digit, 0-9."),
                code='password_no_number1',
            )
        if not re.findall('[()[\]{}|\\`~!@#$%^&*_\-+=;:\'",<>./?]', cd['new_password1']):
            raise ValidationError(
                _("The password must contain at least 1 symbol: " +
                  "()[]{}|\`~!@#$%^&*_-+=;:'\",<>./?"),
                code='password_no_symbol1',
            )
        return cd['new_password2']
