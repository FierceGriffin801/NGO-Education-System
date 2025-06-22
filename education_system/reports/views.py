from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Count, Avg, Q
from django.db import models
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from datetime import date, timedelta
import json
import csv
from io import StringIO

# ReportLab imports
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from django.core.files.base import ContentFile
import io

from students.models import Student, Attendance, Grade
from centers.models import Center, Subject
from .models import Report, ReportSchedule
from .forms import ReportGenerationForm, ReportScheduleForm

def reports_dashboard(request):
    """Main reports dashboard view"""
    # Get recent reports
    recent_reports = Report.objects.all().order_by('-created_at')[:5]
    if request.user.is_authenticated:
        recent_reports = Report.objects.filter(generated_by=request.user).order_by('-created_at')[:5]
    
    # Get scheduled reports
    scheduled_reports = ReportSchedule.objects.filter(is_active=True)[:5]
    
    # Basic statistics for reports
    total_students = Student.objects.filter(is_active=True).count()
    total_centers = Center.objects.filter(is_active=True).count()
    
    # Calculate attendance rate for last 30 days
    thirty_days_ago = date.today() - timedelta(days=30)
    recent_attendance = Attendance.objects.filter(date__gte=thirty_days_ago)
    total_attendance_records = recent_attendance.count()
    present_records = recent_attendance.filter(is_present=True).count()
    attendance_rate = (present_records / total_attendance_records * 100) if total_attendance_records > 0 else 0
    
    # Get report statistics
    total_reports = Report.objects.count()
    completed_reports = Report.objects.filter(status='completed').count()
    
    context = {
        'recent_reports': recent_reports,
        'scheduled_reports': scheduled_reports,
        'total_students': total_students,
        'total_centers': total_centers,
        'attendance_rate': round(attendance_rate, 1),
        'total_reports': total_reports,
        'completed_reports': completed_reports,
    }
    return render(request, 'reports/dashboard.html', context)

def generate_report(request):
    """Generate a new report"""
    if request.method == 'POST':
        form = ReportGenerationForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            if request.user.is_authenticated:
                report.generated_by = request.user
            else:
                # Create a default user if not authenticated (for testing)
                from django.contrib.auth.models import User
                default_user, created = User.objects.get_or_create(
                    username='system',
                    defaults={'email': 'system@example.com'}
                )
                report.generated_by = default_user
            
            report.status = 'generating'
            report.save()
            form.save_m2m()  # Save many-to-many relationships
            
            # Generate the actual report
            try:
                generate_report_file(report)
                messages.success(request, f'✅ Report "{report.title}" generated successfully!')
                return redirect('report_detail', report_id=report.id)
            except Exception as e:
                report.status = 'failed'
                report.save()
                messages.error(request, f'❌ Error generating report: {str(e)}')
        else:
            messages.error(request, '❌ Please correct the errors below.')
    else:
        form = ReportGenerationForm()
    
    return render(request, 'reports/generate_report.html', {'form': form})

def report_list(request):
    """List all reports with filtering"""
    reports = Report.objects.all().order_by('-created_at')
    if request.user.is_authenticated:
        reports = reports.filter(generated_by=request.user)
    
    # Filter by report type
    report_type = request.GET.get('type')
    if report_type:
        reports = reports.filter(report_type=report_type)
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        reports = reports.filter(status=status)
    
    context = {
        'reports': reports,
        'report_types': Report.REPORT_TYPES,
        'status_choices': Report.STATUS_CHOICES,
        'selected_type': report_type,
        'selected_status': status,
    }
    return render(request, 'reports/report_list.html', context)

def report_detail(request, report_id):
    """View detailed report information"""
    report = get_object_or_404(Report, id=report_id)
    
    # Generate report data based on type
    report_data = get_report_data(report)
    
    context = {
        'report': report,
        'report_data': report_data,
    }
    return render(request, 'reports/report_detail.html', context)

