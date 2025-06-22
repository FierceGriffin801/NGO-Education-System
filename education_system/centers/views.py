from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Avg, Q, F
from .models import Center
from students.models import Student, Attendance
from datetime import date, timedelta

def center_list(request):
    centers = Center.objects.annotate(
        student_count=Count('student', filter=Q(student__is_active=True)),
        total_capacity=F('capacity')
    )
    
    context = {
        'centers': centers,
    }
    return render(request, 'centers/center_list.html', context)

def center_detail(request, center_id):
    center = get_object_or_404(Center, id=center_id)
    
    # Get students in this center
    students = Student.objects.filter(center=center, is_active=True)
    
    # Calculate center statistics
    total_students = students.count()
    capacity_utilization = (total_students / center.capacity * 100) if center.capacity > 0 else 0
    
    # Get attendance statistics for last 30 days
    thirty_days_ago = date.today() - timedelta(days=30)
    center_attendance = Attendance.objects.filter(
        student__center=center,
        date__gte=thirty_days_ago
    )
    
    total_attendance_records = center_attendance.count()
    present_records = center_attendance.filter(is_present=True).count()
    attendance_rate = (present_records / total_attendance_records * 100) if total_attendance_records > 0 else 0
    
    context = {
        'center': center,
        'students': students[:10],  # Show first 10 students
        'total_students': total_students,
        'capacity_utilization': round(capacity_utilization, 1),
        'attendance_rate': round(attendance_rate, 1),
    }
    return render(request, 'centers/center_detail.html', context)
