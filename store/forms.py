from django import forms
from .models import ReviewRating, Product, ProductGallery, Variation

class ReviewForm(forms.ModelForm):
    class Meta:
        model = ReviewRating
        fields = ['review', 'rating']


class ContactForm(forms.Form):
    first_name = forms.CharField(max_length = 50)
    email_address = forms.EmailField(max_length = 150)
    message = forms.CharField(widget = forms.Textarea, max_length = 2000)

    def __init__(self, *args, **kwargs):
        super(ContactForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs['placeholder'] = 'John Doe'
        self.fields['email_address'].widget.attrs['placeholder'] = 'info@example.com'
        self.fields['message'].widget.attrs['placeholder'] = 'Enter Your Message here..'
        self.fields['message'].widget.attrs['rows'] = '5'
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'


class GalleryImageForm(forms.ModelForm):
    class Meta:
        model = ProductGallery
        fields = ['image']

    def __init__(self, *args, **kwargs):
        super(GalleryImageForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control border-0'

class ProductImageForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['images']
        labels = {'images':'Main Image'}

    def __init__(self, *args, **kwargs):
        super(ProductImageForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control border-0'


class UpdateProductForm(forms.ModelForm):
    CHOICES=[('True','Yes'),
         ('False','No')]
    is_digital = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect)
    class Meta:
        model = Product
        fields = ['product_name', 'description', 'price', 'stock', 'category', 'is_digital']

    def __init__(self, *args, **kwargs):
        super(UpdateProductForm, self).__init__(*args, **kwargs)
        self.fields['product_name'].widget.attrs['placeholder'] = 'Product name'
        self.fields['description'].widget.attrs['placeholder'] = 'description'
        self.fields['price'].widget.attrs['placeholder'] = 'Price'
        self.fields['stock'].widget.attrs['placeholder'] = 'Available Stock'
        self.fields['category'].widget.attrs['placeholde'] = 'Category'
        for field in self.fields:
            if field == 'is_digital':
                continue
            else:
                self.fields[field].widget.attrs['class'] = 'form-control'

class CreateVariationForm(forms.ModelForm):
    product = forms.CharField(max_length=100)
    class Meta:
        model = Variation
        fields = ['variation_category', 'variation_value']

    def __init__(self, *args, **kwargs):
        super(CreateVariationForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'
