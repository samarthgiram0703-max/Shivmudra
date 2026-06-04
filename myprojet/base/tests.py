from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Event
import datetime

class MarkAsPaidTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.client = Client()
        self.client.login(username='testuser', password='password123')
        
        self.event = Event.objects.create(
            user=self.user,
            name="Test Event",
            scheduled_date=timezone.now(),
            location="Test Location",
            advanced_rs=5000.00,
            pending_rs=3000.00,
            status='PENDING'
        )

    def test_event_total_rs_auto_calculation(self):
        """Verify that total_rs is automatically calculated as advanced + pending on save."""
        self.assertEqual(self.event.total_rs, 8000.00)

    def test_mark_as_paid_view(self):
        """Verify that mark_as_paid view updates payment details and leaves status unchanged."""
        url = reverse('event_mark_paid', kwargs={'pk': self.event.pk})
        response = self.client.post(url)
        
        # Verify redirect
        self.assertEqual(response.status_code, 302)
        
        # Reload event from db
        self.event.refresh_from_db()
        
        self.assertEqual(self.event.advanced_rs, 8000.00)
        self.assertEqual(self.event.pending_rs, 0.00)
        self.assertEqual(self.event.total_rs, 8000.00)
        self.assertEqual(self.event.status, 'PENDING')

class EventFormTestCase(TestCase):
    def test_form_validation_and_datetime_merge_pm(self):
        """Verify that EventForm correctly merges date and time in PM."""
        from .forms import EventForm
        
        form_data = {
            'name': 'Wedding Ceremony',
            'location': 'Mumbai',
            'mobile_no': '9876543210',
            'advanced_rs': 15000.00,
            'pending_rs': 5000.00,
            'status': 'PENDING',
            'scheduled_date_only': '2026-06-15',
            'scheduled_hour': '06',
            'scheduled_minute': '30',
            'scheduled_ampm': 'PM'
        }
        
        form = EventForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        event = form.save(commit=False)
        self.assertIsNotNone(event.scheduled_date)
        self.assertEqual(event.scheduled_date.date(), datetime.date(2026, 6, 15))
        self.assertEqual(event.scheduled_date.time(), datetime.time(18, 30))
        self.assertEqual(event.mobile_no, '9876543210')

    def test_form_validation_and_datetime_merge_am(self):
        """Verify that EventForm correctly merges date and time in AM."""
        from .forms import EventForm
        
        form_data = {
            'name': 'Morning Puja',
            'location': 'Pune',
            'advanced_rs': 5000.00,
            'pending_rs': 0.00,
            'status': 'PENDING',
            'scheduled_date_only': '2026-06-15',
            'scheduled_hour': '06',
            'scheduled_minute': '30',
            'scheduled_ampm': 'AM'
        }
        
        form = EventForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        event = form.save(commit=False)
        self.assertIsNotNone(event.scheduled_date)
        self.assertEqual(event.scheduled_date.date(), datetime.date(2026, 6, 15))
        self.assertEqual(event.scheduled_date.time(), datetime.time(6, 30))

    def test_form_validation_missing_fields(self):
        """Verify that EventForm fails validation if hour, minute, or AM/PM is missing."""
        from .forms import EventForm
        
        form_data = {
            'name': 'Wedding Ceremony',
            'location': 'Mumbai',
            'advanced_rs': 15000.00,
            'pending_rs': 5000.00,
            'status': 'PENDING',
            'scheduled_date_only': '2026-06-15',
            'scheduled_hour': '06',
            'scheduled_minute': '30',
            # missing scheduled_ampm
        }
        
        form = EventForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('scheduled_ampm', form.errors)

class AllEventsViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.client = Client()
        self.client.login(username='testuser', password='password123')
        
        # Create some events with different properties
        self.event1 = Event.objects.create(
            user=self.user,
            name="Mumbai Sangeet",
            scheduled_date=timezone.make_aware(datetime.datetime(2026, 6, 15, 18, 0)),
            location="Mumbai",
            advanced_rs=10000.00,
            pending_rs=5000.00,
            status='PENDING'
        )
        self.event2 = Event.objects.create(
            user=self.user,
            name="Pune Wedding",
            scheduled_date=timezone.make_aware(datetime.datetime(2026, 6, 20, 10, 0)),
            location="Pune",
            advanced_rs=25000.00,
            pending_rs=0.00,
            status='COMPLETED'
        )

    def test_all_events_view_status_code(self):
        """Verify that all_events page loads successfully."""
        url = reverse('all_events')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'base/all_events.html')
        self.assertEqual(len(response.context['events']), 2)

    def test_all_events_view_search(self):
        """Verify search query filters events by name or location."""
        url = reverse('all_events')
        # Search for Pune
        response = self.client.get(url, {'search': 'Pune'})
        self.assertEqual(len(response.context['events']), 1)
        self.assertEqual(response.context['events'][0].name, "Pune Wedding")

    def test_all_events_view_status_filter(self):
        """Verify status query filters events by their status."""
        url = reverse('all_events')
        # Filter by COMPLETED
        response = self.client.get(url, {'status': 'COMPLETED'})
        self.assertEqual(len(response.context['events']), 1)
        self.assertEqual(response.context['events'][0].name, "Pune Wedding")

    def test_all_events_paid_status_rendering(self):
        """Verify that the Paid/Unpaid badges render correctly in the events list."""
        url = reverse('all_events')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        # Check that table header exists
        self.assertContains(response, '<th>Total Paid Status</th>')
        
        # event1 has pending_rs=5000.00, should render "Unpaid" as a clickable button
        self.assertContains(response, 'btn-badge-clickable')
        self.assertContains(response, 'badge-unpaid')
        self.assertContains(response, 'Unpaid')
        
        # event2 has pending_rs=0.00, should render "Paid" as a static span
        self.assertContains(response, 'badge-paid')
        self.assertContains(response, 'Paid')

    def test_event_update_status_view(self):
        """Verify that the event_update_status view updates the status successfully."""
        url = reverse('event_update_status', kwargs={'pk': self.event1.pk})
        response = self.client.post(url, {'status': 'COMPLETED'})
        
        # Verify redirect
        self.assertEqual(response.status_code, 302)
        
        # Reload event
        self.event1.refresh_from_db()
        self.assertEqual(self.event1.status, 'COMPLETED')
        
        # Update to CANCELLED
        response = self.client.post(url, {'status': 'CANCELLED'})
        self.event1.refresh_from_db()
        self.assertEqual(self.event1.status, 'CANCELLED')


class AutoUpdateOnEditTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        
        self.event = Event.objects.create(
            user=self.user,
            name="Mumbai Event",
            scheduled_date=timezone.now(),
            location="Mumbai",
            advanced_rs=6000.00,
            pending_rs=4000.00,
            status='PENDING'
        )

    def test_auto_update_on_pending_zero(self):
        """Verify that saving an event with pending_rs=0 auto-updates advanced_rs but leaves status unchanged."""
        self.event.pending_rs = 0
        self.event.save()
        
        self.assertEqual(self.event.advanced_rs, 10000.00)
        self.assertEqual(self.event.pending_rs, 0.00)
        self.assertEqual(self.event.total_rs, 10000.00)
        self.assertEqual(self.event.status, 'PENDING')

    def test_allow_completed_status_with_pending_money(self):
        """Verify that setting status to COMPLETED manually is allowed even if pending_rs > 0."""
        self.event.status = 'COMPLETED'
        self.event.save()
        
        self.assertEqual(self.event.status, 'COMPLETED')
        self.assertEqual(self.event.pending_rs, 4000.00)
        self.assertEqual(self.event.advanced_rs, 6000.00)
        self.assertEqual(self.event.total_rs, 10000.00)