def download_report(request, report_id):
    """Download report PDF file"""
    report = get_object_or_404(Report, id=report_id)
    
    if report.file_path and report.file_path.name:
        try:
            # Check if file exists
            if report.file_path.storage.exists(report.file_path.name):
                response = HttpResponse(
                    report.file_path.read(), 
                    content_type='application/pdf'
                )
                response['Content-Disposition'] = f'attachment; filename="{report.title}.pdf"'
                return response
            else:
                messages.error(request, '❌ Report file not found on storage.')
        except Exception as e:
            messages.error(request, f'❌ Error accessing report file: {str(e)}')
    else:
        messages.error(request, '❌ No report file available for download.')
    
    return redirect('report_detail', report_id=report_id)

def generate_report_file(report):
    """Generate the actual report file based on report type"""
    try:
        if report.report_type == 'attendance':
            generate_attendance_report(report)
        elif report.report_type == 'academic':
            generate_academic_report(report)
        elif report.report_type == 'center':
            generate_center_report(report)
        elif report.report_type == 'financial':
            generate_financial_report(report)
        elif report.report_type == 'donor':
            generate_donor_report(report)
        elif report.report_type == 'risk':
            generate_risk_report(report)
        else:
            generate_default_report(report)
        
        report.status = 'completed'
        report.save()
    except Exception as e:
        report.status = 'failed'
        report.save()
        print(f"Error generating report: {str(e)}")  # For debugging
        raise e

def generate_attendance_report(report):
    """Generate attendance report as PDF"""
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Title
    p.setFont("Helvetica-Bold", 20)
    p.drawString(50, height - 50, f"Attendance Report")
    
    # Subtitle
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 80, f"{report.title}")
    
    # Date range
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 110, f"Period: {report.date_from.strftime('%B %d, %Y')} to {report.date_to.strftime('%B %d, %Y')}")
    p.drawString(50, height - 130, f"Generated on: {timezone.now().strftime('%B %d, %Y at %I:%M %p')}")
    
    # Get attendance data
    attendance_data = Attendance.objects.filter(
        date__range=[report.date_from, report.date_to]
    )
    
    if report.centers.exists():
        attendance_data = attendance_data.filter(student__center__in=report.centers.all())
        center_names = ", ".join([center.name for center in report.centers.all()])
        p.drawString(50, height - 150, f"Centers: {center_names}")
    
    # Summary statistics
    total_records = attendance_data.count()
    present_records = attendance_data.filter(is_present=True).count()
    absent_records = total_records - present_records
    attendance_rate = (present_records / total_records * 100) if total_records > 0 else 0
    
    # Draw summary box
    y_position = height - 200
    p.rect(50, y_position - 80, 500, 80)
    
    p.setFont("Helvetica-Bold", 14)
    p.drawString(60, y_position - 20, "SUMMARY STATISTICS")
    
    p.setFont("Helvetica", 12)
    p.drawString(60, y_position - 40, f"Total Attendance Records: {total_records}")
    p.drawString(300, y_position - 40, f"Present: {present_records}")
    p.drawString(60, y_position - 60, f"Absent: {absent_records}")
    p.drawString(300, y_position - 60, f"Attendance Rate: {attendance_rate:.1f}%")
    
    # Detailed data
    y_position -= 120
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y_position, "DETAILED ATTENDANCE DATA")
    
    y_position -= 30
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, y_position, "Student Name")
    p.drawString(200, y_position, "Center")
    p.drawString(350, y_position, "Date")
    p.drawString(450, y_position, "Status")
    
    # Draw line
    p.line(50, y_position - 5, 550, y_position - 5)
    y_position -= 20
    
    p.setFont("Helvetica", 9)
    
    # List attendance records
    for attendance in attendance_data.select_related('student', 'student__center')[:30]:  # Limit to first 30
        if y_position < 100:  # Start new page if needed
            p.showPage()
            y_position = height - 50
            p.setFont("Helvetica", 9)
        
        student_name = f"{attendance.student.first_name} {attendance.student.last_name}"
        center_name = attendance.student.center.name[:15]  # Truncate if too long
        date_str = attendance.date.strftime('%m/%d/%Y')
        status = "Present" if attendance.is_present else "Absent"
        
        p.drawString(50, y_position, student_name[:20])
        p.drawString(200, y_position, center_name)
        p.drawString(350, y_position, date_str)
        p.drawString(450, y_position, status)
        
        y_position -= 15
    
    if attendance_data.count() > 30:
        y_position -= 20
        p.drawString(50, y_position, f"... and {attendance_data.count() - 30} more records")
    
    p.save()
    buffer.seek(0)
    
    # Save the PDF file
    report.file_path.save(
        f"attendance_report_{report.id}.pdf",
        ContentFile(buffer.read()),
        save=True
    )

