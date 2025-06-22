from django.shortcuts import render
from django.db.models import Count, Q
from students.models import Student, Attendance
from centers.models import Center
from datetime import date, timedelta

def dashboard(request):
    # Get statistics
    total_students = Student.objects.filter(is_active=True).count()
    total_centers = Center.objects.filter(is_active=True).count()
    
    # Calculate attendance rate for last 30 days
    thirty_days_ago = date.today() - timedelta(days=30)
    recent_attendance = Attendance.objects.filter(date__gte=thirty_days_ago)
    total_attendance_records = recent_attendance.count()
    present_records = recent_attendance.filter(is_present=True).count()
    attendance_rate = (present_records / total_attendance_records * 100) if total_attendance_records > 0 else 0
    
    # Get centers with student counts
    centers_with_counts = Center.objects.annotate(
        student_count=Count('student', filter=Q(student__is_active=True))
    ).filter(is_active=True)
    
    context = {
        'total_students': total_students,
        'total_centers': total_centers,
        'attendance_rate': round(attendance_rate, 1),
        'centers_with_counts': centers_with_counts,
    }
    return render(request, 'dashboard.html', context)
