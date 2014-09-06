# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vote3fe', '0002_auto_20140906_0338'),
    ]

    operations = [
        migrations.RenameField(
            model_name='election',
            old_name='elections',
            new_name='candidates',
        ),
    ]