def generate_academic_report(report):
    """Generate academic performance report as PDF"""
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Title
    p.setFont("Helvetica-Bold", 20)
    p.drawString(50, height - 50, f"Academic Performance Report")
    
    # Subtitle
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 80, f"{report.title}")
    
    # Date range
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 110, f"Period: {report.date_from.strftime('%B %d, %Y')} to {report.date_to.strftime('%B %d, %Y')}")
    p.drawString(50, height - 130, f"Generated on: {timezone.now().strftime('%B %d, %Y at %I:%M %p')}")
    
    # Get grade data
    grades = Grade.objects.filter(
        assessment_date__range=[report.date_from, report.date_to]
    ).select_related('student', 'subject', 'student__center')
    
    if report.centers.exists():
        grades = grades.filter(student__center__in=report.centers.all())
        center_names = ", ".join([center.name for center in report.centers.all()])
        p.drawString(50, height - 150, f"Centers: {center_names}")
    
    # Summary statistics
    total_assessments = grades.count()
    if total_assessments > 0:
        avg_marks = grades.aggregate(
            avg_obtained=models.Avg('marks_obtained'),
            avg_total=models.Avg('total_marks')
        )
        avg_percentage = (avg_marks['avg_obtained'] / avg_marks['avg_total'] * 100) if avg_marks['avg_total'] else 0
        
        # Grade distribution
        grade_dist = grades.values('grade_letter').annotate(count=Count('id')).order_by('grade_letter')
    else:
        avg_percentage = 0
        grade_dist = []
    
    # Draw summary box
    y_position = height - 200
    p.rect(50, y_position - 100, 500, 100)
    
    p.setFont("Helvetica-Bold", 14)
    p.drawString(60, y_position - 20, "ACADEMIC PERFORMANCE SUMMARY")
    
    p.setFont("Helvetica", 12)
    p.drawString(60, y_position - 40, f"Total Assessments: {total_assessments}")
    p.drawString(300, y_position - 40, f"Average Score: {avg_percentage:.1f}%")
    
    # Grade distribution
    if grade_dist:
        p.drawString(60, y_position - 60, "Grade Distribution:")
        x_pos = 60
        for grade in grade_dist:
            p.drawString(x_pos, y_position - 80, f"{grade['grade_letter']}: {grade['count']}")
            x_pos += 80
    
    p.save()
    buffer.seek(0)
    
    # Save the PDF file
    report.file_path.save(
        f"academic_report_{report.id}.pdf",
        ContentFile(buffer.read()),
        save=True
    )

