from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.

class User(AbstractUser):
    class Role(models.TextChoices):
        CUSTOMER = 'CUSTOMER', 'Customer'
        ARTISAN = 'ARTISAN', 'Artisan'

    phone_number = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    location = models.CharField(max_length=255, blank=True)
    role = models.CharField(max_length=50, choices=Role.choices, default=Role.CUSTOMER)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class ArtisanProfile(models.Model):
    class ServiceCategory(models.TextChoices):
        PLUMBING = 'PLUMBING', 'Plumbing'
        ELECTRICAL = 'ELECTRICAL', 'Electrical'
        TILING = 'TILING', 'Tiling'
        PAINTING = 'PAINTING', 'Painting'
        MECHANIC = 'MECHANIC', 'Mechanic'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='artisan_profile')
    service_category = models.CharField(max_length=50, choices=ServiceCategory.choices, null=True, blank=True)
    bio = models.TextField(blank=True)
    average_rating = models.FloatField(default=0.0)
    number_of_jobs = models.IntegerField(default=0)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

class PortfolioImage(models.Model):
    artisan_profile = models.ForeignKey(ArtisanProfile, on_delete=models.CASCADE, related_name='portfolio_images')
    image = models.ImageField(upload_to='portfolio_images/')


class Job(models.Model):
    class JobStatus(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        ASSIGNED = 'ASSIGNED', 'Assigned'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    posted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posted_jobs')
    title = models.CharField(max_length=255)
    description = models.TextField()
    job_category = models.CharField(max_length=50, choices=ArtisanProfile.ServiceCategory.choices)
    location = models.CharField(max_length=255)
    status = models.CharField(max_length=50, choices=JobStatus.choices, default=JobStatus.OPEN)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_jobs')
    date_posted = models.DateTimeField(auto_now_add=True)
    final_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.title

class JobPhoto(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='job_photos/')


class Quote(models.Model):
    class QuoteStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        REJECTED = 'REJECTED', 'Rejected'

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='quotes')
    artisan = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quotes')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    message = models.TextField()
    status = models.CharField(max_length=50, choices=QuoteStatus.choices, default=QuoteStatus.PENDING)

    def __str__(self):
        return f"Quote for {self.job.title} by {self.artisan.username}"

class Review(models.Model):
    job = models.OneToOneField(Job, on_delete=models.CASCADE, related_name='review')
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_reviews')
    artisan = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_reviews')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    date_submitted = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for {self.job.title} by {self.customer.username}"
