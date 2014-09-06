import os
from base64 import b64encode
from django.db import models

class Candidate(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Election(models.Model):
    name = models.CharField(max_length=50, unique=True)
    notes = models.CharField(max_length=3000, blank=True)
    candidates = models.ManyToManyField(Candidate, through='BallotEntry')
    def __str__(self):
        return self.name


class BallotEntry(models.Model):
    election = models.ForeignKey(Election)
    candidate = models.ForeignKey(Candidate)
    position = models.IntegerField()

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