def generate_center_report(report):
    """Generate center performance report as PDF"""
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Title
    p.setFont("Helvetica-Bold", 20)
    p.drawString(50, height - 50, f"Center Performance Report")
    
    # Subtitle
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 80, f"{report.title}")
    
    # Date range
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 110, f"Period: {report.date_from.strftime('%B %d, %Y')} to {report.date_to.strftime('%B %d, %Y')}")
    p.drawString(50, height - 130, f"Generated on: {timezone.now().strftime('%B %d, %Y at %I:%M %p')}")
    
    # Get center data
    centers_query = Center.objects.filter(is_active=True)
    if report.centers.exists():
        centers_query = report.centers.all()
    
    # Get students per center with attendance data
    centers_with_stats = centers_query.annotate(
        total_students=models.Count('student', filter=models.Q(student__is_active=True)),
        total_attendance=models.Count(
            'student__attendance',
            filter=models.Q(
                student__attendance__date__range=[report.date_from, report.date_to]
            )
        ),
        present_attendance=models.Count(
            'student__attendance',
            filter=models.Q(
                student__attendance__date__range=[report.date_from, report.date_to],
                student__attendance__is_present=True
            )
        )
    )
    
    y_position = height - 180
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y_position, "CENTER PERFORMANCE SUMMARY")
    y_position -= 30
    
    # Headers
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, y_position, "Center Name")
    p.drawString(180, y_position, "Location")
    p.drawString(320, y_position, "Students")
    p.drawString(380, y_position, "Capacity")
    p.drawString(440, y_position, "Utilization")
    p.drawString(500, y_position, "Attendance")
    
    # Draw line
    p.line(50, y_position - 5, 580, y_position - 5)
    y_position -= 20
    
    p.setFont("Helvetica", 9)
    
    total_students_all = 0
    total_capacity_all = 0
    
    for center in centers_with_stats:
        if y_position < 100:  # Start new page if needed
            p.showPage()
            y_position = height - 50
            p.setFont("Helvetica", 9)
        
        utilization = (center.total_students / center.capacity * 100) if center.capacity > 0 else 0
        attendance_rate = (center.present_attendance / center.total_attendance * 100) if center.total_attendance > 0 else 0
        
        # Center data
        p.drawString(50, y_position, center.name[:18])  # Truncate long names
        p.drawString(180, y_position, center.location[:18])
        p.drawString(320, y_position, str(center.total_students))
        p.drawString(380, y_position, str(center.capacity))
        p.drawString(440, y_position, f"{utilization:.1f}%")
        p.drawString(500, y_position, f"{attendance_rate:.1f}%")
        
        total_students_all += center.total_students
        total_capacity_all += center.capacity
        
        y_position -= 15
    
    # Summary statistics
    y_position -= 20
    p.line(50, y_position, 580, y_position)
    y_position -= 20
    
    overall_utilization = (total_students_all / total_capacity_all * 100) if total_capacity_all > 0 else 0
    
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y_position, f"TOTALS:")
    y_position -= 20
    p.setFont("Helvetica", 11)
    p.drawString(50, y_position, f"Total Centers: {centers_with_stats.count()}")
    p.drawString(200, y_position, f"Total Students: {total_students_all}")
    y_position -= 15
    p.drawString(50, y_position, f"Total Capacity: {total_capacity_all}")
    p.drawString(200, y_position, f"Overall Utilization: {overall_utilization:.1f}%")
    
    p.save()
    buffer.seek(0)
    
    # Save the PDF file
    report.file_path.save(
        f"center_report_{report.id}.pdf",
        ContentFile(buffer.read()),
        save=True
    )

def generate_financial_report(report):
    """Generate financial report as PDF"""
    generate_default_report(report, "Financial Report", "Financial data and budget analysis will be implemented here.")

def generate_donor_report(report):
    """Generate donor impact report as PDF"""
    generate_default_report(report, "Donor Impact Report", "Donor impact metrics and success stories will be implemented here.")

def generate_risk_report(report):
    """Generate risk assessment report as PDF"""
    generate_default_report(report, "Risk Assessment Report", "Risk factors and intervention strategies will be implemented here.")

def generate_default_report(report, title=None, description=None):
    """Generate a default report when specific type is not implemented"""
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Title
    p.setFont("Helvetica-Bold", 20)
    p.drawString(50, height - 50, title or f"Report: {report.title}")
    
    # Content
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 100, f"Report Type: {report.get_report_type_display()}")
    p.drawString(50, height - 120, f"Period: {report.date_from.strftime('%B %d, %Y')} to {report.date_to.strftime('%B %d, %Y')}")
    p.drawString(50, height - 140, f"Generated on: {timezone.now().strftime('%B %d, %Y at %I:%M %p')}")
    
    p.drawString(50, height - 180, description or "This report type is currently under development.")
    p.drawString(50, height - 200, "More detailed analytics will be available in future updates.")
    
    p.save()
    buffer.seek(0)
    
    # Save the PDF file
    report.file_path.save(
        f"{report.report_type}_report_{report.id}.pdf",
        ContentFile(buffer.read()),
        save=True
    )

