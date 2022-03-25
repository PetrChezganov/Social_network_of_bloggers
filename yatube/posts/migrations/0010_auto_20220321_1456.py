# Generated by Django 2.2.16 on 2022-03-21 11:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0009_profile'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='avatar',
            field=models.ImageField(blank=True, help_text='Аватарка пользователя', null=True, upload_to='img/avatars/', verbose_name='Аватарка'),
        ),
    ]