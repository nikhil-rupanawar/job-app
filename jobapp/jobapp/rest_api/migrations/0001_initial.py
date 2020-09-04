# Generated by Django 3.1.1 on 2020-09-03 15:08

from django.conf import settings
import django.contrib.auth.models
import django.contrib.auth.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import jobapp.jobapp.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Groupset',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('groups', models.ManyToManyField(to='auth.Group')),
                ('users', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='GroupsetJob',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_status', models.IntegerField(null=True)),
                ('_ui_status', models.CharField(choices=[('Pending', 'Pending'), ('Acknowledged', 'Request Ack'), ('Running', 'Running'), ('Failed', 'Failed'), ('Errored', 'Errored'), ('Success', 'Success'), ('Success with warning(s)', 'Success With Warning'), ('Cancel requested', 'Cancel Requested'), ('Canceled', 'Canceled')], max_length=255)),
                ('_data', models.JSONField(null=True)),
                ('type', models.IntegerField(null=True)),
                ('created_by', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
                ('ttl', models.IntegerField(default=259200)),
                ('_progress_total_units', models.IntegerField(default=0)),
                ('_progress_done_units', models.IntegerField(default=0)),
                ('_progress_percent', models.IntegerField(null=True)),
                ('groupset', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='rest_api.groupset')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, jobapp.jobapp.models.StepDiagnosticJobMixin),
        ),
        migrations.CreateModel(
            name='GroupsetJobDiagnostic',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('severity', models.IntegerField(default=1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('details', models.JSONField(null=True)),
                ('stage', models.CharField(blank=True, max_length=50, null=True)),
                ('step', models.CharField(blank=True, max_length=50, null=True)),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='diagnostics', to='rest_api.groupsetjob')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CreateGroupsetJob',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('rest_api.groupsetjob',),
        ),
        migrations.CreateModel(
            name='DeleteGroupsetJob',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('rest_api.groupsetjob',),
        ),
        migrations.CreateModel(
            name='UpdateGroupsetJob',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('rest_api.groupsetjob',),
        ),
    ]
