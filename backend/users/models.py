from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from foodgram_backend.settings import (USER_EMAIL_MAX_LENGTH,
                                       USER_FIRST_NAME_MAX_LENGTH,
                                       USER_LAST_NAME_MAX_LENGTH,
                                       USER_PASSWORD_MAX_LENGTH,
                                       USER_USERNAME_MAX_LENGTH)

from .validators import validate_me


class User(AbstractUser):
    """ Модель пользователя. """

    email = models.EmailField(
        max_length=USER_EMAIL_MAX_LENGTH,
        unique=True,
        verbose_name='E-mail',
    )
    username = models.CharField(
        max_length=USER_USERNAME_MAX_LENGTH,
        unique=True,
        validators=(
            validate_me,
            RegexValidator(
                regex=r'^[\w.@+-]+\Z',
                message='В имени пользователя можно использовать'
                        ' только буквы, цифры и символы "@/./+/-/_"!',
            ),
        ),
        verbose_name='Имя пользователя',
    )
    first_name = models.CharField(
        max_length=USER_FIRST_NAME_MAX_LENGTH,
        verbose_name='Имя',
    )
    last_name = models.CharField(
        max_length=USER_LAST_NAME_MAX_LENGTH,
        verbose_name='Фамилия',
    )
    password = models.CharField(
        max_length=USER_PASSWORD_MAX_LENGTH,
        verbose_name='Пароль',
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = (
            'username',
        )

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """ Модель подписчика. """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followers',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followings',
        verbose_name='Автор публикации',
    )

    class Meta:
        verbose_name = 'Подписчик'
        verbose_name_plural = 'Подписчики'
        constraints = (
            models.UniqueConstraint(
                fields=(
                    'user',
                    'author'
                ),
                name='unique_subscription'
            ),
        )

    def __str__(self):
        return f'{self.user} подписан на {self.author}'
