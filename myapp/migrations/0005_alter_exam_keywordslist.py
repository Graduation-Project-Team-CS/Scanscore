# Generated by Django 5.0.4 on 2024-05-01 09:04

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("myapp", "0004_alter_exam_keywordslist"),
    ]

    operations = [
        migrations.AlterField(
            model_name="exam",
            name="keywordsList",
            field=models.TextField(blank=True, max_length=10000, null=True),
        ),
    ]
