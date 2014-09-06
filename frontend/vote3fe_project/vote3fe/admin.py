from django.contrib import admin
from vote3fe.models import Election, Candidate, Vote, VoteCode, BallotEntry

class BallotEntryInline(admin.StackedInline):
    model = BallotEntry
    extra = 3

class ElectionAdmin(admin.ModelAdmin):
    inlines = (BallotEntryInline,
               )
    
admin.site.register(Election, ElectionAdmin)
admin.site.register(Candidate)
admin.site.register(Vote)
admin.site.register(VoteCode)
