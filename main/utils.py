# utils.py
from django.utils.timezone import now
from django.contrib.auth.models import User
from .models import Attendance
from datetime import date

def mark_absentees(date=None):
    """
    Identify users who did not scan attendance and mark them as 'Absent'.
    """
    if date is None:
        date = now().date()  # Default to today

    # Get all users
    all_users = User.objects.all()

    # Get users who scanned attendance on the given date
    attended_users = Attendance.objects.filter(date=date).values_list('user', flat=True)

    # Find absentees
    absentees = all_users.exclude(id__in=attended_users)

    # Create 'Absent' records for absentees
    for user in absentees:
        Attendance.objects.create(
            user=user,
            date=date,
            status='Absent',
        )
def is_weekday(date):
    return date.weekday() < 5  # 0 = Monday, 4 = Friday