import csv

from django.core.management.base import BaseCommand

from recipes.models import Tag


class Command(BaseCommand):
    help = 'Загрузка тегов из csv файла!'

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, help='Путь к файлу')

    def handle(self, *args, **options):
        print('Загрузка данных ...')
        file_path = 'data/tags.csv'
        with open(file_path, 'rt', encoding='utf-8') as csv_file:
            reader = csv.reader(csv_file, delimiter=',')
            for row in reader:
                name_csv = 0
                color_csv = 1
                slug_csv = 2
                try:
                    obj, created = Tag.objects.get_or_create(
                        name=row[name_csv],
                        color=row[color_csv],
                        slug=row[slug_csv],
                    )
                    if not created:
                        print(f"Тег {obj} уже существует!")
                except Exception as err:
                    print(f"NB Ошибка в строке {row}: {err}")
        print('Загрузка ТЕГОВ в БД завершена!!!')
