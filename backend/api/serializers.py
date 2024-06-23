import base64

import requests
from django.core.files.base import ContentFile
from django.core.validators import MinValueValidator, MaxValueValidator
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import exceptions, serializers


from recipes.models import (
    Favorite, Ingredient, Recipe, RecipeIngredient,
    ShoppingCart, Tag
)
from users.models import Subscription, User
from foodgram_backend.settings import (
    USER_PASSWORD_MAX_LENGTH, RECIPE_MIN_VOL_VALIDATOR,
    RECIPE_ING_MIN_VOL_VALIDATOR, RECIPE_ING_MAX_VOL_VALIDATOR,
    RECIPE_NAME_MAX_LENGTH, RECIPE_MAX_VOL_VALIDATOR
)


class Base64ImageField(serializers.ImageField):
    """ Работа с изображением в формате base64. """

    def to_internal_value(self, data):
        if (
            isinstance(data, str)
            and data.startswith('data:image')
        ):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(
                base64.b64decode(imgstr),
                name='temp.' + ext
            )
        return super().to_internal_value(data)


class CustomUserSerializer(UserSerializer):
    """ Проверка подписки. """

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'first_name',
            'last_name', 'email', 'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request:
            return False
        if request.user.is_authenticated:
            return (
                Subscription.objects.filter(
                    author=obj.id, user=request.user
                ).exists()
            )
        return False


class CustomUserCreateSerializer(UserCreateSerializer):
    """ Создание пользователя. """

    password = serializers.CharField(
        max_length=USER_PASSWORD_MAX_LENGTH,
        write_only=True,
    )

    class Meta:
        model = User
        fields = (
            'id', 'username', 'first_name', 'last_name',
            'email', 'password',
        )


class LimitRecipeSerializer(serializers.ModelSerializer):
    """ Сериализатор для сокращения рецепта! """

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'image', 'cooking_time'
        )


class FavoriteCartSerializer(serializers.Serializer):
    """ Добавление рецепта в покупки/избранное! """

    def validate(self, data):
        name = self.context['action_name']
        user = self.context['user']
        recipe_pk = self.context['recipe_id']
        model = self.context['cur_model']

        if Recipe.objects.filter(id=recipe_pk).exists():
            recipe = get_object_or_404(
                Recipe, id=recipe_pk
            )
        else:
            raise serializers.ValidationError(
                f'Нельзя добавить несуществующий '
                f'в базе рецепт в {name}'
            )
        relation = model.objects.filter(
            user=user, recipe=recipe.pk
        ).exists()
        if relation:
            raise serializers.ValidationError(
                f'Рецепт уже в {name}'
            )
        model.objects.create(user=user, recipe=recipe)
        serializer = LimitRecipeSerializer(recipe)
        return serializer.data


class SubscriptionSerializer(CustomUserSerializer):
    """ Работа с подпиской. """

    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'first_name', 'last_name',
            'email', 'is_subscribed', 'recipes',
            'recipes_count',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        user = self.context.get('request').user
        if not request or not user.is_authenticated:
            return False
        return obj.followers.filter(user=user).exists()

    def get_recipes(self, obj):
        """ Получение списка рецептов автора.

            Лимит отображения рецептов, если указан параметр
            recipes_limit в запросе.
        """

        query_params = self.context.get('request').query_params
        if 'recipes_limit' in query_params:
            limit = int(query_params.get('recipes_limit'))
            author_recipes = obj.recipes.all()[:limit]
        else:
            author_recipes = obj.recipes.all()
        if author_recipes:
            serializer = LimitRecipeSerializer(
                author_recipes,
                context={'request': self.context.get('request')},
                many=True,
            )
            return serializer.data
        return []

    def get_recipes_count(self, obj):
        """ Получаем количество рецептов автора. """

        return Recipe.objects.filter(
            author=obj.id
        ).count()


class SubscribeSerializer(serializers.ModelSerializer):
    """ Добавление/удаление подписок. """

    class Meta:
        model = Subscription
        fields = '__all__'

    def validate(self, data):
        user = data['user']
        author = data['author']
        if user == author:
            raise serializers.ValidationError(
                'Нельзя подписаться на себя!'
            )
        if Subscription.objects.filter(
                user=user, author=author
        ).exists():
            raise serializers.ValidationError(
                'Подписка уже оформлена!'
            )
        return data

    def to_representation(self, instance):
        request = self.context.get('request')
        return SubscriptionSerializer(
            instance.author, context={'request': request}
        ).data


class TagSerializer(serializers.ModelSerializer):
    """ Работа с тегами. """

    class Meta:
        model = Tag
        fields = (
            'id', 'name', 'color', 'slug',
        )


class IngredientSerializer(serializers.ModelSerializer):
    """ Работа с ингредиентами."""

    class Meta:
        model = Ingredient
        fields = (
            'id', 'name', 'measurement_unit',
        )


class RecipeIngredientsSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(
        source='ingredient.id'
    )
    name = serializers.ReadOnlyField(
        source='ingredient.name'
    )
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = (
            'id', 'name', 'measurement_unit', 'amount'
        )


class CreateUpdateRecipeIngredientsSerializer(serializers.ModelSerializer):
    """ Добавление/обновление ингредиентов при создании/изменении
        рецепта.
    """

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(
        validators=(
            MinValueValidator(
                RECIPE_MIN_VOL_VALIDATOR,
                message=f'Количество ингредиента не может быть '
                        f'меньше {RECIPE_ING_MIN_VOL_VALIDATOR}.'
            ),
            MaxValueValidator(
                RECIPE_ING_MAX_VOL_VALIDATOR,
                message=f'Количество ингредиента не может быть '
                        f'больше {RECIPE_ING_MAX_VOL_VALIDATOR}.'
            ),
        )
    )

    class Meta:
        model = Ingredient
        fields = (
            'id', 'amount'
        )


class RecipeSerializer(serializers.ModelSerializer):
    """ Работа с рецептами. """

    author = CustomUserSerializer(
        read_only=True
    )
    tags = TagSerializer(
        many=True,
    )
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    def get_ingredients(self, obj):
        ingredients = RecipeIngredient.objects.filter(
            recipe=obj
        )
        serializer = RecipeIngredientsSerializer(
            ingredients,
            many=True
        )
        return serializer.data

    def get_is_favorited(self, obj):
        """ Проверка наличия рецепта в избранных. """

        user = self.context.get('request').user.id
        return Favorite.objects.filter(
            user=user,
            recipe=obj.id
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        """ Проверка наличия рецепта в списке покупок. """

        user = self.context.get('request').user.id
        return ShoppingCart.objects.filter(
            user=user,
            recipe=obj.id
        ).exists()

    class Meta:
        model = Recipe
        exclude = ('pub_date',)


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """ Добавление/обновление рецепта. """

    name = serializers.CharField(
        max_length=RECIPE_NAME_MAX_LENGTH,
    )
    author = CustomUserSerializer(
        read_only=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    ingredients = CreateUpdateRecipeIngredientsSerializer(
        many=True,
    )
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(
        validators=(
            MinValueValidator(
                RECIPE_MIN_VOL_VALIDATOR,
                message=f'Время приготовления должно быть '
                        f'не меньше {RECIPE_MIN_VOL_VALIDATOR} минуты!'
            ),
            MaxValueValidator(
                RECIPE_MAX_VOL_VALIDATOR,
                message=f'Время приготовления должно быть '
                        f'не больше {RECIPE_MAX_VOL_VALIDATOR} минут!'
            ),
        )
    )

    def validate_tags(self, data):
        """ Проверяем наличие тегов в запросе.

            Проверка наличия. Проверка на дубли.
        """

        if not data:
            raise exceptions.ValidationError(
                'Добавьте хотя бы один тег!'
            )
        if len(data) > len(set(data)):
            raise exceptions.ValidationError(
                'Рецепт не может содержать два одинаковых тега!'
            )
        return data

    def validate_ingredients(self, data):
        """ Проверяем наличие ингредиентов в запросе.

            Проверка наличия. Проверка на дубли.
        """

        if not data:
            raise exceptions.ValidationError(
                'Добавьте хотя бы один ингредиент!'
            )
        ingredients = [item['id'] for item in data]
        if len(ingredients) > len(set(ingredients)):
            raise exceptions.ValidationError(
                'Рецепт не может содержать два одинаковых ингредиента!'
            )
        return data

    def create(self, validated_data):
        """ Создаем рецепт. """

        author = self.context.get('request').user
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(
            author=author,
            **validated_data
        )
        recipe.tags.set(tags)
        ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            ) for ingredient in ingredients
        ]
        RecipeIngredient.objects.bulk_create(ingredients)
        return recipe

    def update(self, instance, validated_data):
        """ Обновляем рецепт. """

        if 'tags' not in validated_data:
            raise exceptions.ValidationError(
                'Добавьте хотя бы один тег!'
            )
        tags = validated_data.pop('tags', None)
        if tags is None:
            instance.tags.set(tags)
        ingredients = validated_data.pop('ingredients', None)
        if ingredients is None:
            raise exceptions.ValidationError(
                'Добавьте хотя бы один ингредиент!'
            )
        instance.ingredients.clear()
        for ingredient in ingredients:
            amount = ingredient.get('amount')
            ingredient = get_object_or_404(
                Ingredient,
                pk=ingredient.get('id').id
            )
            RecipeIngredient.objects.update_or_create(
                recipe=instance,
                ingredient=ingredient,
                defaults={'amount': amount},
            )
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        serializer = RecipeSerializer(
            instance,
            context={
                'request': self.context.get('request')
            }
        )
        return serializer.data

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'name', 'image', 'text', 'cooking_time',
        )
