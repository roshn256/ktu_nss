from django.shortcuts import render, redirect
from . import forms, models
from django.http import HttpResponseRedirect
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.mail import send_mail
from datetime import date, timedelta
from blood import forms as bforms
from blood import models as bmodels

# Donor Signup
def donor_signup_view(request):
    userForm = forms.DonorUserForm()
    donorForm = forms.DonorForm()
    mydict = {'userForm': userForm, 'donorForm': donorForm}
    
    if request.method == 'POST':
        userForm = forms.DonorUserForm(request.POST)
        donorForm = forms.DonorForm(request.POST, request.FILES)
        if userForm.is_valid() and donorForm.is_valid():
            user = userForm.save()
            user.set_password(user.password)
            user.save()

            donor = donorForm.save(commit=False)
            donor.user = user
            donor.bloodgroup = donorForm.cleaned_data['bloodgroup']
            donor.save()

            my_donor_group, _ = Group.objects.get_or_create(name='DONOR')
            my_donor_group.user_set.add(user)

            return HttpResponseRedirect('donorlogin')
    
    return render(request, 'donor/donorsignup.html', context=mydict)


# Donor Dashboard
@login_required(login_url='donorlogin')
def donor_dashboard_view(request):
    try:
        donor = models.Donor.objects.get(user_id=request.user.id)
    except models.Donor.DoesNotExist:
        return redirect('donorlogin')

    context = {
        'requestpending': bmodels.BloodRequest.objects.filter(request_by_donor=donor, status='Pending').count(),
        'requestapproved': bmodels.BloodRequest.objects.filter(request_by_donor=donor, status='Approved').count(),
        'requestmade': bmodels.BloodRequest.objects.filter(request_by_donor=donor).count(),
        'requestrejected': bmodels.BloodRequest.objects.filter(request_by_donor=donor, status='Rejected').count(),
    }
    return render(request, 'donor/donor_dashboard.html', context)


# Donate Blood
@login_required(login_url='donorlogin')
def donate_blood_view(request):
    donation_form = forms.DonationForm()

    if request.method == 'POST':
        donation_form = forms.DonationForm(request.POST)
        if donation_form.is_valid():
            try:
                donor = models.Donor.objects.get(user_id=request.user.id)
            except models.Donor.DoesNotExist:
                return redirect('donorlogin')

            blood_donate = donation_form.save(commit=False)
            blood_donate.bloodgroup = donation_form.cleaned_data['bloodgroup']
            blood_donate.donor = donor
            blood_donate.save()
            return HttpResponseRedirect('donation-history')
    
    return render(request, 'donor/donate_blood.html', {'donation_form': donation_form})


# Donation History
@login_required(login_url='donorlogin')
def donation_history_view(request):
    try:
        donor = models.Donor.objects.get(user_id=request.user.id)
    except models.Donor.DoesNotExist:
        return redirect('donorlogin')

    donations = models.BloodDonate.objects.filter(donor=donor)
    return render(request, 'donor/donation_history.html', {'donations': donations})


# Make Blood Request
@login_required(login_url='donorlogin')
def make_request_view(request):
    request_form = bforms.RequestForm()

    if request.method == 'POST':
        request_form = bforms.RequestForm(request.POST)
        if request_form.is_valid():
            try:
                donor = models.Donor.objects.get(user_id=request.user.id)
            except models.Donor.DoesNotExist:
                return redirect('donorlogin')

            blood_request = request_form.save(commit=False)
            blood_request.bloodgroup = request_form.cleaned_data['bloodgroup']
            blood_request.request_by_donor = donor
            blood_request.save()
            return HttpResponseRedirect('request-history')
    
    return render(request, 'donor/makerequest.html', {'request_form': request_form})


# Request History
@login_required(login_url='donorlogin')
def request_history_view(request):
    try:
        donor = models.Donor.objects.get(user_id=request.user.id)
    except models.Donor.DoesNotExist:
        return redirect('donorlogin')

    blood_request = bmodels.BloodRequest.objects.filter(request_by_donor=donor)
    return render(request, 'donor/request_history.html', {'blood_request': blood_request})
