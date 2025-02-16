from django.contrib import admin
from .models import Attendance
from django.utils.timezone import localtime
from datetime import timedelta
from django.utils.timezone import now
# Register your models here.
from django.contrib import admin
from .models import Product
from .models import Attendance
from django.db.models import Count
from .utils import mark_absentees
from openpyxl import Workbook
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from .models import Person
from .models import Person, Province, District, Commune, Village
from django.db.models import Sum
from django.urls import path
from django.shortcuts import render
from django.utils.safestring import mark_safe
from import_export import resources
from import_export.admin import ExportMixin
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price')
    search_fields = ('name', 'description')




class AttendanceAdmin(admin.ModelAdmin):
    search_fields = ('user__username', 'status')

    list_display = ('user', 'date', 'local_time', 'status')

    def local_time(self, obj):
        return localtime(obj.time).strftime('%H:%M:%S')  # Convert to local time
    local_time.short_description = 'Local Time'



class DayFilter(admin.SimpleListFilter):
    title = 'Day'
    parameter_name = 'day'

    def lookups(self, request, model_admin):
        return [
            ('today', 'Today'),
            ('yesterday', 'Yesterday'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'today':
            return queryset.filter(date=now().date())
        elif self.value() == 'yesterday':
            return queryset.filter(date=now().date() - timedelta(days=1))
        return queryset

class WeekFilter(admin.SimpleListFilter):
    title = 'Week'
    parameter_name = 'week'

    def lookups(self, request, model_admin):
        return [
            ('current_week', 'This Week'),
            ('last_week', 'Last Week'),
        ]

    def queryset(self, request, queryset):
        today = now().date()
        start_of_week = today - timedelta(days=today.weekday())
        if self.value() == 'current_week':
            return queryset.filter(date__gte=start_of_week, date__lte=today)
        elif self.value() == 'last_week':
            start_of_last_week = start_of_week - timedelta(weeks=1)
            end_of_last_week = start_of_week - timedelta(days=1)
            return queryset.filter(date__gte=start_of_last_week, date__lte=end_of_last_week)
        return queryset

class MonthFilter(admin.SimpleListFilter):
    title = 'Month'
    parameter_name = 'month'

    def lookups(self, request, model_admin):
        return [
            ('current_month', 'This Month'),
            ('last_month', 'Last Month'),
        ]

    def queryset(self, request, queryset):
        today = now().date()
        first_of_month = today.replace(day=1)
        if self.value() == 'current_month':
            return queryset.filter(date__gte=first_of_month)
        elif self.value() == 'last_month':
            last_month_end = first_of_month - timedelta(days=1)
            last_month_start = last_month_end.replace(day=1)
            return queryset.filter(date__gte=last_month_start, date__lte=last_month_end)
        return queryset

class YearFilter(admin.SimpleListFilter):
    title = 'Year'
    parameter_name = 'year'

    def lookups(self, request, model_admin):
        current_year = now().year
        return [
            (str(current_year), f'{current_year}'),
            (str(current_year - 1), f'{current_year - 1}'),
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(date__year=self.value())
        return queryset


    


class FiveLateInMonthFilter(admin.SimpleListFilter):
    title = 'Staff with 5+ Late in a Month'
    parameter_name = 'five_late_month'

    def lookups(self, request, model_admin):
        return [
            ('current_month', 'Current Month'),
            ('last_month', 'Last Month'),
        ]

    def queryset(self, request, queryset):
        today = now().date()
        first_of_current_month = today.replace(day=1)

        if self.value() == 'current_month':
            filtered_users = (
                queryset.filter(status='Late', date__gte=first_of_current_month)
                .values('user')
                .annotate(late_count=Count('id'))
                .filter(late_count__gte=5)
                .values_list('user', flat=True)
            )
            return queryset.filter(user__id__in=filtered_users)

        elif self.value() == 'last_month':
            first_of_last_month = (first_of_current_month - timedelta(days=1)).replace(day=1)
            last_of_last_month = first_of_current_month - timedelta(days=1)

            filtered_users = (
                queryset.filter(
                    status='Late',
                    date__gte=first_of_last_month,
                    date__lte=last_of_last_month,
                )
                .values('user')
                .annotate(late_count=Count('id'))
                .filter(late_count__gte=5)
                .values_list('user', flat=True)
            )
            return queryset.filter(user__id__in=filtered_users)

        return queryset
    



@admin.action(description='Mark Absentees for Selected Date')
def mark_absentees_action(modeladmin, request, queryset):
    # Get the selected date(s)
    selected_dates = queryset.values_list('date', flat=True).distinct()
    for date in selected_dates:
        mark_absentees(date)


class AbsentFilter(admin.SimpleListFilter):
    title = 'Absent Filter'
    parameter_name = 'absent'

    def lookups(self, request, model_admin):
        return [
            ('absent', 'Absent'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'absent':
            return queryset.filter(status='Absent')
        return queryset

    
# Export to Excel
def export_to_excel(modeladmin, request, queryset):
    # Create an Excel workbook and worksheet
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Attendance Records"

    # Define column headers
    headers = ['User', 'Date', 'Time', 'Status']
    worksheet.append(headers)

    # Add attendance data to the worksheet
    for attendance in queryset:
        worksheet.append([
            attendance.user.username,
            attendance.date.strftime('%Y-%m-%d'),
            attendance.time.strftime('%H:%M:%S'),
            attendance.status
        ])

    # Create HTTP response for the Excel file
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=attendance.xlsx'
    workbook.save(response)
    return response

export_to_excel.short_description = "Export Selected Attendance to Excel"

# Export to PDF
def export_to_pdf(modeladmin, request, queryset):
    # Create HTTP response with PDF content type
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="attendance.pdf"'

    # Create PDF canvas
    p = canvas.Canvas(response)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 800, "Attendance Records")

    # Column headers
    p.setFont("Helvetica", 12)
    headers = ["User", "Date", "Time", "Status"]
    x_offset = [100, 250, 350, 450]
    y = 770

    for i, header in enumerate(headers):
        p.drawString(x_offset[i], y, header)

    # Add attendance records to PDF
    y -= 20
    for attendance in queryset:
        p.drawString(x_offset[0], y, attendance.user.username)
        p.drawString(x_offset[1], y, attendance.date.strftime('%Y-%m-%d'))
        p.drawString(x_offset[2], y, attendance.time.strftime('%H:%M:%S'))
        p.drawString(x_offset[3], y, attendance.status)
        y -= 20

        # Check for page overflow
        if y < 50:
            p.showPage()
            y = 770

    p.showPage()
    p.save()
    return response

export_to_pdf.short_description = "Export Selected Attendance to PDF"
    
@admin.register(Attendance) 
class AttendanceAdmin(admin.ModelAdmin):
    
    list_display = ('user', 'date', 'time', 'status', 'late_count')
   
    def late_count(self, obj):
        return Attendance.objects.filter(user=obj.user, status='Late', date__month=obj.date.month).count()
    late_count.short_description = 'Late Count'
    search_fields = ('user__username', 'status')
    list_filter = (DayFilter, WeekFilter, MonthFilter, YearFilter,FiveLateInMonthFilter, AbsentFilter)
    actions = [mark_absentees_action, export_to_excel, export_to_pdf]

class PersonResource(resources.ModelResource):
    class Meta:
        model = Person
        fields = ('name', 'price_usd', 'price_khr', 'gender', 'relationship', 
                  'province_kh_name', 'district_kh_name', 'commune_kh_name', 'village_kh_name')
    
    def before_export(self, queryset, *args, **kwargs):
        """
        This method is called before the export.
        You can manipulate the data here before it's exported.
        """
        for obj in queryset:
            # Ensure Khmer names are used for export
            obj.province_kh_name = obj.province.kh_name if obj.province else ''
            obj.district_kh_name = obj.district.kh_name if obj.district else ''
            obj.commune_kh_name = obj.commune.kh_name if obj.commune else ''
            obj.village_kh_name = obj.village.kh_name if obj.village else ''
        return queryset

@admin.register(Province)
class ProvinceAdmin(admin.ModelAdmin):
    list_display = ('name', 'kh_name')

@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('name', 'kh_name', 'province')

@admin.register(Commune)
class CommuneAdmin(admin.ModelAdmin):
    list_display = ('name', 'kh_name', 'district')

@admin.register(Village)
class VillageAdmin(admin.ModelAdmin):
    list_display = ('name', 'kh_name', 'commune')
@admin.register(Person)
class PersonAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ('name', 'price_usd', 'price_khr', 'gender', 'relationship', 
                    'province_kh_name', 'district_kh_name', 'commune_kh_name', 'village_kh_name')

    search_fields = ('name', 'address', 'province__name', 'province__kh_name', 
                     'district__name', 'district__kh_name', 'commune__name', 
                     'commune__kh_name', 'village__name', 'village__kh_name')

    def changelist_view(self, request, extra_context=None):
        # Add totals to the context
        totals = Person.objects.aggregate(
            total_usd=Sum('price_usd'),
            total_khr=Sum('price_khr')
        )
        extra_context = extra_context or {}
        extra_context['total_usd'] = totals['total_usd']
        extra_context['total_khr'] = totals['total_khr']
        return super().changelist_view(request, extra_context=extra_context)

    # Add export functionality to the admin
    resource_class = PersonResource

    # Custom methods to display Khmer names
    def province_kh_name(self, obj):
        return obj.province.kh_name if obj.province else None
    province_kh_name.short_description = 'Province (Khmer)'

    def district_kh_name(self, obj):
        return obj.district.kh_name if obj.district else None
    district_kh_name.short_description = 'District (Khmer)'

    def commune_kh_name(self, obj):
        return obj.commune.kh_name if obj.commune else None
    commune_kh_name.short_description = 'Commune (Khmer)'

    def village_kh_name(self, obj):
        return obj.village.kh_name if obj.village else None
    village_kh_name.short_description = 'Village (Khmer)'


class CustomAdminSite(admin.AdminSite):
    def get_urls(self):
        # Get the default URLs and add the custom dashboard URL
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(self.dashboard_view)),  # Custom URL for dashboard
        ]
        return custom_urls + urls

    def dashboard_view(self, request):
        # Aggregate the total price_usd and price_khr
        totals = Person.objects.aggregate(
            total_price_usd=Sum('price_usd'),
            total_price_khr=Sum('price_khr')
        )
        total_price_usd = totals['total_price_usd'] or 0
        total_price_khr = totals['total_price_khr'] or 0

        # Render the totals in a custom template or return as a simple HttpResponse
        context = {
            'total_price_usd': total_price_usd,
            'total_price_khr': total_price_khr
        }
        return render(request, 'admin/dashboard.html', context)

# Create an instance of the custom admin site
custom_admin_site = CustomAdminSite(name='custom_admin')

# Register the models with the custom admin site
custom_admin_site.register(Person)

# Optionally, you can register other models as well
# custom_admin_site.register(OtherModel)