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
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('position', models.IntegerField()),
            ],
            options={
                'verbose_name_plural': 'Ballot Entries',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Candidate',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(unique=True, max_length=50)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Election',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(unique=True, max_length=50)),
                ('notes', models.CharField(blank=True, max_length=3000)),
                ('candidates', models.ManyToManyField(through='vote3fe.BallotEntry', to='vote3fe.Candidate')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ElectionVoteCode',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
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
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
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
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('election', models.ForeignKey(to='vote3fe.Election')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='VoteCode',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('vote_code', models.CharField(default=vote3fe.models.VoteCode.generate_vote_code, unique=True, max_length=24)),
                ('elections', models.ManyToManyField(through='vote3fe.ElectionVoteCode', to='vote3fe.Election')),
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
            name='vote_code',
            field=models.ForeignKey(to='vote3fe.VoteCode'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='electionvotecode',
            unique_together=set([('election', 'vote_code')]),
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
