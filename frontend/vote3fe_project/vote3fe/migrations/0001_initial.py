# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import vote3fe.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BallotEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('position', models.IntegerField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Candidate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('name', models.CharField(max_length=50, unique=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Election',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('name', models.CharField(max_length=50, unique=True)),
                ('notes', models.CharField(max_length=3000)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ElectionVotecode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('used', models.BooleanField(default=False)),
                ('election', models.ForeignKey(to='vote3fe.Election')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Preference',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('preference', models.IntegerField(blank=True, null=True)),
                ('candidate', models.ForeignKey(to='vote3fe.Candidate')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Vote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('election', models.ForeignKey(to='vote3fe.Election')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Votecode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('votecode', models.CharField(max_length=24, default=vote3fe.models.Votecode.generate_votecode, unique=True)),
                ('elections', models.ManyToManyField(to='vote3fe.Election', through='vote3fe.ElectionVotecode')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='preference',
            name='vote',
            field=models.ForeignKey(to='vote3fe.Vote'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='preference',
            unique_together=set([('vote', 'candidate')]),
        ),
        migrations.AddField(
            model_name='electionvotecode',
            name='votecode',
            field=models.ForeignKey(to='vote3fe.Votecode'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='electionvotecode',
            unique_together=set([('election', 'votecode')]),
        ),
        migrations.AddField(
            model_name='candidate',
            name='elections',
            field=models.ManyToManyField(to='vote3fe.Election', through='vote3fe.BallotEntry'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='ballotentry',
            name='candidate',
            field=models.ForeignKey(to='vote3fe.Candidate'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='ballotentry',
            name='election',
            field=models.ForeignKey(to='vote3fe.Election'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='ballotentry',
            unique_together=set([('election', 'candidate'), ('election', 'position')]),
        ),
    ]
