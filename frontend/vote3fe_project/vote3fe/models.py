import os
from base64 import b64encode
from django.db import models
from django.template.loader import render_to_string
import hashlib
from django.conf import settings
import gpgme
from io import BytesIO

class Candidate(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def save(self, *args, **kwargs):
        super(Candidate, self).save(*args, **kwargs)
        entry = render_to_string('vote3fe/audit/candidate_saved.txt',
                                 {'candidate': self,
                                  'hash': AuditEntry.next_hash(),
                                 })
        AuditEntry.objects.create(entry=entry)

    def delete(self, *args, **kwargs):
        entry = render_to_string('vote3fe/audit/candidate_deleted.txt',
                                 {'candidate': self,
                                  'hash': AuditEntry.next_hash(),
                                 })
        AuditEntry.objects.create(entry=entry)
        super(Candidate, self).delete(*args, **kwargs)

    def __str__(self):
        return self.name


class Election(models.Model):
    name = models.CharField(max_length=50, unique=True)
    isOpen = models.BooleanField(default=False)
    notes = models.CharField(max_length=3000, blank=True)
    candidates = models.ManyToManyField(Candidate, through='BallotEntry')
    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super(Election, self).save(*args, **kwargs)
        # save an audit trail entry
        entry = render_to_string('vote3fe/audit/election_saved.txt',
                                 {'election': self,
                                  'hash': AuditEntry.next_hash(),
                                 })
        AuditEntry.objects.create(entry=entry)

    def delete(self, *args, **kwargs):
        entry = render_to_string('vote3fe/audit/election_deleted.txt',
                                 {'election': self,
                                  'hash': AuditEntry.next_hash(),
                                 })
        AuditEntry.objects.create(entry=entry)
        super(Election, self).delete(*args, **kwargs)


class BallotEntry(models.Model):
    election = models.ForeignKey(Election)
    candidate = models.ForeignKey(Candidate)
    position = models.IntegerField()

    def save(self, *args, **kwargs):
        super(BallotEntry, self).save(*args, **kwargs)
        entry = render_to_string('vote3fe/audit/ballotentry_saved.txt',
                                 {'ballotentry': self,
                                  'election': self.election,
                                  'hash': AuditEntry.next_hash(),
                                 })
        AuditEntry.objects.create(entry=entry)

    def delete(self, *args, **kwargs):
        entry = render_to_string('vote3fe/audit/ballotentry_deleted.txt',
                                 {'ballotentry': self,
                                  'election': self.election,
                                  'hash': AuditEntry.next_hash(),
                                 })
        AuditEntry.objects.create(entry=entry)
        super(BallotEntry, self).delete(*args, **kwargs)


    class Meta:
        unique_together = (('election', 'candidate'),
                           ('election', 'position'),
                           )
        verbose_name_plural = 'Ballot Entries'


class Vote(models.Model):
    election = models.ForeignKey(Election)


class Preference(models.Model):
    vote = models.ForeignKey(Vote)
    candidate = models.ForeignKey(Candidate)
    preference = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = (('vote', 'candidate'),
                           )


# our use only
class VoteCode(models.Model):
    def generate_vote_code():
        return b64encode(os.urandom(16))[0:22]

    vote_code = models.CharField(max_length=22, unique=True,
                                default=generate_vote_code)
    elections = models.ManyToManyField(Election, through='ElectionVoteCode') 


class ElectionVoteCode(models.Model):
    election = models.ForeignKey(Election)
    vote_code = models.ForeignKey(VoteCode)
    used = models.BooleanField(default=False)

    class Meta:
        unique_together = (('election', 'vote_code'),
                           )

# audit trail!
class AuditEntry(models.Model):
    entry = models.TextField()

    def hash(self):
        return hashlib.sha384(self.entry.encode('UTF-8')).hexdigest()

    def next_hash():
        return AuditEntry.objects.last().hash()

    def sign(msg):
        ctx = gpgme.Context()
        key = ctx.get_key(settings.VOTE3_SIGNING_KEY)
        ctx.armor = True
        ctx.signers = [key]

        plaintext = BytesIO(msg.encode('UTF-8'))
        signature = BytesIO()

        ctx.sign(plaintext, signature, gpgme.SIG_MODE_CLEAR)

        signature.seek(0)

        signedentry = signature.read().decode('UTF-8')

        return signedentry
    
    def save(self, *args, **kwargs):
        # this is *deliberately* not idempotent. There's no reason a
        # audit entry should be resaved.

        
        self.entry = AuditEntry.sign(self.entry)

        super(AuditEntry, self).save(*args, **kwargs)

