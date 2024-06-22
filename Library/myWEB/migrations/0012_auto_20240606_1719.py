# Generated by Django 3.2.25 on 2024-06-06 09:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('myWEB', '0011_auto_20200612_1455'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dztable',
            name='psw',
            field=models.CharField(max_length=256),
        ),
        migrations.AlterField(
            model_name='jstable',
            name='dzid',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='myWEB.dztable'),
        ),
        migrations.AlterField(
            model_name='jstable',
            name='tsid',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='myWEB.tstable'),
        ),
        migrations.AlterField(
            model_name='tsglytable',
            name='psw',
            field=models.CharField(max_length=256),
        ),
    ]
