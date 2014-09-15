from django.core.management.base import BaseCommand, CommandError
from vote3fe.models import AuditEntry
from annoying.functions import get_object_or_None
from django.template.loader import render_to_string

class Command(BaseCommand):
    help = 'Begins the audit trail'

    requires_system_checks = True
    
    def handle(self, *args, **options):
        first_entry = get_object_or_None(AuditEntry, pk=1)

        if first_entry is not None:
            raise CommandError("The audit trail has already been started.")

        response = render_to_string('vote3fe/audit/init.txt', {})
        a = AuditEntry(entry=response)
        a.save()

        self.stdout.write(a.entry)
