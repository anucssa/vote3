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
class Votecode(models.Model):
    def generate_votecode():
        return b64encode(os.urandom(16))

    votecode = models.CharField(max_length=24, unique=True,
                                default=generate_votecode)
    elections = models.ManyToManyField(Election, through='ElectionVotecode') 


class ElectionVotecode(models.Model):
    election = models.ForeignKey(Election)
    votecode = models.ForeignKey(Votecode)
    used = models.BooleanField(default=False)

    class Meta:
        unique_together = (('election', 'votecode'),
                           )
