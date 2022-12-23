from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()
LEN_POST_TEXT = 15


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(
        'Текст поста',
        help_text='Введите текст поста'
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        # добавлено недавно
        related_name='posts',
        verbose_name='Автор',
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        related_name="posts",
        blank=True,
        null=True,
        # добавлено недавно
        verbose_name='Группа',
        help_text='Выберите группу'
    )
    # Поле для картинки (необязательное)
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )
    # Аргумент upload_to указывает директорию,
    # в которую будут загружаться пользовательские файлы.

    class Meta:
        ordering = ['-pub_date']
        # добавлено недавно
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return self.text[:LEN_POST_TEXT]


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    text = models.TextField(
        'Текст',
        help_text='Текст нового комментария'
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return self.text[:LEN_POST_TEXT]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Пользователь',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'user'],
                name='unique follow'
            ),
            models.CheckConstraint(
                check=~models.Q(author=models.F('user')),
                name='author_not_user'
            ),
        ]

    def __str__(self):
        return f'{self.user.username} подписался на {self.author.username}'
