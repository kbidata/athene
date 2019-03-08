import copy

from django.contrib import admin
from django.apps import apps
from django import forms
from django.http import HttpResponseRedirect
from django.urls import reverse

from . import models
from events.admin import SeekerCalendarSubscriptionAdmin

class SeekerMilestoneAdmin(admin.TabularInline):
    model = models.SeekerMilestone
    extra = 1
    classes = ["collapse"]
    

class HumanNoteAdmin(admin.StackedInline):
    model = models.HumanNote
    extra = 1
    template = 'admin/edit_inline/stacked_safe_display.html'
    fieldsets = (
        (None, {
            'fields': ('note',)
    }),)

    def has_change_permission(self, request, obj=None):
        return False

class HumanAdminMixin(object):

    def get_inline_instances(self, request, obj=None):
        inline_instances = super().get_inline_instances(request, obj)
        if not obj and '_popup' in request.GET: # this is an add
            return []
        return inline_instances

    def show_id(self, instance):
        return instance.id
    show_id.short_description = 'Identifier'
 
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)

        for instance in instances:
            if isinstance(instance, models.HumanNote):
                if not instance.id:
                    instance.added_by = request.user
            instance.save()

class HumanAdmin(HumanAdminMixin, admin.ModelAdmin):
    inlines = [HumanNoteAdmin,]
    model = models.Human

    def get_urls(self):
        from django.urls import path
        urlpatterns = super().get_urls()
        urlpatterns = [
            path('<path:object_id>/enroll/', 
                 self.admin_site.admin_view(self.enroll_seeker), 
                 name='seekers_human_enroll')
        ] + urlpatterns
        return urlpatterns

    def enroll_seeker(self, request, object_id):
        human = self.get_object(request, object_id)
        seeker = human.upgrade_to_seeker()
        self.message_user(request, f'{human} has been enrolled as a Seeker.')
        return HttpResponseRedirect(reverse('admin:seekers_seeker_change', args=(object_id,)))

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(seeker__isnull=True)

    fieldsets = (
        (None, {
            'fields': ['show_id', ('first_names', 'last_names'), 
                       ('city', 'state')],
        }),
        ('Contact information', {
            'fields': (('email', 'phone_number'), 'contact_preference')
        }), 
        ('Record history', {
            'fields': (('created', 'updated'),),
        }),
    )

    def _get_obj_does_not_exist_redirect(self, request, opts, object_id):
        try:
            seeker_obj = models.Seeker.objects.get(pk=object_id)
        except models.Seeker.DoesNotExist as e:
            return HttpResponseRedirect(
                reverse('admin:seekers_seeker_change', args=(object_id,))
            )
        else:
            return super()._get_obj_does_not_exist_redirect(request, opts, object_id)

    def get_fieldsets(self, request, obj=None):
        if obj is None and '_popup' in request.GET:
            shortened_fieldsets = copy.deepcopy(self.fieldsets[0:2])
            shortened_fieldsets[0][1]['fields'].remove('show_id')
            return shortened_fieldsets
        return super().get_fieldsets(request, obj)
    
    readonly_fields = ['show_id', 'created','updated']
    list_display = ['__str__', 'email', 'phone_number']
    search_fields = ['last_names', 'first_names', 'email', 'phone_number']

    def enroll_as_seeker(self, request, queryset):
        for obj in queryset:
            obj.upgrade_to_seeker()
        self.message_user(request, f'{len(queryset)} prospect(s) enrolled as Seekers.')
    enroll_as_seeker.short_description = 'Enroll as Seeker'

    actions = ['enroll_as_seeker']

class IsActiveFilter(admin.SimpleListFilter):
    title = 'Active'
    parameter_name = 'is_active'

    def lookups(self, request, model_admin):
        return (
            ('1', 'Yes'),
            ('0', 'No')
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'true':
            return queryset.filter(inactive_date__isnull=True)
        elif self.value() == 'false':
            return queryset.filter(inactive_date__isnull=False)
        else:
            return queryset

class IsPairedFilter(admin.SimpleListFilter):
    title = 'Paired'
    parameter_name = 'is_paired'

    def lookups(self, request, model_admin):
        

class SeekerAdmin(HumanAdminMixin, admin.ModelAdmin):
    inlines = [HumanNoteAdmin, SeekerMilestoneAdmin, 
               SeekerCalendarSubscriptionAdmin,]

    model = models.Seeker
    fieldsets = (
        (None, {
            'fields': ['show_id', ('first_names', 'last_names'), 
                       ('city', 'state'), 'seeker_pairs',
                       'listener_trained', 'extra_care', 'extra_care_graduate'],
        }),
        ('Contact information', {
            'fields': (('email', 'phone_number'), ('facebook_username',
                       'facebook_alias'), 'contact_preference')
        }),
        ('Service Opportunities', {
            'fields': (('ride_share', 'space_holder', 'activity_buddy', 'outreach'),),
        }),
        ('Important dates', {
            'fields': (('birthdate', 'sober_anniversary'),),
        }),
        ('Record history', {
            'fields': (('created', 'updated'), 'inactive_date'),
        }),
    )

    def get_fieldsets(self, request, obj=None):
        if obj is None and '_popup' in request.GET:
            shortened_fieldsets = copy.deepcopy(self.fieldsets[0:2])
            shortened_fieldsets[0][1]['fields'].remove('show_id')
            shortened_fieldsets[0][1]['fields'].remove('seeker_pair')
            return shortened_fieldsets
        return super().get_fieldsets(request, obj)

    readonly_fields = ['show_id', 'seeker_pairs', 'listener_trained', 
                       'extra_care', 'extra_care_graduate', 
                       'created', 'updated']
    list_display = ['__str__', 'email', 'phone_number', 'listener_trained', 'extra_care', 'extra_care_graduate', 'is_active']
    list_filter = ['listener_trained', 'extra_care', 'extra_care_graduate', IsActiveFilter,
                   'ride_share', 'space_holder', 'activity_buddy', 'outreach']
    search_fields = ['last_names', 'first_names', 'email', 'phone_number']

    def seeker_pairs(self, instance):
        return ', '.join(map(str, instance.seeker_pairs))

class SeekerPairingAdmin(admin.ModelAdmin):
    model = models.SeekerPairing
    list_display = ('left', 'right', 'pair_date', 'unpair_date')


admin.site.register(models.Human, HumanAdmin)
admin.site.register(models.Seeker, SeekerAdmin)
admin.site.register(models.SeekerPairing, SeekerPairingAdmin)