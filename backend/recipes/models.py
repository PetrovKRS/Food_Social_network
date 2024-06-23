from django.core.validators import (
    MinValueValidator, RegexValidator,
    MaxValueValidator,
)
from django.db import models

from foodgram_backend.settings import (
    ING_MEASUREMENT_UNIT_MAX_LENGTH,
    ING_NAME_MAX_LENGTH,
    RECIPE_ING_MIN_VOL_VALIDATOR,
    RECIPE_MIN_VOL_VALIDATOR,
    RECIPE_MAX_VOL_VALIDATOR,
    RECIPE_NAME_MAX_LENGTH,
    TAG_COLOR_MAX_LENGTH,
    TAG_NAME_MAX_LENGTH,
    TAG_SLUG_MAX_LENGTH,
    RECIPE_ING_MAX_VOL_VALIDATOR,
)

from users.models import User


class Tag(models.Model):
    """ Модель тега. """

    name = models.CharField(
        max_length=TAG_NAME_MAX_LENGTH,
        unique=True,
        verbose_name='Наименование тега',
    )
    color = models.CharField(
        max_length=TAG_COLOR_MAX_LENGTH,
        unique=True,
        verbose_name='Цвет в HEX формате',
        validators=(
            RegexValidator(
                regex=r'#[A-F0-9]{6}',
                message='Цвет в HEX формате пример: "#000FFF".',
            ),
        ),
    )
    slug = models.SlugField(
        max_length=TAG_SLUG_MAX_LENGTH,
        unique=True,
        validators=(
            RegexValidator(
                regex=r'^[-a-zA-Z0-9_]+$',
                message='Недопустимые символы в идентификаторе!!!',
            ),
        ),
        verbose_name='Уникальный идентификатор тега',
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """ Модель ингредиента. """

    name = models.CharField(
        max_length=ING_NAME_MAX_LENGTH,
        verbose_name='Наименование ингредиента',
    )
    measurement_unit = models.CharField(
        max_length=ING_MEASUREMENT_UNIT_MAX_LENGTH,
        verbose_name='Единицы измерения',
    )

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_ingredient',
            ),
        )

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """ Модель рецепта. """

    name = models.CharField(
        max_length=RECIPE_NAME_MAX_LENGTH,
        verbose_name='Название блюда',
    )
    text = models.TextField(
        verbose_name='Описание блюда',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Список ингредиентов',
    )
    cooking_time = models.PositiveIntegerField(
        validators=(
            MinValueValidator(
                RECIPE_MIN_VOL_VALIDATOR,
                message='Время приготовления должно быть '
                        'не меньше минуты!'
            ),
            MaxValueValidator(
                RECIPE_MAX_VOL_VALIDATOR,
                message=f'Время приготовления должно быть '
                        f'не больше {RECIPE_MAX_VOL_VALIDATOR} минут!'
            ),
        ),
        verbose_name='Время приготовления (в минутах)',
    )
    image = models.ImageField(
        upload_to='recipes/',
        verbose_name='Изображение блюда',
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Дата публикации'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта',
    )
    tags = models.ManyToManyField(
        Tag,
        through="RecipeTags",
        related_name="recipes",
        verbose_name="Теги рецепта",
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = (
            '-pub_date',
        )

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """ Модель ингредиента для рецепта. """

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
    )
    amount = models.PositiveIntegerField(
        validators=(
            MinValueValidator(
                RECIPE_ING_MIN_VOL_VALIDATOR,
                message='Количество ингредиента не может быть'
                        f'меньше {RECIPE_ING_MIN_VOL_VALIDATOR}!'
            ),
            MaxValueValidator(
                RECIPE_ING_MAX_VOL_VALIDATOR,
                message='Количество ингредиента не может быть'
                        f'меньше {RECIPE_ING_MAX_VOL_VALIDATOR}!'
            ),
        ),
        verbose_name='Количество ингредиента',
    )

    class Meta:
        verbose_name = 'Ингредиент для рецепта'
        verbose_name_plural = 'Ингредиенты для рецепта'

    def __str__(self):
        return f'{self.ingredient} - {self.amount}'


class RecipeTags(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        verbose_name='Тег'
    )

    class Meta:
        verbose_name = 'Теги'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return f'{self.recipe} - {self.tag}'


class ShoppingCart(models.Model):
    """ Модель списка покупок """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_list',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_list',
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = (
            models.UniqueConstraint(
                fields=(
                    'user',
                    'recipe'
                ),
                name='unique_shopping_list_recipe'
            ),
        )

    def __str__(self):
        return f'{self.user} добавил {self.recipe}'


class Favorite(models.Model):
    """ Модель избранного. """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite',
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = (
            models.UniqueConstraint(
                fields=(
                    'user',
                    'recipe'
                ),
                name='unique_favorite_recipe'
            ),
        )

    def __str__(self):
        return f'{self.user} добавил {self.recipe}'
