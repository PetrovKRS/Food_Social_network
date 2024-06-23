from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny, IsAuthenticated,
    IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response

from recipes.models import (
    Favorite, Ingredient, Recipe, RecipeIngredient,
    ShoppingCart, Tag,
)
from users.models import Subscription, User

from .filters import IngredientFilter, RecipeFilter, UserFilter
from .pagination import LimitPagination
from .permissions import IsAdminAuthorOrReadOnly
from .serializers import (
    IngredientSerializer,
    RecipeCreateUpdateSerializer, RecipeSerializer,
    SubscriptionSerializer, TagSerializer, SubscribeSerializer,
    CustomUserSerializer, FavoriteCartSerializer,
)
from .mixins import CheckIntOrStrMixin
from .utils import shopping_cart_to_pdf


class CustomUserViewSet(UserViewSet, CheckIntOrStrMixin):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = UserFilter

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
    )
    def me(self, request):
        """ Запрос пользователя к me. """
        user = self.request.user
        serializer = CustomUserSerializer(user)
        return Response(
            serializer.data, status=status.HTTP_200_OK
        )

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
        url_path='subscriptions'
    )
    def subscriptions(self, request):
        """ Список авторов, на которых подписан пользователь. """

        user = self.request.user
        queryset = User.objects.filter(followings__user=user)
        pages = self.paginate_queryset(
            queryset
        )
        serializer = SubscriptionSerializer(
            pages, many=True,
            context={'request': request}
        )
        return self.get_paginated_response(
            serializer.data
        )

    @action(
        detail=True,
        methods=('post', 'delete'),
    )
    def subscribe(self, request, id=None):
        """ Подписка на автора.

            Добавление/удаление подписки.
        """

        if not self.validate_pk(id):
            return Response(
                {'detail': 'Страница не найдена.'},
                status=status.HTTP_404_NOT_FOUND
            )

        user = self.request.user
        author = get_object_or_404(
            User, id=id
        )

        if self.request.method == 'POST':
            serializer = SubscribeSerializer(
                data={
                    'user': request.user.id,
                    'author': author.id
                },
                context={'request': request}

            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                serializer.data, status=status.HTTP_201_CREATED
            )
        if not Subscription.objects.filter(
            user=user, author=author
        ).exists():
            return Response(
                {'errors': 'Вы уже отписаны!'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        subscription = get_object_or_404(
            Subscription, user=user, author=author
        )
        subscription.delete()
        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet, CheckIntOrStrMixin):
    queryset = Recipe.objects.all().order_by('-pub_date')
    permission_classes = (IsAdminAuthorOrReadOnly,)
    pagination_class = LimitPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeSerializer
        return RecipeCreateUpdateSerializer

    def add_recipe_to_fav_cart(self, model, user, pk, name):
        """ Добавление рецепта. """

        serializer = FavoriteCartSerializer(
            data=self.request.data,
            context={
                'request': self.request, 'recipe_id': pk,
                'cur_model': model, 'user': user,
                'action_name': name,
            },
        )
        if serializer.is_valid(raise_exception=True):
            return Response(
                serializer.validated_data, status=status.HTTP_201_CREATED
            )

    def delete_recipe_from_fav_cart(self, model, user, pk, name):
        """ Удаление рецепта из списка пользователя. """

        if Recipe.objects.filter(id=pk).exists():
            recipe = get_object_or_404(
                Recipe, id=pk
            )
        else:
            return Response(
                status=status.HTTP_404_NOT_FOUND
            )
        relation = model.objects.filter(
            user=user, recipe=recipe
        ).exists()
        if not relation:
            return Response(
                {
                    'errors': f'Нельзя повторно удалить рецепт '
                              f'из {name}'
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        relation = model.objects.filter(
            user=user, recipe=recipe
        )
        relation.delete()
        return Response(
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        detail=True,
        methods=('post', 'delete'),
        url_path='favorite',
        url_name='favorite',
    )
    def favorite(self, request, pk=None):
        """ Добавление и удаление рецептов из избранного. """

        if not self.validate_pk(pk):
            return Response(
                status=status.HTTP_400_BAD_REQUEST
            )
        user = request.user
        if request.method == 'POST':
            name = 'избранном'
            return self.add_recipe_to_fav_cart(
                Favorite, user, pk, name
            )
        name = 'избранного'
        return self.delete_recipe_from_fav_cart(
            Favorite, user, pk, name
        )

    @action(
        detail=True,
        methods=('post', 'delete'),
        url_path='shopping_cart',
        url_name='shopping_cart',
    )
    def shopping_cart(self, request, pk=None):
        """ Добавление и удаление рецепта в
            список покупок.
        """

        if not self.validate_pk(pk):
            return Response(
                status=status.HTTP_400_BAD_REQUEST
            )
        user = request.user
        if request.method == 'POST':
            name = 'список покупок'
            return self.add_recipe_to_fav_cart(
                ShoppingCart, user, pk, name
            )
        name = 'списка покупок'
        return self.delete_recipe_from_fav_cart(
            ShoppingCart, user, pk, name
        )

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
        url_path='download_shopping_cart',
        url_name='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        """ Отдача пользователю списка покупок в формате pdf. """

        shopping_cart = ShoppingCart.objects.filter(
            user=self.request.user
        )
        recipes = [item.recipe.id for item in shopping_cart]
        cart = (
            RecipeIngredient.objects.filter(
                recipe__in=recipes
            ).values('ingredient').annotate(
                amount=Sum('amount')
            )
        )
        response = HttpResponse(content_type='application/pdf')
        response[
            'Content-Disposition'
        ] = 'attachment; filename="ShoppingCart.pdf"'
        shopping_cart_to_pdf(response, cart)
        return response
