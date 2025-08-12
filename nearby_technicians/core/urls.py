from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomePageView.as_view(), name='home'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('job/create/', views.JobCreateView.as_view(), name='job_create'),
    path('job/<int:pk>/', views.JobDetailView.as_view(), name='job_detail'),
    path('artisan/<int:pk>/', views.ArtisanProfileDetailView.as_view(), name='artisan_profile_detail'),
    path('quote/<int:pk>/accept/', views.accept_quote, name='accept_quote'),
    path('job/<int:pk>/complete/', views.complete_job, name='complete_job'),
]
