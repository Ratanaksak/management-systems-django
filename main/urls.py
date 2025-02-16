from django.urls import path
from django.shortcuts import render
from . import views
from .views import generate_qr_code, scan_qr_code
from .views import record_attendance
from .views import add_person
from .views import person_list

urlpatterns = [
    path('', views.home, name='home'),
    path('home/', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.register, name='register'),
    path('generate-qr/', generate_qr_code, name='generate_qr'),
    path('scan-qr/', scan_qr_code, name='scan_qr'),
    path('record-attendance/', record_attendance, name='record_attendance'),
    path('attendance-result/', views.attendance_result, name='attendance_result'),
    path('add-person/', add_person, name='add_person'),
    path('add-person/', views.add_person, name='add_person'),
    path('get_districts/', views.get_districts, name='get_districts'),
    path('get_communes/', views.get_communes, name='get_communes'),
    path('get_villages/', views.get_villages, name='get_villages'),
    path('edit-person/<int:id>/', views.edit_person, name='edit_person'),
    path('search-person/', views.search_person, name='search_person'),
    path('success/', lambda request: render(request, 'main/success.html'), name='success'), 
    path('persons/', person_list, name='person_list'),
    path('export-pdf/', views.export_pdf, name='export_pdf'),
    path('export-excel/', views.export_excel, name='export_excel'),
    path('persons-list/', views.render_persons, name='persons_list'),
]