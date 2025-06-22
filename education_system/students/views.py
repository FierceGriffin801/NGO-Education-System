from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q, Avg
from django.core.paginator import Paginator
from .models import Student, Attendance, Grade
from .forms import StudentForm, AttendanceForm
from datetime import date, timedelta
from centers.models import Center

def student_list(request):
    students = Student.objects.filter(is_active=True).select_related('center')
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        students = students.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(student_id__icontains=search_query)
        )
    
    # Filter by center
    center_filter = request.GET.get('center')
    if center_filter:
        students = students.filter(center_id=center_filter)
    
    # Pagination
    paginator = Paginator(students, 20)
    page_number = request.GET.get('page')
    students = paginator.get_page(page_number)
    
    # Get centers for filter dropdown
    from centers.models import Center
    centers = Center.objects.filter(is_active=True)
    
    context = {
        'students': students,
        'centers': centers,
        'search_query': search_query,
        'center_filter': center_filter,
    }
    return render(request, 'students/student_list.html', context)

def student_detail(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    today = date.today()
    dob = student.date_of_birth
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    
    # Get recent attendance (last 30 days)
    thirty_days_ago = date.today() - timedelta(days=30)
    recent_attendance = Attendance.objects.filter(
        student=student,
        date__gte=thirty_days_ago
    ).order_by('-date')
    
    # Calculate attendance percentage
    total_days = recent_attendance.count()
    present_days = recent_attendance.filter(is_present=True).count()
    attendance_percentage = (present_days / total_days * 100) if total_days > 0 else 0
    
    # Get recent grades
    recent_grades = Grade.objects.filter(student=student).select_related('subject').order_by('-assessment_date')[:10]
    
    # Calculate average performance
    avg_percentage = Grade.objects.filter(student=student).aggregate(
        avg_percentage=Avg('marks_obtained') * 100 / Avg('total_marks')
    )['avg_percentage'] or 0
    
    context = {
        'student': student,
        'age': age,
        'recent_attendance': recent_attendance[:10],
        'attendance_percentage': round(attendance_percentage, 1),
        'recent_grades': recent_grades,
        'avg_percentage': round(avg_percentage, 1),
    }
    return render(request, 'students/student_detail.html', context)

def add_student(request):
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Student added successfully!')
            return redirect('student_list')
    else:
        form = StudentForm()
    
    return render(request, 'students/add_student.html', {'form': form})

def mark_attendance(request):
    selected_date = date.today()
    selected_center = None
    
    # Handle GET parameters for filtering
    if request.GET.get('date'):
        try:
            selected_date = date.fromisoformat(request.GET.get('date'))
        except ValueError:
            selected_date = date.today()
    
    if request.GET.get('center'):
        selected_center = request.GET.get('center')
    
    # Get students based on filters
    students = Student.objects.filter(is_active=True).select_related('center')
    if selected_center:
        students = students.filter(center_id=selected_center)
    
    # Get today's attendance
    today_attendance = Attendance.objects.filter(
        date=selected_date
    ).select_related('student')
    
    if selected_center:
        today_attendance = today_attendance.filter(student__center_id=selected_center)
    
    # Handle POST request for marking attendance
    if request.method == 'POST':
        attendance_date = request.POST.get('attendance_date')
        if attendance_date:
            attendance_date = date.fromisoformat(attendance_date)
        else:
            attendance_date = selected_date
        
        success_count = 0
        error_count = 0
        
        for student in students:
            attendance_status = request.POST.get(f'student_{student.id}')
            remarks = request.POST.get(f'remarks_{student.id}', '')
            
            if attendance_status:
                is_present = attendance_status == 'present'
                
                # Create or update attendance record
                attendance, created = Attendance.objects.update_or_create(
                    student=student,
                    date=attendance_date,
                    defaults={
                        'is_present': is_present,
                        'remarks': remarks
                    }
                )
                
                if created or attendance:
                    success_count += 1
                else:
                    error_count += 1
        
        if success_count > 0:
            messages.success(
                request, 
                f'✅ Successfully marked attendance for {success_count} students!'
            )
        
        if error_count > 0:
            messages.error(
                request, 
                f'❌ Failed to mark attendance for {error_count} students.'
            )
        
        return redirect('mark_attendance')
    
    # Get all centers for filter dropdown
    centers = Center.objects.filter(is_active=True)
    
    context = {
        'students': students,
        'centers': centers,
        'today_attendance': today_attendance,
        'selected_date': selected_date,
        'selected_center': selected_center,
    }
    return render(request, 'students/mark_attendance.html', context)

def add_student(request):
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            try:
                student = form.save()
                messages.success(
                    request, 
                    f'🎉 Student {student.first_name} {student.last_name} has been successfully registered!'
                )
                return redirect('student_detail', student_id=student.id)
            except Exception as e:
                messages.error(
                    request, 
                    f'❌ Error registering student: {str(e)}'
                )
        else:
            messages.error(
                request, 
                '❌ Please correct the errors below and try again.'
            )
    else:
        form = StudentForm()
    
    return render(request, 'students/add_student.html', {'form': form})

from .forms import GradeForm
from .models import Grade, Subject

def add_grade(request):
    if request.method == 'POST':
        form = GradeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Grade entry saved successfully!")
            return redirect('grade_list')
    else:
        form = GradeForm()
    return render(request, 'students/add_grade.html', {'form': form})

def grade_list(request):
    grades = Grade.objects.select_related('student', 'subject').order_by('-assessment_date')
    # Optional: implement filtering by student, subject, or date
    return render(request, 'students/grade_list.html', {'grades': grades})
