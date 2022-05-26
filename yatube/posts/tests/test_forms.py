import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.forms import PostForm
from posts.models import Comment, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовый текст',
            description='Тестовое описание',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Модуль shutil - библиотека Python с удобными инструментами
        # для управления файлами и директориями:
        # создание, удаление, копирование, изменение папок и файлов
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        # Подсчитаем количество записей в Post
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст 2',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': self.post.author.username}
            )
        )
        # Получаем последний пост из БД и проверяем его
        post = Post.objects.latest("pub_date")
        post_data = {
            post.text: form_data["text"],
            post.group.pk: form_data["group"],
            post.image: 'posts/small.gif',
        }
        for value, expectation in post_data.items():
            with self.subTest(value=value):
                self.assertEqual(value, expectation)
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count + 1)
        # Проверяем, что создалась запись с нашим с текстом
        self.assertTrue(Post.objects.filter(
            text=form_data['text'],
            group=form_data['group'],
            image='posts/small.gif',
        ).exists())

    def test_post_edit(self):
        """Валидная форма создает запись в Post."""
        # Подсчитаем количество записей в Post
        posts_count = Post.objects.count()
        small_gif_2 = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small_2.gif',
            content=small_gif_2,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст 3',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )

        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count)
        # Проверяем, что изменилась запись на новый текст
        self.assertTrue(Post.objects.filter(
            text=form_data['text'],
            group=form_data['group'],
            image='posts/small_2.gif',
        ).exists())

    def test_add_comment(self):
        """Валидная форма создает запись в Comment."""
        # Подсчитаем количество записей в Comment
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий 2',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            )
        )
        # Получаем последний пост из БД и проверяем его
        cmmnt = Comment.objects.latest("id")
        cmmnt_data = {
            cmmnt.text: form_data["text"],
        }
        for value, expectation in cmmnt_data.items():
            with self.subTest(value=value):
                self.assertEqual(value, expectation)
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        # Проверяем, что создалась запись с нашим с текстом
        self.assertTrue(Comment.objects.filter(
            text=form_data['text'],
        ).exists())

    def test_title_label(self):
        title_label = PostCreateFormTests.form.fields['text'].label
        self.assertEqual(title_label, "Текст поста")
        title_label = PostCreateFormTests.form.fields['group'].label
        self.assertEqual(title_label, "Группа")

    def test_title_help_text(self):
        title_help_text = PostCreateFormTests.form.fields['text'].help_text
        self.assertEqual(title_help_text, "Текст нового поста")
        title_help_text = PostCreateFormTests.form.fields['group'].help_text
        self.assertEqual(
            title_help_text,
            "Группа, к которой будет относиться пост"
        )
