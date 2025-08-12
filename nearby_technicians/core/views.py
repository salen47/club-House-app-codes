from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.views.generic import TemplateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.db import models
from .forms import SignUpForm, JobCreationForm, QuoteForm, ReviewForm
from .models import User, Job, ArtisanProfile, Quote

class SignUpView(CreateView):
    form_class = SignUpForm
    success_url = reverse_lazy('login') # Redirect to login page after successful sign-up
    template_name = 'registration/signup.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.object.role == User.Role.ARTISAN:
            ArtisanProfile.objects.create(user=self.object)
        return response

class HomePageView(TemplateView):
    def get_template_names(self):
        if self.request.user.is_authenticated:
            if self.request.user.role == User.Role.ARTISAN:
                return ['artisan_home.html']
            else:
                return ['customer_home.html']
        return ['home.html'] # For anonymous users

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            if self.request.user.role == User.Role.ARTISAN:
                # This will fail if an artisan has no profile.
                # I should handle that case.
                # For now, I'll assume the profile exists.
                artisan_profile = self.request.user.artisan_profile
                context['jobs'] = Job.objects.filter(
                    status=Job.JobStatus.OPEN,
                    job_category=artisan_profile.service_category
                )
            else: # Customer
                context['jobs'] = Job.objects.filter(posted_by=self.request.user)
        return context

class JobDetailView(DetailView):
    model = Job
    template_name = 'job_detail.html'
    context_object_name = 'job'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            if self.request.user.role == User.Role.ARTISAN:
                context['quote_form'] = QuoteForm()
            elif self.request.user.role == User.Role.CUSTOMER and self.object.status == Job.JobStatus.COMPLETED and not hasattr(self.object, 'review'):
                context['review_form'] = ReviewForm()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_type = request.POST.get('form_type')

        if form_type == 'quote' and self.request.user.role == User.Role.ARTISAN:
            form = QuoteForm(request.POST)
            if form.is_valid():
                quote = form.save(commit=False)
                quote.job = self.object
                quote.artisan = request.user
                quote.save()
                return redirect('job_detail', pk=self.object.pk)

        elif form_type == 'review' and self.request.user.role == User.Role.CUSTOMER:
            form = ReviewForm(request.POST)
            if form.is_valid():
                review = form.save(commit=False)
                review.job = self.object
                review.customer = request.user
                review.artisan = self.object.assigned_to
                review.save()

                return redirect('job_detail', pk=self.object.pk)

        # Handle form errors or invalid form_type
        context = self.get_context_data()
        if 'form' in locals():
            if form_type == 'quote':
                context['quote_form'] = form
            elif form_type == 'review':
                context['review_form'] = form
        return self.render_to_response(context)

class ArtisanProfileDetailView(DetailView):
    model = ArtisanProfile
    template_name = 'artisan_profile_detail.html'
    context_object_name = 'profile'

class JobCreateView(LoginRequiredMixin, CreateView):
    model = Job
    form_class = JobCreationForm
    template_name = 'job_create.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        form.instance.posted_by = self.request.user
        return super().form_valid(form)

@login_required
def complete_job(request, pk):
    job = get_object_or_404(Job, pk=pk)

    # Security check: only the assigned artisan can complete the job
    if job.assigned_to != request.user:
        return redirect('home')

    job.status = Job.JobStatus.COMPLETED
    job.save()

    return redirect('job_detail', pk=job.pk)

@login_required
def accept_quote(request, pk):
    quote = get_object_or_404(Quote, pk=pk)
    job = quote.job

    # Security check: only the job poster can accept a quote
    if job.posted_by != request.user:
        # Or raise Http404, or show an error message
        return redirect('home')

    # Action 1: Update Job
    job.status = Job.JobStatus.ASSIGNED
    job.assigned_to = quote.artisan
    job.final_price = quote.amount
    job.save()

    # Action 2: Update Quotes
    quote.status = Quote.QuoteStatus.ACCEPTED
    quote.save()

    # Reject other quotes for this job
    job.quotes.exclude(pk=quote.pk).update(status=Quote.QuoteStatus.REJECTED)

    # Action 3: Notification (I'll skip the actual email/push notification for now)

    return redirect('job_detail', pk=job.pk)
