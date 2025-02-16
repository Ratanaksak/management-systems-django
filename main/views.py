
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
import qrcode
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from io import BytesIO
from django.utils.timezone import now
from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from django.contrib.auth.models import User
from .models import Attendance
import json
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, time
from datetime import timedelta
from .forms import PersonForm
from .models import Person
from .models import Province, District, Commune, Village
from django.db.models import Sum
from decimal import Decimal
from django.template.loader import render_to_string
from xhtml2pdf import pisa
import os
import openpyxl

# Create your views here.
def home(request):
    return render(request, 'main/home.html')

def about(request):
    return render(request, 'main/about.html')

# Authentication views
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'main/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                # Redirect to the next page if provided
                next_url = request.GET.get('next', 'home')
                return redirect(next_url)
    else:
        form = AuthenticationForm()
    return render(request, 'main/login.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('home')

@login_required
def generate_qr_code(request):
    # Generate QR code with today's date for all staff
    qr_data = f"attendance|{now().date()}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer)
    buffer.seek(0)
    return HttpResponse(buffer, content_type="image/png")

@login_required
def scan_qr_code(request):
    return render(request, "main/scan_qr.html")


@login_required
@csrf_exempt
def record_attendance(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            qr_data = data.get("qr_data")

            # Validate QR data format
            if not qr_data or not qr_data.startswith("attendance|"):
                return JsonResponse({"error": "Invalid QR data format"}, status=400)

            # Extract data from QR code
            _, qr_date = qr_data.split("|")
            qr_date = datetime.strptime(qr_date, "%Y-%m-%d").date()

           

              # Get the current time in the configured timezone
            current_time = now().astimezone().time()
            cutoff_time = time(8, 0, 0)

            # Determine the attendance status based on the current time
            status = "Late" if current_time > cutoff_time else "Morning"

            # Check if an attendance record already exists for this user and date
            attendance, created = Attendance.objects.get_or_create(
                user=request.user,
                date=qr_date,
                defaults={
                    "time": current_time,
                    "status": status,
                },
            )

            # If the record already exists, update it
            if not created:
                attendance.time = current_time
                attendance.status = status
                attendance.save()

            return JsonResponse({"message": f"Attendance recorded: {status}"})

        except Exception as e:
            return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)


def attendance_result(request):
    # Extract the message from query parameters
    message = request.GET.get('message', 'No message available')
    return render(request, 'main/attendance_result.html', {'message': message})


#for add attendance wedding


def add_person(request):
    # Fetch all provinces
    provinces = Province.objects.all()

    # Check if an ID is provided for editing
    person = None
    if request.GET.get('id'):
        person = get_object_or_404(Person, id=request.GET['id'])

    if request.method == 'POST':
        # If editing, instance is the person object; otherwise, it's None
        form = PersonForm(request.POST, instance=person)
        if form.is_valid():
            form.save()
            return redirect('add_person')  # Redirect to prevent form resubmission
    else:
        # Render the form with the existing person object or as a blank form
        form = PersonForm(instance=person)

    # Calculate totals for price_usd and price_khr
    totals = Person.objects.aggregate(
        total_usd=Sum('price_usd') or Decimal(0.00),
        total_khr=Sum('price_khr') or Decimal(0.00)
    )

    # Count the total number of persons
    person_count = Person.objects.count()

    return render(request, 'main/add_person.html', {
        'form': form,
        'provinces': provinces,
        'person': person,
        'total_usd': totals['total_usd'],
        'total_khr': totals['total_khr'],
        'person_count': person_count,  # Pass person count to the template
    })


def export_pdf(request):
    # Get data you want to export
    persons = Person.objects.all()

    # Render the HTML template
    html_content = render_to_string('main/export_pdf_template.html', {'persons': persons})

    # Path to your custom Khmer font (adjust the path as needed)
    font_path = os.path.join(os.path.dirname(__file__), 'path_to_fonts', 'NotoSansKhmer-Regular.ttf')

    # Create a response object with PDF content type
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="persons_list.pdf"'

    # Create PDF with custom font
    pdf_file = BytesIO()
    pisa_status = pisa.CreatePDF(html_content, dest=pdf_file, link_callback=lambda uri, rel: uri if uri.startswith('http') else os.path.join(os.path.dirname(__file__), uri))

    # Check if there was an error generating the PDF
    if pisa_status.err:
        return HttpResponse('Error generating PDF', status=500)

    # Write the PDF to the response object
    pdf_file.seek(0)
    response.write(pdf_file.read())
    return response

def export_excel(request):
    # Create an Excel workbook and sheet
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Persons"

    # Add header row
    headers = ['Name', 'Province (Khmer)', 'District (Khmer)', 'Commune (Khmer)', 'Village (Khmer)', 'Price-KHR', 'Price-USD']
    sheet.append(headers)

    # Add data rows
    persons = Person.objects.all()
    for person in persons:
        sheet.append([
            person.name,
            person.province.kh_name if person.province else 'N/A',
            person.district.kh_name if person.district else 'N/A',
            person.commune.kh_name if person.commune else 'N/A',
            person.village.kh_name if person.village else 'N/A',
            person.price_khr,
            person.price_usd,
        ])

    # Create a response object for the Excel file
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="persons_list.xlsx"'

    # Save workbook to the response
    workbook.save(response)
    return response

def render_persons(request):
    persons = Person.objects.all()
    return render(request, 'main/persons_list.html', {'persons': persons})

def search_person(request):
    search = request.GET.get('search')
    if search:
        persons = Person.objects.filter(name__icontains=search)
    else:
        persons = Person.objects.all()
    return render(request, 'main/search_results.html', {'persons': persons})

def get_districts(request):
    province_id = request.GET.get('province_id')
    districts = District.objects.filter(province_id=province_id).values('id', 'name', 'kh_name')
    return JsonResponse(list(districts), safe=False)

def get_communes(request):
    district_id = request.GET.get('district_id')
    communes = Commune.objects.filter(district_id=district_id).values('id', 'name', 'kh_name')
    return JsonResponse(list(communes), safe=False)

def get_villages(request):
    commune_id = request.GET.get('commune_id')
    villages = Village.objects.filter(commune_id=commune_id).values('id', 'name', 'kh_name')
    return JsonResponse(list(villages), safe=False)

def edit_person(request, id):
    # Get the person by id or return 404 if not found
    person = get_object_or_404(Person, id=id)
    
    if request.method == 'POST':
        form = PersonForm(request.POST, instance=person)
        if form.is_valid():
            form.save()
            return redirect('add_person')  # Redirect to a success page or back to the form
    else:
        form = PersonForm(instance=person)

    return render(request, 'main/edit_person.html', {'form': form, 'person': person})

def person_list(request):
    # Calculate totals
    totals = Person.objects.aggregate(
        total_price_usd=Sum('price_usd'),
        total_price_khr=Sum('price_khr')
    )
    grand_total = (totals['total_price_usd'] or 0) + (totals['total_price_khr'] or 0)

    # Pass totals to the template
    context = {
        'persons': Person.objects.all(),  # If you want to list all persons
        'total_price_usd': totals['total_price_usd'] or 0,
        'total_price_khr': totals['total_price_khr'] or 0,
        'grand_total': grand_total,
    }
    return render(request, 'person_list.html', context)
