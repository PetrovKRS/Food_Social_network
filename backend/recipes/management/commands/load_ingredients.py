import csv

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загрузка ингредиентов из csv файла!'

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, help='Путь к файлу')

    def handle(self, *args, **options):
        print('Загрузка данных ...')
        file_path = 'data/ingredients.csv'
        with open(file_path, 'rt', encoding='utf-8') as csv_file:
            reader = csv.reader(csv_file, delimiter=',')
            for row in reader:
                name_csv = 0
                measurement_unit_csv = 1
                try:
                    obj, created = Ingredient.objects.get_or_create(
                        name=row[name_csv],
                        measurement_unit=row[measurement_unit_csv],
                    )
                    if not created:
                        print(f"Ингредиент {obj} уже существует!")
                except Exception as err:
                    print(f"NB Ошибка в строке {row}: {err}")
        print('Загрузка ИНГРЕДИЕНТОВ в БД завершена!!!')
