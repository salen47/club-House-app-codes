from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Avg
from .models import Review

@receiver(post_save, sender=Review)
def update_artisan_rating(sender, instance, **kwargs):
    artisan_profile = instance.artisan.artisan_profile
    reviews = artisan_profile.user.received_reviews.all()
    artisan_profile.average_rating = reviews.aggregate(Avg('rating'))['rating__avg']
    artisan_profile.number_of_jobs = reviews.count()
    artisan_profile.save()
