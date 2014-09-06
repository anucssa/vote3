# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import vote3fe.models


class Migration(migrations.Migration):

    dependencies = [
        ('vote3fe', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='votecode',
            name='vote_code',
            field=models.CharField(default=vote3fe.models.VoteCode.generate_vote_code, max_length=22, unique=True),
        ),
    ]
