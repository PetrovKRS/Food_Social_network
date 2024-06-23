from django_filters.rest_framework import FilterSet, filters

from recipes.models import Ingredient, Recipe
from users.models import User
from .mixins import CheckIntOrStrMixin


class UserFilter(FilterSet):
    limit = filters.CharFilter(
        method='get_users_limit'
    )

    class Meta:
        model = User
        fields = '__all__'

    def get_users_limit(self, queryset, name, value):
        query_params = self.request.query_params
        if 'limit' in query_params:
            limit = int(query_params.get('limit'))
            return User.objects.all()[:limit]


class IngredientFilter(FilterSet):
    name = filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith',
    )

    class Meta:
        model = Ingredient
        fields = (
            'name',
        )


class RecipeFilter(FilterSet, CheckIntOrStrMixin):
    """Фильтрация по избранному, автору, списку покупок и тегам."""

    author = filters.CharFilter(
        method='get_author',
        field_name='author',
    )
    tags = filters.CharFilter(
        method='get_tags',
    )
    is_favorited = filters.BooleanFilter(
        method='get_is_favorite',
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='get_is_in_shopping_cart',
    )

    class Meta:
        model = Recipe
        fields = (
            'tags',
            'author',
        )

    def get_author(self, queryset, name, value):
        if (
            self.validate_pk(value)
            and User.objects.filter(id=value).exists()
        ):
            return Recipe.objects.filter(author=value)
        return queryset.none()

    def get_tags(self, queryset, name, value):
        if value:
            tags = self.request.query_params.getlist('tags')
            return queryset.filter(tags__slug__in=tags).distinct()
        return queryset

    def get_is_favorite(self, queryset, name, value):
        user = self.request.user
        if (
            (user.is_authenticated and value)
            or not value
        ):
            return Recipe.objects.filter(
                favorite__user=user.pk
            )
        return queryset.none()

    def get_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if (
            (user.is_authenticated and value)
            or not value
        ):
            return Recipe.objects.filter(
                shopping_list__user=user.pk
            )
        return queryset.none()
