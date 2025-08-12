from django.test import TestCase
from django.urls import reverse
from .models import User, Job, Quote, Review, ArtisanProfile
from django.db.models import Avg

class CoreWorkflowTests(TestCase):

    def setUp(self):
        self.customer = User.objects.create_user(
            username='customer',
            password='password123',
            email='customer@example.com',
            role=User.Role.CUSTOMER,
            first_name='Customer',
            last_name='User'
        )
        self.artisan_user = User.objects.create_user(
            username='artisan',
            password='password123',
            email='artisan@example.com',
            role=User.Role.ARTISAN,
            first_name='Artisan',
            last_name='User'
        )
        self.artisan_profile = ArtisanProfile.objects.create(
            user=self.artisan_user,
            service_category=ArtisanProfile.ServiceCategory.PLUMBING
        )

    def test_customer_can_create_job(self):
        self.client.login(username='customer', password='password123')
        response = self.client.post(reverse('job_create'), {
            'title': 'Leaky faucet',
            'description': 'My kitchen faucet is leaking.',
            'job_category': ArtisanProfile.ServiceCategory.PLUMBING,
            'location': 'Harare'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Job.objects.filter(title='Leaky faucet', posted_by=self.customer).exists())

    def test_artisan_can_quote_for_job(self):
        job = Job.objects.create(
            posted_by=self.customer,
            title='Test Job',
            description='Test description',
            job_category=ArtisanProfile.ServiceCategory.PLUMBING,
            location='Harare'
        )
        self.client.login(username='artisan', password='password123')
        response = self.client.post(reverse('job_detail', kwargs={'pk': job.pk}), {
            'form_type': 'quote',
            'amount': 100.00,
            'message': 'I can fix this.'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Quote.objects.filter(job=job, artisan=self.artisan_user, amount=100.00).exists())

    def test_customer_can_accept_quote(self):
        job = Job.objects.create(
            posted_by=self.customer,
            title='Test Job',
            description='Test description',
            job_category=ArtisanProfile.ServiceCategory.PLUMBING,
            location='Harare'
        )
        quote = Quote.objects.create(
            job=job,
            artisan=self.artisan_user,
            amount=100.00,
            message='I can fix this.'
        )
        self.client.login(username='customer', password='password123')
        self.client.post(reverse('accept_quote', kwargs={'pk': quote.pk}))

        job.refresh_from_db()
        self.assertEqual(job.status, Job.JobStatus.ASSIGNED)
        self.assertEqual(job.assigned_to, self.artisan_user)

        quote.refresh_from_db()
        self.assertEqual(quote.status, Quote.QuoteStatus.ACCEPTED)

    def test_artisan_can_complete_job(self):
        job = Job.objects.create(
            posted_by=self.customer,
            assigned_to=self.artisan_user,
            status=Job.JobStatus.ASSIGNED,
            title='Test Job',
            description='Test description',
            job_category=ArtisanProfile.ServiceCategory.PLUMBING,
            location='Harare'
        )
        self.client.login(username='artisan', password='password123')
        self.client.post(reverse('complete_job', kwargs={'pk': job.pk}))
        job.refresh_from_db()
        self.assertEqual(job.status, Job.JobStatus.COMPLETED)

    def test_customer_can_leave_review_and_rating_updates(self):
        job = Job.objects.create(
            posted_by=self.customer,
            assigned_to=self.artisan_user,
            status=Job.JobStatus.COMPLETED,
            title='Test Job',
            description='Test description',
            job_category=ArtisanProfile.ServiceCategory.PLUMBING,
            location='Harare'
        )
        self.client.login(username='customer', password='password123')
        self.client.post(reverse('job_detail', kwargs={'pk': job.pk}), {
            'form_type': 'review',
            'rating': 5,
            'comment': 'Great job!'
        })

        self.assertTrue(Review.objects.filter(job=job, rating=5).exists())

        self.artisan_profile.refresh_from_db()
        self.assertEqual(self.artisan_profile.average_rating, 5.0)
        self.assertEqual(self.artisan_profile.number_of_jobs, 1)

        # Test with a second review
        job2 = Job.objects.create(
            posted_by=self.customer,
            assigned_to=self.artisan_user,
            status=Job.JobStatus.COMPLETED,
        )
        Review.objects.create(job=job2, customer=self.customer, artisan=self.artisan_user, rating=3)

        self.artisan_profile.refresh_from_db()
        self.assertEqual(self.artisan_profile.average_rating, 4.0)
        self.assertEqual(self.artisan_profile.number_of_jobs, 2)
