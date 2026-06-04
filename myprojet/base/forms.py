from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Event
from django.utils import timezone
import datetime

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'})
    )
    first_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply form-control CSS classes to help with styling
        for field_name, field in self.fields.items():
            if field_name not in ['email', 'first_name', 'last_name']:
                field.widget.attrs['class'] = 'form-control'
                field.widget.attrs['placeholder'] = field.label

class EventForm(forms.ModelForm):
    scheduled_date_only = forms.DateField(
        label="Scheduled Date",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        required=True
    )
    scheduled_hour = forms.ChoiceField(
        label="Hour",
        choices=[(f"{i:02d}", f"{i:02d}") for i in range(1, 13)],
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )
    scheduled_minute = forms.ChoiceField(
        label="Minute",
        choices=[(f"{i:02d}", f"{i:02d}") for i in range(60)],
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )
    scheduled_ampm = forms.ChoiceField(
        label="AM/PM",
        choices=[('AM', 'AM'), ('PM', 'PM')],
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )

    class Meta:
        model = Event
        fields = ['name', 'location', 'mobile_no', 'advanced_rs', 'pending_rs', 'status']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter event name'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter event location'}),
            'mobile_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter mobile number'}),
            'advanced_rs': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'min': '0', 'step': '0.01'}),
            'pending_rs': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'min': '0', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            if self.instance.scheduled_date:
                # Convert scheduled_date to local time and extract date and time components
                local_dt = timezone.localtime(self.instance.scheduled_date)
                self.fields['scheduled_date_only'].initial = local_dt.date()
                
                # Convert 24h to 12h format
                hour_24 = local_dt.hour
                ampm = 'PM' if hour_24 >= 12 else 'AM'
                hour_12 = hour_24 % 12
                if hour_12 == 0:
                    hour_12 = 12
                    
                self.fields['scheduled_hour'].initial = f"{hour_12:02d}"
                self.fields['scheduled_minute'].initial = f"{local_dt.minute:02d}"
                self.fields['scheduled_ampm'].initial = ampm
        else:
            # Clear default 0.00 values for new events to show empty fields with placeholders
            self.fields['advanced_rs'].initial = None
            self.fields['pending_rs'].initial = None

    def clean(self):
        cleaned_data = super().clean()
        date_only = cleaned_data.get('scheduled_date_only')
        hour = cleaned_data.get('scheduled_hour')
        minute = cleaned_data.get('scheduled_minute')
        ampm = cleaned_data.get('scheduled_ampm')

        if date_only and hour and minute and ampm:
            h = int(hour)
            m = int(minute)
            
            # Convert 12h to 24h format
            if ampm == 'PM' and h < 12:
                h += 12
            elif ampm == 'AM' and h == 12:
                h = 0
                
            time_obj = datetime.time(h, m)
            combined_naive = datetime.datetime.combine(date_only, time_obj)
            # Make timezone aware using current system timezone
            combined_aware = timezone.make_aware(combined_naive, timezone.get_current_timezone())
            self.instance.scheduled_date = combined_aware
        else:
            self.add_error('scheduled_date_only', 'Complete scheduled date and time selection are required.')

        advanced = cleaned_data.get('advanced_rs') or 0
        pending = cleaned_data.get('pending_rs') or 0
        if advanced < 0 or pending < 0:
            raise forms.ValidationError("Amounts cannot be negative.")
        return cleaned_data
