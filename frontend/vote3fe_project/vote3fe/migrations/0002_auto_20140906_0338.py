# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vote3fe', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='candidate',
            name='elections',
        ),
        migrations.AddField(
            model_name='election',
            name='elections',
            field=models.ManyToManyField(to='vote3fe.Candidate', through='vote3fe.BallotEntry'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='election',
            name='notes',
            field=models.CharField(max_length=3000, blank=True),
        ),
    ]