def get_report_data(report):
    """Get data for displaying in report detail view"""
    data = {}
    
    if report.report_type == 'attendance':
        attendance_data = Attendance.objects.filter(
            date__range=[report.date_from, report.date_to]
        )
        
        if report.centers.exists():
            attendance_data = attendance_data.filter(student__center__in=report.centers.all())
        
        total_records = attendance_data.count()
        present_records = attendance_data.filter(is_present=True).count()
        
        data = {
            'total_records': total_records,
            'present_records': present_records,
            'absent_records': total_records - present_records,
            'attendance_rate': (present_records / total_records * 100) if total_records > 0 else 0,
        }
    
    elif report.report_type == 'academic':
        grades = Grade.objects.filter(
            assessment_date__range=[report.date_from, report.date_to]
        )
        
        if report.centers.exists():
            grades = grades.filter(student__center__in=report.centers.all())
        
        total_assessments = grades.count()
        if total_assessments > 0:
            avg_marks = grades.aggregate(
                avg_obtained=models.Avg('marks_obtained'),
                avg_total=models.Avg('total_marks')
            )
            avg_percentage = (avg_marks['avg_obtained'] / avg_marks['avg_total'] * 100) if avg_marks['avg_total'] else 0
        else:
            avg_percentage = 0
        
        data = {
            'total_assessments': total_assessments,
            'average_percentage': round(avg_percentage, 1),
            'grade_distribution': grades.values('grade_letter').annotate(count=Count('id')),
        }
    
    elif report.report_type == 'center':
        centers_query = Center.objects.filter(is_active=True)
        if report.centers.exists():
            centers_query = report.centers.all()
        
        centers_with_stats = centers_query.annotate(
            total_students=models.Count('student', filter=models.Q(student__is_active=True))
        )
        
        total_centers = centers_with_stats.count()
        total_students = sum(center.total_students for center in centers_with_stats)
        total_capacity = sum(center.capacity for center in centers_with_stats)
        overall_utilization = (total_students / total_capacity * 100) if total_capacity > 0 else 0
        
        data = {
            'total_centers': total_centers,
            'total_students': total_students,
            'total_capacity': total_capacity,
            'overall_utilization': round(overall_utilization, 1),
            'centers_data': centers_with_stats,
        }
    
    return data

# Schedule Reports (Future Enhancement)
def schedule_report(request):
    """Schedule automatic report generation"""
    if request.method == 'POST':
        form = ReportScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            if request.user.is_authenticated:
                schedule.created_by = request.user
            schedule.save()
            form.save_m2m()
            messages.success(request, f'✅ Report schedule "{schedule.name}" created successfully!')
            return redirect('reports')
    else:
        form = ReportScheduleForm()
    
    return render(request, 'reports/schedule_report.html', {'form': form})

def export_report_csv(request, report_id):
    """Export report data as CSV"""
    report = get_object_or_404(Report, id=report_id)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{report.title}.csv"'
    
    writer = csv.writer(response)
    
    if report.report_type == 'attendance':
        writer.writerow(['Student Name', 'Center', 'Date', 'Status', 'Remarks'])
        
        attendance_data = Attendance.objects.filter(
            date__range=[report.date_from, report.date_to]
        ).select_related('student', 'student__center')
        
        if report.centers.exists():
            attendance_data = attendance_data.filter(student__center__in=report.centers.all())
        
        for attendance in attendance_data:
            writer.writerow([
                f"{attendance.student.first_name} {attendance.student.last_name}",
                attendance.student.center.name,
                attendance.date.strftime('%Y-%m-%d'),
                'Present' if attendance.is_present else 'Absent',
                attendance.remarks or ''
            ])
    
    return response

