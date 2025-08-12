from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import User, Job, Quote, Review

class SignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email', 'phone_number', 'location', 'role')

class JobCreationForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'description', 'job_category', 'location']

class QuoteForm(forms.ModelForm):
    class Meta:
        model = Quote
        fields = ['amount', 'message']

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
