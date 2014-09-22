# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vote3fe', '0003_auditentry'),
    ]

    operations = [
        migrations.AddField(
            model_name='election',
            name='isOpen',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
